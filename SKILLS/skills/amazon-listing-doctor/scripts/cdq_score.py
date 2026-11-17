#!/usr/bin/env python3
# cdq_score.py — CDQ (Catalog Data Quality) 质量评分引擎
# 计算 6 维子分(0-1) × 权重 → 总分(0-100) → 档位 + 改进建议。
# 依据：cdq_weights.json。

import sys
import json
import argparse
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_ROOT / "references"

# 组件 key（与 cdq_weights.json 的 components 一致）
COMPONENT_KEYS = [
    "structured_attribute",
    "title",
    "variation",
    "image",
    "bullet_point",
    "a_plus",
]


# ---------------------------------------------------------------------------
# 配置加载
# ---------------------------------------------------------------------------
def _load_json(path):
    """安全加载 JSON 文件，不存在返回 None。"""
    if not Path(path).exists():
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_weights():
    """加载 cdq_weights.json，缺失则用默认值兜底。"""
    w = _load_json(REFERENCES / "cdq_weights.json")
    if w is None:
        w = {
            "components": {
                "structured_attribute": {"weight": 0.30},
                "title": {"weight": 0.25},
                "variation": {"weight": 0.20},
                "image": {"weight": 0.15},
                "bullet_point": {"weight": 0.05},
                "a_plus": {"weight": 0.05},
            },
            "title_rule": {"compliant_full": 1.0, "any_violation": 0.0},
            "image_scoring": {
                "ge4_no_defect": 1.0,
                "ge4_defect": 0.4,
                "lt4_no_defect": 0.6,
                "lt4_defect": 0.0,
            },
            "a_plus_scoring": {"has": 1.0, "missing": 0.0},
            "attributes_scoring": {
                "critical_6_full": 1.0,
                "formula": "filled_top10_ratio",
                "critical_defect_if_band_a_missing_gt_half": True,
            },
            "variation_scoring": {
                "correct_structure": 1.0,
                "defect": 0.0,
                "orphan_inapplicable": True,
            },
            "orphan_redistribute": True,
            "grades": {
                "optimized": [90, 100],
                "great": [80, 89],
                "good": [70, 79],
                "fair": [50, 69],
                "poor": [0, 49],
            },
        }
    return w


def _load_category_attrs(category):
    """按 category 名查 categories.json → category_attributes/<file>.json。"""
    if not category:
        return None
    cats = _load_json(REFERENCES / "categories.json") or {}
    cat_key = None
    target = str(category).strip().lower().replace(" ", "_")
    for k in cats:
        if k.startswith("_"):
            continue
        if k.lower().replace(" ", "_") == target:
            cat_key = k
            break
    if cat_key is None:
        return None
    attr_file = cats[cat_key].get("attr_file")
    if not attr_file:
        return None
    return _load_json(REFERENCES / "category_attributes" / attr_file)


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------
def _to_list(value):
    """接受 list 或 dict（取 keys），统一返回 list。"""
    if value is None:
        return []
    if isinstance(value, list):
        return [v for v in value if v]
    if isinstance(value, dict):
        return [k for k in value.keys() if k]
    return []


def _is_orphan(data):
    """孤儿 ASIN 判定：既非 parent 又非 variation 子体。"""
    if "is_orphan" in data:
        return bool(data["is_orphan"])
    return (not data.get("is_parent", False)) and (not data.get("is_variation", False))


def _round1(x):
    """保留 1 位小数（用于展示 score）。"""
    return round(x, 1)


def _round_score(x):
    """内部 score 保留 4 位避免浮点抖动。"""
    return round(x, 4)


