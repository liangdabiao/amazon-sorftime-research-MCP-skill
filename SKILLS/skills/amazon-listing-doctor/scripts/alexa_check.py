#!/usr/bin/env python3
"""alexa_check.py — Alexa 可发现性评估（doctor 独占维度，AEO 双模式）。

ALEXA 跟 COSMO 本质差异化：
  - COSMO = listing 内容写全了没（静态概念覆盖，agent 语义四维）
  - ALEXA = AI 购物助手（Alexa for Shopping / Rufus）在买家问答里能不能找到/推荐你
            （动态可发现性，AEO：Answer Engine Optimization）

双模式（镜像 cosmo_check.py 的双模式架构）：
  - AEO 模式（优先）：data 含 _alexa_aeo_result 时，用 Agent 针对该产品生成的买家问题
    的回答质量（buyer_alignment 三态：covered / partial / missing）算分。
  - substring 兜底：data 无 _alexa_aeo_result 时，走原场景/人群/限制词匹配（零依赖）。

AEO 算分（区别于 COSMO 的概念覆盖）：
    buyer_alignment_score = (covered*1.0 + partial*0.5) / total_questions * 100
  ALEXA 不算"概念覆盖"（那是 COSMO 的活），算"问题回答质量"。

用法：
  # Agent 前置：获取 AEO 提取提示词
  from alexa_check import get_agent_prompt
  ctx = get_agent_prompt(data)  # → listing_text + question_protocol + output_schema

  # 然后：Agent 判断每个买家问题的回答三态 → 写回 data["_alexa_aeo_result"] → run(data)
"""

import sys
import json
import re
import argparse
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
LEXICON_PATH = SKILL_ROOT / "references" / "alexa_lexicon.json"
PROTOCOL_PATH = SKILL_ROOT / "references" / "alexa_question_protocol.md"

# ---- substring 兜底模式参数（保留原值，零依赖可复现）----
TARGET_SCENE = 2
TARGET_AUDIENCE = 1
TARGET_LIMIT = 2
W_SCENE = 0.40
W_AUDIENCE = 0.30
W_LIMIT = 0.30

# ---- AEO 模式：三态加权（covered/partial/missing）----
W_COVERED = 1.0
W_PARTIAL = 0.5


# --------------------------- 工具函数 ---------------------------

def _load_lexicon():
    """加载 alexa_lexicon.json（substring 兜底用；AEO 不依赖）。"""
    if not LEXICON_PATH.exists():
        return {}
    return json.loads(LEXICON_PATH.read_text(encoding="utf-8"))


def _load_protocol():
    """加载 AEO 问题生成规范（alexa_question_protocol.md）。

    Agent 读规范 + listing，针对【该具体产品】生成买家问题（替代固定问题库，消除品类偏向）。
    """
    if not PROTOCOL_PATH.exists():
        return ""
    return PROTOCOL_PATH.read_text(encoding="utf-8")


def _get_category_lexicon(lexicon, category):
    """按 category 取词库; category 优先, 缺失维度回退 _common。

    返回 (merged_dict, used_fallback_flag)。
    merged_dict keys: scene / audience / limitation。
    """
    common = lexicon.get("_common", {}) if isinstance(lexicon.get("_common"), dict) else {}
    cat_entry = lexicon.get(category, {}) if isinstance(lexicon.get(category), dict) else {}

    merged = {}
    fallback_used = False
    for dim in ("scene", "audience", "limitation"):
        cval = cat_entry.get(dim)
        bval = common.get(dim)
        if cval:
            merged[dim] = list(cval)
        elif bval:
            merged[dim] = list(bval)
            fallback_used = True
        else:
            merged[dim] = []
    return merged, fallback_used


def _collect_listing_text(data):
    """合并 Alexa 可发现来源全文: title/highlights/bullets/description/backend/attributes。"""
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
    """词/短语是否在文本中出现 (词边界匹配, 大小写不敏感)。"""
    pattern = r"\b" + re.escape(word.lower()) + r"\b"
    return re.search(pattern, text) is not None


def _scan_dimension(words, text):
    """扫描一个维度的词表, 返回 (matched, missing)。"""
    matched, missing = [], []
    for w in words:
        (matched if _word_in_text(w, text) else missing).append(w)
    return matched, missing


