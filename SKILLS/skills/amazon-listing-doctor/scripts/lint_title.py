#!/usr/bin/env python3
# lint_title.py —— 亚马逊标题合规体检（最核心）。
import sys
import json
import argparse
import re
from pathlib import Path
from collections import Counter

SKILL_ROOT = Path(__file__).resolve().parent.parent
REF_DIR = SKILL_ROOT / "references"


# ---------------------------------------------------------------------------
# 归一化工具
# ---------------------------------------------------------------------------
def strip_hyphen(word: str) -> str:
    """去除连字符。"""
    return word.replace("-", "")


def singularize(word: str) -> str:
    """极简去复数：s/es/ies。"""
    low = word.lower()
    # ies -> y (babies -> baby)
    if low.endswith("ies") and len(low) > 4:
        return word[:-3] + "y"
    # es -> 去 (boxes -> box; 注：简单实现，不处理 hero/heroes 这类)
    if low.endswith("es") and len(low) > 3:
        return word[:-2]
    # s -> 去 (apples -> apple)
    if low.endswith("s") and not low.endswith("ss") and len(low) > 2:
        return word[:-1]
    return word


def normalize_word(word: str) -> str:
    """按 repeat_normalization 顺序归一化：strip_hyphen -> singularize -> lowercase。"""
    w = strip_hyphen(word)
    w = singularize(w)
    return w.lower()


def tokenize(text: str):
    """提取 token，保留连字符/撇号为整体（便于 strip_hyphen 归一化）。"""
    # 字母数字，允许中间连字符或撇号
    return re.findall(r"[A-Za-z0-9]+(?:[-’'][A-Za-z0-9]+)*", text)


# ---------------------------------------------------------------------------
# 配置加载
# ---------------------------------------------------------------------------
def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        # 配置坏掉不应静默，直接抛出
        raise RuntimeError(f"配置文件解析失败 {path}: {e}")


def load_rules():
    return _load_json(REF_DIR / "rules.json")


def load_categories():
    return _load_json(REF_DIR / "categories.json")


# ---------------------------------------------------------------------------
# 各检查项（纯函数，返回单个 check dict）
# ---------------------------------------------------------------------------
def check_char_limit(title, rules, categories_cfg, market, language, mode, category):
    """字符数检查：按 mode 取限值，媒体类目/ME 站豁免。"""
    title_rules = rules.get("title", {})
    max_chars = title_rules.get("max_chars", {"strict_75": 75, "transition_200": 200})
    cat_exempt = rules.get("category_exempt", {})
    media_cats = cat_exempt.get("media_categories", [])
    site_overrides = rules.get("site_overrides", {})

    # 默认上限
    mode = mode or "strict_75"
    limit = max_chars.get(mode, 75)

    # 媒体类目豁免 -> 200
    is_media = (
        category in media_cats
        or categories_cfg.get(category, {}).get("exempt_75_rule", False)
        or category == "Media"
    )
    if is_media:
        limit = max(limit, 200)

    # 站点覆盖
    me_override = site_overrides.get("ME", {})
    if me_override.get("skip_75_rule") and (market or "").upper() == "ME":
        limit = 200
        is_media = True

    jp_rec = site_overrides.get("JP", {}).get("recommended_max")

    actual = len(title)

    details = []
    if is_media:
        details.append("媒体类目豁免 75 字符新规")
    if (market or "").upper() == "ME":
        details.append("中东站跳过 75 字符规则")

    # 拼接串排查提示：页面抓取/第三方 API 拿到的常是「标题+亮点」拼接串（有 | 或无竖线逗号形态），
    # 拼接串当 title 审计会误判 FAIL。只给信号，拆分判断留给 Agent（见 SKILL.md §1.2）。
    has_pipe = "|" in title or "¦" in title
    if has_pipe:
        # 竖线是确定信号，与长度无关（真实 title + 亮点拼接后可能仍 <75），故独立于 FAIL 分支。
        details.append("标题含 | 分隔符：「标题+亮点」竖线拼接串，先按 | 拆分再判（见 SKILL.md 输入归一化 §1.2）")

    if actual > limit:
        status = "FAIL"
        details.append(f"超出上限 {actual}/{limit}")
        if not has_pipe:
            details.append("若来源为页面抓取/第三方 API：可能是「标题+亮点」拼接串（无竖线降级模板），先按无空格逗号边界拆分并自洽验证再判（见 SKILL.md 输入归一化 §1.2）")
    else:
        status = "PASS"

    # JP 推荐值附加提醒
    if jp_rec and actual > jp_rec and (market or "").upper() == "JP" and status != "FAIL":
        status = "WARN"
        details.append(f"日本站推荐 ≤{jp_rec}")

    check = {
        "status": status,
        "actual": actual,
        "limit": limit,
    }
    if details:
        check["details"] = details
    return check