# ---------------------------------------------------------------------------
# 6 维子分计算（每项返回 dict: {score, reason, missing?}）
# ---------------------------------------------------------------------------
def _score_attributes(data, cat_attrs, attr_cfg):
    """structured_attribute：filled_top10_ratio；band_a 缺失过半 → 严重缺陷 0 分。

    expected 来源标记 basis：user_provided（用户传入，可信）/
    builtin_fallback（类目文件兜底，公开版大类近似 → 分数为参考值）/
    no_reference（无任何基准 → 满分属数据假设，非真实满分）。
    """
    expected = _to_list(data.get("attributes_top10_expected"))
    if expected:
        basis = "user_provided"
    elif cat_attrs and _to_list(cat_attrs.get("top10_attributes")):
        expected = _to_list(cat_attrs.get("top10_attributes"))
        basis = "builtin_fallback"
    else:
        basis = "no_reference"
    # fallback 分数仍是参考值：清单为公开版大类近似，未经子品类校准
    ref_tag = " [reference: builtin broad-category list]" if basis == "builtin_fallback" else ""

    band_a = _to_list(data.get("band_a"))
    if not band_a and cat_attrs:
        band_a = _to_list(cat_attrs.get("band_a_critical_6"))

    filled = _to_list(data.get("attributes_filled"))
    if not filled:
        filled = _to_list(data.get("attributes"))
    # 属性名大小写归一（filled 常见 "Color"，清单为 "color"，同名不同写）
    filled_set = {str(a).strip().lower() for a in filled}

    def _norm(items):
        return [str(a).strip().lower() for a in items]

    band_a_filled = [a for a in _norm(band_a) if a in filled_set]
    band_a_missing = [a for a in _norm(band_a) if a not in filled_set]

    severe_flag = attr_cfg.get("critical_defect_if_band_a_missing_gt_half", True)
    # 惩罚性判决（0 分）只建立在可信基准上：builtin_fallback 清单未校准，
    # 缺失可能是"该子品类无此属性"而非"卖家漏填"——降为 ratio 参考值呈现
    if severe_flag and basis == "user_provided" and band_a and len(band_a_missing) > len(band_a) / 2:
        names = ",".join(band_a_missing[:3])
        suffix = " etc" if len(band_a_missing) > 3 else ""
        return {
            "score": 0.0,
            "basis": basis,
            "reason": f"critical defect: band_a missing {len(band_a_missing)}/"
                      f"{len(band_a)} (>half): {names}{suffix}{ref_tag}",
            "missing_top10": [a for a in expected if a not in filled_set],
        }

    if not expected:
        return {"score": 1.0, "basis": basis,
                "reason": "no expected attributes defined (assumed full — data gap, not verified)",
                "missing_top10": []}

    expected_norm = _norm(expected)
    filled_in_expected = [a for a in expected_norm if a in filled_set]
    missing = [a for a in expected_norm if a not in filled_set]
    ratio = len(filled_in_expected) / len(expected)
    return {
        "score": _round_score(ratio),
        "basis": basis,
        "reason": f"{len(filled_in_expected)}/{len(expected)} top10 filled{ref_tag}",
        "missing_top10": missing,
    }


def _score_title(data, title_cfg):
    """title：compliant_full=1.0 / any_violation=0.0。"""
    compliant = data.get("title_compliant")
    if compliant is None:
        tc = data.get("title_check")
        if isinstance(tc, dict):
            compliant = tc.get("compliant")
    if compliant is None:
        cc = data.get("compliance_checks")
        if isinstance(cc, dict) and isinstance(cc.get("title"), dict):
            compliant = cc["title"].get("compliant")
    if compliant is None:
        compliant = True  # 未提供则保守假设合规
    if compliant:
        return {"score": float(title_cfg.get("compliant_full", 1.0)),
                "reason": "compliant"}
    return {"score": float(title_cfg.get("any_violation", 0.0)),
            "reason": "violation detected → title 项 0 分"}


def _score_variation(data):
    """variation：correct_structure=1.0 / defect=0.0（孤儿不参与此项）。"""
    vc = data.get("variation_compliant")
    if vc is None:
        vc = True  # 未提供则保守假设正确
    if vc:
        return {"score": 1.0, "reason": "correct variation structure"}
    return {"score": 0.0, "reason": "defect: variation structure incorrect"}