# --------------------------- AEO Agent 提取接口 ---------------------------

def get_agent_prompt(data):
    """返回 Agent 做 ALEXA AEO 判断所需的全部上下文。

    模拟"AI 购物助手读到这条 listing 后，能否回答买家问题"。Agent 对问题池
    里每个问题判断 listing 能否回答，输出三态 covered / partial / missing。

    Args:
        data: listing dict（需含 category 与文本字段）。

    Returns:
        dict:
          - listing_text: listing 全文（同 _collect_listing_text 输出）
          - question_protocol: 问题生成规范（Agent 据此针对该产品生成问题，替代固定问题库）
          - instruction: AEO 生成+判断指令
          - output_schema: Agent 应输出的 JSON 格式（含 product / buyer_questions / buyer_alignment）
    """
    if not isinstance(data, dict):
        data = {}
    listing_text = _collect_listing_text(data)
    protocol = _load_protocol()

    return {
        "listing_text": listing_text,
        "question_protocol": protocol,
        "instruction": (
            "Read the question_protocol below — it defines an 8-aspect framework for generating real buyer questions. "
            "Do this in one pass: (1) understand what THIS product is from the listing; "
            "(2) generate 14-18 real buyer questions tailored to THIS specific product across the 8 aspects — "
            "DO NOT reuse generic or other-subcategory questions (e.g. don't ask earbuds questions for a phone, "
            "don't ask dog questions for a cat product); "
            "(3) for each generated question, judge whether the listing answers it: covered / partial / missing "
            "(strict — a generic spec list does NOT cover 'is this good for running?' unless the listing ties the "
            "product to running; uncertain → partial or missing, never pad covered). "
            "Return product, buyer_questions, and buyer_alignment per the schema."
        ),
        "output_schema": {
            "extraction_method": "aeo_agent",
            "product": "one line: what this product is + core attributes + typical buyer",
            "buyer_questions": ["14-18 real buyer questions tailored to THIS product"],
            "buyer_alignment": {
                "covered": ["question the listing fully answers"],
                "partial": ["question the listing partially addresses"],
                "missing": ["question the listing does not answer"],
            },
        },
    }


def _run_aeo_mode(aeo_result, category):
    """用 Agent AEO 三态结果算分。

    buyer_alignment_score = (covered*1.0 + partial*0.5) / total_questions * 100
    """
    if not isinstance(aeo_result, dict):
        aeo_result = {}
    product = aeo_result.get("product", "") or ""
    buyer_questions = list(aeo_result.get("buyer_questions", []) or [])
    alignment = aeo_result.get("buyer_alignment", {}) if isinstance(aeo_result.get("buyer_alignment"), dict) else {}
    covered = list(alignment.get("covered", []) or [])
    partial = list(alignment.get("partial", []) or [])
    missing = list(alignment.get("missing", []) or [])
    total = len(covered) + len(partial) + len(missing)
    # 三态为空但 Agent 生成了问题 → 用问题数兜底（防 Agent 只填 buyer_questions 漏分态）
    if total == 0 and buyer_questions:
        total = len(buyer_questions)

    score = (
        round((len(covered) * W_COVERED + len(partial) * W_PARTIAL) / total * 100)
        if total else 0
    )

    # 卖家最该补的回答：missing 的前 5 个
    top_missing = missing[:5]

    # suggestions：把 missing 问题转成"补这个回答"（区别于 COSMO 的"补概念词"）
    suggestions = [f'add an answer to this buyer question: "{q}"' for q in top_missing]

    source = category or "_common"

    return {
        "score": score,
        "product": product,
        "buyer_questions": buyer_questions,
        "buyer_alignment": {
            "covered": covered,
            "partial": partial,
            "missing": missing,
        },
        "total_questions": total,
        "covered_count": len(covered),
        "partial_count": len(partial),
        "missing_count": len(missing),
        "top_missing_questions": top_missing,
        "suggestions": suggestions,
        "category": category or None,
        "lexicon_source": source,
        "used_fallback": not bool(category),
        "weights": {"covered": W_COVERED, "partial": W_PARTIAL},
        "_extraction_method": "aeo_agent",
    }