def check_char_utilization(title, rules, categories_cfg, market, category, mode):
    """字符利用率检查：尽量用满 75 字符预算（A9 索引最大化）。

    75 是 A9 索引上限（免费预算），不用满=浪费索引空间。
    策略：核心词前置 50-60（移动端可见）+ 用满 75（A9 索引最大化）。
    媒体类目/ME 站豁免（无 75 限制，不查利用率）。
    这是 WARN 级建议（非硬规），但会进 fix_suggestions 引导补词。

    注（2026-07-27 新规）：标题与 item_highlights 在前端拼成一行，合计
    75+125=200 字符连续展示空间。但标题 75 仍是 A9 索引主战场（权重最高），
    用满 75 仍合理；亮点 125 的利用率由 lint_highlights.check_char_utilization
    负责。本函数只管标题内部预算，不越界管亮点。
    """
    title_rules = rules.get("title", {})
    max_chars = title_rules.get("max_chars", {"strict_75": 75, "transition_200": 200})
    cat_exempt = rules.get("category_exempt", {})
    media_cats = cat_exempt.get("media_categories", [])
    site_overrides = rules.get("site_overrides", {})

    cur_mode = mode or "strict_75"
    limit = max_chars.get(cur_mode, 75)

    # 媒体类目 / ME 站豁免 75，不查利用率
    is_media = (category in media_cats
                or categories_cfg.get(category, {}).get("exempt_75_rule", False)
                or category == "Media")
    is_me = ((market or "").upper() == "ME"
             and site_overrides.get("ME", {}).get("skip_75_rule"))
    if is_media or is_me:
        return {"status": "PASS", "actual": len(title), "limit": limit,
                "skipped": True, "details": ["媒体/ME 豁免,不查利用率"]}

    actual = len(title)
    full_threshold = limit - 3  # 用满阈值:留 3 字符安全余量(72)
    mobile_visible = title_rules.get("recommended_max", 60)  # 移动端首屏

    if actual >= full_threshold:
        status = "PASS"
        detail = f"用满预算 {actual}/{limit}"
    elif actual >= mobile_visible:
        status = "WARN"
        detail = f"未用满({actual}/{limit}),建议补有效属性/场景词用满 {limit} 字符(A9 索引最大化)"
    else:
        status = "WARN"
        detail = f"严重未用满({actual}/{limit}),浪费 A9 索引预算,建议补词至接近 {limit}"

    return {"status": status, "actual": actual, "limit": limit,
            "full_threshold": full_threshold, "details": [detail]}


def check_repeated_word(title, rules):
    """重复词检查：归一化后计数，虚词豁免，超 word_repeat_max 即 FAIL。"""
    title_rules = rules.get("title", {})
    word_repeat_max = title_rules.get("word_repeat_max", 2)
    exempt = set(title_rules.get("repeat_exempt", []))

    tokens = tokenize(title)
    norm_counts = Counter()
    # 记录归一化后的词对应的原始词示例
    sample = {}
    for tok in tokens:
        n = normalize_word(tok)
        if not n:
            continue
        if n in exempt:
            continue
        # 纯数字 token 跳过（型号/容量数字不算词重复）
        if n.isdigit():
            continue
        norm_counts[n] += 1
        sample.setdefault(n, tok)

    violations = [
        {"word": sample[n], "normalized": n, "count": c}
        for n, c in norm_counts.items()
        if c > word_repeat_max
    ]
    violations.sort(key=lambda x: -x["count"])

    return {
        "status": "FAIL" if violations else "PASS",
        "limit": word_repeat_max,
        "details": violations,
    }


def check_forbidden_char(title, rules, brand):
    """禁用字符检查：forbidden_chars + forbidden_non_ascii，品牌名 token 豁免。"""
    title_rules = rules.get("title", {})
    forbidden = list(title_rules.get("forbidden_chars", [])) + list(
        title_rules.get("forbidden_non_ascii", [])
    )

    # 品牌名豁免：从标题中删除品牌名出现处后再查
    remainder = title
    if brand:
        remainder = re.sub(re.escape(brand), "", title, flags=re.IGNORECASE)

    found = sorted({c for c in forbidden if c in remainder})
    return {
        "status": "FAIL" if found else "PASS",
        "details": found,
    }


