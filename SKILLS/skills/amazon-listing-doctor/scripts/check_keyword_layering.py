#!/usr/bin/env python3
# check_keyword_layering.py —— 关键词分层与去重检测
# 1) 四层去重检测（title / item_highlights / bullets / backend 间无意义重复）
# 2) A9 加权索引分（indexability_rules.json 的 field_weights 加权命中）

import sys
import json
import argparse
import re
from pathlib import Path
from collections import defaultdict

SKILL_ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = SKILL_ROOT / "references" / "indexability_rules.json"


# ---------- 配置加载 ----------
def _load_rules():
    """加载 indexability_rules.json；缺失则回退硬编码默认值。"""
    if RULES_PATH.exists():
        return json.loads(RULES_PATH.read_text(encoding="utf-8"))
    return {
        "field_weights": {
            "title": 5, "highlights": 4, "bullets": 4,
            "backend": 4, "description": 3, "attributes": 3,
        },
        "core_keyword_within_chars": 50,
        "backend_hygiene_rules": [
            "space_separated", "no_stopwords",
            "no_special_chars", "no_dup_with_title_bullets",
        ],
    }


# ---------- 词归一化（与 lint_backend 一致） ----------
def _normalize_word(w):
    w = w.lower()
    w = w.replace("-", "")  # strip_hyphen
    if len(w) > 3 and w.endswith("ies"):
        w = w[:-3] + "y"
    elif len(w) > 2 and w.endswith("es"):
        w = w[:-2]
    elif len(w) > 1 and w.endswith("s"):
        w = w[:-1]
    return w


def _tokenize(text):
    if not text:
        return []
    return [t for t in re.findall(r"\w+", text, flags=re.UNICODE) if t]


def _bullets_text(bullets):
    """把 bullets 拼成纯文本用于切词。"""
    parts = []
    if not bullets:
        return ""
    for b in bullets:
        if not isinstance(b, dict):
            continue
        parts.append(b.get("header", "") or "")
        parts.append(b.get("body", "") or "")
    return " ".join(parts)


# ---------- 四层词集 ----------
def _layer_word_sets(data):
    """返回 {layer_name: set(归一化词)}。"""
    layers = {
        "title": _tokenize(data.get("title", "") or ""),
        "highlights": _tokenize(data.get("item_highlights", "") or ""),
        "bullets": _tokenize(_bullets_text(data.get("bullets", []))),
        "backend": _tokenize(data.get("backend_search_terms", "") or ""),
    }
    return {k: {_normalize_word(t) for t in v if t} for k, v in layers.items()}


# ---------- 关键词命中（支持短语） ----------
def _phrase_hit_layers(phrase, layer_sets):
    """一个关键词（可能是多词短语，如 'noise cancelling'）命中了哪些层。

    命中判定：短语的每个组成词（归一化后）都出现在该层的 token 序列里
    （token 序列包含位置信息，避免 set 丢失多词短语语义）。
    """
    p_tokens = [_normalize_word(t) for t in _tokenize(phrase) if t]
    if not p_tokens:
        return []
    found = []
    for layer, seq_raw in layer_sets.items():
        seq = [_normalize_word(t) for t in _tokenize(layer_texts_raw.get(layer, ""))]
        # 子序列匹配（短语连续出现）
        ok = any(seq[i:i + len(p_tokens)] == p_tokens
                 for i in range(len(seq) - len(p_tokens) + 1))
        # 退化：若连续匹配失败，退到「所有组成词都在该层出现」(宽松命中)
        if not ok:
            sset = set(seq)
            ok = all(pt in sset for pt in p_tokens)
        if ok:
            found.append(layer)
    return found


# 占位：layer_texts_raw 由 run() 注入原始文本，供短语子序列匹配使用
layer_texts_raw = {}


def _build_layer_raw(data):
    return {
        "title": data.get("title", "") or "",
        "highlights": data.get("item_highlights", "") or "",
        "bullets": _bullets_text(data.get("bullets", [])),
        "backend": data.get("backend_search_terms", "") or "",
    }