# --------------------------- substring fallback ---------------------------

def _run_lexicon_mode(data, lexicon, category):
    """用 substring 匹配算分（原逻辑，从 run() 抽离，零依赖兜底）。"""
    cat_lex, fallback = _get_category_lexicon(lexicon, category)
    text = _collect_listing_text(data)

    scene_words = cat_lex.get("scene", [])
    audience_words = cat_lex.get("audience", [])
    limit_words = cat_lex.get("limitation", [])

    scene_matched, scene_missing = _scan_dimension(scene_words, text)
    aud_matched, aud_missing = _scan_dimension(audience_words, text)
    lim_matched, lim_missing = _scan_dimension(limit_words, text)

    scene_score = min(len(scene_matched) / TARGET_SCENE, 1.0) if scene_words else 0.0
    aud_score = min(len(aud_matched) / TARGET_AUDIENCE, 1.0) if audience_words else 0.0
    lim_score = min(len(lim_matched) / TARGET_LIMIT, 1.0) if limit_words else 0.0

    score = (scene_score * W_SCENE + aud_score * W_AUDIENCE + lim_score * W_LIMIT) * 100
    score = round(score)

    suggestions = []
    if scene_missing:
        suggestions.append(f"add scene word e.g. {'/'.join(scene_missing[:3])}")
    if aud_missing:
        suggestions.append(f"add audience word e.g. {'/'.join(aud_missing[:3])}")
    if lim_missing:
        suggestions.append(f"add limitation word e.g. {'/'.join(lim_missing[:3])}")

    if category and category in lexicon:
        source = category
    elif fallback:
        source = "_common (fallback)"
    else:
        source = "_common" if "_common" in lexicon else "none"

    return {
        # 必填字段（向后兼容 output-template / report-template / compliance_report）
        "score": score,
        "scene_coverage": scene_matched,
        "audience_coverage": aud_matched,
        "limit_coverage": lim_matched,
        "missing_scene": scene_missing,
        "suggestions": suggestions,
        # 诊断扩展字段
        "missing_audience": aud_missing,
        "missing_limit": lim_missing,
        "category": category or None,
        "lexicon_source": source,
        "used_fallback": fallback,
        "targets": {"scene": TARGET_SCENE, "audience": TARGET_AUDIENCE, "limit": TARGET_LIMIT},
        "weights": {"scene": W_SCENE, "audience": W_AUDIENCE, "limit": W_LIMIT},
        "_extraction_method": "substring",
    }


# --------------------------- 核心纯函数 ---------------------------

def run(data):
    """Alexa 可发现性评估（AEO 双模式）。

    支持双模式：
      - AEO 模式（优先）：data 含 _alexa_aeo_result（extraction_method=aeo_agent）
        → 用 Agent 对买家问题池的回答三态算 buyer_alignment 分。
      - substring 匹配回退：data 无 _alexa_aeo_result → 走场景/人群/限制词匹配。

    Args:
        data: listing dict（需含 category 与若干文本字段）。
              可选 _alexa_aeo_result: Agent 提前判断的 buyer_alignment 三态。

    Returns:
        dict。AEO 模式含 score/buyer_alignment/total_questions/covered_count/
        partial_count/missing_count/top_missing_questions/suggestions/_extraction_method。
        substring 模式含原 score/scene_coverage/audience_coverage/limit_coverage/
        missing_*/suggestions（向后兼容）。
    """
    if not isinstance(data, dict):
        data = {}

    category = (data.get("category") or "").strip()

    # ---- AEO 路径（优先）----
    aeo_result = data.get("_alexa_aeo_result")
    if isinstance(aeo_result, dict) and aeo_result.get("extraction_method") == "aeo_agent":
        return _run_aeo_mode(aeo_result, category)

    # ---- substring 匹配回退（原逻辑，不变）----
    lexicon = _load_lexicon()
    return _run_lexicon_mode(data, lexicon, category)


# --------------------------- CLI ---------------------------

def load_input():
    parser = argparse.ArgumentParser(description="Alexa discoverability check (AEO + substring fallback)")
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