def _score_image(data, img_cfg):
    """image：优先用 image_check 注入的真实缺陷评分；否则按 images_count 四级估算。

    V1 集成：compliance_report 先跑 image_check，把 cdq_image_score 注入 data。
    0 张图特殊处理——无主图即严重缺陷，判 0 分（覆盖默认的 0.6）。
    """
    injected = data.get("image_cdq_score")
    if injected is not None:
        count = int(data.get("images_count", 0) or 0)
        if count == 0:
            return {"score": 0.0,
                    "reason": "0 images → no main image, image 项 0 分"}
        defects = data.get("image_defects") or []
        if defects:
            return {"score": float(injected),
                    "reason": f"from image_check: {len(defects)} defect(s) detected"}
        return {"score": float(injected),
                "reason": f"from image_check: {count} images, no defect"}
    # fallback：未注入 image_check 结果时，按 images_count + defect 标志估算
    count = int(data.get("images_count", 0) or 0)
    defect = bool(data.get("images_defect", False) or
                  data.get("images_has_defect", False))
    if count >= 4:
        if defect:
            return {"score": float(img_cfg.get("ge4_defect", 0.4)),
                    "reason": f"{count} images (>=4), defect present (estimated)"}
        return {"score": float(img_cfg.get("ge4_no_defect", 1.0)),
                "reason": f"{count} images (>=4), no defect (estimated)"}
    else:
        if count == 0:
            return {"score": 0.0,
                    "reason": "0 images → no main image, image 项 0 分"}
        if defect:
            return {"score": float(img_cfg.get("lt4_defect", 0.0)),
                    "reason": f"{count} images (<4), defect present (estimated)"}
        return {"score": float(img_cfg.get("lt4_no_defect", 0.6)),
                "reason": f"{count} images (<4), no defect (estimated)"}


def _score_bullets(data):
    """bullet_point：5-6 条且合规=1.0；3-4 条=0.5；<3=0.0。"""
    bullets = data.get("bullets") or []
    count = len(bullets) if isinstance(bullets, list) else 0
    compliant = data.get("bullets_compliant")
    if compliant is None:
        compliant = True if count >= 5 else None
    if count >= 5:
        if compliant is False:
            return {"score": 0.5, "reason": f"{count} bullets but non-compliant"}
        return {"score": 1.0, "reason": f"{count} bullets, compliant"}
    if count >= 3:
        return {"score": 0.5, "reason": f"{count} bullets (<5)"}
    return {"score": 0.0, "reason": f"{count} bullets (<3)"}


def _score_a_plus(data, ap_cfg):
    """a_plus：has=1.0 / missing=0.0。"""
    if data.get("has_a_plus", False):
        return {"score": float(ap_cfg.get("has", 1.0)), "reason": "present"}
    return {"score": float(ap_cfg.get("missing", 0.0)), "reason": "missing"}


# ---------------------------------------------------------------------------
# 档位判定
# ---------------------------------------------------------------------------
def _grade(total, grades_cfg):
    """按 grades 区间返回档位名（首字母大写）。"""
    order = ["optimized", "great", "good", "fair", "poor"]
    t = int(round(total))
    for name in order:
        rng = grades_cfg.get(name)
        if rng and rng[0] <= t <= rng[1]:
            return name.capitalize()
    return "Poor"


