#!/usr/bin/env python3
"""indexability.py — A9 收录健康度评估。

读取 references/indexability_rules.json，综合 4 个维度算 0-100 收录健康度:
  1. 核心词前置度 (brand+product_type 在 title 前 50 字符内)
  2. backend 卫生分 (space_separated / no_stopwords / no_special_chars / no_dup_with_title_bullets)
  3. 属性完整度 (top10 属性填充率, A9 强索引)
  4. 有效索引词数 (全字段去重归一化实词数)
同时输出收录风险清单 (基于 index_failure_causes)。
"""

import sys
import json
import re
import argparse
from collections import Counter
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = SKILL_ROOT / "references" / "indexability_rules.json"
CATEGORIES_PATH = SKILL_ROOT / "references" / "categories.json"
ATTRS_DIR = SKILL_ROOT / "references" / "category_attributes"

# 停用词 (与 rules.json -> backend_search_terms.stopwords 对齐)
STOPWORDS = {
    "and", "the", "for", "with", "of", "a", "an", "or", "but",
    "in", "on", "to", "is", "it", "this", "that",
}

# 有效索引词达标线 (达到 → 该维度满分)
EFFECTIVE_TERMS_TARGET = 20

# 评分权重 (4 维度和为 1.0)
W_CORE_KW = 0.30
W_BACKEND = 0.20
W_ATTR = 0.25
W_TERMS = 0.25


# --------------------------- 工具函数 ---------------------------

def _load_rules():
    """加载收录规则 JSON。"""
    if not RULES_PATH.exists():
        return {}
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def _load_category_attrs(category):
    """按 category 名查 categories.json → category_attributes/<file>.json（与 cdq_score 同源兜底，空格/下划线归一匹配）。"""
    if not category or not CATEGORIES_PATH.exists():
        return {}
    try:
        cats = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8")) or {}
        target = str(category).strip().lower().replace(" ", "_")
        attr_file = None
        for k, v in cats.items():
            if str(k).startswith("_"):
                continue
            if str(k).lower().replace(" ", "_") == target:
                attr_file = (v or {}).get("attr_file")
                break
        if attr_file and (ATTRS_DIR / attr_file).exists():
            return json.loads((ATTRS_DIR / attr_file).read_text(encoding="utf-8")) or {}
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _singularize(word):
    """简单去复数: boxes→box / babies→baby / apples→apple。"""
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("es") and len(word) > 3:
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 2:
        return word[:-1]
    return word


def _normalize(word):
    """归一化: 去连字符 + 去复数 + 小写。"""
    w = word.replace("-", "").lower()
    return _singularize(w)


def _tokenize(text):
    """切词: 连续字母数字串。"""
    if not text:
        return []
    return re.findall(r"[A-Za-z0-9]+", text)


def _collect_indexed_text(data):
    """合并所有 A9 可索引字段的文本 (title/highlights/bullets/description/backend/attributes)。"""
    parts = []
    for key in ("title", "item_highlights", "description", "backend_search_terms"):
        v = data.get(key)
        if v:
            parts.append(str(v))
    bullets = data.get("bullets") or []
    for b in bullets:
        if isinstance(b, dict):
            parts.append(str(b.get("header", "")))
            parts.append(str(b.get("body", "")))
        elif isinstance(b, str):
            parts.append(b)
    attrs = data.get("attributes") or {}
    if isinstance(attrs, dict):
        for v in attrs.values():
            if v:
                parts.append(str(v))
    return " ".join(parts)


# --------------------------- 4 个维度计算 ---------------------------

def _compute_core_keyword_position(data, rules):
    """核心词前置度。

    核心词组 = brand + 至第一个分隔符(逗号/连字符)之间的 title 前缀。
    title 公式通常为 "[Brand] [Product Type] [Key Spec], ..."，逗号前的核心信息
    若能在 core_keyword_within_chars (默认 50) 内被 A9 完整索引, 移动端/搜索结果截断风险低。

    返回 dict: {position, limit, within}。position = 核心词组结束字符偏移。
    """
    title = (data.get("title") or "").strip()
    brand = (data.get("brand") or "").strip()
    limit = rules.get("core_keyword_within_chars", 50)

    if not title:
        return {"position": -1, "limit": limit, "within": False, "reason": "empty_title"}

    # brand 出现位置
    pos = -1
    if brand:
        idx = title.lower().find(brand.lower())
        if idx >= 0:
            pos = idx + len(brand)
    if pos < 0:
        # brand 未在 title 中找到, 退化为 title 全长
        pos = len(title)

    # 从 brand 结束处向后找第一个分隔符 (逗号/破折号), 标记核心词组右边界
    after = title[pos:]
    m = re.search(r"[,\-–—]|$", after)
    if m and m.start() > 0:
        pos += m.start()

    within = pos <= limit
    return {"position": pos, "limit": limit, "within": within}