# ---------- 主纯函数 ----------
def run(data):
    """关键词分层与 A9 加权索引检测。

    入参：完整 listing（含 title/item_highlights/bullets/
    backend_search_terms）+ keywords 分层 {P0..P4:[...]}
    返回：{duplicates_across_layers, weighted_index_score, coverage_per_layer, ...}
    """
    global layer_texts_raw
    layer_texts_raw = _build_layer_raw(data)

    rules = _load_rules()
    field_weights = rules.get("field_weights", {})

    layer_sets = _layer_word_sets(data)

    # --- 1) 四层去重检测 ---
    # 统计每个归一化词出现在哪些层；出现在 ≥2 层即「跨层重复」
    word_to_layers = defaultdict(list)
    for layer, wset in layer_sets.items():
        for w in wset:
            word_to_layers[w].append(layer)

    duplicates = []
    for w, layers in word_to_layers.items():
        if len(layers) >= 2:
            duplicates.append({
                "word": w,
                "layers": layers,
                "layer_count": len(layers),
            })
    # 词出现在越多层越靠前；同长度按字母序
    duplicates.sort(key=lambda x: (-x["layer_count"], x["word"]))

    # backend 与前端重复 = 最该避免的浪费（dup_front_back 风险）
    front_layers = {"title", "highlights", "bullets"}
    backend_overlap = sorted({
        d["word"] for d in duplicates
        if "backend" in d["layers"] and any(l in front_layers for l in d["layers"])
    })

    # --- 2) A9 加权索引分 ---
    keywords = data.get("keywords", {}) or {}
    # priority 展开成列表
    flat = []  # [{keyword, priority}]
    for prio in ("P0", "P1", "P2", "P3", "P4"):
        for kw in keywords.get(prio, []) or []:
            flat.append({"keyword": kw, "priority": prio})

    weights = {
        "title": field_weights.get("title", 5),
        "highlights": field_weights.get("highlights", 4),
        "bullets": field_weights.get("bullets", 4),
        "backend": field_weights.get("backend", 4),
    }
    # 用于加权分归一化的最大可能分（即 title 权重）
    max_weight = max(weights.values()) if weights else 1

    keyword_details = []
    per_layer_hit = {k: 0 for k in weights}
    score_accum = 0.0
    scored_count = 0

    for item in flat:
        kw = item["keyword"]
        hit_layers = _phrase_hit_layers(kw, layer_texts_raw)
        # 该词命中的最高权重层（A9 按最高权重字段索引）
        if hit_layers:
            max_w = max(weights[l] for l in hit_layers)
        else:
            max_w = 0.0
        keyword_details.append({
            "keyword": kw,
            "priority": item["priority"],
            "found_in": hit_layers,
            "max_weight": max_w,
        })
        score_accum += max_w
        scored_count += 1
        for l in hit_layers:
            per_layer_hit[l] += 1

    total_kw = len(flat)
    if scored_count:
        # 平均命中权重（0 ~ max_weight），保留 2 位
        weighted_index_score = round(score_accum / scored_count, 2)
    else:
        weighted_index_score = 0.0

    # --- 3) 每层覆盖 ---
    coverage_per_layer = {}
    for layer in ("title", "highlights", "bullets", "backend"):
        hit = per_layer_hit.get(layer, 0)
        coverage_per_layer[layer] = {
            "hit": hit,
            "total": total_kw,
            "ratio": round(hit / total_kw, 2) if total_kw else 0.0,
            "weight": weights.get(layer, 0),
        }

    # 缺失关键词（未命中任何层，索引 0）
    missing_keywords = [d["keyword"] for d in keyword_details if not d["found_in"]]

    return {
        "duplicates_across_layers": duplicates,
        "backend_overlap": backend_overlap,
        "weighted_index_score": weighted_index_score,
        "coverage_per_layer": coverage_per_layer,
        "keyword_details": keyword_details,
        "missing_keywords": missing_keywords,
        "total_keywords": total_kw,
        # 评分类：始终退 0；分数与状态在 JSON 里
    }


# ---------- IO 层 ----------
def load_input():
    parser = argparse.ArgumentParser(description="check keyword layering")
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
    # 评分类脚本始终退 0
    sys.exit(0)


if __name__ == "__main__":
    main()
