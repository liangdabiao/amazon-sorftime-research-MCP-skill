#!/usr/bin/env python3
"""lint_bullets.py — 校验 bullets 五点描述字段。

检查项：
  1. 条目数量在 count_min(5) ~ count_max(6) 条之间
  2. 每条（header+body）≤ max_chars_each(500) 字符
  3. 单条内关键词堆砌：归一化后同一词出现 ≥3 次 → WARN

输入：{bullets:[{header, body}]}
输出：stdout 单个 JSON 对象；退出码 0=全通过 / 1=有 FAIL。
"""

import sys
import json
import argparse
import re
from collections import Counter
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- #
# 配置加载
# --------------------------------------------------------------------------- #
def _load_rules():
    """从 references/rules.json 读取规则；缺失则返回空 dict。"""
    rules_path = SKILL_ROOT / "references" / "rules.json"
    if rules_path.exists():
        return json.loads(rules_path.read_text(encoding="utf-8"))
    return {}


# 多语言虚词兜底（与 rules.json.title.repeat_exempt 合并使用）。
# 解决：用户用德语 listing 时，'mit/für/durch/aus/bei' 等介词被误判关键词堆砌。
# 字段为空时不会引入新假阳性（短词也不会被豁免）。
_FALLBACK_STOPWORDS_BY_LANG = {
    "de": [
        # 介词
        "mit", "für", "durch", "aus", "bei", "über", "unter", "von", "zu",
        "ohne", "gegen", "nach", "seit", "bis", "während",
        # 连词
        "und", "oder", "aber", "denn", "weil", "wenn", "als", "damit",
        "sowie", "noch",
        # 冠词 / 代词
        "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer",
        "eines", "einem", "einen", "kein", "keine",
        "ich", "du", "er", "sie", "es", "wir", "ihr",
        "dieser", "diese", "dieses", "jener", "jene", "jenes",
        "alle", "alles", "beide",
    ],
    "fr": [
        "avec", "pour", "par", "dans", "sur", "sans", "sous", "entre",
        "vers", "chez", "de", "du", "des", "le", "la", "les", "un", "une",
        "et", "ou", "mais", "donc", "or", "ni", "car",
        "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
        "ce", "cette", "ces", "mon", "ton", "son", "notre", "votre", "leur",
        "qui", "que", "quoi", "dont", "où",
    ],
    "it": [
        "con", "per", "da", "in", "su", "senza", "sotto", "tra", "fra",
        "verso", "di", "del", "della", "dei", "degli", "delle",
        "il", "lo", "la", "i", "gli", "le", "un", "una", "uno",
        "e", "o", "ma", "che", "perché", "quando", "come", "dove",
        "io", "tu", "lui", "lei", "noi", "voi", "loro",
        "mio", "tuo", "suo", "nostro", "vostro", "loro",
    ],
    "es": [
        "con", "para", "por", "de", "del", "en", "sobre", "sin", "bajo",
        "entre", "hacia", "desde", "hasta", "durante", "mediante",
        "el", "la", "los", "las", "un", "una", "unos", "unas",
        "y", "o", "pero", "sino", "porque", "cuando", "como", "donde",
        "yo", "tú", "él", "ella", "nosotros", "vosotros", "ellos", "ellas",
        "mi", "tu", "su", "nuestro", "vuestro",
        "que", "cuyo", "quien",
    ],
    "ja": [
        "の", "に", "は", "を", "が", "で", "と", "も", "から", "まで",
        "より", "や", "か", "ね", "よ",
    ],
    "en": [
        "in", "on", "over", "with", "for", "to", "of", "at", "by",
        "and", "or", "but", "nor", "so", "yet",
        "the", "a", "an",
    ],
}


def _resolve_stopwords(rules, language):
    """按 language 取虚词集合，缺则回退 en。

    优先用 rules.json.title.repeat_exempt_by_lang（按语种分组的字典），
    否则用顶层 repeat_exempt 数组，再叠加多语言兜底。
    """
    lang = (language or "en").lower()
    t_rules = rules.get("title", {})

    # 新格式：按语种分组的字典
    by_lang = t_rules.get("repeat_exempt_by_lang")
    if isinstance(by_lang, dict):
        exempt = set(w.lower() for w in by_lang.get(lang, []) or [])
        # 同语系兜底：en 永远叠加（不重复添加）
        fallback_lang = "en" if lang != "en" else None
        if fallback_lang:
            exempt.update(w.lower() for w in by_lang.get(fallback_lang, []) or [])
    else:
        # 旧格式兼容：单一数组（视为英文）
        exempt = set(w.lower() for w in t_rules.get("repeat_exempt", []) or [])

    # 叠加多语言兜底（确保德语介词即使没在 rules.json 里也豁免）
    fallback_set = set(_FALLBACK_STOPWORDS_BY_LANG.get(lang, []))
    exempt.update(fallback_set)
    return exempt


# --------------------------------------------------------------------------- #
# 词形归一化（strip_hyphen + singularize + lowercase，标准库实现）
# --------------------------------------------------------------------------- #
def _strip_hyphen(word):
    """去连字符：noise-cancelling → noisecancelling。"""
    return word.replace("-", "")


def _singularize(word):
    """极简英文复数还原：ies→y, es→去es, s→去s。

    例：babies→baby, boxes→box, apples→apple。
    中文 token 一般不以这些结尾，几乎不受影响。
    """
    if len(word) > 3 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 2 and word.endswith("es"):
        return word[:-2]
    if len(word) > 1 and word.endswith("s"):
        return word[:-1]
    return word


