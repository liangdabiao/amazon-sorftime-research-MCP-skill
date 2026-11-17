#!/usr/bin/env python3
# lint_backend.py —— 校验 backend_search_terms 合规性
# 规则：≤250 字节 / 空格分隔(无逗号等) / 无停用词 / 无特殊字符 / 不重复标题与五点的词

import sys
import json
import argparse
import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = SKILL_ROOT / "references" / "rules.json"


# ---------- 配置加载 ----------
def _load_rules():
    """加载 rules.json；缺失时回退到硬编码默认值，保证零依赖可跑。"""
    if RULES_PATH.exists():
        return json.loads(RULES_PATH.read_text(encoding="utf-8"))
    # 默认值兜底（与 references/rules.json 同源）
    return {
        "backend_search_terms": {
            "max_bytes": 250,
            "separator": "space",
            "strip_stopwords": True,
            "stopwords": [
                "and", "the", "for", "with", "of", "a", "an", "or", "but",
                "in", "on", "to", "is", "it", "this", "that",
            ],
            "no_special_chars": True,
            "distinct_from_title_bullets": True,
        }
    }


# ---------- 词归一化 ----------
def _normalize_word(w):
    """strip_hyphen + singularize + lowercase（标准库简单版）。"""
    w = w.lower()
    w = w.replace("-", "")  # strip_hyphen
    # singularize（顺序敏感：ies→y 优先于 s）
    if len(w) > 3 and w.endswith("ies"):
        w = w[:-3] + "y"
    elif len(w) > 2 and w.endswith("es"):
        w = w[:-2]
    elif len(w) > 1 and w.endswith("s"):
        w = w[:-1]
    return w


def _tokenize(text):
    """切词：提取字母数字 token（含 unicode 字母，支持中英混排）。"""
    if not text:
        return []
    # \w 支持 unicode 字母数字下划线；再去掉下划线开头的纯符号串
    return [t for t in re.findall(r"\w+", text, flags=re.UNICODE) if t]


# ---------- 五项检查 ----------
def _check_byte_limit(value, limit):
    actual = len(value.encode("utf-8"))
    status = "PASS" if actual <= limit else "FAIL"
    return {
        "status": status,
        "actual": actual,
        "limit": limit,
    }


def _check_separator(value):
    """backend 必须空格分隔；出现逗号/分号/竖线/tab/换行等多分隔符即 FAIL。"""
    bad = sorted(set(c for c in value if c in ",;|\t\r\n"))
    return {
        "status": "FAIL" if bad else "PASS",
        "found_separators": bad,
    }


def _check_stopwords(value, stopwords):
    """命中停用词即 FAIL（backend 应剔除所有停用词以省字节）。"""
    stop_set = {w.lower() for w in stopwords}
    tokens = [t.lower() for t in _tokenize(value)]
    found = sorted({t for t in tokens if t in stop_set})
    return {
        "status": "FAIL" if found else "PASS",
        "found": found,
    }


def _check_special_chars(value):
    """非字母/数字/空格的字符即特殊字符（标点、符号一律禁止）。"""
    bad = sorted({c for c in value if not (c.isalnum() or c.isspace())})
    return {
        "status": "FAIL" if bad else "PASS",
        "found": sorted(set(bad)),
    }


def _check_distinct(value, title, bullets):
    """backend 词不得与 title / bullets(header+body) 的词重复（归一化后比较）。"""
    # 收集前端词集
    front_tokens = []
    front_tokens += _tokenize(title or "")
    if bullets:
        for b in bullets:
            if not isinstance(b, dict):
                continue
            front_tokens += _tokenize(b.get("header", "") or "")
            front_tokens += _tokenize(b.get("body", "") or "")
    front_set = {_normalize_word(t) for t in front_tokens}

    backend_tokens = _tokenize(value)
    dups = sorted({
        orig for orig in backend_tokens
        if _normalize_word(orig) in front_set and _normalize_word(orig)
    })
    return {
        "status": "FAIL" if dups else "PASS",
        "duplicates": dups,
    }


# ---------- 主纯函数 ----------
def run(data):
    """校验 backend_search_terms。

    入参：{backend_search_terms, title, bullets, language}
    返回：标准合规结果 dict。
    """
    rules_cfg = _load_rules()
    bs_cfg = rules_cfg.get("backend_search_terms", {})

    value = data.get("backend_search_terms", "") or ""
    title = data.get("title", "") or ""
    bullets = data.get("bullets", []) or []
    # language 默认 en（停用词表当前不分语种，预留字段）
    data.get("language", "en")

    max_bytes = bs_cfg.get("max_bytes", 250)
    stopwords = bs_cfg.get("stopwords", [])

    checks = {
        "byte_limit": _check_byte_limit(value, max_bytes),
        "separator": _check_separator(value),
        "no_stopwords": _check_stopwords(value, stopwords),
        "no_special_chars": _check_special_chars(value),
        "distinct_from_title_bullets": _check_distinct(value, title, bullets),
    }

    compliant = all(c.get("status") == "PASS" for c in checks.values())

    fix = []
    if checks["byte_limit"]["status"] == "FAIL":
        fix.append(
            f"缩减 backend 至 {max_bytes} 字节以内（当前 {checks['byte_limit']['actual']}），删冗余词"
        )
    if checks["separator"]["status"] == "FAIL":
        fix.append(
            f"仅用空格分隔，移除: {', '.join(checks['separator']['found_separators'])}"
        )
    if checks["no_stopwords"]["status"] == "FAIL":
        fix.append(f"删除停用词: {', '.join(checks['no_stopwords']['found'])}")
    if checks["no_special_chars"]["status"] == "FAIL":
        fix.append(
            f"删除特殊字符: {''.join(checks['no_special_chars']['found'])}"
        )
    if checks["distinct_from_title_bullets"]["status"] == "FAIL":
        fix.append(
            f"删除与标题/五点重复的词（前端已索引，浪费字节且触发 dup_front_back 风险）: "
            f"{', '.join(checks['distinct_from_title_bullets']['duplicates'])}"
        )

    return {
        "field": "backend_search_terms",
        "value": value,
        "byte_count": len(value.encode("utf-8")),
        "checks": checks,
        "compliant": compliant,
        "fix_suggestions": fix,
    }


# ---------- IO 层 ----------
def load_input():
    parser = argparse.ArgumentParser(description="lint backend_search_terms")
    parser.add_argument("--data", help="inline JSON")
    parser.add_argument("--file", help="path to JSON file")
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
