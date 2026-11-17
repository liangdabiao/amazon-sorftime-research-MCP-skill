#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
50-copy · 体检评分（第三方 amazon-listing-doctor）

做什么：把 copy.json 归一化成 listing.json，调 vendor 里的体检工具，把结果摊平成
CP-07-评分明细.csv，供 build_copy.py 渲染成 xlsx 的「04_评分」表。

为什么单独一个脚本：体检工具是第三方代码（MIT），本项目不改它、也不往主流程里嵌逻辑，
只做一件事——进出格式的搬运。它挂了、或者 vendor 目录没跟着走，主流程照常跑，评分表标「未执行」。

用法：
    python score_copy.py --category sponge-holder
    python score_copy.py --category sponge-holder --offline   # 只生成 listing.json，不调工具
"""

import argparse
import ast
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent


# ------------------------------------------------------------------ 工具
def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig")))


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def split_bullet(text):
    """`Header: body` → {header, body}。五点格式是官方规定的，冒号前是 header。"""
    m = re.match(r"^([^:]{2,60}):\s*(.+)$", text.strip())
    if m:
        return {"header": m.group(1).strip(), "body": m.group(2).strip()}
    return {"header": "", "body": text.strip()}


def fmt_score(v):
    if v is None:
        return "—"
    return ("%.1f" % v) if isinstance(v, float) else str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, help="品类目录名，如 sponge-holder")
    ap.add_argument("--config", default=str(Path(__file__).parent / "copy_config.yaml"))
    ap.add_argument("--offline", action="store_true", help="只生成评分输入，不调用体检工具")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    out = {k: v.replace("{category}", args.category) for k, v in cfg["outputs"].items()}
    outdir = ROOT / out["dir"]
    outdir.mkdir(parents=True, exist_ok=True)
    src = ROOT / cfg["inputs"]["copy"].replace("{category}", args.category)
    sc = cfg["score"]

    d = json.load(open(src, encoding="utf-8"))
    brand = d.get("_meta", {}).get("brand") or sc.get("brand", "")

    # 关键词分层输入：工具按 P0..P4 算加权索引分与每层覆盖率。
    # 词库没有 P3/P4（本项目只分 P0/P1/P2），空着即可。
    kw_rows = read_csv(ROOT / cfg["inputs"]["keyword_library"].replace("{category}", args.category))
    keywords = {}
    for r in kw_rows:
        keywords.setdefault(r["prio"], []).append(r["keyword"])

    # ---------- 1. 归一化：copy.json → listing.json ----------
    listing = {
        "market": sc.get("market", "US"),
        "language": sc.get("language", "en"),
        "mode": sc.get("mode", "strict_75"),
        "category": sc.get("category", "Home & Kitchen"),
        "brand": brand,
        "is_parent": sc.get("is_parent", True),
        "is_variation": sc.get("is_variation", False),
        "title": d["title"],
        "item_highlights": d["highlights"],
        "bullets": [split_bullet(b) for b in d["bullets"]],
        "description": d.get("description", ""),
        "backend_search_terms": d["search_terms"],
        "attributes_filled": sc.get("attributes_filled", []),
        "attributes_top10_expected": sc.get("attributes_top10_expected", []),
        "has_a_plus": sc.get("has_a_plus", False),
        "keywords": keywords,
    }
    listing_path = outdir / out["score_listing"]
    listing_path.write_text(json.dumps(listing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    header = ["维度", "指标", "值", "等级/状态", "依据与说明"]
    rows, meta_note = [], []

    tool = ROOT / sc["tool"]
    if args.offline or not tool.exists():
        reason = "offline 模式，未调用" if args.offline else "vendor 缺失：%s" % sc["tool"]
        rows.append(["体检工具", "执行状态", "未执行", "SKIP",
                     "%s。评分输入已生成：%s" % (reason, out["score_listing"])])
        write_csv(outdir / out["score_detail"], header, rows)
        print("评分未执行：%s" % reason)
        return 0

    # ---------- 2. 调体检工具 ----------
    proc = subprocess.run([sys.executable, str(tool), "--file", str(listing_path)],
                          capture_output=True, text=True, encoding="utf-8")
    if not proc.stdout.strip():
        rows.append(["体检工具", "执行状态", "失败", "FAIL",
                     (proc.stderr or "无输出").strip().splitlines()[-1][:160]])
        write_csv(outdir / out["score_detail"], header, rows)
        print("评分失败：体检工具无输出")
        return 0
    rep = json.loads(proc.stdout)
    (outdir / out["score_raw"]).write_text(
        json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ---------- 3. 摊平 ----------
    cdq = rep.get("cdq_score", {})
    comps = cdq.get("components", {})
    avail_w = sum(c["weight"] for c in comps.values() if c.get("score") is not None)
    got = sum(c["score"] * c["weight"] for c in comps.values() if c.get("score") is not None)
    derived = round(got / avail_w * 100, 1) if avail_w else None

    rows.append(["CDQ", "总分（含降级维度）", fmt_score(cdq.get("total")), cdq.get("grade", ""),
                 "6 维加权。属性 30% / 图片 15% 无数据，按缺失计 0，总分被压低"])
    rows.append(["CDQ", "可用维度折算分（本项目自算）", fmt_score(derived), "DERIVED",
                 "剔除无数据维度后按剩余权重折算；权重覆盖 %d%%，不是官方口径" % round(avail_w * 100)])
    for k, c in comps.items():
        st = "降级·无数据" if c.get("score") is None else "计分"
        rows.append(["CDQ·子分", "%s（权重 %d%%）" % (k, round(c["weight"] * 100)),
                     fmt_score(c.get("score")), st, c.get("reason", "")])

    idx = rep.get("indexability_report", {})
    rows.append(["A9 收录", "总分", fmt_score(idx.get("score")), "—",
                 "核心词位置 %s / backend 卫生度 %s / 有效索引词 %s"
                 % (idx.get("core_keyword_position"), idx.get("backend_hygiene"),
                    idx.get("effective_index_terms"))])
    for r in idx.get("risks", [])[:6]:
        detail = r.get("detail")
        rows.append(["A9 收录", r.get("cause", ""), "—", "风险",
                     json.dumps(detail, ensure_ascii=False)[:150] if not isinstance(detail, str) else detail[:150]])

    cos = rep.get("cosmo_report", {})
    cos_st = "降级·通用本体" if cos.get("used_fallback") or not cos.get("ontology_source") else "计分"
    rows.append(["COSMO 意图", "总分", fmt_score(cos.get("score")), cos_st,
                 "覆盖 %.1f%%；本体未按类目收敛时只作参考" % (cos.get("coverage_ratio", 0) * 100)])
    pm = cos.get("per_dimension", {})
    for k, v in pm.items():
        rows.append(["COSMO 意图", k,
                     "%s/%s（%.0f%%）" % (v.get("covered"), v.get("total"), v.get("ratio", 0) * 100),
                     "—", "四维之一"])

    alx = rep.get("alexa_discoverability", {})
    alx_st = "降级·substring 兜底" if alx.get("used_fallback") or alx.get("_extraction_method") != "aeo_agent" else "计分"
    rows.append(["Alexa 可发现性", "总分", fmt_score(alx.get("score")), alx_st,
                 "提取方式 %s；提问数 %s。降级时该分不代表 AEO 表现"
                 % (alx.get("_extraction_method"), alx.get("total_questions"))])

    comp = rep.get("compliance_report", {})
    nf, nw = comp.get("failed_checks") or 0, comp.get("warnings") or 0
    # 工具只要存在警告就判 NON-COMPLIANT，和"有没有硬伤"不是一回事，分开显示
    if nf:
        level, status = "不合规", "FAIL"
    elif nw:
        level, status = "无失败项·有警告", "WARN"
    else:
        level, status = "合规", "PASS"
    rows.append(["合规体检", "结论", "%s 失败 / %s 警告" % (nf, nw), status,
                 "工具原判 %s；它把警告也算作不合规，本项目按失败项分档"
                 % ("NON-COMPLIANT" if not comp.get("overall_compliant") else "COMPLIANT")])
    for it in comp.get("critical_issues", []):
        rows.append(["合规体检", "%s · %s" % (it.get("field"), it.get("check")), "—", "FAIL",
                     json.dumps(it.get("detail"), ensure_ascii=False)[:150]])
    for w in comp.get("warnings_detail", []) or []:
        rows.append(["合规体检", str(w.get("field", "")), "—", "WARN",
                     str(w.get("check", ""))[:150]])

    # 逐字段的警告项（未用满、核心词位置等），比只报「3 项警告」有用
    for fld in ("title", "highlights", "bullets", "backend"):
        v = rep.get(fld) or {}
        for name, ch in (v.get("checks") or {}).items():
            if isinstance(ch, dict) and ch.get("status") == "WARN":
                det = ch.get("details")
                rows.append(["字段检查", "%s · %s" % (fld, name), "—", "WARN",
                             (json.dumps(det, ensure_ascii=False) if det else "")[:150]])

    kw = rep.get("keyword_coverage", {})
    dup = kw.get("duplicates_across_layers", [])
    rows.append(["关键词分层", "跨层重复词数", len(dup), "—",
                 "同一词出现在 2 个及以上字段：%s"
                 % "、".join(x.get("word", "") for x in dup[:10])])
    for layer, v in kw.get("coverage_per_layer", {}).items():
        rows.append(["关键词分层", layer,
                     "%s/%s（%.0f%%）" % (v.get("hit"), v.get("total"), v.get("ratio", 0) * 100),
                     "—", "该字段命中率（整短语口径）"])
    rows.append(["关键词分层", "覆盖率口径", "整短语命中", "说明",
                 "关键词整条出现在该字段才算命中。与 CP-03 的词干匹配不同口径，数字必然更低，两者不可比"])

    tri = rep.get("triage_report", {})
    for p in tri.get("phrases", [])[:10]:
        rows.append(["标题分诊", p.get("phrase", ""), p.get("action", ""), "—",
                     p.get("reason", "")])

    acts = comp.get("action_items", [])
    kw_acts, other_acts = [], []
    for a in acts:
        (kw_acts if a.get("source") == "keyword" else other_acts).append(a)
    for a in other_acts:
        act = a.get("action", "")
        rows.append(["改进建议", a.get("source", ""), "—", "建议",
                     act if isinstance(act, str) else json.dumps(act, ensure_ascii=False)[:160]])
    if kw_acts:
        # 26 条跨层重复里大半是 for / and / or 这类虚词，逐条列会把表撑满且没有动作价值，合并成一条
        words = []
        for a in kw_acts:
            act = a.get("action", "")
            if isinstance(act, str):
                try:
                    act = ast.literal_eval(act)
                except (ValueError, SyntaxError):
                    pass
            if isinstance(act, dict):
                words.append(str(act.get("word", "")))
        rows.append(["改进建议", "keyword（合并 %d 条）" % len(kw_acts), "—", "建议",
                     "跨层重复词：%s。其中 for / and / or 等虚词可忽略，实词按「第二次出现不加权」原则处理"
                     % "、".join(w for w in words if w)[:150]])

    write_csv(outdir / out["score_detail"], header, rows)

    print("CDQ %s（%s）| 可用维度折算 %s | A9 %s | COSMO %s | 合规 %s 项失败 | 建议 %d 条"
          % (fmt_score(cdq.get("total")), cdq.get("grade"), fmt_score(derived),
             idx.get("score"), cos.get("score"), comp.get("failed_checks"), len(acts)))
    print("产物：%s / %s / %s" % (out["score_detail"], out["score_raw"], out["score_listing"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
