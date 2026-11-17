#!/usr/bin/env python3
# compliance_report.py —— 汇总检查脚本，输出最终体检报告。
#
# 行为：通过 import 同目录其他脚本的 run() 函数汇总（不用 subprocess）。
# 依赖（运行时解析，缺一不崩溃，对应字段回退到 output-template.json 空值）：
#   lint_title / lint_highlights / lint_bullets / lint_backend
#   cdq_score / indexability / alexa_check / check_keyword_layering
#
# 输入：完整 listing（stdin JSON 优先 / --data / --file）
# 输出：stdout 一个 JSON 对象（完整 output-template.json 结构）
# 退出码：0=总体合规 / 1=有 FAIL
#
# 数据分层：
#   - 前台（详情页可见）: title / item_highlights / bullets / description / images / has_a_plus /
#                         brand / category / market / language / attributes_filled /
#                         attributes_top10_expected
#     买家在 Amazon 详情页可直接看到的字段（item_highlights 与 title 标题区竖线拼接同行显示；
#     但 item_highlights 卖家精灵取不到，需 Seller Central 导出）
#   - 后台（仅 Seller Central）: backend_search_terms / band_a_critical_6 /
#                                 is_parent / is_variation / parent_sku_attrs
#     详情页不显示，必须从 Seller Central 后台导出
#   - 评分维度对各字段的最低依赖：
#     * COSMO / Alexa:  title + 至少 1 个意图来源（bullets / item_highlights / description）
#     * CDQ:             title（合规判定） + attributes_filled 或 attributes_top10_expected +
#                        bullets（≥3） + images（含元数据）+ has_a_plus
#     * Indexability:    title（核心词前置） + backend_search_terms + attributes
#
# 降级原则：
#   - 缺关键字段时，相关评分维度显式返回 score=null + reason=字段缺失，不强行给 0/100
#   - 汇总报告增加 data_coverage 板块：标记已收字段、缺失字段、可解锁维度

import sys
import json
import argparse
import importlib
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent

# 插入脚本目录到 sys.path，便于 import 同目录其他脚本
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# 数据分层定义
# ---------------------------------------------------------------------------
# 每个维度依赖的"关键字段"。缺失时该维度降级为 score=null。
DIMENSION_REQUIRED_FIELDS = {
    "cosmo_intent": ["title"],
    "alexa_discoverability": ["title"],
    "cdq_score": ["title_compliant_status"],  # 由 compliance_report 内部注入
    "indexability": ["title"],
    "backend_hygiene": ["backend_search_terms"],
    "attribute_completeness": ["attributes_top10_expected"],
    "image_defect": ["images"],
}


# 前台 vs 后台字段清单（用于 data_coverage 报告）
# 原则：详情页可见 = 前台；仅 Seller Central 后台可编辑/查看 = 后台
FRONTEND_FIELDS = [
    ("title", "商品标题（前台核心）"),
    ("item_highlights", "商品亮点（≤125字符，标题区竖线拼接可见，但需 Seller Central 导出）"),
    ("bullets", "五点描述（前台详情页，5 条卖点）"),
    ("description", "产品详情 / A+ 描述（前台）"),
    ("images", "图片组（含 width/height/is_white_background 等元数据）"),
    ("brand", "品牌名"),
    ("category", "类目"),
    ("has_a_plus", "A+ 内容存在性（badge.ebc）"),
    ("market", "目标站点"),
    ("language", "目标语言"),
    ("attributes_filled", "已填属性列表（前台 Product Details 表格可见）"),
    ("attributes_top10_expected", "类目 Top10 必填属性清单（参考项，可查 category_attributes/<cat>.json 兜底）"),
]

BACKEND_FIELDS = [
    ("backend_search_terms", "后台搜索词（≤250 字节，详情页不显示，纯 A9 索引）"),
    ("band_a_critical_6", "Band A 关键 6 项"),
    ("is_parent", "父 ASIN 标记"),
    ("is_variation", "子体 ASIN 标记"),
    ("parent_sku_attrs", "父子体属性映射（父→子 SKU 配色/尺寸）"),
]