def _compute_backend_hygiene(data, rules):
    """backend 卫生分 (0-1): 按 backend_hygiene_rules 4 项各占均权。

    返回 (score, checks_dict, dup_terms_set)。
    """
    backend = (data.get("backend_search_terms") or "").strip()
    rules_list = rules.get("backend_hygiene_rules", []) or [
        "space_separated", "no_stopwords", "no_special_chars", "no_dup_with_title_bullets"
    ]

    tokens = _tokenize(backend)

    # 1. space_separated: 无逗号/分号/管道
    space_ok = bool(backend) and not re.search(r"[,;|]", backend)
    # 2. no_stopwords
    has_stop = any(t.lower() in STOPWORDS for t in tokens)
    no_stop = not has_stop
    # 3. no_special_chars: 仅字母数字 + 空格
    special_ok = bool(backend) and not re.search(r"[^A-Za-z0-9\s]", backend)
    # 4. no_dup_with_title_bullets: backend 归一化词 与 title/bullets 归一化词 不重合
    tb_parts = [str(data.get("title") or ""), str(data.get("item_highlights") or "")]
    for b in (data.get("bullets") or []):
        if isinstance(b, dict):
            tb_parts.append(str(b.get("header", "")) + " " + str(b.get("body", "")))
        else:
            tb_parts.append(str(b))
    tb_tokens = {_normalize(t) for t in _tokenize(" ".join(tb_parts))} - STOPWORDS
    tb_tokens.discard("")
    be_tokens = {_normalize(t) for t in tokens}
    be_tokens.discard("")
    dup = be_tokens & tb_tokens
    no_dup = len(dup) == 0

    checks = {
        "space_separated": space_ok,
        "no_stopwords": no_stop,
        "no_special_chars": special_ok,
        "no_dup_with_title_bullets": no_dup,
    }

    active = [r for r in rules_list if r in checks] or list(checks.keys())
    passed = sum(1 for r in active if checks[r])
    score = passed / len(active) if active else 0.0
    return score, checks, dup


def _compute_attribute_completeness(data, cat_attrs=None):
    """属性完整度 (0-1): filled_top10 / expected_top10。

    expected 优先级：用户传入 (user_provided) > 类目文件兜底 (builtin_fallback，
    公开版大类近似 → 分数为参考值) > 无基准 (no_reference → None，降级不记 0 分：
    0 分是「确认缺失」，None 是「无法评估」)。
    """
    filled = data.get("attributes_filled") or []
    expected = list(data.get("attributes_top10_expected") or [])
    if expected:
        basis = "user_provided"
    else:
        expected = list((cat_attrs or {}).get("top10_attributes") or [])
        basis = "builtin_fallback" if expected else "no_reference"
    if not expected:
        return None, 0, 0, basis
    # 属性名大小写归一（filled 常见 "Color"，清单为 "color"）
    filled_set = {str(f).strip().lower() for f in filled if f}
    expected_set = {str(e).strip().lower() for e in expected}
    inter = filled_set & expected_set
    ratio = len(inter) / len(expected_set)
    return ratio, len(inter), len(expected), basis


def _compute_effective_index_terms(data):
    """有效索引词数: 全字段去重归一化后的实词数 (去停用词、长度>1)。"""
    text = _collect_indexed_text(data)
    tokens = _tokenize(text)
    normed = set()
    for t in tokens:
        n = _normalize(t)
        if n and len(n) > 1 and n not in STOPWORDS:
            normed.add(n)
    return len(normed), sorted(normed)


# --------------------------- 风险识别 ---------------------------