def check_promo_word(title, rules, language):
    """促销词检查：按 language 取黑名单，子串匹配。

    语言兜底顺序：当前 language → 同语系近邻（de↔en, fr↔en, es↔en）→ en。
    多语言共用 en 黑名单可避免 de/fr 等黑名单尚未录入时的假阴性（漏报）。
    """
    title_rules = rules.get("title", {})
    promo_map = title_rules.get("forbidden_promo_words", {})
    lang = (language or "en").lower()
    blacklist = (
        list(promo_map.get(lang, []))
        + list(promo_map.get("en", []))
    )
    # 去重保持顺序
    seen = set()
    blacklist = [w for w in blacklist if not (w in seen or seen.add(w))]

    low = title.lower()
    found = [w for w in blacklist if w and w.lower() in low]
    return {
        "status": "FAIL" if found else "PASS",
        "details": found,
    }


def check_subjective_word(title, rules, language):
    """主观夸大词检查：按 language 取黑名单（与 promo 同源兜底）。"""
    title_rules = rules.get("title", {})
    subj_map = title_rules.get("forbidden_subjective", {})
    lang = (language or "en").lower()
    blacklist = (
        list(subj_map.get(lang, []))
        + list(subj_map.get("en", []))
    )
    seen = set()
    blacklist = [w for w in blacklist if not (w in seen or seen.add(w))]

    low = title.lower()
    found = [w for w in blacklist if w and w.lower() in low]
    return {
        "status": "FAIL" if found else "PASS",
        "details": found,
    }


# 合法全大写缩写白名单（常见科技/单位/型号缩写）
_ABBR_WHITELIST = {
    # 通用科技
    "USB", "HDMI", "LED", "LCD", "OLED", "QLED", "HD", "FHD", "UHD", "4K", "8K",
    "RGB", "CPU", "GPU", "RAM", "ROM", "SSD", "HDD", "TF", "SD", "SIM",
    "AC", "DC", "PWM", "DAC", "ADC", "AMP", "W", "V", "A", "Hz", "kHz", "MHz",
    "GHz", "mAh", "Ah", "Wh",
    "BT", "WIFI", "NFC", "GPS", "BLE",
    "ANC", "NC", "PA", "SNR", "THD",
    "AI", "API", "OS", "UI", "AR", "VR", "HDR",
    "Pro", "Max", "Plus", "Ultra", "Air", "Lite", "Mini", "Nano",
    "SUV", "MPV",
    "DJ", "MC", "PR", "HR",
    "USA", "UK", "EU",
    "MM", "CM", "KG", "G", "MG", "LB", "OZ", "FT", "IN",
    "PC", "TV", "PCB",
    "IP",  # IP67 防水等级
    "UPS", "PFC",
    "CD", "DVD", "CDN",
    "OK",
}

# 常见全大写品牌名兜底（不依赖用户传入 brand 字段）。
# 场景：用户直接复制 ASIN 详情页的标题，未填 brand；脚本不应当把品牌名当大小写违规。
# 与 brand_tokens 互补：本表是行业公认的"看起来像缩写但其实是品牌名"的兜底。
_BRAND_ABBR_WHITELIST = {
    "DJI",   # 大疆
    "BMW", "VW", "MG",   # 汽车（MG 同时也是重量单位，存疑时可走 brand_tokens）
    "LG", "HP", "HTC",   # 消费电子
    "OPPO", "VIVO", "IQOO", "REALME",   # 中国手机品牌
    "BYD",   # 比亚迪
    "SKF", "NSK",   # 轴承品牌（型号常用）
    "TCL", "SKYWORTH", "HISENSE",   # 家电
    "BAFANG",   # 电机品牌
    "SHIMANO", "SRAM", "CAMPAGNOLO",   # 自行车件
    "LEGO",
}


