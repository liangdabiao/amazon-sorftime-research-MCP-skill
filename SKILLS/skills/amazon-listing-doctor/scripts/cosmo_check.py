#!/usr/bin/env python3
"""cosmo_check.py — COSMO 意图覆盖度评估（doctor 独占维度）。

读取 references/cosmo_ontology.json, 按 category 取本体 (缺类目时 fallback _common),
支持两种模式:
  - Agent 语义提取（优先）: data 中含 _cosmo_extracted 字段时直接用于算分
  - substring 匹配（回退）: data 中无 _cosmo_extracted 时走旧词库 substring 匹配

输出:
  - score: 达标线加权 0-100 (对标 alexa, 友好可比)
  - coverage_ratio: 精确覆盖率 matched/total (诚实反映概念覆盖)
  - covered/missing_concepts: 每维已覆盖与缺失的概念清单 (可操作)
  - suggestions: 补概念建议

用法:
  # Agent 前置: 获取提取提示词
  from cosmo_check import get_agent_prompt
  prompt = get_agent_prompt(data)  # → 返回 listing_text + dimensions + output_schema

  # 然后: Agent 语义提取 → 写回 data["_cosmo_extracted"] → run(data)

设计要点: goal 维度故意偏难 —— listing 通常堆属性词而不写"用户目标",
goal 覆盖率低正是诊断价值所在 (指出 listing 缺少意图层表达)。

Agent 提取 vs substring: substring 匹配只能识别词库中已有的精确关键词,
Agent 语义提取能理解 "keeps cat fed while at work" 表达了 work 场景——
这是 COSMO 作为常识知识图谱的核心价值,正则做不到。
"""

import sys
import json
import re
import argparse
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = SKILL_ROOT / "references" / "cosmo_ontology.json"

# 四维度 (COSMO 论文常识分类; goal 为 COSMO 区别于 Alexa 的核心维度)
DIMENSIONS = ("use_case", "audience", "goal", "constraint")

# 各维度达标线: 命中 N 个不同概念 → 该维度满分
TARGET_USE_CASE = 3
TARGET_AUDIENCE = 2
TARGET_GOAL = 2
TARGET_CONSTRAINT = 2

# 四维权重 (和为 1.0); use_case 权重最高 (场景/用途是意图匹配主信号)
W_USE_CASE = 0.30
W_AUDIENCE = 0.25
W_GOAL = 0.25
W_CONSTRAINT = 0.20

_WEIGHTS = {
    "use_case": W_USE_CASE,
    "audience": W_AUDIENCE,
    "goal": W_GOAL,
    "constraint": W_CONSTRAINT,
}
_TARGETS = {
    "use_case": TARGET_USE_CASE,
    "audience": TARGET_AUDIENCE,
    "goal": TARGET_GOAL,
    "constraint": TARGET_CONSTRAINT,
}


# --------------------------- 工具函数 ---------------------------

def _load_ontology():
    """加载 cosmo_ontology.json。"""
    if not ONTOLOGY_PATH.exists():
        return {}
    return json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))


def _get_category_ontology(ontology, category):
    """按 category 取本体; 类目词 + _common 词合并去重 (类目分词 + 通用词叠加, 覆盖更全)。

    返回 (merged_dict, used_fallback_flag)。
    merged_dict keys: use_case / audience / goal / constraint。
    used_fallback=True 表示无该类目分词块, 纯靠 _common。
    合并去重保证: 吸收更多词后, 同一 listing 的命中数只会持平或上升, score 不下降。
    """
    common = ontology.get("_common", {}) if isinstance(ontology.get("_common"), dict) else {}
    cat_entry = (
        ontology.get(category, {})
        if category and isinstance(ontology.get(category), dict)
        else {}
    )

    merged = {}
    for dim in DIMENSIONS:
        cval = list(cat_entry.get(dim) or [])
        bval = list(common.get(dim) or [])
        # 类目词在前, _common 兜底, 按小写去重保持原形
        combined, seen = [], set()
        for w in cval + bval:
            key = w.lower()
            if key not in seen:
                seen.add(key)
                combined.append(w)
        merged[dim] = combined
    fallback_used = not bool(cat_entry)
    return merged, fallback_used


def _collect_listing_text(data):
    """合并 COSMO 意图来源全文。（public: Agent 提取也需要这段全文。）"""
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
    return " ".join(parts).lower()


