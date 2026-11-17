#!/usr/bin/env python3
"""title_triage.py — 标题词组分诊（结构化诊断，路 A，零依赖）。

把标题拆成语义词组，按"词性 + 合规信号"给每个词组一个去向建议：
  keep_title        标题必留
  prefer_title      标题优先
  demote_highlights 下移亮点
  demote_bullets    下移五点
  remove            不建议使用（违规）

只诊断不改写。词组切分为启发式（标点 + 介词/连词边界），未分类词组标 low
confidence 留 Agent 复核。不依赖外部数据（流量/排名），复用 doctor 已有
references：
  - rules.json 的 forbidden_promo_words / forbidden_subjective
  - cosmo_ontology.json 的 use_case / audience / goal / constraint
  - alexa_lexicon.json 的 scene / audience / limitation（含分品类）

run(data) -> dict，契约同其他检查脚本。
"""

import sys
import json
import re
import argparse
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = SKILL_ROOT / "references" / "rules.json"
COSMO_PATH = SKILL_ROOT / "references" / "cosmo_ontology.json"
ALEXA_PATH = SKILL_ROOT / "references" / "alexa_lexicon.json"

# 动作枚举
A_KEEP = "keep_title"
A_PREFER = "prefer_title"
A_HIGHLIGHTS = "demote_highlights"
A_BULLETS = "demote_bullets"
A_REMOVE = "remove"

# 规格词信号：含阿拉伯数字（型号 / 版本 / 容量 / 尺寸 / 续航）
_SPEC_NUM = re.compile(r"\d")

# 词组切分：先按括号字符切（括号内容独立成块），再按标点切，再按虚词/介词/连词切
_PUNCT_SPLIT = re.compile(r"[,;|/—–]")
# 非捕获组 + 后接空格/结尾：避免介词本身进结果，也避免吃掉 "in-Ear" 这类连字符复合词里的 in
_FUNC_SPLIT = re.compile(r"\b(?:with|for|of|and|to|in|on|the|a|an|or)\b(?=\s|$)", re.IGNORECASE)


# --------------------------- 工具函数 ---------------------------

def _load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _split_phrases(text):
    """把一段文本切成有意义词组（启发式：标点 → 介词/连词边界）。"""
    chunks = re.split(r"[\[\]()]", text)  # 括号内容独立成块
    out = []
    for ch in chunks:
        ch = ch.strip()
        if not ch:
            continue
        for seg in _PUNCT_SPLIT.split(ch):
            seg = seg.strip()
            if not seg:
                continue
            for sub in _FUNC_SPLIT.split(seg):
                sub = sub.strip(" .,&\"'")
                if sub:
                    out.append(sub)
    return out


def _build_word_sets(rules, cosmo, alexa, lang, category):
    """合并 rules / cosmo / alexa 为分诊用的词集（去重）。"""
    t = rules.get("title", {})
    promo_kw = t.get("forbidden_promo_words", {})
    subj_kw = t.get("forbidden_subjective", {})
    promo = set(promo_kw.get(lang, []) + promo_kw.get("en", []))
    subjective = set(subj_kw.get(lang, []) + subj_kw.get("en", []))

    cc = cosmo.get("_common", {}) if isinstance(cosmo.get("_common"), dict) else {}
    ac_common = alexa.get("_common", {}) if isinstance(alexa.get("_common"), dict) else {}
    ac_cat = alexa.get(category, {}) if (category and isinstance(alexa.get(category), dict)) else {}

    scenes = set(cc.get("use_case", [])) | set(ac_common.get("scene", [])) | set(ac_cat.get("scene", []))
    audiences = set(cc.get("audience", [])) | set(ac_common.get("audience", [])) | set(ac_cat.get("audience", []))
    limits = set(cc.get("constraint", [])) | set(ac_common.get("limitation", [])) | set(ac_cat.get("limitation", []))
    goals = set(cc.get("goal", []))

    return {
        "promo": promo,
        "subjective": subjective,
        "scenes": scenes,
        "audiences": audiences,
        "limits": limits,
        "goals": goals,
    }


