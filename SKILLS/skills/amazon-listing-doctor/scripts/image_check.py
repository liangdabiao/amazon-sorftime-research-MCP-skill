#!/usr/bin/env python3
"""image_check.py — 图片缺陷检测 + CDQ 图片分（CDQ 权重 15%）。

检查项（任一命中即记为缺陷）：
  1. low_resolution      —— width < min_width(1000px)，不支持 zoom 缩放
  2. non_square          —— width != height（非 1:1 正方形）；若未给宽高则回退 is_square=false
  3. watermark           —— has_watermark=true（水印/品牌 logo 均禁止）
  4. main_not_white_bg   —— 第 1 张（主图）is_white_background=false（违反主图纯白底规则）

CDQ 四级打分（image_scoring）：
  image_count >= 4 且 无缺陷  -> 1.0
  image_count >= 4 且 有缺陷  -> 0.4
  image_count <  4 且 无缺陷  -> 0.6
  image_count <  4 且 有缺陷  -> 0.0

输入：{"images":[{"url":"","width":1200,"height":1200,"has_watermark":false,
                  "is_white_background":true,"is_square":true}],
       "category":"Electronics"}
输出：stdout 单个 JSON 对象；退出码 0=PASS / 1=FAIL（有缺陷或无主图均判 FAIL）。

说明：图片元数据（宽高/水印/白底）实战中由 LLM 视觉分析预填，本脚本只做规则判定。
"""

import sys
import json
import argparse
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- #
# 配置加载
# --------------------------------------------------------------------------- #
def _load_json(rel_path, default):
    """从 SKILL_ROOT/references/<rel_path> 读 JSON；缺失返回 default。"""
    p = SKILL_ROOT / "references" / rel_path
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default


def _load_rules():
    """图片规则（references/image_rules.json）。"""
    return _load_json("image_rules.json", {
        "min_width": 1000,
        "main_image_background": "white",
        "aspect_ratio": "1:1",
        "max_images": 9,
        "min_images_for_full_score": 4,
        "watermark_forbidden": True,
        "defect_types": ["low_resolution", "non_square", "watermark", "main_not_white_bg"],
    })


def _load_cdq_weights():
    """CDQ 权重（references/cdq_weights.json），用于读取 image_scoring 四级分值。"""
    return _load_json("cdq_weights.json", {})