def check_casing(title, rules, brand):
    """全大写检查：标题中不应有整词全大写（品牌名/单位缩写/常见缩写豁免）。

    三道豁免：
      1) rules.allowed_unit_abbr（单位缩写）
      2) _ABBR_WHITELIST（通用科技/型号缩写）
      3) brand_tokens（用户传入 brand 字段派生的全大写 token）
      4) _BRAND_ABBR_WHITELIST（行业公认全大写品牌兜底，防 DJI/BMW/LG 等误判）
    """
    title_rules = rules.get("title", {})
    if not title_rules.get("no_all_caps", True):
        return {"status": "PASS", "details": []}

    allowed_units = set(u.upper() for u in title_rules.get("allowed_unit_abbr", []))
    whitelist = _ABBR_WHITELIST | allowed_units | _BRAND_ABBR_WHITELIST

    # 品牌名 token 加入白名单（常见写法 ANKER / Nike）
    brand_tokens = set()
    if brand:
        for part in re.split(r"[\s\-&]+", brand):
            if part:
                brand_tokens.add(part)
                brand_tokens.add(part.upper())

    violations = []
    for tok in tokenize(title):
        # 全大写判定：长度>=3、字母组成、全部大写
        if len(tok) >= 3 and tok.isalpha() and tok.isupper():
            if tok in whitelist or tok in brand_tokens:
                continue
            violations.append(tok)

    return {
        "status": "FAIL" if violations else "PASS",
        "details": sorted(set(violations)),
    }


def check_core_keyword_pos(title, brand, category, data, rules):
    """核心词前置：品牌（+品类词，若有 keywords.P1）须在前 core_keyword_within_chars 字符内。"""
    title_rules = rules.get("title", {})
    limit = title_rules.get("core_keyword_within_chars", 50)

    head = title[:limit]
    details = []

    # 1) 品牌前置（硬约束）
    brand_pos = None
    if brand:
        m = re.search(re.escape(brand), title, flags=re.IGNORECASE)
        if m:
            brand_pos = m.end()  # 品牌结束位置
            if brand_pos <= limit:
                details.append(f"品牌 '{brand}' 在前 {brand_pos} 字符内")
            else:
                details.append(f"品牌 '{brand}' 出现在第 {m.start()}~{m.end()} 字符，超出前 {limit}")

    # 2) 品类词前置（增强检查，有 keywords.P1 才查）
    keywords = (data or {}).get("keywords", {}) or {}
    p1_words = keywords.get("P1", []) or []
    p1_hit = None
    p1_miss = []
    for w in p1_words:
        m = re.search(re.escape(w), title, flags=re.IGNORECASE)
        if m and m.end() <= limit:
            p1_hit = w
        else:
            p1_miss.append(w)

    status = "PASS"
    if brand and brand_pos is None:
        status = "FAIL"
        details.append(f"标题中未找到品牌名 '{brand}'")
    elif brand and brand_pos is not None and brand_pos > limit:
        status = "FAIL"

    # 品类词不在前 limit 内：WARN（建议，非硬约束）
    if p1_words and p1_hit is None:
        if status != "FAIL":
            status = "WARN"
        details.append(f"品类词 {p1_miss} 均未出现在前 {limit} 字符内")

    # 取品牌或品类的最靠前结束位置作为 within_chars
    within = brand_pos if brand_pos is not None else limit
    return {
        "status": status,
        "within_chars": within,
        "limit": limit,
        "details": details,
    }


# 常见变体属性词（颜色/尺寸/口味/香味/款式），父 ASIN 标题不应包含
_VARIATION_LEXICON = {
    # 颜色
    "black", "white", "red", "blue", "green", "pink", "gray", "grey", "silver",
    "gold", "golden", "navy", "purple", "orange", "yellow", "brown", "beige",
    "teal", "maroon", "burgundy", "ivory", "cyan", "magenta", "charcoal",
    # 尺寸
    "small", "medium", "large", "x-large", "xxl", "xl", "xs", "s", "m", "l",
    "size", "tiny", "huge", "big",
    # 口味/香味
    "flavor", "flavoured", "flavored", "scent", "scented", "mint", "vanilla",
    "chocolate", "strawberry", "lemon", "lavender", "rose",
    # 款式
    "style", "version", "edition",
}


