#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
50-copy · 文案交付前自检

十五项（C0-C12，含 C2b），退出码非 0 即失败（与 check.py / check_sp.py / check_facts.py 同一套规矩）：
  C0  输入齐备     copy.json / 事实卡 / 词库 / 定稿卖点 都在
  C1  字段边界     标题 75 / 亮点 125 / 五点 150-255-500 / 描述 2000 / ST 250 字节
  C2  五点结构     恰好 5 条，冒号开头 + 含分号 + 句末无标点 + 首字母大写
  C2b 亮点结构     3-5 段短语，第 1 段 ≤40 字符且 ≤6 词（移动端展示位）
  C3  禁用表       红线 FAIL / AI 腔 FAIL / 空话 WARN / 品类禁写 FAIL
  C4  短语重复     同一整短语全篇 ≤3 次，最多出现在 1 条五点上
  C5  词根重复     P0 词根 ≤8 次/≤4 条，P1 词根 ≤3 次/≤2 条
  C6  可读性       连续名词 ≥4 个、单子句 >20 词（描述 ≤30）
  C7  覆盖         P0 未覆盖 FAIL / P1 未覆盖 WARN（须归因）/ P2 只报数
  C8  HTML 检查    四个字段零标签、零实体
  C9  事实越权     无实测承重时全篇禁 lbs / pound / kg
  C10 亮点重复     与标题重复的实义词 ≤2 个，且须过删除测试
  C11 描述密度     只报数，不评分（口径本身不成立）
  C12 官方边界     全大写 / 特殊字符 / 句末标点 / 单词 ≤2 次 / emoji / 占位 / 缩写 / 单位空格

用法：
  python check_copy.py --category sponge-holder
  python check_copy.py --category sponge-holder --no-write
  python check_copy.py --file path/to/copy.json --category sponge-holder
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
# emoji 与常见符号图形，官方要点 requirements 页明列禁项
EMOJI_RE = r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u2B00-\u2BFF\u2190-\u21FF]"
# C12 各命中类别 → severity 键 / issue 定位（2026-11-17 扩到 emoji、占位、缩写、单位空格）
HARD_SEV = {"全大写": "title_format", "特殊字符": "title_format", "句末标点": "title_format",
            "单词重复": "title_word_repeat", "促销语": "promo", "卖家信息": "promo",
            "emoji": "emoji", "占位内容": "placeholder"}
HARD_LOC = {"促销语": "全篇", "卖家信息": "全篇", "emoji": "全篇", "占位内容": "全篇"}
SOFT_SEV = {"尺寸重量": "title_measure", "颜色词": "title_color", "非拉丁字符": "title_measure",
            "不必要缩写": "abbrev", "单位缺空格": "unit_space"}
CASES = []
COVER = []
ISSUES = []


def ok(item, msg):
    CASES.append(("PASS", item, msg))


def fail(item, msg):
    CASES.append(("FAIL", item, msg))


def warn(item, msg):
    CASES.append(("WARN", item, msg))


def issue(level, check, loc, text, problem, fix):
    ISSUES.append({"level": level, "check": check, "位置": loc,
                   "原文": (text or "")[:120], "问题": problem, "建议": fix})


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig")))


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------- 文本工具 ----------------

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")


def tokens(text, stop=()):
    """切词 + 小写。stop 为空时不去停用词。"""
    out = []
    for m in TOKEN_RE.finditer((text or "").lower()):
        w = m.group(0)
        if w in stop:
            continue
        out.append(w)
    return out


def stem(w):
    """极简词干化：只处理复数与 -ing，够用且不引依赖。"""
    w = w.lower().strip(".,;:!?()[]{}\"'")
    if len(w) <= 3:
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("ss"):
        return w
    if w.endswith("es") and len(w) > 4:
        return w[:-2]
    if w.endswith("s"):
        return w[:-1]
    if w.endswith("ing") and len(w) > 5:
        return w[:-3]
    return w


def stems(text, stop=()):
    return [stem(t) for t in tokens(text, stop)]


def norm_phrase(s):
    return " ".join(tokens(s))


def count_phrase(phrase, text):
    """整短语出现次数（词边界匹配，避免 cup 命中 occupy）。"""
    p = norm_phrase(phrase)
    if not p:
        return 0
    t = norm_phrase(text)
    if not t:
        return 0
    return len(re.findall(r"(?<![a-z0-9])" + re.escape(p) + r"(?![a-z0-9])", t))


def bytes_len(s):
    return len((s or "").encode("utf-8"))


def clauses(text):
    """按句末与分号切子句，用于句长检查。"""
    parts = re.split(r"[.!?;:]", text or "")
    return [p.strip() for p in parts if p.strip()]