# --------------------------------------------------------------------------- #
# 核心纯函数
# --------------------------------------------------------------------------- #
def run(data):
    """检测图片缺陷并计算 CDQ 图片分（纯函数，无副作用）。

    Args:
        data: dict，含 images 列表与可选 category。
              每个 image: {url, width, height, has_watermark,
                           is_white_background, is_square}

    Returns:
        dict: {field, image_count, defects, cdq_image_score,
               compliant, fix_suggestions}
    """
    rules = _load_rules()
    cdq = _load_cdq_weights()
    scoring = cdq.get("image_scoring", {})

    min_width = rules.get("min_width", 1000)
    full_score_min = rules.get("min_images_for_full_score", 4)
    max_images = rules.get("max_images", 9)

    images = data.get("images", []) or []
    image_count = len(images)

    defects = []

    # ---- 逐图缺陷检测 ----
    for idx, img in enumerate(images):
        width = img.get("width")
        height = img.get("height")
        has_watermark = bool(img.get("has_watermark", False))
        is_white_bg = img.get("is_white_background", True)
        is_square = img.get("is_square", True)

        # 缺陷 1：低分辨率（width < min_width，无法触发 zoom）
        if width is not None and width < min_width:
            defects.append({
                "image_index": idx,
                "defect_type": "low_resolution",
                "detail": (f"width={width}px 低于 {min_width}px，"
                           f"不支持 Amazon 图片 zoom 缩放功能"),
            })

        # 缺陷 2：非正方形。优先用 width/height 判定，二者缺失时回退 is_square
        if width is not None and height is not None:
            if width != height:
                defects.append({
                    "image_index": idx,
                    "defect_type": "non_square",
                    "detail": (f"width={width} ≠ height={height}，"
                               f"非 1:1 正方形（要求 {rules.get('aspect_ratio','1:1')}）"),
                })
        elif is_square is False:
            defects.append({
                "image_index": idx,
                "defect_type": "non_square",
                "detail": "is_square=false，非 1:1 正方形",
            })

        # 缺陷 3：水印
        if rules.get("watermark_forbidden", True) and has_watermark:
            defects.append({
                "image_index": idx,
                "defect_type": "watermark",
                "detail": "检测到水印（has_watermark=true），图片禁止含水印/品牌 logo",
            })

        # 缺陷 4：仅主图（第 1 张）——必须纯白底
        if idx == 0 and is_white_bg is False:
            defects.append({
                "image_index": idx,
                "defect_type": "main_not_white_bg",
                "detail": ("主图（第 1 张）背景非纯白"
                           f"（is_white_background=false，要求 {min_width}×{min_width} "
                           f"以上、RGB(255,255,255) 纯白底）"),
            })

    has_defect = len(defects) > 0

    # ---- CDQ 图片四级打分 ----
    if image_count >= full_score_min:
        cdq_image_score = (scoring.get("ge4_defect", 0.4) if has_defect
                           else scoring.get("ge4_no_defect", 1.0))
    else:
        cdq_image_score = (scoring.get("lt4_defect", 0.0) if has_defect
                           else scoring.get("lt4_no_defect", 0.6))

    # 量化为 0-1 浮点，避免 0.4 这种写成 0.4000000001 之类
    cdq_image_score = round(float(cdq_image_score), 4)

    # ---- 合规判定 ----
    # 有主图且无任何缺陷视为合规；数量不足（<4）只影响 CDQ 分，不计硬违规。
    # 但 0 张图（无主图）直接判 FAIL。
    compliant = (image_count >= 1) and (not has_defect)

    # ---- 修复建议 ----
    fix_suggestions = []
    if image_count == 0:
        fix_suggestions.append(
            "未提供任何图片，主图缺失；请至少上传 1 张纯白底正方形主图。"
        )
    else:
        if image_count < full_score_min:
            fix_suggestions.append(
                f"图片数量不足（当前 {image_count} 张 < {full_score_min} 张），"
                f"CDQ 图片分被压至 {cdq_image_score}；建议补充至 "
                f"{full_score_min}-{max_images} 张以拿满 1.0 分。"
            )
        if image_count > max_images:
            fix_suggestions.append(
                f"图片数量超过上限（{image_count} > {max_images} 张），"
                f"Amazon 单 ASIN 最多展示 {max_images} 张，建议删减。"
            )

    defect_types_found = sorted({d["defect_type"] for d in defects})
    if "low_resolution" in defect_types_found:
        fix_suggestions.append(
            f"存在低分辨率图片（width < {min_width}px），"
            f"需替换为 ≥{min_width}×{min_width}px 高清图以支持 zoom。"
        )
    if "non_square" in defect_types_found:
        fix_suggestions.append(
            f"存在非正方形图片，需裁剪/重做为 1:1 正方形"
            f"（推荐 {min_width}×{min_width}px 或 1600×1600px）。"
        )
    if "watermark" in defect_types_found:
        fix_suggestions.append(
            "检测到水印，需去除所有水印/品牌 logo/边框/文字叠加。"
        )
    if "main_not_white_bg" in defect_types_found:
        fix_suggestions.append(
            "主图（第 1 张）必须为 RGB(255,255,255) 纯白背景，"
            "需重新抠图并替换为纯白底。"
        )

    return {
        "field": "image",
        "image_count": image_count,
        "defects": defects,
        "cdq_image_score": cdq_image_score,
        "compliant": compliant,
        "fix_suggestions": fix_suggestions,
    }


# --------------------------------------------------------------------------- #
# IO 层（CLI）
# --------------------------------------------------------------------------- #
def load_input():
    """统一输入：--data > --file > stdin。"""
    parser = argparse.ArgumentParser(
        description="图片缺陷检测 + CDQ 图片分"
    )
    parser.add_argument("--data", help="inline JSON 字符串")
    parser.add_argument("--file", help="JSON 文件路径")
    a = parser.parse_args()
    if a.data:
        return json.loads(a.data)
    if a.file:
        return json.loads(Path(a.file).read_text(encoding="utf-8"))
    if not sys.stdin.isatty():  # is_tty 为笔误，正确为 isatty()
        return json.loads(sys.stdin.read())
    return {}


def main():
    data = load_input()
    result = run(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("compliant", True) else 1)


if __name__ == "__main__":
    main()