def _word_in_text(word, text):
    """概念词是否在文本中出现 (substring 匹配, 覆盖单复数/词形变化; 大小写不敏感)。"""
    return word.lower() in text


def _scan_dimension(words, text):
    """扫描一个维度的概念词表, 返回 (matched, missing)。"""
    matched, missing = [], []
    for w in words:
        (matched if _word_in_text(w, text) else missing).append(w)
    return matched, missing


# --------------------------- Agent 提取接口 ---------------------------

def get_agent_prompt(data):
    """返回 Agent 做 COSMO 语义提取所需的全部上下文。

    Args:
        data: listing dict（需含 category 与文本字段）。

    Returns:
        dict:
          - listing_text: listing 全文（同 _collect_listing_text 输出）
          - dimensions: 四维定义 + 示例（来自 extraction_guidance）
          - output_schema: Agent 应输出的 JSON 格式说明
          - instruction: 提取指令（来自 extraction_guidance._instruction）
    """
    if not isinstance(data, dict):
        data = {}

    ontology = _load_ontology()
    guidance = ontology.get("extraction_guidance", {}) if isinstance(ontology, dict) else {}
    listing_text = _collect_listing_text(data)

    dimensions = {}
    for dim in DIMENSIONS:
        dim_guidance = guidance.get(dim)
        if isinstance(dim_guidance, dict):
            dimensions[dim] = dim_guidance
        else:
            dimensions[dim] = {"definition": "", "examples": []}

    return {
        "listing_text": listing_text,
        "dimensions": dimensions,
        "output_schema": {
            "covered_concepts": {
                "use_case": ["concept1", "concept2", "..."],
                "audience": ["concept1", "..."],
                "goal": ["concept1", "..."],
                "constraint": ["concept1", "..."]
            },
            "missing_concepts": {
                "use_case": ["missing_concept1", "..."],
                "audience": ["missing_concept1", "..."],
                "goal": ["missing_concept1", "..."],
                "constraint": ["missing_concept1", "..."]
            },
            "extraction_method": "agent_semantic"
        },
        "instruction": guidance.get("_instruction", ""),
    }


def _run_agent_mode(agent_extracted, ontology, category):
    """用 Agent 语义提取的结果算分（跳过 substring 匹配）。

    Args:
        agent_extracted: listing["_cosmo_extracted"] 字段。
        ontology: 完整 ontology dict。
        category: listing category（用于来源标签）。

    Returns:
        与 run() 相同结构的 dict。
    """
    covered = agent_extracted.get("covered_concepts", {})
    missing = agent_extracted.get("missing_concepts", {})

    per_dim = {}
    total_matched = 0
    total_concepts = 0

    for dim in DIMENSIONS:
        cv = list(covered.get(dim, []) or [])
        ms = list(missing.get(dim, []) or [])
        cnt = len(cv)
        total = cnt + len(ms)
        total_matched += cnt
        total_concepts += total
        per_dim[dim] = {
            "covered": cnt,
            "total": total,
            "ratio": round(cnt / total, 4) if total else 0.0,
        }

    # 达标线 + 加权 → score (与 substring 模式公式完全一致)
    dim_score = {}
    for dim in DIMENSIONS:
        cv = list(covered.get(dim, []) or [])
        target = _TARGETS[dim]
        dim_score[dim] = min(len(cv) / target, 1.0)
    score = sum(dim_score[d] * _WEIGHTS[d] for d in DIMENSIONS) * 100
    score = round(score)

    # 精确覆盖率
    coverage_ratio = round(total_matched / total_concepts, 4) if total_concepts else 0.0

    # 补概念建议
    suggestions = []
    label_map = {
        "use_case": "use-case / scenario",
        "audience": "audience / persona",
        "goal": "user goal / outcome (why people buy)",
        "constraint": "constraint / qualifier",
    }
    for dim in DIMENSIONS:
        ms = list(missing.get(dim, []) or [])
        if ms:
            suggestions.append(
                f"add {label_map[dim]} concept e.g. {'/'.join(ms[:4])}"
            )

    # 来源标签
    source = "agent_semantic"
    if category and category in ontology:
        source += f" ({category})"

    return {
        "score": score,
        "coverage_ratio": coverage_ratio,
        "covered_concepts": covered,
        "missing_concepts": missing,
        "per_dimension": per_dim,
        "suggestions": suggestions,
        "category": category or None,
        "ontology_source": source,
        "used_fallback": False,
        "targets": dict(_TARGETS),
        "weights": dict(_WEIGHTS),
        "_extraction_method": "agent_semantic",
    }