def _detect_risks(data, core_kw, backend_checks, backend_dup, attr_ratio):
    """收录风险清单 (映射 index_failure_causes)。"""
    risks = []
    title = data.get("title") or ""

    # keyword_stuffing: 标题同词重复 ≥3
    title_tokens = [_normalize(t) for t in _tokenize(title)]
    cnt = Counter([t for t in title_tokens if t and t not in STOPWORDS])
    stuffed = sorted([w for w, c in cnt.items() if c >= 3])
    if stuffed:
        risks.append({
            "cause": "keyword_stuffing",
            "detail": f"title words repeated >=3: {stuffed}",
        })

    # backend_stopwords
    if not backend_checks.get("no_stopwords"):
        risks.append({
            "cause": "backend_stopwords",
            "detail": "stopwords in backend_search_terms dilute indexing and waste bytes",
        })

    # dup_front_back
    if not backend_checks.get("no_dup_with_title_bullets") and backend_dup:
        risks.append({
            "cause": "dup_front_back",
            "detail": f"backend duplicates title/bullets terms: {sorted(backend_dup)[:10]}",
        })

    # empty_attributes
    if attr_ratio == 0:
        risks.append({
            "cause": "empty_attributes",
            "detail": "no top10 attributes filled; structured attributes carry strong A9 index weight",
        })

    # core_keyword_late (派生风险: 移动端截断)
    if core_kw["position"] > 0 and not core_kw["within"]:
        risks.append({
            "cause": "core_keyword_late",
            "detail": f"core keyword ends at char {core_kw['position']}, beyond {core_kw['limit']} (mobile truncation risk)",
        })

    # backend 分隔符 / 特殊字符 (派生)
    if not backend_checks.get("space_separated"):
        risks.append({
            "cause": "backend_separator",
            "detail": "backend not space-separated; commas/pipes are stripped or waste bytes",
        })
    if not backend_checks.get("no_special_chars"):
        risks.append({
            "cause": "backend_special_chars",
            "detail": "special characters in backend ignored by A9 indexer",
        })

    return risks


# --------------------------- 核心纯函数 ---------------------------

def run(data):
    """收录健康度评估。

    Args:
        data: listing dict。

    Returns:
        dict, 至少含:
          score(0-100), core_keyword_position(int),
          backend_hygiene(0-1), attribute_completeness(0-1),
          effective_index_terms(int), risks(list)。
    """
    rules = _load_rules()
    cat_attrs = _load_category_attrs(data.get("category"))

    core_kw = _compute_core_keyword_position(data, rules)
    backend_score, backend_checks, backend_dup = _compute_backend_hygiene(data, rules)
    attr_ratio, attr_filled, attr_expected, attr_basis = _compute_attribute_completeness(data, cat_attrs)
    eff_count, _ = _compute_effective_index_terms(data)

    # 核心词前置度 → 0-1 子分
    if core_kw["position"] <= 0:
        core_kw_score = 0.0
    elif core_kw["within"]:
        # ≤limit: 起始=1.0, limit 处=0.8
        core_kw_score = 1.0 - 0.2 * (core_kw["position"] / max(core_kw["limit"], 1))
    else:
        # 超出 limit: 线性衰减
        over = core_kw["position"] - core_kw["limit"]
        core_kw_score = max(0.0, 0.5 - 0.01 * over)

    eff_score = min(eff_count / EFFECTIVE_TERMS_TARGET, 1.0)

    if attr_ratio is None:
        # 无基准：数据不足≠缺失，该子项退出加权、剩余权重归一
        denom = W_CORE_KW + W_BACKEND + W_TERMS
        score = (
            core_kw_score * W_CORE_KW
            + backend_score * W_BACKEND
            + eff_score * W_TERMS
        ) / denom * 100
    else:
        score = (
            core_kw_score * W_CORE_KW
            + backend_score * W_BACKEND
            + attr_ratio * W_ATTR
            + eff_score * W_TERMS
        ) * 100
    score = round(score)

    risks = _detect_risks(data, core_kw, backend_checks, backend_dup, attr_ratio)
    if attr_basis == "builtin_fallback":
        risks.append({
            "cause": "attribute_reference_fallback",
            "detail": "expected top10 from builtin broad-category list — score is a reference value; verify via Seller Central export or storefront facet filters",
        })
    elif attr_ratio is None:
        risks.append({
            "cause": "attribute_no_reference",
            "detail": "no expected top10 available — attribute dimension excluded from scoring; supply Seller Central export or category facet filters to unlock",
        })

    return {
        # 必填字段
        "score": score,
        "core_keyword_position": core_kw["position"],
        "backend_hygiene": round(backend_score, 2),
        "attribute_completeness": None if attr_ratio is None else round(attr_ratio, 2),
        "attribute_basis": attr_basis,
        "effective_index_terms": eff_count,
        "risks": risks,
        # 诊断扩展字段
        "core_keyword_within_limit": core_kw["within"],
        "core_keyword_limit": core_kw["limit"],
        "backend_hygiene_checks": backend_checks,
        "attribute_filled": attr_filled,
        "attribute_expected": attr_expected,
        "effective_index_terms_target": EFFECTIVE_TERMS_TARGET,
        "weights": {
            "core_keyword": W_CORE_KW,
            "backend_hygiene": W_BACKEND,
            "attribute": W_ATTR,
            "effective_terms": W_TERMS,
        },
    }


# --------------------------- CLI ---------------------------

def load_input():
    parser = argparse.ArgumentParser(description="A9 indexability health check")
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
    # 评分类脚本始终退出 0 (分数在 JSON 里)
    sys.exit(0)


if __name__ == "__main__":
    main()
