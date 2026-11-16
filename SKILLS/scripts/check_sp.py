#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
40-selling-point · 交付前自检

七项，退出码非 0 即失败（与 10-keyword 的 check.py 同一套规矩）：
  1 字段完整     主表列齐、sp_id 唯一、等级取值合法
  2 证据双维     A/B 级卖点必须同时有五点证据和评论证据
  3 单源占比     只有一维证据的卖点不得超过阈值
  4 A 级名额     A 级数量不超过配置名额，且每个 A 都过 G 门槛
  5 冲突披露     主表标了冲突的卖点，冲突表里必须有对应行
  6 覆盖可回查   证据链里五点命中的 ASIN 数 = 主表覆盖ASIN数
  7 无空证据     证据链每行的原文非空，且五点原文能在源文件里找到

用法：python check_sp.py [--dir 输出目录]
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
CASES = []


def ok(item, msg):
    CASES.append(("PASS", item, msg))


def fail(item, msg):
    CASES.append(("FAIL", item, msg))


def warn(item, msg):
    CASES.append(("WARN", item, msg))


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None)
    args = ap.parse_args()

    cfg = yaml.safe_load(open(Path(__file__).parent / "sp_config.yaml", encoding="utf-8"))
    outdir = Path(args.dir) if args.dir else ROOT / cfg["outputs"]["dir"]

    need = ["SP-01-卖点库.csv", "SP-02-证据链.csv", "SP-03-五点拆解矩阵.csv",
            "SP-04-图片降级清单.csv", "SP-05-评论映射.csv", "SP-06-冲突与风险.csv",
            "SP-07-待补证据.csv", "卖点库.xlsx"]
    missing = [f for f in need if not (outdir / f).exists()]
    if missing:
        fail("0 文件齐备", f"缺文件：{missing}")
        report(outdir)
        return 1

    main_rows = read_csv(outdir / "SP-01-卖点库.csv")
    evi_rows = read_csv(outdir / "SP-02-证据链.csv")
    conf_rows = read_csv(outdir / "SP-06-冲突与风险.csv")

    # ---------------- 1 字段完整
    hdr = set(main_rows[0].keys()) if main_rows else set()
    required = {"sp_id", "卖点名", "英文主张", "五点覆盖", "覆盖ASIN数", "好评验证条数",
                "差评条数", "M", "G机会分", "角色", "等级", "证据维度", "confidence"}
    miss = required - hdr
    ids = [r["sp_id"] for r in main_rows]
    if miss:
        fail("1 字段完整", f"主表缺列：{sorted(miss)}")
    elif len(ids) != len(set(ids)):
        fail("1 字段完整", "sp_id 有重复")
    elif any(r["等级"] not in ("A", "B", "C", "D") for r in main_rows):
        fail("1 字段完整", "等级出现 A/B/C/D 之外的值")
    elif any(not r["卖点名"].strip() for r in main_rows):
        fail("1 字段完整", "存在空卖点名")
    else:
        ok("1 字段完整", f"{len(main_rows)} 个卖点，列齐、ID 唯一、等级合法")

    # ---------------- 2 证据双维
    dims = {}
    for r in evi_rows:
        dims.setdefault(r["sp_id"], set()).add(r["维度"])
    bad = []
    for r in main_rows:
        if r["等级"] in ("A", "B"):
            d = dims.get(r["sp_id"], set())
            if "五点" not in d or "评论" not in d:
                bad.append(f"{r['sp_id']}{r['卖点名']}({r['等级']})")
    if bad:
        fail("2 证据双维", f"A/B 级缺一维证据：{bad}")
    else:
        ok("2 证据双维", "A/B 级卖点均同时具备五点与评论证据")

    # ---------------- 3 单源占比
    single = [r["sp_id"] for r in main_rows if len(dims.get(r["sp_id"], set())) < 2]
    ratio = len(single) / len(main_rows) if main_rows else 0
    limit = 0.40
    if ratio > 0.60:
        fail("3 单源占比", f"单源卖点 {len(single)}/{len(main_rows)} = {ratio:.0%}，超过 60%")
    elif ratio > limit:
        warn("3 单源占比", f"单源卖点 {len(single)}/{len(main_rows)} = {ratio:.0%}，超过警戒线 {limit:.0%}：{single}")
    else:
        ok("3 单源占比", f"单源卖点 {len(single)}/{len(main_rows)} = {ratio:.0%}")

    # ---------------- 4 A 级名额
    slots = cfg["grades"]["A"]["slots"]
    g_min = cfg["grades"]["A"]["g_min"]
    a_rows = [r for r in main_rows if r["等级"] == "A"]
    if len(a_rows) > slots:
        fail("4 A 级名额", f"A 级 {len(a_rows)} 个，超过名额 {slots}")
    elif any(float(r["G机会分"]) < g_min for r in a_rows):
        fail("4 A 级名额", f"A 级里有 G < {g_min} 的卖点")
    else:
        ok("4 A 级名额", f"A 级 {len(a_rows)}/{slots}，G 全部 ≥ {g_min}")

    # ---------------- 5 冲突披露
    flagged = [r["sp_id"] for r in main_rows if r["冲突"].strip().upper() == "Y"]
    listed = {r["sp_id"] for r in conf_rows}
    lost = [x for x in flagged if x not in listed]
    if lost:
        fail("5 冲突披露", f"主表标了冲突但冲突表没写：{lost}")
    else:
        ok("5 冲突披露", f"{len(flagged)} 个冲突卖点全部在冲突表中有行")

    # ---------------- 6 覆盖可回查
    bullet_asins = {}
    for r in evi_rows:
        if r["维度"] == "五点":
            bullet_asins.setdefault(r["sp_id"], set()).add(r["定位"].split("#")[0])
    mismatch = []
    for r in main_rows:
        got = len(bullet_asins.get(r["sp_id"], set()))
        want = int(float(r["覆盖ASIN数"] or 0))
        if got != want:
            mismatch.append(f"{r['sp_id']}: 证据链 {got} vs 主表 {want}")
    if mismatch:
        fail("6 覆盖可回查", f"覆盖 ASIN 数对不上：{mismatch[:5]}")
    else:
        ok("6 覆盖可回查", "每个卖点的覆盖 ASIN 数与证据链一致")

    # ---------------- 7 无空证据 + 原文可回查
    src = json.loads((ROOT / cfg["inputs"]["bullets_json"]).read_text(encoding="utf-8"))
    pool = {}
    for item in src:
        for i, b in enumerate(item.get("bullets") or [], 1):
            pool[f"{item['asin']}#{i}"] = b
    empty, notfound = [], []
    for r in evi_rows:
        if not (r["原文/计数"] or "").strip():
            empty.append(r["定位"])
            continue
        if r["维度"] == "五点":
            origin = pool.get(r["定位"])
            if origin is None:
                notfound.append(r["定位"])
            elif r["原文/计数"][:60] not in origin:
                notfound.append(r["定位"])
    if empty:
        fail("7 无空证据", f"有 {len(empty)} 行原文为空：{empty[:5]}")
    elif notfound:
        fail("7 无空证据", f"有 {len(notfound)} 条五点证据回查不到：{notfound[:5]}")
    else:
        ok("7 无空证据", f"{len(evi_rows)} 条证据全部非空，五点证据可回查原文")

    return report(outdir)


def report(outdir):
    fails = [c for c in CASES if c[0] == "FAIL"]
    warns = [c for c in CASES if c[0] == "WARN"]
    lines = ["卖点库交付自检", "=" * 60, ""]
    for status, item, msg in CASES:
        lines.append(f"[{status}] {item}  {msg}")
    lines.append("")
    lines.append(f"合计 {len(CASES)} 项：PASS {len(CASES) - len(fails) - len(warns)} / "
                 f"WARN {len(warns)} / FAIL {len(fails)}")
    lines.append("" if fails else "结论：全部通过，可以交付。")
    text = "\n".join(lines)
    print(text)
    (outdir / "08-卖点库自检.txt").write_text(text + "\n", encoding="utf-8")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
