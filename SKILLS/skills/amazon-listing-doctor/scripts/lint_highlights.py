#!/usr/bin/env python3
"""lint_highlights.py — 校验 item_highlights 字段（2026 新规）。

核心认知（2026-08 联网核实，一手来源）：标题(title)与商品亮点(item_highlights)
在后台是两个独立字段，但前端实际渲染把两者用竖线 `|`（pipe U+007C）拼成一行
显示在标题位（亚马逊官方承认的展示 bug，正在调查）。因此质检不能 title /
highlights 各查各的——本脚本除校验 highlights 字段本身，还产出"合并呈现串"
(display_string) 视角，含跨字段重复词(WARN，标 TBD)。

检查项：
  硬规(影响 compliant)：
    1. char_limit        ≤ max_chars(125)
    2. min_clauses       ≥ min_short_clauses(3) 个短语
  软规(仅 WARN，不计入 compliant)：
    3. separator_format  逗号分隔（官方要求；用了 ;/|/换行 等非逗号分隔符→WARN）
    4. phrase_not_sentence 逗号分隔的短语、非完整句子（含句号/单段超长→WARN）
    5. no_embedded_pipe  内容不应自含 `|`/`¦`（系统渲染层自动拼接，手填会干扰）
    6. char_utilization  尽量用满 125 字符预算（A9 索引空间）
    7. distinct_from_title 不整段重复标题文本
    8. cross_field_repeat 跨字段重复词（拼接同行后买家会看到堆砌，TBD 无官方明文）

顶层 display_string：合并呈现串预览(title | highlights) + 合并字符数。

输入：{item_highlights, title, language, mode, category}
输出：stdout 单个 JSON 对象；退出码 0=全通过(无 FAIL) / 1=有 FAIL。
"""

import sys
import json
import argparse
import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent

# 复用 lint_title 的归一化/分词能力做跨字段重复词（同目录 import）。
# CLI 直跑时 sys.path[0] 即 scripts 目录，import lint_title 可直接命中。
try:
    import lint_title as _lt
    _HAS_LINT_TITLE = True
except Exception:
    _HAS_LINT_TITLE = False


# --------------------------------------------------------------------------- #
# 配置加载
# --------------------------------------------------------------------------- #
def _load_rules():
    """从 references/rules.json 读取规则；缺失则返回空 dict（用默认值兜底）。"""
    rules_path = SKILL_ROOT / "references" / "rules.json"
    if rules_path.exists():
        return json.loads(rules_path.read_text(encoding="utf-8"))
    return {}


# --------------------------------------------------------------------------- #
# 纯工具函数
# --------------------------------------------------------------------------- #
def _normalize_text(s):
    """归一化文本：去除所有非字母数字/中文的字符（空格、标点、分隔符），并小写。

    用于判断 highlights 与 title 是否"实质相同"。
    """
    return re.sub(r"[^a-zA-Z0-9一-鿿]", "", s).lower()


def _split_clauses(highlights):
    """按常见分隔符切分 highlights 为短语列表，过滤空段（用于 clause_count）。

    支持分隔符：, ， ; ； | ｜ 以及换行（计数时兼容多种写法）。
    注：separator_format check 会单独标记"非逗号分隔符"为 WARN。
    """
    parts = re.split(r"[,，;；|｜\n\r]+", highlights)
    return [p.strip() for p in parts if p.strip()]


def _split_by_comma(highlights):
    """仅按逗号切分（用于短语粒度的句子启发式检测）。"""
    parts = re.split(r"[,，]+", highlights)
    return [p.strip() for p in parts if p.strip()]


# --------------------------------------------------------------------------- #
# 各检查项（纯函数）
# --------------------------------------------------------------------------- #
def check_char_limit(highlights, h_rules):
    """字符数上限：≤ max_chars(125) 即 PASS，否则 FAIL。"""
    max_chars = h_rules.get("max_chars", 125)
    actual = len(highlights)
    return {"status": "PASS" if actual <= max_chars else "FAIL",
            "actual": actual, "limit": max_chars}


def check_min_clauses(clause_count, h_rules):
    """最少短语数：≥ min_short_clauses(3) 即 PASS，否则 FAIL。"""
    min_clauses = h_rules.get("min_short_clauses", 3)
    return {"status": "PASS" if clause_count >= min_clauses else "FAIL",
            "actual": clause_count, "limit": min_clauses}


def check_separator_format(highlights):
    """官方要求逗号分隔短语；出现非逗号分隔符(;；|｜换行)→WARN。"""
    non_comma = sorted(set(re.findall(r"[;；|｜\n\r]", highlights)))
    if non_comma:
        return {"status": "WARN", "found": non_comma,
                "details": ["检测到非逗号分隔符，官方要求用逗号分隔短语"]}
    return {"status": "PASS", "found": []}