# ---------------------------------------------------------------------------
# 改进建议
# ---------------------------------------------------------------------------
def _build_suggestions(comp_raw, weights, orphan):
    """针对非满分项生成可提分动作（gain 用重分配后的权重计算）。"""
    suggestions = []

    def gain(key):
        w = weights.get(key, 0.0)
        return round((1.0 - comp_raw[key]["score"]) * w * 100, 1)

    # A+（最易提分，单独列）
    if comp_raw["a_plus"]["score"] < 1.0:
        suggestions.append(f"Add A+ content (+{gain('a_plus')}%)")

    # 属性
    sa = comp_raw["structured_attribute"]
    if sa["score"] < 1.0:
        missing = sa.get("missing_top10", [])
        if missing:
            names = ",".join(missing[:3])
            suffix = " etc" if len(missing) > 3 else ""
            suggestions.append(
                f"Fill top10 attributes: {names}{suffix} (+{gain('structured_attribute')}%)")
        else:
            suggestions.append(
                f"Fix band_a critical attributes (+{gain('structured_attribute')}%)")

    # 标题
    if comp_raw["title"]["score"] < 1.0:
        suggestions.append(f"Fix title violations (+{gain('title')}%)")

    # 图片
    if comp_raw["image"]["score"] < 1.0:
        suggestions.append(
            f"Upload images to >=4 & fix defects (+{gain('image')}%)")

    # 五点
    if comp_raw["bullet_point"]["score"] < 1.0:
        suggestions.append(
            f"Write 5-6 bullets (500 chars each) (+{gain('bullet_point')}%)")

    # 变体（孤儿无此项）
    if not orphan and comp_raw["variation"]["score"] < 1.0:
        suggestions.append(
            f"Fix variation parent/child structure (+{gain('variation')}%)")

    return suggestions


# ---------------------------------------------------------------------------
# 主纯函数 run(data) -> dict
# ---------------------------------------------------------------------------
def run(data):
    """CDQ 评分主入口。

    输入 data（listing 子集 + 合规状态）：
      title_compliant / attributes_filled / attributes_top10_expected /
      band_a / is_variation / is_parent / images_count / images_defect /
      has_a_plus / bullets / category / variation_compliant ...
    输出：{total, grade, components:{...}, improve_suggestions:[...]}
    """
    if not isinstance(data, dict):
        data = {}

    cfg = _load_weights()
    comp_cfg = cfg.get("components", {})
    cat_attrs = _load_category_attrs(data.get("category"))

    orphan = _is_orphan(data)
    orphan_redist = bool(cfg.get("orphan_redistribute", True))

    # ---- 计算原始子分 ----
    sa = _score_attributes(data, cat_attrs,
                           cfg.get("attributes_scoring", {}))
    tt = _score_title(data, cfg.get("title_rule", {}))
    vr = _score_variation(data)
    im = _score_image(data, cfg.get("image_scoring", {}))
    bp = _score_bullets(data)
    ap = _score_a_plus(data, cfg.get("a_plus_scoring", {}))

    comp_raw = {
        "structured_attribute": sa,
        "title": tt,
        "variation": vr,
        "image": im,
        "bullet_point": bp,
        "a_plus": ap,
    }

    # ---- 确定各组件最终权重（孤儿重分配）----
    weights = {k: comp_cfg.get(k, {}).get("weight", 0.0) for k in COMPONENT_KEYS}
    if orphan and orphan_redist:
        # 去掉 variation，其余 5 项按比例放大
        remain = sum(w for k, w in weights.items() if k != "variation")
        if remain > 0:
            for k in weights:
                if k == "variation":
                    weights[k] = 0.0
                else:
                    weights[k] = weights[k] / remain

    # ---- 组装 components 输出 + 求总分 ----
    components_out = {}
    total = 0.0
    for k in COMPONENT_KEYS:
        if orphan and k == "variation":
            # 孤儿：variation 不适用，不参与计分
            components_out[k] = {
                "score": None,
                "weight": 0.0,
                "reason": "orphan ASIN: variation not applicable",
            }
            continue
        score = comp_raw[k]["score"]
        w = weights[k]
        components_out[k] = {
            "score": _round1(score),
            "weight": round(w, 4),
            "reason": comp_raw[k]["reason"],
        }
        if comp_raw[k].get("basis"):
            components_out[k]["basis"] = comp_raw[k]["basis"]
        total += score * w

    total_100 = _round1(total * 100)
    grade = _grade(total_100, cfg.get("grades", {}))
    suggestions = _build_suggestions(comp_raw, weights, orphan)

    return {
        "total": total_100,
        "grade": grade,
        "components": components_out,
        "improve_suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# CLI IO
# ---------------------------------------------------------------------------
def load_input():
    parser = argparse.ArgumentParser(description="CDQ quality scoring engine")
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