def _is_present(value):
    """字段是否"非空"。None / 空字符串 / 空列表 / 空 dict 都视为缺失。"""
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, (list, dict, tuple)) and len(value) == 0:
        return False
    return True


def _assess_data_coverage(data):
    """扫描 listing 输入，输出数据覆盖度报告。

    Returns:
        dict: {
          frontend: {provided: [...], missing: [...]},
          backend:  {provided: [...], missing: [...]},
          overall:  "minimal" | "partial" | "complete",
          unlock_dimensions: [...],
        }
    """
    if not isinstance(data, dict):
        data = {}

    frontend_provided, frontend_missing = [], []
    for key, label in FRONTEND_FIELDS:
        if _is_present(data.get(key)):
            frontend_provided.append(key)
        else:
            frontend_missing.append({"field": key, "label": label})

    backend_provided, backend_missing = [], []
    for key, label in BACKEND_FIELDS:
        if _is_present(data.get(key)):
            backend_provided.append(key)
        else:
            backend_missing.append({"field": key, "label": label})

    total = len(FRONTEND_FIELDS) + len(BACKEND_FIELDS)
    got = len(frontend_provided) + len(backend_provided)
    ratio = got / total if total else 0.0

    if ratio < 0.3:
        overall = "minimal"
    elif ratio < 0.7:
        overall = "partial"
    else:
        overall = "complete"

    # 评分维度解锁清单：补齐这些字段后，可解锁对应评分
    unlock = []
    if not _is_present(data.get("item_highlights")):
        unlock.append({
            "field": "item_highlights",
            "label": "补 item_highlights → 解锁 A9 收录高亮强度 + COSMO 覆盖广度",
            "source": "Seller Central 后台导出",
        })
    if not _is_present(data.get("backend_search_terms")):
        unlock.append({
            "field": "backend_search_terms",
            "label": "补 backend_search_terms → 解锁 backend 卫生分 + A9 长尾词覆盖",
            "source": "Seller Central 后台导出",
        })
    if not (_is_present(data.get("attributes_filled"))
            and _is_present(data.get("attributes_top10_expected"))):
        unlock.append({
            "field": "attributes_filled + attributes_top10_expected",
            "label": "补 structured attributes → 解锁 CDQ 30% 权重 + A9 属性完整度",
            "source": "第三方 API（attributes 字段）/ 类目属性文件 category_attributes/<cat>.json",
        })
    if not (_is_present(data.get("is_parent"))
            and _is_present(data.get("is_variation"))):
        unlock.append({
            "field": "is_parent + is_variation",
            "label": "补父子体标记 → 解锁 CDQ variation 20% 权重 + 父体属性隔离检查",
            "source": "Seller Central 父子体关系",
        })
    if not _is_present(data.get("images")):
        unlock.append({
            "field": "images",
            "label": "补图片组（含 width/height/is_white_background/is_square 元数据）→ 解锁 CDQ 15% 权重",
            "source": "Claude 视觉分析用户贴图后填入，或第三方 API 取主图 URL",
        })

    return {
        "frontend": {
            "provided": frontend_provided,
            "missing": frontend_missing,
            "provided_count": len(frontend_provided),
            "total_count": len(FRONTEND_FIELDS),
        },
        "backend": {
            "provided": backend_provided,
            "missing": backend_missing,
            "provided_count": len(backend_provided),
            "total_count": len(BACKEND_FIELDS),
        },
        "ratio": round(ratio, 4),
        "overall": overall,
        "unlock_dimensions": unlock,
    }


def _safe_score(value, reason=None):
    """评分降级封装：score=null + reason，否则原值透传。"""
    if value is None:
        return {"score": None, "available": False, "reason": reason or "input insufficient"}
    return {"score": value, "available": True}


def _try_import(name):
    """安全 import 一个同目录脚本模块，失败返回 None（其他脚本可能尚未生成）。"""
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def _safe_run(module, data):
    """调用 module.run(data)；模块缺失或抛错返回 None，不中断汇总。"""
    if module is None:
        return None
    run_fn = getattr(module, "run", None)
    if run_fn is None:
        return None
    try:
        return run_fn(data)
    except Exception as e:
        return {"error": f"{module.__name__}.run failed: {e}"}


