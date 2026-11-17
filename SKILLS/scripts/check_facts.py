#!/usr/bin/env python3
"""事实卡 × 卖点库 交叉核对。

做四件事：
  1. 拿本品事实卡逐条判定 22 条卖点：可写 / 改写 / 降级 / 锁定 / 冲突 / 作废
  2. 按事实卡重写英文主张，保留 claim_v1 可回查
  3. 按 d_tiers（vendor 四档）重算 D / M，并按 fact_status 重算等级
  4. 跑 7 项自检，任一 FAIL 退出码非 0

用法：
  python check_facts.py                        # 用 fact_schema.yaml 里的默认路径
  python check_facts.py --facts <json路径>
  python check_facts.py --no-write             # 只判定不落盘（预览用）
退出码 0 = 全部 PASS；1 = 有 FAIL；2 = 输入缺失或配置错误
"""
import argparse
import csv
import io
import json
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

try:
    import yaml
except ImportError:
    sys.exit("需要 pyyaml：pip install pyyaml")

ROOT = Path(__file__).resolve().parents[2]

SAFE = {"len": len, "any": any, "all": all, "min": min, "max": max,
        "abs": abs, "round": round, "str": str, "int": int, "float": float,
        "sum": sum, "sorted": sorted, "True": True, "False": False, "None": None}

# 中文取值 → 英文措辞，由 main() 从 fact_schema.yaml 的 enums 段装入
ENUMS = {}


def tr(v):
    """把事实卡里的中文取值翻成英文措辞；查不到就原样返回。"""
    s = str(v)
    return ENUMS.get(s, s)

ACTION = {
    "CONFIRMED": "保留，可直接进文案",
    "REWRITE":   "换措辞，原主张禁用",
    "DOWNGRADE": "只写结构，禁写数值，不单独成点",
    "BLOCKED":   "禁写，等事实补齐",
    "CONFLICT":  "撤回，与本品事实冲突",
    "DEPRECATE": "从卖点库移除",
}


# ------------------------------------------------------------------ 基础
def p(rel):
    """配置里的相对路径 → 绝对路径（绝对路径原样返回）。"""
    q = Path(rel)
    return q if q.is_absolute() else (ROOT / q)


def load_yaml(path):
    with io.open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_path(obj, dotted, default=None):
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part, None)
        else:
            return default
        if cur is None:
            return default
    return cur


def namespace_from(facts):
    """把事实卡 dict 变成可用点号访问的对象树：install.methods 就是属性访问。"""
    root = {}
    for k, v in facts.items():
        if k.startswith("_"):
            continue
        root[k] = _wrap(v)
    for k, v in facts.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict):
            root[k] = SimpleNamespace(**{kk: _wrap(vv) for kk, vv in v.items()})
    return root


def _wrap(v):
    if isinstance(v, dict):
        return SimpleNamespace(**{kk: _wrap(vv) for kk, vv in v.items()})
    return v


def make_joins(facts):
    """给 claim 模板提供几个拼接好的文本变量。"""
    def join(path, sep=", "):
        v = get_path(facts, path) or []
        return sep.join(tr(x) for x in v) if isinstance(v, list) else ""
    return {
        "surfaces_ok_join": join("surfaces.ok"),
        "zone_use_join": join("structure.zone_use"),
        "scenes_join": join("surfaces.scenes"),
        "positions_join": join("install.positions"),
    }


class SafeFmt(dict):
    def __missing__(self, key):
        return "—"


def fmt(tpl, ctx):
    def conv(v):
        if v is None:
            return "—"
        if isinstance(v, bool):
            return "是" if v else "否"
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        if isinstance(v, list):
            return " / ".join(tr(x) for x in v) if v else "—"
        return tr(v)
    return str(tpl).format_map(SafeFmt({k: conv(v) for k, v in ctx.items() if not k.startswith("_")}))


# ------------------------------------------------------------------ 规则求值
def build_ns(facts, joins, rule):
    ns = dict(joins)
    # 第一层：把所有事实字段以「点号可访问对象」挂上去
    for k, v in namespace_from(facts).items():
        ns[k] = v
    # 第二层：规则自带变量（按顺序求值，后面的可以引用前面的）
    for name, expr in (rule.get("vars") or {}).items():
        try:
            ns[name] = eval(expr, {"__builtins__": SAFE}, ns)  # noqa: S307
        except Exception as e:
            raise RuntimeError("SP %s 变量 %s 求值失败：%r → %s" % (rule["id"], name, expr, e))
    return ns


