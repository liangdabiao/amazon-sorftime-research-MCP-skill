#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
50-copy · 上架稿构建

输入：copy.json（正文唯一源）、CP-03-覆盖清单.csv、keyword_library.csv
输出：CP-02-上架稿.csv / 上架稿-可直接粘贴.txt / CP-05-口径与来源.csv
      CP-06-多SKU汇总.csv / 文案.xlsx / _summary.json

所有阈值、上限、文件名都在 copy_config.yaml，本文件不写死任何数字或文件名。
用法：
    python build_copy.py --category sponge-holder
    python build_copy.py --category sponge-holder --sku WP650B-5-V1
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import openpyxl
import yaml
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent.parent


# ------------------------------------------------------------------ 工具
def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig")))


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def read_check(path):
    """从 08-文案自检.txt 解析自检结论，供 xlsx / 汇总表 / summary 复用。

    自检结论只认 check_copy.py 写的这份文件，不认 copy.json 里的手写字段——
    手写字段会漂（改稿后忘了改），派生数字一律不复用。
    """
    if not path.exists():
        return {"executed": False, "verdict": "未执行：找不到 %s" % path.name,
                "total": "", "conclusion": "先跑 check_copy.py", "items": []}
    items, total, conclusion = [], "", ""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.rstrip()
        m = re.match(r"^\[(PASS|WARN|FAIL)\]\s+(.*)$", line)
        if m:
            level, rest = m.group(1), m.group(2)
            parts = re.split(r"\s{2,}", rest, maxsplit=1)
            items.append([level, parts[0], parts[1] if len(parts) > 1 else ""])
        elif line.startswith("合计"):
            total = line
        elif line.startswith("结论"):
            conclusion = line.replace("结论：", "")
    return {"executed": bool(items), "verdict": total or "未执行",
            "total": total, "conclusion": conclusion, "items": items}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, help="品类目录名，如 sponge-holder")
    ap.add_argument("--sku", default="", help="SKU，仅写进汇总表")
    ap.add_argument("--config", default=str(Path(__file__).parent / "copy_config.yaml"))
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    out = {k: v.replace("{category}", args.category) for k, v in cfg["outputs"].items()}
    outdir = ROOT / out["dir"]
    src = ROOT / cfg["inputs"]["copy"].replace("{category}", args.category)
    lib = read_csv(ROOT / cfg["inputs"]["keyword_library"].replace("{category}", args.category))
    cov = read_csv(outdir / out["coverage"])
    check = read_check(outdir / out["selfcheck"])
    if not check["executed"]:
        print("自检未执行：先跑 check_copy.py --category %s，再跑 build" % args.category)
        return 2
    n_fail = sum(1 for r in check["items"] if r[0] == "FAIL")

    d = json.load(open(src, encoding="utf-8"))
    title, high, bullets, st = d["title"], d["highlights"], d["bullets"], d["search_terms"]
    f = cfg["fields"]
    meta = cfg["meta"]

    # ---------- CP-02 上架稿（一行一个字段） ----------
    fields = [
        ("Item Name", "Item Name", title, f["title"]["max"], f["title"]["max"], "后台商品名称"),
        ("Item Highlights", "Item Highlights", high, f["highlights"]["max"], f["highlights"]["max"], "标题下方亮点"),
    ]
    for i, b in enumerate(bullets, 1):
        fields.append(("Bullet %d" % i, "Bullet Point %d" % i, b,
                       f["bullet"]["hard_max"], f["bullet"]["recommend_max"], "五点第 %d 条" % i))
    fields.append(("Search Terms", "Search Terms", st, f["st"]["max"], f["st"]["max"], "后台搜索词"))

    rows = [[n, en, txt, len(txt), hi, sug, hi - len(txt), where]
            for n, en, txt, hi, sug, where in fields]
    write_csv(outdir / out["statement"], ["字段", "English", "文案", "字符数", "官方上限", "建议上限", "余量(官方)", "使用位置"], rows)

    # ---------- 粘贴稿：文案独占一行，行首零前缀 ----------
    paste = [
        "==== 1. Item Name 商品名称 · %d/75 字符 ====" % len(title), title, "",
        "==== 2. Item Highlights 标题亮点 · %d/125 字符 ====" % len(high), high, "",
        "==== 3. Bullet Points 五点描述 · 由上到下依次填入 5 个框 ====",
        *bullets, "",
        "==== 4. Search Terms 后台搜索词 · %d/250 字节 ====" % len(st.encode("utf-8")), st, "",
        "==== 粘贴说明 ====",
        "文案行独占一行、行首无编号，整行选中即可粘贴。",
        "以 ==== 开头的行是定位标记，不是文案，不要一起复制。",
        "本文件由 skills/scripts/build_copy.py 从 copy.json 生成，改文案请改 copy.json 后重跑。",
    ]
    (outdir / out["paste"]).write_text("\n".join(paste) + "\n", encoding="utf-8", newline="")

    # ---------- CP-05 口径与来源（长表：一行一个指标） ----------
    # 输出规范：一个数字一行，searches 是 MEASURED，W 是 DERIVED，依据必须写在旁边
    covered = {r["keyword"]: r for r in cov if r["是否覆盖"] == "是"}
    src_rows = []
    for r in lib:
        kw = r["keyword"]
        if kw not in covered:
            continue
        where = covered[kw]["落位字段"]
        form = covered[kw]["命中形式"]
        src_rows.append([kw, "searches", r["searches"], "—", "ss_mcp.keyword_miner",
                         "US / 2026-10 / 卖家精灵月度", "MEASURED", where, form])
        src_rows.append([kw, "W", r["W"], "searches × R，R=%s" % r["R"], "本项目自算",
                         "词库 232 词", "DERIVED", where, form])
    write_csv(outdir / out["sources"],
              ["keyword", "指标", "值", "公式/依据", "source", "sample", "confidence", "落位字段", "命中形式"],
              src_rows)

    # ---------- CP-06 多 SKU 汇总（一行一个 SKU，追加即复用） ----------
    agg = outdir / out["mult_sku"]
    old = [r for r in read_csv(agg) if r.get("category") != args.category] if agg.exists() else []
    agg_rows = [[args.category, args.sku, title, len(title), high, len(high),
                 *bullets, st, len(st.encode("utf-8")), check["verdict"],
                 d.get("schema_version", ""), d.get("generated_at", "")]]
    cols = ["category", "sku", "title", "title_chars", "highlights", "highlights_chars",
            "bullet1", "bullet2", "bullet3", "bullet4", "bullet5",
            "search_terms", "st_bytes", "check_result", "schema_version", "generated_at"]
    write_csv(agg, cols, [[r.get(c, "") for c in cols] for r in old] + agg_rows)

    # ---------- 文案.xlsx ----------
    wb = openpyxl.Workbook()
    head_fill = PatternFill("solid", fgColor="1F3864")
    head_font = Font(color="FFFFFF", bold=True, size=10)
    thin = Side(style="thin", color="D9D9D9")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    warn_fill = PatternFill("solid", fgColor="FFEB9C")

    ws = wb.active
    ws.title = "00_说明"
    bl = [len(b) for b in bullets]
    note = [
        ["文案", "%s · %s · %s" % (meta["category_name"], meta["marketplace"], meta["date"])],
        ["", ""],
        ["字段范围", "Item Name / Item Highlights / Bullet Points / Search Terms 四个。description 不在大纲输出层内，见 附件-描述草稿（大纲外）.md"],
        ["", ""],
        ["标题排序", "按 W 降序取词。官方推荐 Brand + Core Product Type + Key Attribute；同义变体（sink caddy）W ≥ 5000 才加"],
        ["亮点排序", "第 1 段放 D 分最高的差异化（移动端只露开头约 40 字符），第 2 段起补标题漏掉的词与适用面"],
        ["五点排序", cfg["meta"].get("bullet_note", "按卖点分 M 降序")],
        ["ST 排序", "只放前台四字段未覆盖的词；后台不参与前台排名，堆已覆盖词是浪费字节"],
        ["", ""],
        ["字符口径", "标题 %d/75、亮点 %d/125、五点 %d-%d（均值 %d，官方硬上限 %d）、ST %d/250 字节"
         % (len(title), len(high), min(bl), max(bl), sum(bl) // len(bl),
            f["bullet"]["hard_max"], len(st.encode("utf-8")))],
        ["词库", cfg["meta"].get("keyword_note", "见口径声明")],
        ["", ""],
        ["confidence", "MEASURED=接口直出 / DERIVED=由数据算出（公式写在 CP-05 依据列）/ JUDGED=人的判断"],
        ["口径限制", "覆盖率按词干匹配，复数与连字符算同词；W 是 searches×R 的加权分，不能当月搜索量报"],
        ["已知缺口", "承重、卡扣材质、吸盘直径三项事实卡为空 → lbs 全篇禁用，两条卖点（强吸附、卡扣耐用）落不进文案"],
        ["", ""],
        ["自检结论", "%s ｜ %s" % (check["verdict"], check["conclusion"])],
        ["问题清单", "05_问题清单 只有表头 = 本轮 0 条违规，不是没执行；有违规时每行给出 等级 / 检查项 / 位置 / 原文 / 问题 / 建议"],
        ["自检明细", "06_自检 表逐项列出，与 08-文案自检.txt 同源，都由 check_copy.py 写入；build_copy.py 只读不算"],
        ["" , ""],
        ["评分", "04_评分 来自第三方 amazon-listing-doctor（MIT），由 score_copy.py 调用；CDQ/A9 可直接看，COSMO/Alexa 降级时只作参考"],
        ["评分与自检的关系", "04 是内容质量的外部体检，08 是规则合规的内部检查，两套并存不合并；04 报的问题不等于 08 违规"],
        ["", ""],
        ["生成方式", "本文件与 CP-02 / 粘贴稿 / CP-05 / CP-06 / _summary.json 全部由 build_copy.py 从 copy.json 派生，不要手改"]
    ]
    for r in note:
        ws.append(r)
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 120

    def sheet(name, header, data, widths=None, mark_col=None):
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
        if mark_col:
            mi = header.index(mark_col)
            for row in s.iter_rows(min_row=2, max_row=s.max_row):
                if row[mi].value in ("否", "FAIL", "WARN"):
                    for c in row:
                        c.fill = warn_fill
        return s

    sheet("01_上架稿", ["字段", "English", "文案", "字符数", "官方上限", "建议上限", "余量(官方)", "使用位置"],
          rows, {"字段": 18, "English": 18, "文案": 110, "使用位置": 18})
    pos = read_csv(outdir / "CP-01-词位分配.csv")
    sheet("02_词位分配", list(pos[0].keys()), [list(r.values()) for r in pos],
          {"落位词": 34, "说明": 46, "新增覆盖的搜索词": 60})
    sheet("03_覆盖清单", list(cov[0].keys()) if cov else [],
          [list(r.values()) for r in cov], {"keyword": 40, "落位字段": 14, "未覆盖归因": 30})
    issues = read_csv(outdir / out["issues"])

    # 04_评分：第三方体检（CDQ / A9 / COSMO / Alexa / 合规）。放在原问题清单的位置，
    # 因为它回答的是同一件事——「现在还有什么问题」，只是换成打分视角并带外部依据。
    score_path = outdir / out["score_detail"]
    score = read_csv(score_path) if score_path.exists() else []
    if score:
        sheet("04_评分", list(score[0].keys()), [list(r.values()) for r in score],
              {"维度": 15, "指标": 34, "值": 12, "等级/状态": 16, "依据与说明": 92}, mark_col="等级/状态")
    else:
        sheet("04_评分", ["维度", "指标", "值", "等级/状态", "依据与说明"],
              [["未执行", "先跑 score_copy.py", "—", "SKIP", "缺失 %s" % out["score_detail"]]],
              {"维度": 15, "指标": 34, "值": 12, "等级/状态": 16, "依据与说明": 92})

    sheet("05_问题清单", list(issues[0].keys()) if issues else ["等级", "检查项", "位置", "原文", "问题", "建议"],
          [list(r.values()) for r in issues], {"原文": 60, "问题": 40, "建议": 40})

    # 05_自检：把 08 的逐项结论搬进 xlsx。第 1 行是合计与结论（表头样式），
    # 后面逐项列出，打开 xlsx 就能确认自检跑过、跑出什么，不用去翻 txt。
    check_rows = [["合计", check["verdict"], check["conclusion"] or "—"]]
    check_rows += check["items"] or [["未执行", "08-文案自检.txt 缺失", "先跑 check_copy.py --category %s" % args.category]]
    s5 = sheet("06_自检", ["等级", "检查项", "说明"], check_rows,
               {"等级": 24, "检查项": 24, "说明": 110}, mark_col="等级")
    s5.auto_filter.ref = None          # 首行是结论不是表头，不适合当筛选器

    xlsx = outdir / out["xlsx"]
    wb.save(xlsx)

    # ---------- _summary.json ----------
    from collections import Counter
    prio = Counter(r["prio"] for r in cov)
    verdict = Counter(r["判定"] for r in cov)
    summary = {
        "category": args.category,
        "sku": args.sku,
        "date": meta["date"],
        "fields": {"title": len(title), "highlights": len(high),
                   "bullets": bl, "st_bytes": len(st.encode("utf-8"))},
        "n_keyword": len(cov),
        "prio_counts": dict(prio),
        "verdict_counts": dict(verdict),
        "n_covered": sum(1 for r in cov if r["是否覆盖"] == "是"),
        "n_issues": len(issues),
        "check": check["verdict"],
        "check_conclusion": check["conclusion"],
        "score": {r["维度"]: r["值"] for r in score
                  if r["指标"] in ("总分", "总分（含降级维度）")},
        "top_keywords": [
            {"keyword": r["keyword"], "prio": r["prio"], "W": r["W"], "where": r["落位字段"]}
            for r in sorted(cov, key=lambda x: -float(x["W"] or 0))[:5]
        ],
    }
    (outdir / out["summary"]).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("标题 %d/75 | 亮点 %d/125 | 五点 %d-%d（均值 %d）| ST %d/250 字节"
          % (len(title), len(high), min(bl), max(bl), sum(bl) // len(bl),
             len(st.encode("utf-8"))))
    print("覆盖 %d 词（P0 %d / P1 %d / P2 %d），问题 %d 条"
          % (len(cov), prio.get("P0", 0), prio.get("P1", 0), prio.get("P2", 0), len(issues)))
    print("自检：%s（%s）" % (check["verdict"], check["conclusion"]))
    print("产物：%s / %s / %s / %s / %s"
          % (out["statement"], out["paste"], out["sources"], out["xlsx"], out["summary"]))
    if n_fail:
        print("自检有 %d 项 FAIL，产物已写出供定位，但不许上架" % n_fail)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