# --------------------------- substring fallback ---------------------------

def _run_substring_mode(data, ontology, category):
    """用 substring 匹配算分（原逻辑，从 run() 抽离出来）。"""
    cat_ont, fallback = _get_category_ontology(ontology, category)
    text = _collect_listing_text(data)

    covered = {}
    missing = {}
    per_dim = {}
    total_matched = 0
    total_concepts = 0

    for dim in DIMENSIONS:
        words = cat_ont.get(dim, [])
        matched, miss = _scan_dimension(words, text)
        covered[dim] = matched
        missing[dim] = miss
        total = len(words)
        cnt = len(matched)
        total_matched += cnt
        total_concepts += total
        per_dim[dim] = {
            "covered": cnt,
            "total": total,
            "ratio": round(cnt / total, 4) if total else 0.0,
        }

    # 达标线 + 加权 → score
    dim_score = {}
    for dim in DIMENSIONS:
        words = cat_ont.get(dim, [])
        target = _TARGETS[dim]
        if not words:
            dim_score[dim] = 0.0
        else:
            dim_score[dim] = min(len(covered[dim]) / target, 1.0)
    score = sum(dim_score[d] * _WEIGHTS[d] for d in DIMENSIONS) * 100
    score = round(score)

    # 精确覆盖率
    coverage_ratio = round(total_matched / total_concepts, 4) if total_concepts else 0.0

    # 补概念建议
    suggestions = []
    label_map = {
        "use_case": "use-case / scenario",
        "audience": "audience / persona",
        "goal": "user goal / outcome (why people buy)",
        "constraint": "constraint / qualifier",
    }
    for dim in DIMENSIONS:
        if missing[dim]:
            suggestions.append(
                f"add {label_map[dim]} concept e.g. {'/'.join(missing[dim][:4])}"
            )

    # 本体来源标签
    if category and category in ontology:
        source = category
    elif fallback:
        source = "_common (fallback)"
    else:
        source = "_common" if "_common" in ontology else "none"

    return {
        "score": score,
        "coverage_ratio": coverage_ratio,
        "covered_concepts": covered,
        "missing_concepts": missing,
        "per_dimension": per_dim,
        "suggestions": suggestions,
        "category": category or None,
        "ontology_source": source,
        "used_fallback": fallback,
        "targets": dict(_TARGETS),
        "weights": dict(_WEIGHTS),
        "_extraction_method": "substring",
    }


# --------------------------- 核心纯函数 ---------------------------

def run(data):
    """COSMO 意图覆盖度评估。

    支持双模式：
      - Agent 语义提取优先: data 含 _cosmo_extracted → 直接用提取结果算分
      - substring 匹配回退: data 无 _cosmo_extracted → 走旧词库匹配

    Args:
        data: listing dict (需含 category 与若干文本字段)。
              可选 _cosmo_extracted: Agent 提前提取的 covered/missing concepts。

    Returns:
        dict, 含:
          score(0-100 达标线评分), coverage_ratio(0-1 精确覆盖率),
          covered_concepts(dict per dim), missing_concepts(dict per dim),
          per_dimension(dict per dim {covered,total,ratio}),
          suggestions(list), category, ontology_source, used_fallback,
          targets, weights, _extraction_method。
    """
    if not isinstance(data, dict):
        data = {}

    ontology = _load_ontology()
    category = (data.get("category") or "").strip()

    # ---- Agent 语义提取路径（优先）----
    agent_extracted = data.get("_cosmo_extracted")
    if isinstance(agent_extracted, dict) and agent_extracted.get("extraction_method") == "agent_semantic":
        return _run_agent_mode(agent_extracted, ontology, category)

    # ---- substring 匹配回退（原逻辑，不变）----
    return _run_substring_mode(data, ontology, category)


# --------------------------- CLI ---------------------------

def load_input():
    parser = argparse.ArgumentParser(description="COSMO intent-coverage check")
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
    # 评分类脚本始终退出 0
    sys.exit(0)


if __name__ == "__main__":
    main()