def judge(rule, facts, joins):
    ns = build_ns(facts, joins, rule)
    for case in rule["cases"]:
        try:
            ok = eval(case["where"], {"__builtins__": SAFE}, ns)  # noqa: S307
        except Exception as e:
            raise RuntimeError("SP %s 条件 %r 求值失败：%s" % (rule["id"], case["where"], e))
        if ok:
            status = case["status"]
            reason = fmt(case.get("reason", ""), ns)
            claim = rule.get("claims", {}).get(status, "—")
            claim = fmt(claim, ns)
            return status, reason, claim, ns
    raise RuntimeError("SP %s 没有命中任何 case（最后一条兜底应为 True）" % rule["id"])


# ------------------------------------------------------------------ 重算
def d_of(cov, tiers):
    for t in tiers:
        if cov >= float(t["min"]):
            return float(t["d"])
    return float(tiers[-1]["d"])


def grade_of(row, sp_cfg, fact_cfg, status):
    role_label = (row.get("角色") or "").strip()
    # sp_config 的 roles 是 key→{label:中文}，库里存的是中文标签，要反查 key 才能对 grades.roles
    roles_map = {v["label"]: k for k, v in (sp_cfg.get("roles") or {}).items()}
    role = roles_map.get(role_label, role_label)
    g = float(row["G机会分"]) if row.get("G机会分") not in (None, "") else 0.0
    dims = (row.get("证据维度") or "").strip()
    # 证据维度列存的是「维度个数」（如 2 = 五点+评论），不是维度名清单
    try:
        dims_n = int(float(dims))
    except (TypeError, ValueError):
        dims_n = len([x for x in re.split(r"[,;/]", dims) if x.strip()]) if dims else 0

    G = sp_cfg["grades"]
    base = "C"
    if role in G["A"]["roles"] and g >= G["A"]["g_min"] and dims_n >= G["A"]["evidence_dims_min"]:
        base = "A"
    elif role in G["B"]["roles"]:
        base = "B"
    elif role in G["C"]["roles"]:
        base = "C"
    elif role in G["D"]["roles"]:
        base = "D"

    rules = fact_cfg.get("grade_rules") or {}
    if status in (rules.get("hard_drop") or []):
        return base, "D", "fact_status=%s，硬降 D" % status
    down = rules.get("downgrade") or {}
    if status in down:
        target = down[status]
        if base in ("A", "B") and target > base:
            return base, target, "%s → %s（%s）" % (base, target, status)
    return base, base, ""


# ------------------------------------------------------------------ 自检
def run_selfcheck(cfg, facts, rows, judge_rows):
    out = []

    # C1 必填项（两级，2026-11-17 改）
    # hard 缺 → FAIL：整篇写不成，必须补
    # soft 缺 → 不拦路：只是某个卖点不能写，文案绕开即可，写进附注
    def _blank(v):
        return v is None or v == "" or (isinstance(v, list) and not v)

    unknown = set(facts.get("_unknown") or [])
    hard = cfg.get("required_hard") or cfg.get("required") or []
    soft = cfg.get("required_soft") or []
    hard_missing = [r for r in hard if _blank(get_path(facts, r["path"]))]
    soft_missing = [r for r in soft if _blank(get_path(facts, r["path"]))]

    if hard_missing:
        detail = "骨架缺 %d 项：%s" % (
            len(hard_missing), "、".join(r["label"] for r in hard_missing))
        declared = [r for r in hard_missing if r["path"] in unknown]
        if declared:
            detail += "（其中 %d 项已标明确未知，但骨架项仍需补）" % len(declared)
    else:
        detail = "%d 项骨架齐全" % len(hard)

    if soft_missing:
        detail += "；另有 %d 项软必填未填，不拦路：%s" % (
            len(soft_missing), "、".join(r["label"] for r in soft_missing))
    out.append(("C1", "必填项齐全", "FAIL" if hard_missing else "PASS", detail))

    # 通用 forbidden_when
    for ck in cfg["selfcheck"]:
        if ck["type"] != "forbidden_when":
            continue
        ns = dict(make_joins(facts))
        for k, v in namespace_from(facts).items():
            ns[k] = v
        try:
            active = eval(ck["when"], {"__builtins__": SAFE}, ns)  # noqa: S307
        except Exception as e:
            out.append((ck["id"], ck["name"], "FAIL", "条件求值失败：%s" % e))
            continue
        if not active:
            out.append((ck["id"], ck["name"], "PASS", "前提不成立，跳过"))
            continue
        hits = [j["sp_id"] for j in judge_rows
                if re.search(ck["pattern"], j["claim_v2"] or "", re.I)]
        out.append((ck["id"], ck["name"], "FAIL" if hits else "PASS",
                    ("命中：%s" % ",".join(hits)) if hits else "无命中"))

    # C6 非 CONFIRMED 必须改过措辞
    bad = [j["sp_id"] for j in judge_rows
           if j["fact_status"] != "CONFIRMED" and j["claim_v2"] == j["claim_v1"]]
    out.append(("C6", "非 CONFIRMED 必须改过措辞", "FAIL" if bad else "PASS",
                ("未改：%s" % ",".join(bad)) if bad else "全部已改"))

    # C7 每条都有 deps
    nodeps = [r["id"] for r in cfg["sp_rules"] if not r.get("deps")]
    out.append(("C7", "每条都有事实锚点", "FAIL" if nodeps else "PASS",
                ("无 deps：%s" % ",".join(nodeps)) if nodeps else "%d 条全有" % len(cfg["sp_rules"])))

    order = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]
    out.sort(key=lambda x: order.index(x[0]))
    return out