def check_phrase_not_sentence(highlights, h_rules):
    """逗号分隔的短语、非完整句子。启发式：含句号或单段超长→WARN。

    非语法分析（那是 LLM 的活），仅给提示进人工复核。
    """
    max_clause = h_rules.get("max_clause_chars", 40)
    clauses = _split_by_comma(highlights)
    long_clauses = [c for c in clauses if len(c) > max_clause]
    # 句号检测：先把小数(1.5)抠掉，再查是否含独立句号
    has_period = bool(re.search(r"[.。]", re.sub(r"\d\.\d", "", highlights)))
    details = []
    if long_clauses:
        details.append(f"{len(long_clauses)} 个短语超过 {max_clause} 字符，可能写成完整句子")
    if has_period:
        details.append("含句号，亮点应为短语而非完整句子")
    if details:
        return {"status": "WARN", "details": details}
    return {"status": "PASS", "details": []}


def check_no_embedded_pipe(highlights):
    """内容不应自含 |（pipe U+007C）或 ¦（broken bar U+00A6）。

    系统渲染层会自动用 | 把标题与亮点拼成一行，手填会干扰拼接。
    """
    found = []
    if "|" in highlights:  # |
        found.append("| (pipe U+007C)")
    if "¦" in highlights:  # ¦
        found.append("¦ (broken bar U+00A6，且为标题禁用字符)")
    if found:
        return {"status": "WARN", "found": found,
                "details": ["亮点内容不应自含分隔符，系统渲染层会自动拼接标题与亮点"]}
    return {"status": "PASS", "found": []}


def check_char_utilization(highlights, h_rules):
    """尽量用满 125 字符预算（A9 索引空间最大化）。WARN 级建议。

    空亮点跳过（不强制填亮点）。
    """
    max_chars = h_rules.get("max_chars", 125)
    if not highlights.strip():
        return {"status": "PASS", "actual": 0, "limit": max_chars,
                "skipped": True, "details": ["亮点为空，跳过利用率检查"]}
    actual = len(highlights)
    full_threshold = max_chars - 3  # 留 3 字符安全余量(122)
    if actual >= full_threshold:
        return {"status": "PASS", "actual": actual, "limit": max_chars,
                "details": [f"用满预算 {actual}/{max_chars}"]}
    return {"status": "WARN", "actual": actual, "limit": max_chars,
            "details": [f"未用满({actual}/{max_chars})，建议补差异化卖点短语用满 {max_chars} 字符"]}


def check_distinct_from_title(highlights, title):
    """与标题去重（WARN 级）：完全相同或一方包含另一方→WARN。"""
    if not (title and highlights):
        return {"status": "PASS"}
    h_norm = _normalize_text(highlights)
    t_norm = _normalize_text(title)
    if h_norm and t_norm:
        same = h_norm == t_norm
        contained = (t_norm in h_norm) or (h_norm in t_norm)
        if same or contained:
            return {"status": "WARN",
                    "reason": "item_highlights 与 title 文本高度重复，建议改写为差异化短语"}
    return {"status": "PASS"}


def check_cross_field_repeat(highlights, title, rules):
    """跨字段重复词：标题词在亮点里再出现，拼接同行后买家会看到堆砌。

    WARN 级（TBD：官方无跨字段重复明文规则，不计入 compliant/FAIL）。
    归一化/分词复用 lint_title；lint_title 不可用或缺字段时跳过。
    """
    if not _HAS_LINT_TITLE or not (title and highlights):
        return {"status": "PASS", "skipped": True,
                "details": ["lint_title 不可用或缺 title/highlights，跳过跨字段重复检查"]}
    title_rules = rules.get("title", {})
    word_repeat_max = title_rules.get("word_repeat_max", 2)
    exempt = set(title_rules.get("repeat_exempt", []))

    # 拼接成买家实际看到的一行，再统计归一化词频
    combined = f"{title} {highlights}"
    norm_counts = {}
    sample = {}
    for tok in _lt.tokenize(combined):
        n = _lt.normalize_word(tok)
        if not n or n in exempt or n.isdigit():
            continue
        norm_counts[n] = norm_counts.get(n, 0) + 1
        sample.setdefault(n, tok)

    violations = [
        {"word": sample[n], "normalized": n, "count": c}
        for n, c in norm_counts.items() if c > word_repeat_max
    ]
    violations.sort(key=lambda x: -x["count"])
    if violations:
        return {"status": "WARN", "limit": word_repeat_max, "tbd": True,
                "details": violations,
                "note": "跨字段重复：标题与亮点拼接同行后买家会看到堆砌；官方无跨字段明文规则(TBD)，仅 WARN"}
    return {"status": "PASS", "limit": word_repeat_max, "tbd": True, "details": []}


def build_display_string(highlights, title):
    """构建合并呈现串预览（前端实际渲染形态：title | highlights）。

    卖家无需手填分隔符，系统渲染层自动用 pipe 拼接。
    """
    sep = " | "
    has_t = bool(title and title.strip())
    has_h = bool(highlights and highlights.strip())
    if has_t and has_h:
        preview = f"{title}{sep}{highlights}"
    elif has_t:
        preview = title
    elif has_h:
        preview = highlights
    else:
        preview = ""
    return {
        "preview": preview,
        "combined_chars": len(preview),
        "title_chars": len(title) if has_t else 0,
        "highlights_chars": len(highlights) if has_h else 0,
        "separator": " | (pipe U+007C, 渲染层自动拼接, 非字段内容)",
        "note": "前端实测：标题与亮点拼成一行显示在标题位（亚马逊承认的展示 bug）",
    }