def check_variation(title, rules, data, is_parent):
    """变体检查：父 ASIN 标题不应包含颜色/尺寸/口味等子体属性。"""
    var_rules = rules.get("variation", {})
    if not var_rules.get("parent_no_attrs", True):
        return {"status": "PASS", "details": [], "skipped": True}
    if not is_parent:
        return {"status": "PASS", "details": [], "skipped": True, "reason": "非父 ASIN，跳过"}

    child_attrs = var_rules.get("child_attrs", [])
    lexicon = set(_VARIATION_LEXICON)

    # 若 data 提供 attributes，把 color/size/flavor/scent/style 的值也加入检查集
    attributes = (data or {}).get("attributes", {}) or {}
    for key in child_attrs:
        val = attributes.get(key)
        if isinstance(val, str) and val.strip():
            for part in re.split(r"[\s/,\-]+", val):
                if part.strip():
                    lexicon.add(part.strip().lower())

    tokens = [t.lower() for t in tokenize(title)]
    found = sorted({t for t in tokens if t in lexicon})

    return {
        "status": "FAIL" if found else "PASS",
        "details": found,
        "checked_attrs": child_attrs,
    }


# ---------------------------------------------------------------------------
# 主入口（纯函数）
# ---------------------------------------------------------------------------
def run(data: dict) -> dict:
    """标题合规体检主函数。data 进 -> 结果 dict 出。"""
    title = data.get("title", "") or ""
    brand = data.get("brand", "") or ""
    category = data.get("category", "") or ""
    market = data.get("market", "") or ""
    language = data.get("language", "") or "en"
    mode = data.get("mode", "") or "strict_75"
    is_parent = bool(data.get("is_parent", False))

    rules = load_rules()
    categories_cfg = load_categories()

    checks = {}
    checks["char_limit"] = check_char_limit(
        title, rules, categories_cfg, market, language, mode, category
    )
    checks["char_utilization"] = check_char_utilization(
        title, rules, categories_cfg, market, category, mode
    )
    checks["repeated_word"] = check_repeated_word(title, rules)
    checks["forbidden_char"] = check_forbidden_char(title, rules, brand)
    checks["promo_word"] = check_promo_word(title, rules, language)
    checks["subjective_word"] = check_subjective_word(title, rules, language)
    checks["casing"] = check_casing(title, rules, brand)
    checks["core_keyword_pos"] = check_core_keyword_pos(
        title, brand, category, data, rules
    )
    checks["variation"] = check_variation(title, rules, data, is_parent)

    # compliant: 不存在任何 FAIL
    has_fail = any(c.get("status") == "FAIL" for c in checks.values())
    compliant = not has_fail

    # 修复建议
    fix_suggestions = []
    if checks["char_limit"]["status"] == "FAIL":
        fix_suggestions.append(
            f"精简标题至 {checks['char_limit']['limit']} 字符以内（当前 {checks['char_limit']['actual']}）"
        )
    if checks["repeated_word"]["status"] == "FAIL":
        for v in checks["repeated_word"]["details"]:
            fix_suggestions.append(
                f"删除重复词 '{v['word']}'（归一化后出现 {v['count']} 次，上限 {checks['repeated_word']['limit']}）"
            )
    if checks["forbidden_char"]["status"] == "FAIL":
        fix_suggestions.append(
            f"移除禁用字符 {checks['forbidden_char']['details']}"
        )
    if checks["promo_word"]["status"] == "FAIL":
        fix_suggestions.append(
            f"删除促销/营销词 {checks['promo_word']['details']}"
        )
    if checks["subjective_word"]["status"] == "FAIL":
        fix_suggestions.append(
            f"删除主观夸大词 {checks['subjective_word']['details']}"
        )
    if checks["casing"]["status"] == "FAIL":
        fix_suggestions.append(
            f"将全大写词改为 Title Case（合法缩写除外）: {checks['casing']['details']}"
        )
    if checks["core_keyword_pos"]["status"] == "FAIL":
        fix_suggestions.append(
            f"将品牌名 '{brand}' 前置到前 {checks['core_keyword_pos']['limit']} 字符内"
        )
    if checks["variation"]["status"] == "FAIL":
        fix_suggestions.append(
            f"父 ASIN 标题不应包含子体属性词 {checks['variation']['details']}"
        )
    # char_utilization: WARN 级(用满是建议,非硬规),但给补词建议引导用满 75
    util = checks.get("char_utilization", {})
    if util.get("status") == "WARN" and util.get("details"):
        fix_suggestions.append(util["details"][0])

    return {
        "field": "title",
        "value": title,
        "char_count": len(title),
        "checks": checks,
        "compliant": compliant,
        "fix_suggestions": fix_suggestions,
    }


# ---------------------------------------------------------------------------
# CLI IO
# ---------------------------------------------------------------------------
def load_input():
    parser = argparse.ArgumentParser(description="标题合规体检")
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