# ------------------------------------------------------------------ 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facts", help="事实卡 JSON 路径")
    ap.add_argument("--config", default=str(ROOT / "skills/scripts/fact_schema.yaml"))
    ap.add_argument("--sp-config", default=str(ROOT / "skills/scripts/sp_config.yaml"))
    ap.add_argument("--no-write", action="store_true", help="只判定不落盘")
    args = ap.parse_args()

    cfg = load_yaml(args.config)
    sp_cfg = load_yaml(args.sp_config)
    ENUMS.clear()
    ENUMS.update(cfg.get("enums") or {})

    facts_path = p(args.facts or cfg["meta"]["fact_card"])
    if not facts_path.exists():
        print("找不到事实卡：%s\n先填 00-事实卡输入卡.html 并导出 JSON。" % facts_path, file=sys.stderr)
        return 2
    with io.open(facts_path, encoding="utf-8") as f:
        facts = json.load(f)

    lib_path = p(cfg["meta"]["library_v1"])
    if not lib_path.exists():
        print("找不到卖点库：%s" % lib_path, file=sys.stderr)
        return 2
    with io.open(lib_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    by_id = {r["sp_id"]: r for r in rows}

    joins = make_joins(facts)
    tpl_weights = sp_cfg["weights"]
    tiers = sp_cfg["d_tiers"]

    judge_rows, lib_rows = [], []
    for rule in cfg["sp_rules"]:
        sid = rule["id"]
        row = by_id.get(sid)
        if row is None:
            print("卖点库里没有 %s，但配置里有这条规则" % sid, file=sys.stderr)
            return 2

        status, reason, claim, ns = judge(rule, facts, joins)

        dep_vals = []
        for d in rule["deps"]:
            v = get_path(facts, d)
            dep_vals.append("%s=%s" % (d.split(".")[-1], "—" if v is None else
                                       ("、".join(map(str, v)) if isinstance(v, list) else v)))

        cov = float(row["五点覆盖"])
        d_old = float(row["D"])
        d_new = d_of(cov, tiers)
        S, P = float(row["S"]), float(row["P"])
        # M 只随 D 变化。用「CSV 记录的 M + D 变动带来的增量」而不是整体重算，
        # 避免原始 build 脚本里 S/P 舍入留下的 0.1 级噪声被误报成「M 变了」。
        delta_m = 100 * (d_new - d_old) * float(tpl_weights["D"])
        m_v1 = float(row["M"])
        m_new = round(m_v1 + delta_m, 1)
        g = P * (1 - cov)

        base_grade, final_grade, grade_note = grade_of(row, sp_cfg, cfg, status)

        jr = {
            "sp_id": sid,
            "卖点名": row["卖点名"],
            "claim_v1": row["英文主张"],
            "claim_v2": claim,
            "依赖字段": "、".join(rule["deps"]),
            "事实取值": "；".join(dep_vals),
            "fact_status": status,
            "处置": ACTION.get(status, ""),
            "依据": reason,
            "D_v1": row["D"], "D_v2": round(d_new, 2),
            "M_v1": row["M"], "M_v2": round(m_new, 1),
            "等级_v1": row.get("等级", ""), "等级_v2": final_grade,
            "M变动": round(m_new - float(row["M"]), 1) if row.get("M") not in (None, "") else 0.0,
        }
        judge_rows.append(jr)

        # v2 库：原列顺序 + 新列
        out = {}
        for k, v in row.items():
            if k == "英文主张":
                out["claim_v1"] = row["英文主张"]
                out["英文主张"] = claim
                out["fact_ref"] = "、".join(rule["deps"])
                out["fact_status"] = status
            else:
                out[k] = v
        out["D"] = round(d_new, 2)
        out["M"] = round(m_new, 1)
        out["G机会分"] = round(g, 3)
        out["等级"] = final_grade
        out["等级_note"] = grade_note
        lib_rows.append(out)

    # ---------------- 自检
    checks = run_selfcheck(cfg, facts, rows, judge_rows)
    failed = [c for c in checks if c[2] == "FAIL"]

    # ---------------- 落盘
    outp = {k: p(v) for k, v in cfg["outputs"].items()}
    if not args.no_write:
        for q in outp.values():
            q.parent.mkdir(parents=True, exist_ok=True)

        with io.open(outp["judge"], "w", encoding="utf-8-sig", newline="") as f:
            cols = ["sp_id", "卖点名", "claim_v1", "claim_v2", "依赖字段", "事实取值",
                    "fact_status", "处置", "依据", "D_v1", "D_v2", "M_v1", "M_v2",
                    "M变动", "等级_v1", "等级_v2"]
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(judge_rows)

        with io.open(outp["library_v2"], "w", encoding="utf-8-sig", newline="") as f:
            cols = ["sp_id", "卖点名", "claim_v1", "英文主张", "fact_ref", "fact_status",
                    "类型", "关联L1", "五点覆盖", "覆盖ASIN数", "平均位次", "好评验证条数",
                    "差评条数", "差评占比", "支撑词", "S", "P", "V", "D", "M", "G机会分", "角色",
                    "等级", "等级_note", "证据维度", "冲突", "冲突类型", "confidence", "备注"]
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(lib_rows)

        total_m = sum(1 for j in judge_rows if abs(j["M变动"]) > 1e-9)
        with io.open(outp["selfcheck"], "w", encoding="utf-8") as f:
            f.write("事实核对自检 · %s\n" % facts_path.name)
            f.write("生成时间：%s\n" % __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"))
            f.write("=" * 60 + "\n")
            for cid, name, res, detail in checks:
                f.write("[%s] %-4s %-28s %s\n" % (res, cid, name, detail))
            f.write("=" * 60 + "\n")
            f.write("判定分布：%s\n" % _dist(j for j in (x["fact_status"] for x in judge_rows)))
            f.write("M 变动条数：%d / %d\n" % (total_m, len(judge_rows)))
            f.write("结论：%s\n" % ("FAIL" if failed else "PASS"))

    # ---------------- 控制台
    print("事实卡：%s" % facts_path)
    print("卖点库：%s（%d 条）" % (lib_path, len(rows)))
    print("-" * 78)
    print("%-6s %-16s %-10s %-7s %-7s %-6s %s" % ("SP", "卖点", "判定", "D", "M", "等级", "依据"))
    for j in judge_rows:
        print("%-6s %-16s %-10s %-7s %-7s %-6s %s" % (
            j["sp_id"], j["卖点名"], j["fact_status"],
            "%s→%s" % (j["D_v1"], j["D_v2"]),
            "%s→%s" % (j["M_v1"], j["M_v2"]),
            "%s→%s" % (j["等级_v1"], j["等级_v2"]) if j["等级_v1"] != j["等级_v2"] else j["等级_v2"],
            j["依据"]))
    print("-" * 78)
    print("判定分布：%s" % _dist(x["fact_status"] for x in judge_rows))
    for cid, name, res, detail in checks:
        print("[%s] %s %s  %s" % (res, cid, name, detail))
    print("-" * 78)
    if failed:
        print("有 %d 项 FAIL，不许交付。" % len(failed))
        return 1
    print("全部 PASS。")
    return 0


def _dist(it):
    d = {}
    for x in it:
        d[x] = d.get(x, 0) + 1
    order = ["CONFIRMED", "REWRITE", "DOWNGRADE", "BLOCKED", "CONFLICT", "DEPRECATE"]
    return "  ".join("%s=%d" % (k, d[k]) for k in order if k in d)


if __name__ == "__main__":
    sys.exit(main())