# ---------------- 主流程 ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, help="品类目录名，如 sponge-holder")
    ap.add_argument("--file", default=None, help="copy.json 路径，默认按配置推导")
    ap.add_argument("--config", default=str(Path(__file__).parent / "copy_config.yaml"))
    ap.add_argument("--no-write", action="store_true", help="只算不落盘")
    args = ap.parse_args()

    cfg = load_yaml(args.config)
    sev = cfg["severity"]
    inp = {k: v.replace("{category}", args.category) for k, v in cfg["inputs"].items()}
    outdir = ROOT / cfg["outputs"]["dir"].replace("{category}", args.category)

    copy_path = Path(args.file) if args.file else ROOT / inp["copy"]
    facts_path = ROOT / inp["facts"]
    lib_path = ROOT / inp["keyword_library"]
    sp_path = ROOT / inp["selected_sp"]

    # ---------- C0 输入齐备 ----------
    missing = [str(p) for p in [copy_path, facts_path, lib_path, sp_path] if not p.exists()]
    if missing:
        fail("C0 输入齐备", "缺文件：" + "；".join(missing))
        # 输入不全时一律不落盘，避免在建错的目录里生出一堆空产物
        report(outdir, cfg, True)
        return 2
    ok("C0 输入齐备", "copy.json / 事实卡 / 词库 / 定稿卖点 齐备")

    copy = json.load(open(copy_path, encoding="utf-8"))
    facts = json.load(open(facts_path, encoding="utf-8"))
    library = read_csv(lib_path)

    title = copy.get("title") or ""
    high = copy.get("highlights") or ""
    bullets = copy.get("bullets") or []
    desc = copy.get("description") or ""
    st = copy.get("search_terms") or ""
    frontend = " \n".join([title, high, " ".join(bullets), desc])

    stop = set(cfg["stopwords"])
    f = cfg["fields"]

    # ---------- C1 字段边界 ----------
    bad = []
    if len(title) > f["title"]["max"]:
        bad.append("标题 %d 字符 > %d" % (len(title), f["title"]["max"]))
        issue(sev["field_limit"], "C1", "title", title, "超 %d 字符" % f["title"]["max"], "先做词干压缩，再按序砍")
    if len(high) > f["highlights"]["max"]:
        bad.append("亮点 %d 字符 > %d" % (len(high), f["highlights"]["max"]))
        issue(sev["field_limit"], "C1", "highlights", high, "超 %d 字符" % f["highlights"]["max"], "挪词到五点")

    b = f["bullet"]
    short, long_ = [], []
    for i, bl in enumerate(bullets, 1):
        n = len(bl)
        if n > b["hard_max"]:
            bad.append("五点 %d 共 %d 字符 > %d" % (i, n, b["hard_max"]))
            issue(sev["field_limit"], "C1", "bullets[%d]" % (i - 1), bl,
                  "超官方硬上限 %d" % b["hard_max"], "删场景句，保证据")
        elif n > b["recommend_max"]:
            long_.append("第 %d 点 %d 字符" % (i, n))
            issue(sev["field_limit"] + "/建议", "C1", "bullets[%d]" % (i - 1), bl,
                  "超建议上限 %d" % b["recommend_max"], "压到 %d 字符内" % b["target_max"])
        elif n < b["target_min"]:
            short.append("第 %d 点 %d 字符" % (i, n))

    if long_:
        warn("C1 字段边界", "%d 条超建议上限 %d：%s" % (len(long_), b["recommend_max"], "、".join(long_)))
    if short:
        warn("C1 字段边界", "%d 条低于目标下界 %d：%s" % (len(short), b["target_min"], "、".join(short)))

    if len(desc) > f["description"]["max"]:
        bad.append("描述 %d 字符 > %d" % (len(desc), f["description"]["max"]))
        issue(sev["field_limit"], "C1", "description", "", "超 %d 字符" % f["description"]["max"], "压段")
    elif len(desc) > f["description"]["recommend_max"]:
        warn("C1 字段边界", "描述 %d 字符，超建议上限 %d" % (len(desc), f["description"]["recommend_max"]))

    if bytes_len(st) > f["st"]["max"]:
        bad.append("ST %d 字节 > %d" % (bytes_len(st), f["st"]["max"]))
        issue(sev["field_limit"], "C1", "search_terms", st,
              "超 %d 字节" % f["st"]["max"], "删低相关性词")

    if bad:
        fail("C1 字段边界", "；".join(bad))
    else:
        ok("C1 字段边界", "标题 %d/%d，亮点 %d/%d，五点 %d-%d 字符，描述 %d，ST %d 字节"
           % (len(title), f["title"]["max"], len(high), f["highlights"]["max"],
              min([len(x) for x in bullets], default=0),
              max([len(x) for x in bullets], default=0), len(desc), bytes_len(st)))

    # ---------- C2 五点结构 ----------
    cnt = f["bullet_count"]
    problems = []
    if not (cnt["min"] <= len(bullets) <= cnt["max"]):
        problems.append("五点 %d 条，应为 %d-%d 条" % (len(bullets), cnt["min"], cnt["max"]))

    st_cfg = cfg["structure"]
    for i, bl in enumerate(bullets, 1):
        loc = "bullets[%d]" % (i - 1)
        if not bl.strip():
            problems.append("五点 %d 为空" % i)
            continue
        if st_cfg["bullet_requires_colon"] and ":" not in bl:
            problems.append("五点 %d 缺冒号" % i)
            issue(sev["bullet_structure"], "C2", loc, bl, "缺官方要求的冒号分隔", "写成 Header: phrase; phrase")
        if st_cfg["bullet_requires_semicolon"] and ";" not in bl:
            problems.append("五点 %d 缺分号" % i)
            issue(sev["bullet_structure"], "C2", loc, bl, "缺官方要求的分号", "用分号分隔短语")
        if st_cfg["bullet_forbid_end_punct"] and re.search(r"[.!?]\s*$", bl):
            problems.append("五点 %d 句末有标点" % i)
            issue(sev["bullet_structure"], "C2", loc, bl, "句末标点违反官方 requirements 页", "删掉句末标点")
        if bl[:1] and not bl[:1].isupper():
            problems.append("五点 %d 首字母未大写" % i)
            issue(sev["bullet_structure"], "C2", loc, bl, "官方要求 Begin with a capital letter", "首字母大写")

    if st_cfg["highlights_forbid_sentence"] and re.search(r"[.!?]", high):
        problems.append("亮点含完整句子标点")

    if problems:
        fail("C2 五点结构", "；".join(sorted(set(problems))))
    else:
        ok("C2 五点结构", "%d 条，冒号 + 分号 + 句末无标点 + 首字母大写" % len(bullets))

    # ---------- C2-b 亮点短语结构（2026-11-17 补，WARN 级）----------
    # 依据：官方 Item Highlights 示例为逗号分隔的短语，不是主谓句。
    # 短语内部列举也用逗号（fits glass, tile and steel），所以段数按切分数算、区间放宽。
    if high.strip():
        dec = cfg.get("decisions") or {}
        pmin = int(dec.get("highlight_phrase_min", 3))
        pmax = int(dec.get("highlight_phrase_max", 5))
        wmax = int(dec.get("highlight_phrase_max_words", 8))
        vis = int(dec.get("highlight_mobile_visible_chars", 40))
        phrases = [p.strip() for p in high.split(",") if p.strip()]
        hp = []
        if not (pmin <= len(phrases) <= pmax):
            hp.append("%d 段短语，应在 %d-%d 段" % (len(phrases), pmin, pmax))
        if phrases and len(phrases[0]) > vis:
            hp.append("第 1 段 %d 字符，超移动端可见位 %d" % (len(phrases[0]), vis))
        for i, p in enumerate(phrases, 1):
            if len(p.split()) > wmax:
                hp.append("第 %d 段 %d 词，超 %d" % (i, len(p.split()), wmax))
        if hp:
            warn("C2b 亮点结构", "；".join(hp))
            issue("WARN", "C2", "highlights", high, "亮点短语结构不合规则", "拆成 3-5 段短语，每段 ≤8 词，第 1 段 ≤40 字符")
        else:
            ok("C2b 亮点结构", "%d 段短语，第 1 段 %d 字符，最长 %d 词"
               % (len(phrases), len(phrases[0]), max(len(p.split()) for p in phrases)))

    # ---------- C3 禁用表 ----------
    dis = cfg["disallowed"]
    hits = {"redline": [], "ai_cliche": [], "vague": []}
    for name in hits:
        for w in dis[name]:
            n = count_phrase(w, frontend)
            if n:
                hits[name].append("%s×%d" % (w, n))
    cat_forbidden = []
    for item in (cfg.get("categories", {}).get(args.category, {}) or {}).get("forbidden", []):
        if count_phrase(item["word"], frontend):
            cat_forbidden.append(item["word"])
            issue(sev["category_forbidden"], "C3", "全篇", item["word"], item["reason"], "删词并回查卖点库")

    if hits["redline"] or hits["ai_cliche"]:
        fail("C3 禁用表", "红线：%s｜AI 腔：%s"
             % ("、".join(hits["redline"]) or "无", "、".join(hits["ai_cliche"]) or "无"))
        for w in dis["redline"]:
            if count_phrase(w, frontend):
                issue(sev["redline"], "C3", "全篇", w, "红线词",
                      dis["replacements"].get(w, "改为可验证表述"))
        for w in dis["ai_cliche"]:
            if count_phrase(w, frontend):
                issue(sev["ai_cliche"], "C3", "全篇", w, "营销腔，无信息量", "换成具体动作或条件")
    elif cat_forbidden:
        fail("C3 禁用表", "品类禁写：%s" % "、".join(cat_forbidden))
    else:
        ok("C3 禁用表", "红线 0 / AI 腔 0 / 品类禁写 0；空话 %d"
           % len(hits["vague"]))
    if hits["vague"]:
        warn("C3 禁用表", "空话：%s（占掉了能写事实的位置）" % "、".join(hits["vague"]))
        for w in dis["vague"]:
            if count_phrase(w, frontend):
                issue(sev["vague"], "C3", "全篇", w, "无证据的形容词", "换成材料/尺寸/场景事实")

    # ---------- C4 短语重复 ----------
    emb = cfg["embedding"]
    cand = [r for r in library if (r.get("prio") or "") in ("P0", "P1")]
    over_total, over_bullet = [], []
    for r in cand:
        kw = (r.get("keyword") or "").strip()
        if not kw:
            continue
        total = count_phrase(kw, title) + count_phrase(kw, high) + count_phrase(kw, desc) \
            + sum(count_phrase(kw, x) for x in bullets)
        n_bul = sum(1 for x in bullets if count_phrase(kw, x))
        if total > emb["phrase_total_max"]:
            over_total.append("%s×%d" % (kw, total))
        if n_bul > emb["phrase_max_bullets"]:
            over_bullet.append("%s 占 %d 条" % (kw, n_bul))
    if over_total or over_bullet:
        warn("C4 短语重复", "全篇超限：%s｜跨条超限：%s"
             % ("、".join(over_total) or "无", "、".join(over_bullet) or "无"))
        for kw in over_total + over_bullet:
            issue(sev["phrase_repeat"], "C4", "全篇", kw, "同一短语重复", "删一处，或换同义变体")
    else:
        ok("C4 短语重复", "P0/P1 短语全篇 ≤%d 次、每条五点 ≤%d 条短语"
           % (emb["phrase_total_max"], emb["phrase_max_bullets"]))

    # ---------- C5 词根重复 ----------
    # 注意：词库的 root 列是语义维度（共性/品类/属性），不是词根。
    # 词根一律从 P0/P1 关键词的实义 token 现推，否则这条检查会静默变成空跑。
    # 分两档（2026-11-17）：P0 是品类核心词，一篇讲"水槽海绵架"的文案里 sink 出现 7 次是必然；
    # P1 是长尾修饰词，重复才是堆词。
    core_roots, long_roots = set(), set()
    for r in cand:
        bucket = core_roots if (r.get("prio") or "") == "P0" else long_roots
        for t in tokens(r.get("keyword") or "", stop):
            bucket.add(stem(t))
    long_roots -= core_roots          # 已被 P0 认领的词根不再按 P1 计
    front_tokens = stems(frontend, stop)
    root_hit = []
    checks = [(x, emb["root_core_total_max"], emb["root_core_max_bullets"], "P0")
              for x in sorted(core_roots)]
    checks += [(x, emb["root_total_max"], emb["root_max_bullets"], "P1")
               for x in sorted(long_roots)]
    for rt, t_max, b_max, tier in checks:
        total = front_tokens.count(rt)
        if total <= 0:
            continue
        nb = sum(1 for x in bullets if rt in stems(x, stop))
        if total > t_max or nb > b_max:
            root_hit.append("%s[%s] 全篇%d次/五点%d条" % (rt, tier, total, nb))
    if root_hit:
        warn("C5 词根重复", "超限 %d 个词根：%s（P0 上限 全篇%d/五点%d；P1 上限 %d/%d）"
             % (len(root_hit), "；".join(root_hit[:6]),
                emb["root_core_total_max"], emb["root_core_max_bullets"],
                emb["root_total_max"], emb["root_max_bullets"]))
        for x in root_hit:
            issue(sev["root_repeat"], "C5", "全篇", x.split(" ")[0], x, "换同义变体或删一处")
    else:
        ok("C5 词根重复", "P0 词根 ≤%d次/≤%d条；P1 词根 ≤%d次/≤%d条"
           % (emb["root_core_total_max"], emb["root_core_max_bullets"],
              emb["root_total_max"], emb["root_max_bullets"]))

    # ---------- C6 可读性 ----------
    lexicon = set()
    for r in library:
        for t in tokens(r.get("keyword") or "", stop):
            lexicon.add(stem(t))
    noun_runs = []
    for loc, text in [("title", title), ("highlights", high), ("description", desc)] + \
                     [("bullets[%d]" % i, x) for i, x in enumerate(bullets)]:
        # 按标点切段，避免 "Kitchen Sink, Sink Caddy" 跨逗号连成一串
        for seg in re.split(r"[,;:.!?()\[\]|/]", text):
            run = []
            for t in tokens(seg):
                if stem(t) in lexicon:
                    run.append(t)
                    if len(run) == emb["noun_run_warn"]:
                        noun_runs.append((loc, " ".join(run)))
                else:
                    run = []
    noun_runs = list(dict.fromkeys(noun_runs))

    long_clauses = []
    # 描述天然比五点句子长，用单独阈值（2026-11-17 加）
    desc_max = emb.get("desc_sentence_max_words", emb["sentence_max_words"])
    for loc, text, cap in [("bullets[%d]" % i, x, emb["sentence_max_words"])
                           for i, x in enumerate(bullets)] + [("description", desc, desc_max)]:
        for c in clauses(text):
            n = len(tokens(c))
            if n > cap:
                long_clauses.append((loc, n, c, cap))

    if noun_runs or long_clauses:
        msg = []
        if noun_runs:
            msg.append("名词串联 %d 处（%s：%s）" % (len(noun_runs), noun_runs[0][0], noun_runs[0][1]))
            for loc, run in noun_runs:
                issue(sev["noun_run"], "C6", loc, run, "连续名词 ≥%d 个" % emb["noun_run_warn"], "插介词或拆分")
        if long_clauses:
            msg.append("长句 %d 处（%s）" % (len(long_clauses), "、".join("%s %d词" % (a, b) for a, b, _, _ in long_clauses[:3])))
            for loc, n, c, cap in long_clauses:
                issue(sev["sentence_len"], "C6", loc, c, "单子句 %d 词 > %d" % (n, cap), "断句")
        warn("C6 可读性", "；".join(msg))
    else:
        ok("C6 可读性", "无 ≥%d 个连续名词，无 >%d 词的单子句（描述 ≤%d）"
           % (emb["noun_run_warn"], emb["sentence_max_words"], desc_max))

    # ---------- C7 覆盖 ----------
    rule = cfg["coverage"]["missing_rule"]
    ignore = set(cfg["coverage"]["ignore_prio"])
    reasons = copy.get("coverage_reasons") or {}
    field_texts = [("title", title), ("highlights", high)] + \
                  [("bullets[%d]" % i, x) for i, x in enumerate(bullets)] + [("description", desc)]
    all_stems = set()
    for _, t in field_texts:
        all_stems.update(stems(t, stop))

    p0_miss, p1_miss, p1_noreason, counted = [], [], [], 0
    for r in library:
        prio = (r.get("prio") or "").strip()
        if prio in ignore or prio not in ("P0", "P1", "P2"):
            continue
        kw = (r.get("keyword") or "").strip()
        if not kw:
            continue
        need = [stem(t) for t in tokens(kw, stop)]
        covered = all(nt in all_stems for nt in need) if need else False
        where, form = "", ""
        if covered:
            exact_hit, stem_hit = "", ""
            for loc, t in field_texts:
                if count_phrase(kw, t):
                    exact_hit = exact_hit or loc
                elif all(stem(x) in set(stems(t, stop)) for x in tokens(kw, stop)):
                    stem_hit = stem_hit or loc
            if exact_hit:
                where, form = exact_hit, "EXACT"
            elif stem_hit:
                where, form = stem_hit, "STEM"
            else:
                # 所有词都在，但分散在不同字段：算覆盖，标拆词
                where, form = "跨字段", "SPLIT"
        verdict = "PASS" if covered else rule.get(prio, "IGNORE")
        reason = reasons.get(kw, "")
        layer = ""
        if reason.startswith("L0"):
            layer = "L0 事实"
        elif reason.startswith("L1"):
            layer = "L1 表达"
        elif reason.startswith("L2"):
            layer = "L2 重复"
        if not covered:
            counted += 1
            if prio == "P0":
                p0_miss.append(kw)
            elif prio == "P1":
                p1_miss.append(kw)
                if not layer:
                    p1_noreason.append(kw)
        COVER.append({"keyword": kw, "prio": prio, "W": r.get("W", ""),
                      "covered": "是" if covered else "否", "where": where, "form": form,
                      "layer": layer, "reason": reason, "verdict": verdict})

    p0_rule = rule.get("P0", "FAIL")
    if p0_miss and p0_rule == "FAIL":
        fail("C7 覆盖", "P0 未覆盖 %d 个：%s" % (len(p0_miss), "、".join(p0_miss)))
        for kw in p0_miss:
            issue("FAIL", "C7", "全篇", kw, "P0 必放词未覆盖", "补词或改文案")
    else:
        ok("C7 覆盖", "P0 全覆盖（%d 个 P0 词）"
           % sum(1 for r in library if (r.get("prio") or "") == "P0"))

    if p1_miss:
        if p1_noreason:
            warn("C7 覆盖", "P1 未覆盖 %d 个，其中 %d 个无归因：%s"
                 % (len(p1_miss), len(p1_noreason), "、".join(p1_noreason[:5])))
            for kw in p1_noreason:
                issue(sev["coverage_p1"], "C7", "全篇", kw, "P1 未覆盖且无归因", "写 L0/L1/L2 理由，或补词")
        else:
            ok("C7 覆盖", "P1 未覆盖 %d 个，均已归因" % len(p1_miss))

    # ---------- C8 HTML（2026-11-17 扩到全字段，原来只看描述）----------
    # 官方标题指南与要点指南都禁止 HTML/script 标签；描述自 2021 起不支持 HTML。
    # 所以不是「描述例外」，而是四个前台字段一律不允许标签与 HTML 实体。
    html_hits = []
    scan = [("title", title), ("highlights", high)]
    scan += [("bullets[%d]" % i, b) for i, b in enumerate(bullets)]
    if cfg["structure"].get("description_allow_html", False):
        scan_desc = []
    else:
        scan_desc = [("description", desc)]
    for loc, txt in scan + scan_desc:
        for h in re.findall(r"</?[a-zA-Z][^>]*>", txt):
            html_hits.append((loc, h))
        for e in re.findall(r"&[a-zA-Z]+;|&#\d+;", txt):
            html_hits.append((loc, e))
    if html_hits:
        fail("C8 HTML 检查", "含标签/实体：%s"
             % "、".join("%s:%s" % (l, h) for l, h in html_hits[:5]))
        for loc, h in html_hits[:10]:
            issue(sev["html_tag"], "C8", loc, h, "亚马逊全字段不支持 HTML", "删标签，用空行或标点分段")
    else:
        ok("C8 HTML 检查", "标题/亮点/五点/描述 零标签、零实体")

    # ---------- C9 事实越权 ----------
    load_tested = bool((facts.get("load") or {}).get("tested"))
    unit_hits = re.findall(r"\b\d+(?:\.\d+)?\s*(?:lbs?|pounds?|kgs?|kilograms?)\b", frontend, re.I)
    if unit_hits and not load_tested:
        fail("C9 事实越权", "事实卡 load.tested=false，但文案出现：%s" % "、".join(unit_hits[:5]))
        issue(sev["facts_units"], "C9", "全篇", "、".join(unit_hits[:3]),
              "无实测承重数据", "删数值，改结构描述")
    else:
        ok("C9 事实越权", "无实测承重数据，文案%s" % ("已禁 lbs/kg" if not load_tested else "含实测，允许写数值"))

    # ---------- C10 亮点重复标题 ----------
    # 用户 2026-11-17 裁决：允许重复，上限 2 个，且每个须过「删除测试」（删掉后句子是否还成立）
    t_stems = set(stems(title, stop))
    h_stems = set(stems(high, stop))
    overlap = sorted(t_stems & h_stems)
    allow = int((cfg.get("decisions") or {}).get("highlight_repeat_max", 2))
    if len(overlap) > allow:
        warn("C10 亮点重复", "重复标题实义词 %d 个，超上限 %d：%s"
             % (len(overlap), allow, "、".join(overlap[:8])))
        issue(sev["highlights_overlap"], "C10", "highlights", high,
              "重复标题实义词 %d 个，超上限 %d" % (len(overlap), allow), "换同义词变体或删掉凑数词")
    elif overlap:
        ok("C10 亮点重复", "重复标题实义词 %d 个（上限 %d）：%s｜逐个过删除测试，删掉后句子不成立才算表意必需"
           % (len(overlap), allow, "、".join(overlap)))
    else:
        ok("C10 亮点重复", "亮点与标题零实义词重叠")

    # ---------- C11 描述密度（只报数，不判 WARN，2026-11-17 改）----------
    # 为什么不再判：target 收的是 P0/P1 全部 token，而这些恰恰是描述里的普通名词
    # （sponge / holder / sink / kitchen）。一篇 100 词的描述出现 20 个是品类必然，
    # 不是堆词。真正的堆词由 C4（整短语重复）和 C5（词根重复）兜住。
    target = set()
    for r in library:
        if (r.get("prio") or "") in ("P0", "P1"):
            target.update(stem(t) for t in tokens(r.get("keyword") or "", stop))
    d_tokens = stems(desc, stop)
    hits = sum(1 for t in d_tokens if t in target)
    min_words = emb.get("desc_density_min_words", 100)
    if len(d_tokens) < min_words:
        ok("C11 描述密度", "描述仅 %d 词 < %d，不评估（小样本会失真）"
           % (len(d_tokens), min_words))
    else:
        density = hits / (len(d_tokens) / 100.0)
        ok("C11 描述密度", "%.1f 个目标词/100 词，描述 %d 词（仅报数，堆词看 C4/C5）"
           % (density, len(d_tokens)))

    # ---------- C12 官方标题与促销边界（2026-11-17 新增）----------
    # 依据：官方标题指南 GYTR6SYGFA5E3EQC + 要点指南 GX5L8BF8GLMML6CX
    # 官方口径：不得全大写、不得含特殊字符、须为名词短语（非完整句子）、
    #          不得含促销与卖家信息、尺寸与颜色不得进标题（除非是变体）。
    # 「规格槽」专指变体规格（尺码/件数/容量），不是产品尺寸——本品无变体，
    # 所以尺寸进标题属违规，只能进五点或描述作适配说明。
    brand = str(((facts.get("meta") or {}).get("brand") or "")).strip().lower()
    hard, soft = [], []

    if st_cfg.get("title_forbid_all_caps", True):
        minlen = st_cfg.get("title_all_caps_min_len", 4)
        for w in re.findall(r"[A-Za-z][A-Za-z'\-]*", title):
            core = re.sub(r"[^A-Za-z]", "", w)
            if len(core) >= minlen and core.isupper() and core.lower() != brand:
                hard.append(("全大写", w))

    for ch in st_cfg.get("title_forbid_special_chars", []):
        if ch in title:
            hard.append(("特殊字符", ch))

    if st_cfg.get("title_forbid_end_punct", True) and re.search(r"[.!?,;:]\s*$", title.strip()):
        hard.append(("句末标点", title.strip()[-1:]))

    if st_cfg.get("bullet_forbid_promo", True):
        for w in dis.get("promo", []):
            if re.search(r"\b" + re.escape(w) + r"\b", frontend, re.I):
                hard.append(("促销语", w))

    # 卖家信息：URL / 邮箱 / 电话，官方明列不得进标题
    if re.search(r"https?://|www\.|\S+@\S+\.\w+|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b", title, re.I):
        hard.append(("卖家信息", re.search(
            r"https?://\S*|www\.\S*|\S+@\S+\.\w+|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
            title, re.I).group(0)))

    # 非拉丁字符：美国站英文标题不应出现（emoji 已单列 FAIL，此处不重复报）
    if st_cfg.get("title_ascii_only", True):
        for ch in sorted(set(re.findall(r"[^\x00-\x7F]", title))):
            if not re.match(EMOJI_RE, ch):
                soft.append(("非拉丁字符", ch))

    if st_cfg.get("title_measure_warn", True):
        for m in re.findall(r"\b\d+(?:\.\d+)?\s*(?:in|inch|inches|cm|mm|oz|lbs?|kg|qt|gal)\b", title, re.I):
            soft.append(("尺寸重量", m.strip()))

    if st_cfg.get("title_color_warn", True):
        for w in dis.get("title_color_words", []):
            if re.search(r"\b" + re.escape(w) + r"\b", title, re.I):
                soft.append(("颜色词", w))

    # 标题内同一单词超限。依据：官方 2025 标题政策「同一单词不超过两次，冠词介词连词除外」
    wmax = st_cfg.get("title_same_word_max", 2)
    if wmax:
        exempt = set(str(w).lower() for w in st_cfg.get("title_exempt_words", []))
        if brand:
            exempt.add(brand)
        seen = {}
        for w in re.findall(r"[A-Za-z][A-Za-z'\-]*", title):
            lw = w.lower()
            if lw in exempt:
                continue
            seen[lw] = seen.get(lw, 0) + 1
        for w, n in sorted(seen.items(), key=lambda x: -x[1]):
            if n > wmax:
                hard.append(("单词重复", "%s×%d" % (w, n)))

    # emoji：官方要点 requirements 页明列禁项，全字段扫
    if st_cfg.get("frontend_forbid_emoji", True):
        for ch in sorted(set(re.findall(EMOJI_RE, frontend))):
            hard.append(("emoji", ch))

    # 占位内容（N/A、TBD）：官方要点 requirements 页明列
    for w in dis.get("placeholder", []):
        if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", frontend, re.I):
            hard.append(("占位内容", w))

    # 不必要缩写（qty / pkg / approx.）：官方要点 requirements 页明列
    for w in dis.get("abbrev", []):
        if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", frontend, re.I):
            soft.append(("不必要缩写", w))

    # 数字与单位之间缺空格（8.5in → 8.5 in）：官方要点 requirements 页
    if st_cfg.get("unit_space_required", True):
        for m in re.findall(r"\b\d+(?:\.\d+)?(?:in|inch|inches|cm|mm|oz|lbs?|kg|qt|gal|ft)\b", frontend):
            soft.append(("单位缺空格", m))

    if hard:
        msg = "；".join("%s %s" % (k, v) for k, v in hard[:6])
        if soft:
            msg += "｜另有 %d 处待确认：%s" % (len(soft), "、".join("%s %s" % (k, v) for k, v in soft[:4]))
        fail("C12 官方边界", msg)
        for k, v in hard[:12]:
            issue(sev.get(HARD_SEV.get(k, "title_format"), "FAIL"), "C12",
                  HARD_LOC.get(k, "title"), v, k, "官方明列禁项")
        for k, v in soft[:8]:
            issue(sev.get(SOFT_SEV.get(k, "title_measure"), "WARN"), "C12",
                  "title" if k in ("尺寸重量", "颜色词", "非拉丁字符") else "全篇", v, k,
                  "非变体请移到五点或描述" if k in ("尺寸重量", "颜色词") else "按官方写法改")
    elif soft:
        warn("C12 官方边界", "含 %d 处需确认：%s"
             % (len(soft), "、".join("%s %s" % (k, v) for k, v in soft[:6])))
        for k, v in soft[:8]:
            issue(sev.get(SOFT_SEV.get(k, "title_measure"), "WARN"), "C12",
                  "title" if k in ("尺寸重量", "颜色词", "非拉丁字符") else "全篇", v, k,
                  "非变体请移到五点或描述" if k in ("尺寸重量", "颜色词") else "按官方写法改")
    else:
        ok("C12 官方边界", "标题无全大写/特殊字符/句末标点/单词超限，无促销语、尺寸与颜色；全篇无 emoji、占位内容")

    return report(outdir, cfg, args.no_write)