def _load_template():
    """读取 assets/output-template.json 作为空值骨架。"""
    tpl_path = SKILL_ROOT / "assets" / "output-template.json"
    if tpl_path.exists():
        return json.loads(tpl_path.read_text(encoding="utf-8"))
    return {}


def _count_checks(report_sections):
    """统计 lint 段 checks 中 PASS / FAIL / WARN 数量。

    只统计 dict 型 check 的 status 字段；顶层 compliant 不在此处计。
    """
    passed = failed = warnings = 0
    for sec in report_sections:
        if not isinstance(sec, dict):
            continue
        checks = sec.get("checks", {})
        if not isinstance(checks, dict):
            continue
        for chk in checks.values():
            if not isinstance(chk, dict):
                continue
            status = str(chk.get("status", "")).upper()
            if status == "PASS":
                passed += 1
            elif status == "FAIL":
                failed += 1
            elif status == "WARN":
                warnings += 1
    return passed, failed, warnings


def _overall_compliant(sections):
    """所有含 compliant 字段的 lint 段全部 True，才算总体合规。

    attributes/variation 段也参与：attributes.compliant 看 filled_ratio。
    """
    for sec in sections:
        if isinstance(sec, dict) and "compliant" in sec:
            if not sec["compliant"]:
                return False
    return True


def _collect_critical(lint_sections):
    """收集 FAIL 级别检查项作为 critical_issues。"""
    critical = []
    for sec in lint_sections:
        if not isinstance(sec, dict):
            continue
        label = sec.get("field", "unknown")
        checks = sec.get("checks", {})
        if not isinstance(checks, dict):
            continue
        for chk_name, chk in checks.items():
            if isinstance(chk, dict) and str(chk.get("status", "")).upper() == "FAIL":
                critical.append({
                    "field": label,
                    "check": chk_name,
                    "detail": chk,
                })
    return critical


def _collect_action_items(title_r, hl_r, bul_r, bak_r, cdq_r, idx_r, alexa_r, kw_r):
    """汇总各段的 fix/improve/suggestion/risks/duplicates 为 action_items 列表。"""
    items = []
    # lint 段的 fix_suggestions
    for label, sec in (
        ("title", title_r), ("highlights", hl_r),
        ("bullets", bul_r), ("backend", bak_r),
    ):
        if isinstance(sec, dict):
            for s in sec.get("fix_suggestions", []) or []:
                items.append({"source": label, "action": str(s)})
    # cdq 改进建议
    if isinstance(cdq_r, dict):
        for s in cdq_r.get("improve_suggestions", []) or []:
            items.append({"source": "cdq", "action": str(s)})
    # indexability 风险
    if isinstance(idx_r, dict):
        for r in idx_r.get("risks", []) or []:
            items.append({"source": "indexability", "action": str(r)})
    # alexa 建议
    if isinstance(alexa_r, dict):
        for s in alexa_r.get("suggestions", []) or []:
            items.append({"source": "alexa", "action": str(s)})
    # 关键词分层重复
    if isinstance(kw_r, dict):
        for d in kw_r.get("duplicates_across_layers", []) or []:
            items.append({"source": "keyword", "action": str(d)})
    return items


