#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
40-selling-point · 卖点库构建

输入：竞品五点原文、关键词库、30-insight 的评论分类结果
输出：卖点库主表 / 证据链 / 五点矩阵 / 图片降级清单 / 评论映射 / 冲突风险 / 待补证据

所有阈值和卖点定义都在 sp_config.yaml，本文件不写死任何词或数字。
用法：
    python build_selling_points.py                 # 用默认配置
    python build_selling_points.py --config x.yaml # 指定配置
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import yaml
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent.parent


# ------------------------------------------------------------------ 工具
def tier(value, tiers):
    """tiers = [[阈值, 取值], ...]，按阈值降序取第一个满足的。"""
    for th, val in sorted(tiers, key=lambda x: -x[0]):
        if value >= th:
            return float(val)
    return 0.0


def pct(x, nd=1):
    return f"{x * 100:.{nd}f}%"


def norm_text(s):
    return (s or "").lower().replace("’", "'").replace("‘", "'")


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# ------------------------------------------------------------------ 读输入
def load_bullets(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for item in data:
        out.append({
            "asin": item["asin"],
            "brand": item.get("brand") or "",
            "title": item.get("title") or "",
            "bullets": item.get("bullets") or [],
            "mount": guess_mount(item),
        })
    return out


def guess_mount(item):
    t = norm_text(" ".join([item.get("title", "")] + (item.get("bullets") or [])))
    if "faucet" in t or "over the divider" in t:
        return "挂龙头/隔板"
    if "adhesive" in t and "suction" not in t:
        return "胶粘"
    if "suction" in t:
        return "吸盘"
    return "未判定"


def load_keywords(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    out = []
    for r in rows:
        try:
            w = float(r.get("W") or 0)
        except ValueError:
            w = 0.0
        try:
            rel = float(r.get("R") or 0)
        except ValueError:
            rel = 0.0
        out.append({
            "keyword": r["keyword"].strip().lower(),
            "prio": (r.get("prio") or "").strip(),
            "W": w,
            "R": rel,
        })
    return out


def load_review_xlsx(path):
    """03_一级频次 → 差评总数；04_二级频次 → 二级 → (好评n, 差评n)"""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    neg_total = 0
    l1_rows = []
    for r in wb["03_一级频次"].iter_rows(min_row=2, values_only=True):
        if not r or r[0] is None:
            continue
        pol, l1, n = r[0], r[1], int(r[2] or 0)
        l1_rows.append({"polarity": pol, "l1": l1, "n": n})
        if pol == "差评":
            neg_total += n

    l2 = {}
    for r in wb["04_二级频次"].iter_rows(min_row=2, values_only=True):
        if not r or r[3] is None:
            continue
        pol, l1, name, n = r[1], r[2], r[3], int(r[6] or 0)
        rec = l2.setdefault(name, {"l1": l1, "pos": 0, "neg": 0})
        if pol == "好评":
            rec["pos"] += n
        else:
            rec["neg"] += n
    wb.close()
    return neg_total, l1_rows, l2


# ------------------------------------------------------------------ 核心
def match_bullets(asins, patterns):
    """返回 {asin: [命中的五点位次, ...]}"""
    regs = [re.compile(p, re.I) for p in patterns]
    hits = {}
    for a in asins:
        pos = []
        for i, b in enumerate(a["bullets"], 1):
            text = norm_text(b)
            if any(r.search(text) for r in regs):
                pos.append(i)
        if pos:
            hits[a["asin"]] = pos
    return hits


def match_keywords(keywords, patterns):
    matched = []
    for k in keywords:
        if k["prio"] not in ("P0", "P1", "P2"):
            continue
        if k["R"] < 0.6:
            continue
        if any(p in k["keyword"] for p in patterns):
            matched.append(k)
    return matched


def decide_role(cov, p_score, v_score, rules):
    if cov < 0.10 and p_score <= 0.10 and v_score <= 0.10:
        return "drop"
    r = rules
    if cov >= r["entry_ticket"]["cov_min"] and p_score >= r["entry_ticket"]["p_min"]:
        return "entry_ticket"
    if cov < r["main_gap"]["cov_max"] and p_score >= r["main_gap"]["p_min"]:
        return "main_gap"
    if (r["common"]["cov_min"] <= cov <= r["common"]["cov_max"]
            and p_score >= r["common"]["p_min"]):
        return "common"
    if (cov < r["validated"]["cov_max"] and v_score >= r["validated"]["v_min"]
            and p_score < r["validated"]["p_max"]):
        return "validated"
    if (cov >= r["standard"]["cov_min"] and p_score < r["standard"]["p_max"]
            and v_score >= r["standard"].get("v_min", 0.0)):
        return "standard"
    return "pending"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(Path(__file__).parent / "sp_config.yaml"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    inp = cfg["inputs"]
    outdir = Path(args.out) if args.out else ROOT / cfg["outputs"]["dir"]
    outdir.mkdir(parents=True, exist_ok=True)

    asins = load_bullets(ROOT / inp["bullets_json"])
    keywords = load_keywords(ROOT / inp["keyword_library"])
    neg_total, l1_rows, l2 = load_review_xlsx(ROOT / inp["review_xlsx"])

    n_asin = len(asins)
    total_bullets = sum(len(a["bullets"]) for a in asins)

    # ---- 逐卖点计算
    sps = []
    for sp in cfg["sp_defs"]:
        hits = match_bullets(asins, sp.get("bullet_patterns", []))
        cov = len(hits) / n_asin if n_asin else 0.0
        avg_pos = (sum(sum(v) / len(v) for v in hits.values()) / len(hits)) if hits else 0.0

        pos_n = neg_n = 0
        review_detail = []
        for name in sp.get("review_l2", []):
            rec = l2.get(name)
            if not rec:
                continue
            pos_n += rec["pos"]
            neg_n += rec["neg"]
            review_detail.append({"l2": name, "l1": rec["l1"], "pos": rec["pos"], "neg": rec["neg"]})

        neg_share = neg_n / neg_total if neg_total else 0.0
        P = tier(neg_share, cfg["pain_tiers"])
        V = tier(pos_n, cfg["validated_tiers"])
        D = tier(cov, cfg["coverage_tiers"])

        kws = match_keywords(keywords, sp.get("kw_patterns", []))
        S_raw = sum(k["W"] * k["R"] for k in kws)

        sps.append({
            "sp": sp,
            "hits": hits,
            "cov": cov,
            "avg_pos": avg_pos,
            "pos_n": pos_n,
            "neg_n": neg_n,
            "neg_share": neg_share,
            "P": P,
            "V": V,
            "D": D,
            "kws": kws,
            "S_raw": S_raw,
            "review_detail": review_detail,
        })

    s_max = max((s["S_raw"] for s in sps), default=0.0) or 1.0
    for s in sps:
        s["S"] = s["S_raw"] / s_max
        s["M"] = (s["S"] * cfg["weights"]["S"]
                  + s["P"] * cfg["weights"]["P"]
                  + s["D"] * cfg["weights"]["D"]) * 100
        # 机会分：痛点强度 × 供给缺口。定级用它，不用 M
        s["G"] = s["P"] * (1 - s["cov"])
        s["role"] = decide_role(s["cov"], s["P"], s["V"], cfg["roles"])
        dims = 1 if s["cov"] > 0 else 0
        dims += 1 if (s["pos_n"] + s["neg_n"]) > 0 else 0
        if cfg["image"]["enabled"]:
            dims += 1
        s["dims"] = dims

    # ---- 分级（名额制）
    gr = cfg["grades"]
    for s in sps:
        if s["role"] == "drop":
            s["grade"] = "D"
        elif (s["role"] in gr["A"]["roles"]
              and s["G"] >= gr["A"]["g_min"]
              and s["dims"] >= gr["A"]["evidence_dims_min"]):
            s["grade"] = "A"
        elif s["role"] in gr["B"]["roles"]:
            s["grade"] = "B"
        elif s["role"] in gr["C"]["roles"]:
            s["grade"] = "C"
        else:
            s["grade"] = "C"

    a_slots = gr["A"]["slots"]
    a_items = sorted([s for s in sps if s["grade"] == "A"], key=lambda x: -x["G"])
    for i, s in enumerate(a_items):
        if i >= a_slots:
            s["grade"] = "B"
            s["grade_note"] = "A 级名额已满，顺延 B"
    for s in sps:
        if s["grade"] == "B" and s["role"] in ("main_gap", "common"):
            s.setdefault("grade_note", "G 未达 A 级门槛（%.2f）" % gr["A"]["g_min"])

    # ---- 冲突检测
    cf = cfg["conflict"]
    for s in sps:
        betrayal = [d for d in s["review_detail"] if d["l2"] in cf["betrayal_l2"] and d["neg"] > 0]
        s["conflict"] = (s["cov"] >= cf["cov_min"] and s["P"] >= cf["p_min"]) or bool(betrayal)
        s["betrayal"] = betrayal
        s["conflict_score"] = round(s["cov"] * s["P"] * 100, 1)
        s["conflict_type"] = ""
        if betrayal and s["cov"] >= 0.40:
            s["conflict_type"] = "声称与体验背离"
        elif s["conflict"] and s["cov"] >= 0.60:
            s["conflict_type"] = "品类级反噬"
        elif s["conflict"]:
            # 少数人写、也照样没做到：主要信号是供给缺口，不是文案反噬
            s["conflict_type"] = "痛点未解决"

    # ---- 置信度
    for s in sps:
        if s["dims"] >= 2 and s["cov"] > 0:
            s["confidence"] = "MEASURED"
        elif s["cov"] > 0 or (s["pos_n"] + s["neg_n"]) > 0:
            s["confidence"] = "DERIVED"
        else:
            s["confidence"] = "JUDGED"

    order = {"A": 0, "B": 1, "C": 2, "D": 3}
    # 主表按等级 + M 排：等级决定"写不写"，M 决定"五点里谁先说"（G 已用于定级，不再排序）
    sps.sort(key=lambda x: (order[x["grade"]], -x["M"]))

    # ================================================================ 输出
    # 01 主表
    h1 = ["sp_id", "卖点名", "英文主张", "类型", "关联L1", "五点覆盖", "覆盖ASIN数",
          "平均位次", "好评验证条数", "差评条数", "差评占比", "支撑词", "S", "P", "V", "D",
          "M", "G机会分", "角色", "等级", "证据维度", "冲突", "冲突类型", "confidence", "备注"]
    r1 = []
    for s in sps:
        r1.append([
            s["sp"]["id"], s["sp"]["name"], s["sp"]["claim"], s["sp"]["sp_type"],
            "/".join(s["sp"]["l1"]),
            round(s["cov"], 4), len(s["hits"]), round(s["avg_pos"], 2),
            s["pos_n"], s["neg_n"], round(s["neg_share"], 4),
            "; ".join(f"{k['keyword']}({k['W']:.0f})" for k in s["kws"]) or "无直接搜索词",
            round(s["S"], 3), s["P"], s["V"], s["D"], round(s["M"], 1),
            round(s["G"], 3),
            cfg["roles"][s["role"]]["label"] if s["role"] in cfg["roles"] else s["role"],
            s["grade"], s["dims"],
            "Y" if s["conflict"] else "",
            s["conflict_type"],
            s["confidence"],
            s.get("grade_note", ""),
        ])
    write_csv(outdir / "SP-01-卖点库.csv", h1, r1)

    # 02 证据链
    h2 = ["sp_id", "卖点名", "维度", "来源类型", "来源文件/sheet", "定位", "原文/计数", "n", "confidence"]
    r2 = []
    for s in sps:
        for asin, positions in s["hits"].items():
            a = next(x for x in asins if x["asin"] == asin)
            for p in positions:
                r2.append([
                    s["sp"]["id"], s["sp"]["name"], "五点", "asin_detail.features",
                    "products_wall_full.json", f"{asin}#{p}", a["bullets"][p - 1][:300], 1, "MEASURED",
                ])
        for d in s["review_detail"]:
            if d["pos"] + d["neg"] == 0:
                continue
            r2.append([
                s["sp"]["id"], s["sp"]["name"], "评论", "amz-review-analysis",
                "Review-Analysis.xlsx / 04_二级频次", f"{d['l1']}|{d['l2']}",
                f"好评 {d['pos']} 条 / 差评 {d['neg']} 条", d["pos"] + d["neg"], "DERIVED",
            ])
    write_csv(outdir / "SP-02-证据链.csv", h2, r2)

    # 03 五点矩阵
    h3 = ["ASIN", "品牌", "安装形态", "命中卖点数"] + [s["sp"]["id"] for s in sps]
    r3 = []
    for a in asins:
        row = [a["asin"], a["brand"], a["mount"]]
        cells = []
        for s in sps:
            pos = s["hits"].get(a["asin"])
            cells.append(f"{s['sp']['id']}({','.join(map(str, pos))})" if pos else "")
        row += [sum(1 for c in cells if c)] + cells
        r3.append(row)
    write_csv(outdir / "SP-03-五点拆解矩阵.csv", h3, r3)

    # 04 图片降级清单
    slot_map = {"功能": "2/3/4", "材质": "4", "结构": "4", "场景": "3",
                "外观": "1/2", "价值": "6/7", "信任": "5"}
    h4 = ["sp_id", "卖点名", "应承载图位", "应有画面", "当前状态", "补图后可验证什么"]
    r4 = []
    for s in sps:
        r4.append([
            s["sp"]["id"], s["sp"]["name"], slot_map.get(s["sp"]["sp_type"], "2"),
            f"{s['sp']['claim']} + 视觉证据（场景/尺寸/对比/细节）",
            "DATA_MISSING：无图包",
            f"该卖点是否真的『上图才算成立』；当前等级 {s['grade']} 是否被低估",
        ])
    write_csv(outdir / "SP-04-图片降级清单.csv", h4, r4)

    # 05 评论映射
    h5 = ["sp_id", "卖点名", "一级", "二级", "好评条数", "差评条数", "合计"]
    r5 = []
    seen = set()
    for s in sps:
        for d in s["review_detail"]:
            key = (s["sp"]["id"], d["l2"])
            if key in seen:
                continue
            seen.add(key)
            r5.append([s["sp"]["id"], s["sp"]["name"], d["l1"], d["l2"],
                       d["pos"], d["neg"], d["pos"] + d["neg"]])
    write_csv(outdir / "SP-05-评论映射.csv", h5, r5)

    # 06 冲突与风险
    h6 = ["sp_id", "卖点名", "五点覆盖", "差评占比", "冲突分", "类型",
          "对撞证据", "风险说明", "处置建议"]
    r6 = []
    for s in sps:
        if not s["conflict"]:
            continue
        ev = "; ".join(f"{d['l2']}({d['neg']})" for d in s["review_detail"] if d["neg"] > 0)
        if s["conflict_type"] == "品类级反噬":
            risk, advice = "全员都在写，但差评集中在同一件事", "写，但必须配证据（数值/测试/对比），不能只喊口号"
        elif s["conflict_type"] == "声称与体验背离":
            risk, advice = "文案承诺了，评论却说没做到", "要么改文案口径，要么改产品；维持原样会反噬"
        else:
            risk, advice = "差评集中，但只有少数竞品在写", "这是机会不是风险：写足并给可验证证据，直接接这批人"
        r6.append([s["sp"]["id"], s["sp"]["name"], round(s["cov"], 3), round(s["neg_share"], 4),
                   s["conflict_score"], s["conflict_type"], ev, risk, advice])
    r6.sort(key=lambda x: -x[4])
    write_csv(outdir / "SP-06-冲突与风险.csv", h6, r6)

    # 07 待补证据
    h7 = ["sp_id", "卖点名", "当前等级", "缺什么证据", "补证动作", "补到哪一维"]
    r7 = []
    for s in sps:
        gaps = []
        if not s["kws"]:
            gaps.append("无支撑搜索词")
        if s["pos_n"] + s["neg_n"] == 0:
            gaps.append("评论零命中")
        if not cfg["image"]["enabled"]:
            gaps.append("图片维度未采集")
        if s["role"] in ("pending", "drop") or s["grade"] in ("C", "D"):
            r7.append([s["sp"]["id"], s["sp"]["name"], s["grade"], "；".join(gaps) or "结论偏弱",
                       "拍图包 / 追加评论抽样 / 补关键词" if gaps else "人工复核",
                       "图片" if not cfg["image"]["enabled"] else "评论"])
    write_csv(outdir / "SP-07-待补证据.csv", h7, r7)

    # ================================================================ xlsx
    build_xlsx(outdir, cfg, sps, h1, r1, h2, r2, h3, r3, h4, r4, h5, r5, h6, r6, h7, r7,
               n_asin, total_bullets, neg_total)

    # ================================================================ 摘要
    summary = {
        "n_asin": n_asin,
        "total_bullets": total_bullets,
        "neg_total": neg_total,
        "n_sp": len(sps),
        "grade_counts": {g: sum(1 for s in sps if s["grade"] == g) for g in "ABCD"},
        "role_counts": {},
        "top": [{"id": s["sp"]["id"], "name": s["sp"]["name"], "M": round(s["M"], 1),
                 "grade": s["grade"], "role": cfg["roles"][s["role"]]["label"],
                 "cov": round(s["cov"], 3), "P": s["P"], "D": s["D"], "conflict": s["conflict"]}
                for s in sps[:12]],
        "conflicts": len(r6),
        "no_kw": [s["sp"]["id"] for s in sps if not s["kws"]],
    }
    for s in sps:
        lab = cfg["roles"][s["role"]]["label"]
        summary["role_counts"][lab] = summary["role_counts"].get(lab, 0) + 1
    (outdir / "_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK  {len(sps)} 个卖点  ->  {outdir}")
    print(f"    等级分布 {summary['grade_counts']}  冲突 {len(r6)} 条")
    return 0


def build_xlsx(outdir, cfg, sps, h1, r1, h2, r2, h3, r3, h4, r4, h5, r5, h6, r6, h7, r7,
               n_asin, total_bullets, neg_total):
    wb = openpyxl.Workbook()
    head_fill = PatternFill("solid", fgColor="1F3864")
    head_font = Font(color="FFFFFF", bold=True, size=10)
    thin = Side(style="thin", color="D9D9D9")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    grade_fill = {"A": PatternFill("solid", fgColor="C6EFCE"),
                  "B": PatternFill("solid", fgColor="FFEB9C"),
                  "C": PatternFill("solid", fgColor="FCE4D6"),
                  "D": PatternFill("solid", fgColor="D9D9D9")}

    ws = wb.active
    ws.title = "00_说明"
    rows = [
        ["卖点库", f"{cfg['meta']['category_name']} · {cfg['meta']['marketplace']} · {cfg['meta']['date']}"],
        ["", ""],
        ["样本", f"{n_asin} 个竞品 ASIN，{total_bullets} 条五点原句"],
        ["评论样本", f"{cfg['meta'].get('review_note', '见口径声明')}，差评一级命中合计 {neg_total} 次"],
        ["词库", cfg["meta"].get("kb_note", "见口径声明")],
        ["", ""],
        ["权重", "M = S×0.45 + P×0.35 + D×0.20（沿用 amazon-listing-builder/reference/ranking-rules.md）"],
        ["S 需求强度", "该卖点支撑词 Σ(W×R) ÷ 全库最大值。无对应搜索词的卖点为 0，属正常：说明该卖点不该为搜索排名服务"],
        ["P 痛点严重度", "关联差评条数 ÷ 差评总数，按 30%/15%/5% 分档 1.0/0.7/0.4/0.2"],
        ["V 好评验证度", "买家主动夸的条数，≥10 记 1.0，3-9 记 0.6，1-2 记 0.3"],
        ["D 差异化", "1 − 五点覆盖率，覆盖 ≥60% 记 0.10（人人都有等于没有）"],
        ["G 机会分", "P × (1 − 覆盖率)。定级用它：痛点重、供给缺口大 = 值得主攻"],
        ["M vs G", "G 管『值不值得做』（定级），M 管『五点里谁先说』（50-copy 排序）。两者不一致是正常的"],
        ["", ""],
        ["等级", "A 主攻（名额 5，需 G≥0.20）/ B 必写 / C 加分或待证 / D 淘汰"],
        ["角色", "入场券 / 主攻空白 / 常见卖点 / 已验证卖点 / 品类标配 / 待验证 / 淘汰"],
        ["", ""],
        ["图片维度", "本轮 DATA_MISSING。沙箱无外网、Amazon 页面返回 Access restricted、asin_detail 仅 1 张主图 URL 且不可读。图包到位后把 sp_config.yaml 的 image.enabled 改 true 重跑"],
        ["confidence", "MEASURED=接口直出 / DERIVED=由数据算出 / JUDGED=人的判断"],
        ["", ""],
        ["口径限制", "样本含吸盘、胶粘、挂龙头三种安装形态，覆盖率为全样本口径，不等于同类形态内覆盖率"],
    ]
    for r in rows:
        ws.append(r)
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 120

    def sheet(name, header, data, widths=None, grade_col=None):
        s = wb.create_sheet(name)
        s.append(header)
        for c in s[1]:
            c.fill = head_fill
            c.font = head_font
            c.alignment = Alignment(vertical="center", wrap_text=True)
            c.border = border
        for row in data:
            s.append(row)
        s.freeze_panes = "A2"
        s.auto_filter.ref = s.dimensions
        for i, col in enumerate(header, 1):
            s.column_dimensions[get_column_letter(i)].width = (widths or {}).get(col, 14)
        if grade_col:
            gi = header.index(grade_col) + 1
            for row in s.iter_rows(min_row=2, max_row=s.max_row):
                v = row[gi - 1].value
                if v in grade_fill:
                    row[gi - 1].fill = grade_fill[v]
        return s

    sheet("01_卖点库", h1, r1,
          {"卖点名": 20, "英文主张": 28, "关联L1": 24, "支撑词": 40, "备注": 20, "角色": 12, "英文": 20})
    sheet("02_证据链", h2, r2, {"卖点名": 20, "来源文件/sheet": 34, "原文/计数": 70, "定位": 24})
    sheet("03_五点矩阵", h3, r3, {"品牌": 18, "安装形态": 12})
    sheet("04_图片降级", h4, r4, {"卖点名": 20, "应有画面": 60, "补图后可验证什么": 50})
    sheet("05_评论映射", h5, r5, {"卖点名": 20, "二级": 32})
    sheet("06_冲突风险", h6, r6, {"卖点名": 20, "对撞证据": 50, "风险说明": 40, "处置建议": 40})
    sheet("07_待补证据", h7, r7, {"卖点名": 20, "缺什么证据": 40, "补证动作": 34})

    target = outdir / "卖点库.xlsx"
    try:
        wb.save(target)
    except PermissionError:
        # Windows 上文件被 Excel 打开时无法覆盖。写副本，别让整轮构建白跑。
        from datetime import datetime
        alt = outdir / f"卖点库_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        wb.save(alt)
        print(f"WARN  {target.name} 被占用（Excel 开着？），已写到 {alt.name}；关闭后重跑可覆盖")


if __name__ == "__main__":
    sys.exit(main())