def report(outdir, cfg, no_write):
    name = cfg["outputs"]["selfcheck"]
    lines = ["文案交付自检", "=" * 60, ""]
    for level, item, msg in CASES:
        lines.append("[%s] %s  %s" % (level, item, msg))
    fails = sum(1 for c in CASES if c[0] == "FAIL")
    warns = sum(1 for c in CASES if c[0] == "WARN")
    lines.append("")
    lines.append("合计 %d 项：PASS %d / WARN %d / FAIL %d"
                 % (len(CASES), sum(1 for c in CASES if c[0] == "PASS"), warns, fails))
    if fails:
        lines.append("结论：不许交付，先改 FAIL 项。")
    elif warns:
        lines.append("结论：可交付，WARN 项需在口径声明里逐条说明。")
    else:
        lines.append("结论：全部通过。")

    print("\n".join(lines))

    if no_write:
        return 1 if fails else 0

    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / name).write_text("\n".join(lines), encoding="utf-8")

    with open(outdir / cfg["outputs"]["coverage"], "w", encoding="utf-8-sig", newline="") as f:
        # 表头中文、机器键英文（与 SP-01 一致：id/指标用英文，说明列用中文）
        cols = [("keyword", "keyword"), ("prio", "prio"), ("W", "W"), ("covered", "是否覆盖"),
                ("where", "落位字段"), ("form", "命中形式"), ("layer", "词层级"),
                ("reason", "未覆盖归因"), ("verdict", "判定")]
        w = csv.writer(f)
        w.writerow([c[1] for c in cols])
        for row in COVER:
            w.writerow([row.get(c[0], "") for c in cols])

    with open(outdir / cfg["outputs"]["issues"], "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["level", "check", "位置", "原文", "问题", "建议"])
        w.writeheader()
        w.writerows(ISSUES)

    print("\n产物：%s / %s / %s" % (outdir / name, cfg["outputs"]["coverage"], cfg["outputs"]["issues"]))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