# --------------------------------------------------------------------------- #
# 核心纯函数
# --------------------------------------------------------------------------- #
def run(data):
    """校验 item_highlights，返回结果 dict（纯函数，无副作用）。

    Returns:
        dict: {field, value, char_count, clause_count, checks, display_string,
               compliant, fix_suggestions}
    """
    rules = _load_rules()
    h_rules = rules.get("highlights", {})

    highlights = data.get("item_highlights", "") or ""
    title = data.get("title", "") or ""

    char_count = len(highlights)
    clauses = _split_clauses(highlights)
    clause_count = len(clauses)

    checks = {}
    suggestions = []

    # ---- 硬规 1：字符上限 ----
    checks["char_limit"] = check_char_limit(highlights, h_rules)
    if checks["char_limit"]["status"] == "FAIL":
        suggestions.append(
            f"item_highlights 超过 {checks['char_limit']['limit']} 字符"
            f"（当前 {checks['char_limit']['actual']}），请精简。")

    # ---- 硬规 2：最少短语数 ----
    checks["min_clauses"] = check_min_clauses(clause_count, h_rules)
    if checks["min_clauses"]["status"] == "FAIL":
        suggestions.append(
            f"item_highlights 短语数不足（当前 {clause_count}，"
            f"要求 ≥{checks['min_clauses']['limit']}），建议用逗号分隔多个差异化卖点短语。")

    # ---- 软规 3：逗号分隔格式 ----
    checks["separator_format"] = check_separator_format(highlights)
    if checks["separator_format"]["status"] == "WARN":
        suggestions.append(
            f"亮点应使用逗号分隔短语，检测到非逗号分隔符 {checks['separator_format']['found']}，"
            f"官方要求逗号分隔。")

    # ---- 软规 4：短语非句子 ----
    checks["phrase_not_sentence"] = check_phrase_not_sentence(highlights, h_rules)
    if checks["phrase_not_sentence"]["status"] == "WARN":
        suggestions.extend(checks["phrase_not_sentence"]["details"])

    # ---- 软规 5：内容不含分隔符 ----
    checks["no_embedded_pipe"] = check_no_embedded_pipe(highlights)
    if checks["no_embedded_pipe"]["status"] == "WARN":
        suggestions.append(
            f"亮点内容不应自含分隔符 {checks['no_embedded_pipe']['found']}，"
            f"系统渲染层会自动拼接标题与亮点。")

    # ---- 软规 6：字符利用率 ----
    checks["char_utilization"] = check_char_utilization(highlights, h_rules)
    if checks["char_utilization"]["status"] == "WARN":
        suggestions.append(checks["char_utilization"]["details"][0])

    # ---- 软规 7：与标题去重 ----
    checks["distinct_from_title"] = check_distinct_from_title(highlights, title)
    if checks["distinct_from_title"]["status"] == "WARN":
        suggestions.append(checks["distinct_from_title"]["reason"])

    # ---- 软规 8：跨字段重复词（TBD）----
    checks["cross_field_repeat"] = check_cross_field_repeat(highlights, title, rules)
    if checks["cross_field_repeat"]["status"] == "WARN":
        for v in checks["cross_field_repeat"]["details"]:
            suggestions.append(
                f"跨字段重复词 '{v['word']}'（标题+亮点合计 {v['count']} 次，"
                f"上限 {checks['cross_field_repeat']['limit']}）——拼接同行后买家会看到堆砌(TBD)")

    # ---- 合并呈现串（前端实际形态）----
    display_string = build_display_string(highlights, title)

    # ---- 合规：仅 FAIL 影响 ----
    compliant = all(c.get("status") != "FAIL" for c in checks.values())

    return {
        "field": "item_highlights",
        "value": highlights,
        "char_count": char_count,
        "clause_count": clause_count,
        "checks": checks,
        "display_string": display_string,
        "compliant": compliant,
        "fix_suggestions": suggestions,
    }


# --------------------------------------------------------------------------- #
# IO 层（CLI）
# --------------------------------------------------------------------------- #
def load_input():
    """统一输入：--data > --file > stdin。"""
    parser = argparse.ArgumentParser(description="校验 item_highlights 字段（2026 新规）")
    parser.add_argument("--data", help="inline JSON 字符串")
    parser.add_argument("--file", help="JSON 文件路径")
    a = parser.parse_args()
    if a.data:
        return json.loads(a.data)
    if a.file:
        return json.loads(Path(a.file).read_text(encoding="utf-8"))
    if not sys.stdin.isatty():
        return json.loads(sys.stdin.read())
    return {}


def main():
    data = load_input()
    result = run(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("compliant", True) else 1)


if __name__ == "__main__":
    main()