def _normalize_word(word):
    """归一化单个 token：strip_hyphen → singularize → lowercase。"""
    w = _strip_hyphen(word)
    w = _singularize(w)
    return w.lower()


def _tokenize(text):
    """按非字母数字切分为 token 列表（保留 CJK 连续段为一个 token）。"""
    return re.findall(r"[\w]+", text, flags=re.UNICODE)


def _find_keyword_stuffing(text, exempt, threshold=3):
    """检测单条文本内关键词堆砌。

    Args:
        text: 单条 bullet 的完整文本。
        exempt: set，归一化后需豁免的虚词（介词/连词/冠词等）。
        threshold: 出现次数阈值，默认 3。

    Returns:
        list[str]，出现次数 ≥ threshold 的归一化词（升序）。
    """
    tokens = _tokenize(text)
    counter = Counter()
    for tok in tokens:
        norm = _normalize_word(tok)
        if not norm:
            continue
        if norm.isdigit() or len(norm) < 2:  # 跳过纯数字、单字符
            continue
        if norm in exempt:
            continue
        counter[norm] += 1
    stuffed = sorted([w for w, c in counter.items() if c >= threshold])
    return stuffed


# --------------------------------------------------------------------------- #
# 核心纯函数
# --------------------------------------------------------------------------- #
def run(data):
    """校验 bullets，返回结果 dict（纯函数）。

    Args:
        data: dict，含 bullets:[{header, body}]，可选 language。

    Returns:
        dict 结构：
        {field, value, count, checks:{count_limit, bullets:[...]}, compliant, fix_suggestions}
    """
    rules = _load_rules()
    b_rules = rules.get("bullets", {})
    count_min = b_rules.get("count_min", 5)
    count_max = b_rules.get("count_max", 6)
    max_chars_each = b_rules.get("max_chars_each", 500)

    # 词频堆砌的虚词豁免：按 language 取（德语 listing 命中德语介词不报堆砌）
    language = data.get("language", "") or ""
    exempt = _resolve_stopwords(rules, language)

    raw_bullets = data.get("bullets", [])
    if raw_bullets is None:
        raw_bullets = []

    count = len(raw_bullets)

    checks = {}
    suggestions = []

    # ---- 检查 1：条目数量 ----
    count_status = "PASS"
    if count < count_min or count > count_max:
        count_status = "FAIL"
    checks["count_limit"] = {
        "status": count_status,
        "actual": count,
        "min": count_min,
        "max": count_max,
    }
    if count_status == "FAIL":
        if count < count_min:
            suggestions.append(
                f"bullets 数量不足（当前 {count} 条，要求 {count_min}-{count_max} 条），"
                f"建议补充至至少 {count_min} 条，覆盖材质/尺寸/场景/限制/差异化等核心问题。"
            )
        else:
            suggestions.append(
                f"bullets 数量过多（当前 {count} 条，要求 {count_min}-{count_max} 条），"
                f"建议合并精简至 {count_max} 条以内。"
            )

    # ---- 检查 2 & 3：逐条字符数 + 关键词堆砌 ----
    bullet_checks = []
    has_char_fail = False
    for idx, b in enumerate(raw_bullets):
        if not isinstance(b, dict):
            b = {"header": "", "body": str(b)}
        header = b.get("header", "") or ""
        body = b.get("body", "") or ""

        # 整条文本 = header + body（亚马逊 500 字符限制针对整条 bullet point）
        full_text = (header + " " + body).strip() if header and body else (header or body)
        char_count = len(full_text)

        b_checks = {}

        # 2a. 每条字符数上限（FAIL 级）
        char_status = "PASS" if char_count <= max_chars_each else "FAIL"
        b_checks["char_limit"] = {
            "status": char_status,
            "actual": char_count,
            "limit": max_chars_each,
        }
        if char_status == "FAIL":
            has_char_fail = True
            suggestions.append(
                f"第 {idx + 1} 条 bullet 超过 {max_chars_each} 字符"
                f"（当前 {char_count}），请精简 header/body。"
            )

        # 2b. 单条关键词堆砌（WARN 级，不影响 compliant）
        stuffed = _find_keyword_stuffing(full_text, exempt, threshold=3)
        stuff_status = "WARN" if stuffed else "PASS"
        b_checks["keyword_stuffing"] = {
            "status": stuff_status,
            "repeated_words": stuffed,
            "threshold": 3,
        }
        if stuffed:
            suggestions.append(
                f"第 {idx + 1} 条 bullet 疑似关键词堆砌："
                f"'{', '.join(stuffed)}' 重复 ≥3 次，建议自然表述、避免堆砌。"
            )

        bullet_checks.append({
            "index": idx,
            "header": header,
            "char_count": char_count,
            "checks": b_checks,
        })

    checks["bullets"] = bullet_checks

    # ---- 汇总合规：数量 FAIL 或任一条 char_limit FAIL 即不合规 ----
    compliant = (count_status != "FAIL") and (not has_char_fail)

    return {
        "field": "bullets",
        "value": raw_bullets,
        "count": count,
        "checks": checks,
        "compliant": compliant,
        "fix_suggestions": suggestions,
    }


# --------------------------------------------------------------------------- #
# IO 层（CLI）
# --------------------------------------------------------------------------- #
def load_input():
    """统一输入：--data > --file > stdin。"""
    parser = argparse.ArgumentParser(description="校验 bullets 字段")
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