def _classify(phrase, brand_lower, sets):
    """单个词组 → (type, action, confidence, reason)。优先级从高到低，首个命中胜出。"""
    pl = phrase.lower()
    # 1. 促销 / 违规词（新规禁止入标题）
    for w in sets["promo"]:
        if w and w in pl:
            return ("promo", A_REMOVE, "high", f"含促销/违规词 '{w}'，新规禁止入标题")
    # 2. 主观夸大词
    for w in sets["subjective"]:
        if w and w in pl:
            return ("subjective", A_REMOVE, "high", f"含主观夸大词 '{w}'，新规禁止入标题")
    # 3. 品牌（放在 spec 前，防品牌名含数字如 3M 被误判规格）
    if brand_lower and pl == brand_lower:
        return ("brand", A_KEEP, "high", "品牌词，标题首位保留")
    # 4. 规格 / 参数（含数字）
    if _SPEC_NUM.search(phrase):
        return ("spec", A_BULLETS, "high", "规格/参数词，建议下移五点展开")
    # 5. 痛点 / 结果（COSMO goal 维度）
    for w in sets["goals"]:
        if w and w in pl:
            return ("pain_point", A_HIGHLIGHTS, "medium", f"结果/痛点词 '{w}'，建议下移亮点强调")
    # 6. 限制 / 卖点（waterproof / noise cancelling 等）
    for w in sets["limits"]:
        if w and w in pl:
            return ("limitation", A_HIGHLIGHTS, "medium", f"限制/卖点词 '{w}'，建议下移亮点强调")
    # 7. 场景
    for w in sets["scenes"]:
        if w and w in pl:
            return ("scene", A_HIGHLIGHTS, "medium", f"场景词 '{w}'，建议下移亮点")
    # 8. 对象（给谁用 / 适配谁）
    for w in sets["audiences"]:
        if w and w in pl:
            return ("audience", A_PREFER, "medium", f"对象词 '{w}'，购买决策相关，倾向保留标题")
    # 9. 未分类（多为品类 / 身份词）
    return ("general", A_KEEP, "low", "未分类词组（多为品类/身份词），默认保留为标题核心；可人工细分")


# --------------------------- 核心纯函数 ---------------------------

def run(data):
    """标题词组分诊。

    Args:
        data: listing dict（需含 title；brand / category / language / mode 可选）。

    Returns:
        dict: title / char_count / char_limit / over_char_limit / phrases[] /
        summary / note。缺 title 时返回空 phrases。
    """
    title = (data.get("title") or "").strip() if isinstance(data, dict) else ""
    if not title:
        return {"title": "", "char_count": 0, "char_limit": 75,
                "over_char_limit": False, "phrases": [], "summary": {},
                "note": "无标题，跳过词组分诊。"}

    lang = (data.get("language") or "en").strip()
    category = (data.get("category") or "").strip()
    brand = (data.get("brand") or "").strip()
    brand_lower = brand.lower()

    rules = _load_json(RULES_PATH)
    cosmo = _load_json(COSMO_PATH)
    alexa = _load_json(ALEXA_PATH)
    sets = _build_word_sets(rules, cosmo, alexa, lang, category)

    # 品牌单独成首个 phrase（brand_first 规则）；剩余 title 再切分
    phrases_raw = []
    title_for_split = title
    if brand:
        phrases_raw.append(brand)
        title_for_split = re.sub(re.escape(brand), " ", title, count=1, flags=re.IGNORECASE)
    phrases_raw.extend(_split_phrases(title_for_split))

    # 去重保序（同一词组只分诊一次；重复词由 lint_title 负责）
    seen = set()
    phrases = []
    for p in phrases_raw:
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        ptype, action, conf, reason = _classify(p, brand_lower, sets)
        # 多词词组命中单一语义类型 → 降置信，提示拆分（避免品类词被连带下移）
        # brand 不降（品牌必为独立词组）；其余语义类型多词时降，提示 Agent 拆分
        if len(key.split()) >= 3 and ptype in ("scene", "limitation", "pain_point", "audience", "spec"):
            conf = "low"
            reason += "；词组含多词，可能混入品类/身份词，建议拆分后仅移动命中部分"
        phrases.append({
            "phrase": p,
            "type": ptype,
            "action": action,
            "confidence": conf,
            "reason": reason,
        })

    summary = {k: 0 for k in (A_KEEP, A_PREFER, A_HIGHLIGHTS, A_BULLETS, A_REMOVE)}
    for ph in phrases:
        summary[ph["action"]] = summary.get(ph["action"], 0) + 1

    max_chars = rules.get("title", {}).get("max_chars", {}).get(
        data.get("mode") or "strict_75", 75)

    return {
        "title": title,
        "char_count": len(title),
        "char_limit": max_chars,
        "over_char_limit": len(title) > max_chars,
        "phrases": phrases,
        "summary": summary,
        "note": "词组切分为启发式（按标点与介词/连词边界），confidence=low 的词组需人工复核类型；本表只给去向建议，不生成改写文案。",
    }


# --------------------------- CLI ---------------------------

def load_input():
    parser = argparse.ArgumentParser(description="标题词组分诊（结构化诊断）")
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
    sys.exit(0)


if __name__ == "__main__":
    main()