def run(data):
    """汇总 8 个检查脚本，返回完整 output-template 结构。

    Args:
        data: 完整 listing dict。

    Returns:
        dict: 与 assets/output-template.json 结构对齐的最终报告。
        任一依赖脚本缺失或报错，对应字段回退到模板空值，不中断汇总。
        增加 data_coverage 板块（数据分层 + 缺失字段 + 可解锁维度）。
        评分降级：缺关键字段时，相关维度显式标 score=null + reason=字段缺失。
    """
    # 延迟 import：运行时解析，其他脚本可能尚未生成
    lint_title = _try_import("lint_title")
    lint_highlights = _try_import("lint_highlights")
    lint_bullets = _try_import("lint_bullets")
    lint_backend = _try_import("lint_backend")
    cdq_score = _try_import("cdq_score")
    indexability = _try_import("indexability")
    alexa_check = _try_import("alexa_check")
    check_keyword_layering = _try_import("check_keyword_layering")
    image_check = _try_import("image_check")
    cosmo_check = _try_import("cosmo_check")
    title_triage = _try_import("title_triage")

    title_r = _safe_run(lint_title, data)
    hl_r = _safe_run(lint_highlights, data)
    bul_r = _safe_run(lint_bullets, data)
    bak_r = _safe_run(lint_backend, data)

    # ---- 数据覆盖度评估（前置，所有评分共享）----
    data_coverage = _assess_data_coverage(data)
    has_title = _is_present(data.get("title"))
    has_highlights = _is_present(data.get("item_highlights"))
    has_backend = _is_present(data.get("backend_search_terms"))
    has_attributes = _is_present(data.get("attributes_filled")) or _is_present(
        data.get("attributes_top10_expected")
    )
    has_images = isinstance(data, dict) and bool(data.get("images"))
    has_bullets = _is_present(data.get("bullets"))

    # 图片检查：先跑，把真实缺陷评分注入 data 供 cdq_score 使用
    img_r = _safe_run(image_check, data) if has_images else None
    # 始终用副本，避免注入污染原始 data
    data_for_cdq = dict(data) if isinstance(data, dict) else {}
    if isinstance(img_r, dict) and "cdq_image_score" in img_r:
        data_for_cdq["image_cdq_score"] = img_r["cdq_image_score"]
        data_for_cdq["image_defects"] = img_r.get("defects", [])
        data_for_cdq["images_count"] = img_r.get("image_count", data.get("images_count", 0))
    # CDQ 注入：把 lint 合规结果喂给 cdq_score，避免它对 title/bullets 保守假设合规
    if isinstance(title_r, dict) and "compliant" in title_r:
        data_for_cdq["title_compliant"] = title_r["compliant"]
    if isinstance(bul_r, dict) and "compliant" in bul_r:
        data_for_cdq["bullets_compliant"] = bul_r["compliant"]
    # CDQ 注入：标记关键字段缺失，让 cdq_score 优雅降级
    data_for_cdq["_missing"] = {
        "title": not has_title,
        "bullets": not has_bullets,
        "attributes": not has_attributes,
        "images": not has_images,
    }

    cdq_r = _safe_run(cdq_score, data_for_cdq)
    idx_r = _safe_run(indexability, data)
    alexa_r = _safe_run(alexa_check, data)
    kw_r = _safe_run(check_keyword_layering, data)
    cosmo_r = _safe_run(cosmo_check, data)
    triage_r = _safe_run(title_triage, data)

    template = _load_template()

    # ---- 元信息（透传 listing 头部字段）----
    meta = {
        "market": data.get("market", ""),
        "language": data.get("language", ""),
        "mode": data.get("mode", ""),
        "category": data.get("category", ""),
        "brand": data.get("brand", ""),
        "is_parent": data.get("is_parent", False),
        "is_variation": data.get("is_variation", False),
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_coverage_overall": data_coverage["overall"],
        "data_coverage_ratio": data_coverage["ratio"],
    }

    # ---- 合规段：优先脚本结果，否则模板空值 ----
    title_out = title_r if isinstance(title_r, dict) else template.get("title", {})
    hl_out = hl_r if isinstance(hl_r, dict) else template.get("highlights", {})
    bul_out = bul_r if isinstance(bul_r, dict) else template.get("bullets", {})
    bak_out = bak_r if isinstance(bak_r, dict) else template.get("backend", {})

    # ---- 属性完整度（从 listing 原始数据推导）----
    attrs_filled = list(data.get("attributes_filled", []) or [])
    attrs_expected = list(data.get("attributes_top10_expected", []) or [])
    band_a = list(data.get("band_a_critical_6", []) or [])
    filled_ratio = (len(attrs_filled) / len(attrs_expected)) if attrs_expected else 0.0
    band_a_filled = [a for a in attrs_filled if a in band_a]
    # band_a 关键 6 项缺漏过半视为严重缺陷；此处 compliant 用 60% 门槛
    attributes_out = {
        "filled": attrs_filled,
        "top10_expected": attrs_expected,
        "filled_ratio": round(filled_ratio, 4),
        "band_a_critical_6": band_a,
        "band_a_filled": band_a_filled,
        "compliant": filled_ratio >= 0.6,
        "input_available": has_attributes,
        "input_unavailable_reason": (
            None if has_attributes
            else "attributes_filled / attributes_top10_expected 均为空，"
                 "无法计算属性完整度（建议从 Seller Central 后台导出 Top10 属性）"
        ),
    }

    # ---- 变体结构（透传）----
    variation_base = dict(template.get("variation", {}))
    variation_base.update({
        "is_parent": data.get("is_parent", False),
        "is_variation": data.get("is_variation", False),
    })

    cdq_out = cdq_r if isinstance(cdq_r, dict) else template.get("cdq_score", {})
    idx_out = idx_r if isinstance(idx_r, dict) else template.get("indexability_report", {})
    alexa_out = alexa_r if isinstance(alexa_r, dict) else template.get("alexa_discoverability", {})
    kw_out = kw_r if isinstance(kw_r, dict) else template.get("keyword_coverage", {})
    img_out = img_r if isinstance(img_r, dict) else {}
    cosmo_out = cosmo_r if isinstance(cosmo_r, dict) else {}
    triage_out = triage_r if isinstance(triage_r, dict) else template.get("triage_report", {})

    # ---- 评分降级封装 ----
    # COSMO：缺 title → score=null
    if isinstance(cosmo_out, dict):
        cosmo_out.setdefault("input_available", has_title and has_bullets)
        cosmo_out.setdefault("input_unavailable_reason", None)
        if not has_title:
            cosmo_out["score"] = None
            cosmo_out["input_available"] = False
            cosmo_out["input_unavailable_reason"] = "缺 title，COSMO 意图扫描无文本"
        elif not (has_bullets or has_highlights):
            cosmo_out["score"] = None
            cosmo_out["input_available"] = False
            cosmo_out["input_unavailable_reason"] = (
                "缺 bullets / item_highlights，COSMO 意图扫描范围太小"
            )

    # Alexa：缺 title → score=null（AEO 买家问题回答评估）
    if isinstance(alexa_out, dict):
        alexa_out.setdefault("input_available", has_title and has_bullets)
        alexa_out.setdefault("input_unavailable_reason", None)
        if not has_title:
            alexa_out["score"] = None
            alexa_out["input_available"] = False
            alexa_out["input_unavailable_reason"] = "缺 title，Alexa 可发现性评估无文本"
        elif not (has_bullets or has_highlights):
            alexa_out["score"] = None
            alexa_out["input_available"] = False
            alexa_out["input_unavailable_reason"] = (
                "缺 bullets / item_highlights，Alexa 买家问题回答评估范围太小"
            )

    # Indexability：缺 title → core_keyword=null；缺 backend → backend_hygiene=null；
    #                缺 attributes → attribute_completeness=null
    if isinstance(idx_out, dict):
        if not has_title:
            idx_out["core_keyword_position"] = None
            idx_out["core_keyword_within_limit"] = None
            idx_out["score_unavailable"] = idx_out.get("score_unavailable", []) + [
                {"field": "core_keyword", "reason": "缺 title"}
            ]
        if not has_backend:
            idx_out["backend_hygiene"] = None
            idx_out["backend_hygiene_checks"] = {}
            idx_out["score_unavailable"] = idx_out.get("score_unavailable", []) + [
                {"field": "backend_hygiene", "reason": "缺 backend_search_terms"}
            ]
        if not has_attributes:
            idx_out["attribute_completeness"] = None
            idx_out["attribute_filled"] = 0
            idx_out["attribute_expected"] = 0
            idx_out["score_unavailable"] = idx_out.get("score_unavailable", []) + [
                {"field": "attribute_completeness", "reason": "缺 attributes_filled + attributes_top10_expected"}
            ]

    # CDQ：缺标题/属性/图片/五点时，对应子分=null + reason
    if isinstance(cdq_out, dict) and isinstance(cdq_out.get("components"), dict):
        comps = cdq_out["components"]
        unavailable = []
        if not has_title:
            comps["title"] = {"score": None, "weight": comps.get("title", {}).get("weight", 0),
                              "reason": "缺 title，无法判定合规", "available": False}
            unavailable.append({"field": "title", "reason": "缺 title"})
        if not has_attributes:
            comps["structured_attribute"] = {
                "score": None,
                "weight": comps.get("structured_attribute", {}).get("weight", 0),
                "reason": "缺 attributes_filled + attributes_top10_expected",
                "available": False,
            }
            unavailable.append({"field": "structured_attribute", "reason": "缺 attributes"})
        if not has_images:
            comps["image"] = {
                "score": None,
                "weight": comps.get("image", {}).get("weight", 0),
                "reason": "缺 images（含 width/height/is_white_background/is_square）",
                "available": False,
            }
            unavailable.append({"field": "image", "reason": "缺 images"})
        if not has_bullets:
            comps["bullet_point"] = {
                "score": None,
                "weight": comps.get("bullet_point", {}).get("weight", 0),
                "reason": "缺 bullets，无法判定五点合规",
                "available": False,
            }
            unavailable.append({"field": "bullet_point", "reason": "缺 bullets"})
        if unavailable:
            cdq_out["score_unavailable"] = unavailable
            # 总分仅基于可用子分；保留原有 total 但补 available_total 字段
            available_scores = [
                c["score"] for c in comps.values()
                if isinstance(c, dict) and isinstance(c.get("score"), (int, float))
            ]
            available_weights = [
                c.get("weight", 0) for c in comps.values()
                if isinstance(c, dict) and isinstance(c.get("score"), (int, float))
            ]
            if available_scores and sum(available_weights) > 0:
                # 把可用子分按原始权重归一化到 100 分
                avail_total = sum(
                    comps[k]["score"] * comps[k]["weight"]
                    for k in comps
                    if isinstance(comps[k].get("score"), (int, float))
                )
                cdq_out["available_total"] = round(avail_total * 100, 1)
                cdq_out["available_grade"] = (
                    "Partial" if avail_total * 100 < 90 else "Partial (Optimized subset)"
                )

    # ---- description 透传 ----
    desc = data.get("description", "")
    description_out = {
        "value": desc if isinstance(desc, str) else "",
        "char_count": len(desc) if isinstance(desc, str) else 0,
    }

    # ---- compliance_report 汇总段 ----
    lint_sections = [title_out, hl_out, bul_out, bak_out, attributes_out, variation_base]
    if isinstance(img_out, dict) and "compliant" in img_out:
        lint_sections.append(img_out)
    passed, failed, warnings = _count_checks(lint_sections)
    if isinstance(img_out, dict) and img_out.get("compliant") is False:
        failed += 1
    overall = _overall_compliant(lint_sections)
    critical = _collect_critical(lint_sections)
    actions = _collect_action_items(
        title_out, hl_out, bul_out, bak_out, cdq_out, idx_out, alexa_out, kw_out
    )
    if isinstance(img_out, dict):
        for s in img_out.get("fix_suggestions", []) or []:
            actions.append({"source": "image", "action": str(s)})
    if isinstance(cosmo_out, dict):
        for s in cosmo_out.get("suggestions", []) or []:
            actions.append({"source": "cosmo", "action": str(s)})
    if isinstance(triage_out, dict) and triage_out.get("summary"):
        s = triage_out["summary"]
        parts = []
        if s.get("demote_highlights"):
            parts.append(f"{s['demote_highlights']} 个词组建议下移亮点")
        if s.get("demote_bullets"):
            parts.append(f"{s['demote_bullets']} 个词组建议下移五点")
        if s.get("remove"):
            parts.append(f"{s['remove']} 个词组建议删除（违规）")
        if s.get("prefer_title"):
            parts.append(f"{s['prefer_title']} 个词组倾向保留标题")
        if parts:
            actions.append({"source": "triage", "action": "标题词组分诊：" + "，".join(parts) + "（详见 triage_report）"})

    # 降级维度标记：把"评分因缺字段不可用"作为提示 action
    degraded = []
    if isinstance(cosmo_out, dict) and cosmo_out.get("input_available") is False:
        degraded.append({
            "source": "cosmo",
            "action": f"COSMO 评分降级：{cosmo_out.get('input_unavailable_reason')}",
        })
    if isinstance(alexa_out, dict) and alexa_out.get("input_available") is False:
        degraded.append({
            "source": "alexa",
            "action": f"Alexa 评分降级：{alexa_out.get('input_unavailable_reason')}",
        })
    if isinstance(cdq_out, dict) and cdq_out.get("score_unavailable"):
        for u in cdq_out["score_unavailable"]:
            degraded.append({
                "source": "cdq",
                "action": f"CDQ 子分 {u['field']} 降级：{u['reason']}",
            })
    # 属性期望清单来自内置兜底 → 分数为参考值，提示补实测（user_provided 不提示）
    attr_bases = set()
    try:
        sa = (cdq_out.get("components") or {}).get("structured_attribute") or {}
        if sa.get("basis") == "builtin_fallback":
            attr_bases.add("CDQ")
    except (AttributeError, TypeError):
        pass
    if isinstance(idx_out, dict) and idx_out.get("attribute_basis") == "builtin_fallback":
        attr_bases.add("A9")
    if attr_bases:
        degraded.append({
            "source": "attributes",
            "action": (
                f"{'/'.join(sorted(attr_bases))} 属性评分基于内置大类清单（参考值）——"
                "未经子品类校准，X/10 不作官方口径；"
                "补齐方式：Seller Central 导出属性面板，或以前台类目筛选器实测为准"
            ),
        })
    actions = degraded + actions

    total_score = 0
    if isinstance(cdq_out, dict):
        total_score = cdq_out.get("total", 0)

    grade = ""
    if isinstance(cdq_out, dict):
        grade = cdq_out.get("grade", "")

    overall_status = "COMPLIANT" if overall else "NON-COMPLIANT"
    coverage_pct = int(round(data_coverage["ratio"] * 100))
    summary = (
        f"Overall {overall_status}; "
        f"{passed} passed, {failed} failed, {warnings} warn; "
        f"CDQ {total_score}/100 ({grade}); "
        f"data {coverage_pct}% ({data_coverage['overall']})"
    )

    report_out = {
        "overall_compliant": overall,
        "total_score": total_score,
        "summary": summary,
        "passed_checks": passed,
        "failed_checks": failed,
        "warnings": warnings,
        "critical_issues": critical,
        "action_items": actions,
        "data_coverage": data_coverage,
    }

    return {
        "meta": meta,
        "title": title_out,
        "highlights": hl_out,
        "bullets": bul_out,
        "description": description_out,
        "backend": bak_out,
        "attributes": attributes_out,
        "variation": variation_base,
        "cdq_score": cdq_out,
        "indexability_report": idx_out,
        "alexa_discoverability": alexa_out,
        "keyword_coverage": kw_out,
        "image_report": img_out,
        "cosmo_report": cosmo_out,
        "triage_report": triage_out,
        "compliance_report": report_out,
    }


def load_input():
    """统一 CLI：stdin JSON 优先 / --data '<json>' / --file <path>。"""
    parser = argparse.ArgumentParser(description="汇总所有检查脚本，输出最终体检报告")
    parser.add_argument("--data", help="inline JSON")
    parser.add_argument("--file", help="path to JSON file")
    a = parser.parse_args()
    if a.data:
        return json.loads(a.data)
    if a.file:
        return json.loads(Path(a.file).read_text(encoding="utf-8"))
    # 注：原模板写作 is_tty()，但 Python 标准库实际方法为 isatty()；
    # is_tty() 不存在会导致脚本无法运行，此处修正。
    if not sys.stdin.isatty():
        return json.loads(sys.stdin.read())
    return {}


def main():
    data = load_input()
    result = run(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    overall = result.get("compliance_report", {}).get("overall_compliant", True)
    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
