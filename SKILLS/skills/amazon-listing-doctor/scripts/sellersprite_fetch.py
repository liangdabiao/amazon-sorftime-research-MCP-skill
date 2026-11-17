#!/usr/bin/env python3
"""sellersprite_fetch.py —— 用 SellerSprite /v1/asin/{marketplace}/{asin} 接口
拉取 Amazon ASIN 详情，自动映射到 listing JSON 的前台字段。

只取前台数据（title/brand/features/bullets/images/description/has_a_plus/market/category）。
后台字段（item_highlights / backend_search_terms / attributes / 父子体属性）
必须从 Seller Central 导出，本脚本不取。

输入方式：
  CLI:  --marketplace US --asin B0DRVKZHK9 [--secret-key KEY]
  函数: sellersprite_fetch.fetch(marketplace, asin, secret_key=None) -> dict

依赖：
  - 标准库（urllib, json）零依赖；走 HTTPS GET，自带 secret-key 请求头
  - 如有 requests 库自动用，更省心

输出：
  - 完整 listing JSON（前台字段已填，后台字段为空供用户补）
  - meta.source: 标注数据来源 = "sellersprite"（前台字段）
  - meta.fetched_at: UTC 时间戳
  - meta.unfetched_backend: 提示后台字段来源 = "Seller Central 后台导出"

退码：0=成功 / 1=调用失败（无 secret-key 或 HTTP 非 200）
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

API_BASE = "https://api.sellersprite.com"


# ---------------------------------------------------------------------------
# 网络请求（标准库实现，零依赖）
# ---------------------------------------------------------------------------
def _http_get_json(url, headers):
    """标准库 GET + JSON 解析；如有 requests 自动切换。"""
    try:
        import requests  # type: ignore
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except ImportError:
        pass

    from urllib.request import Request, urlopen
    req = Request(url, headers=headers, method="GET")
    with urlopen(req, timeout=15) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8"))


# ---------------------------------------------------------------------------
# 字段映射（API 返回 → listing JSON）
# ---------------------------------------------------------------------------
_MARKET_TO_LANG = {
    "US": "en", "UK": "en", "GB": "en",
    "DE": "de", "FR": "fr", "IT": "it", "ES": "es",
    "JP": "ja", "CA": "en", "MX": "es",
    "IN": "en", "AU": "en",
}


def _map_bullets(features):
    """features (List[str]) -> [{header, body}]。
    SellerSprite 给出 bullet 整段；header 取前 ~12 字符或第一个名词短语。
    简化策略：bullet 整段作 body，header 用 bullet 前 8 字符 + "..."
    """
    out = []
    for feat in features or []:
        if not isinstance(feat, str):
            continue
        s = feat.strip()
        if not s:
            continue
        # header = 前 8 字符（去尾空格 + 加省略号）。最简形式。
        head = (s[:8].rstrip() + "…") if len(s) > 8 else s
        out.append({"header": head, "body": s})
    return out


def _map_images(asin_data, marketplace):
    """imageUrl / zoomImageUrl -> [{url, width?, height?, ...}]。
    只填 url，其他元数据留给 Claude 视觉分析后回填。
    """
    images = []
    zoom = asin_data.get("zoomImageUrl")
    if zoom:
        images.append({"url": zoom, "source": "sellersprite"})
    elif asin_data.get("imageUrl"):
        images.append({"url": asin_data["imageUrl"], "source": "sellersprite"})
    # 注：SellerSprite /v1/asin 当前只返回主图，单张图需用 images_count 兜底
    if not images:
        # 兜底占位（明确告知调用方"图缺失需要补")
        return []
    return images


def _map_description(asin_data):
    """overviews (String, 可能是 JSON 字符串) -> description 字符串。
    """
    ov = asin_data.get("overviews")
    if not ov:
        return ""
    if isinstance(ov, str):
        # 可能是 JSON 字符串，尝试解析为 dict 序列化为可读文本
        try:
            obj = json.loads(ov)
            if isinstance(obj, dict):
                return "\n".join(f"{k}: {v}" for k, v in obj.items())
            if isinstance(obj, list):
                return "\n".join(str(x) for x in obj)
        except (json.JSONDecodeError, ValueError):
            pass
        return ov
    if isinstance(ov, dict):
        return "\n".join(f"{k}: {v}" for k, v in ov.items())
    return str(ov)


def _map_attributes(asin_data):
    """从 API 返回提取 structured attributes → attributes_filled 列表。

    SellerSprite /v1/asin 可能不直接返回 attributes dict；
    sorftime MCP 返回 JSON 字符串格式的 attributes。
    本函数尝试多种格式，提取属性名列表。
    """
    attrs = asin_data.get("attributes")
    if not attrs:
        # 备选：部分 API 用 specifications / techSpecs 等键名
        for alt_key in ("specifications", "techSpecs", "product_details"):
            if asin_data.get(alt_key):
                attrs = asin_data[alt_key]
                break

    if not attrs:
        return []

    # 如果是 JSON 字符串，先解析
    if isinstance(attrs, str):
        try:
            attrs = json.loads(attrs)
        except (json.JSONDecodeError, ValueError):
            return []

    # 如果是 dict → 取所有 key 为已填属性名
    if isinstance(attrs, dict):
        return list(attrs.keys())

    # 如果是 list → 取元素本身
    if isinstance(attrs, list):
        return [str(a) for a in attrs if a]

    return []


def _category_from_path(node_label_path):
    """从类目路径取最后一段（叶类目）。"""
    if not node_label_path or not isinstance(node_label_path, str):
        return ""
    parts = [p.strip() for p in node_label_path.split(">") if p.strip()]
    return parts[-1] if parts else ""


def fetch(marketplace, asin, secret_key=None):
    """拉取 ASIN 详情，映射为 listing JSON（仅前台字段）。

    Args:
        marketplace: 'US' / 'DE' / 'FR' / ...
        asin: B0 开头的 10 位 ASIN
        secret_key: SellerSprite API secret-key；缺则读 env SELLERSPRITE_SECRET_KEY

    Returns:
        dict (listing JSON) 或 {"error": ..., "asin": ..., "marketplace": ...}
    """
    marketplace = (marketplace or "").upper().strip()
    asin = (asin or "").upper().strip()
    secret_key = secret_key or os.environ.get("SELLERSPRITE_SECRET_KEY")

    if not re.match(r"^[A-Z0-9]{10}$", asin):
        return {
            "error": "invalid ASIN format (expect 10 alnum chars, e.g. B0DRVKZHK9)",
            "asin": asin,
            "marketplace": marketplace,
        }
    if not secret_key:
        return {
            "error": "missing secret-key; export SELLERSPRITE_SECRET_KEY or pass --secret-key",
            "asin": asin,
            "marketplace": marketplace,
        }

    url = f"{API_BASE}/v1/asin/{quote(marketplace, safe='')}/{quote(asin, safe='')}"
    headers = {
        "secret-key": secret_key,
        "Content-Type": "application/json;charset=utf-8",
        "x-request-id": f"doctor-{asin}-{int(datetime.now(timezone.utc).timestamp())}",
    }

    try:
        payload = _http_get_json(url, headers)
    except Exception as e:
        return {
            "error": f"http error: {e}",
            "asin": asin,
            "marketplace": marketplace,
        }

    if not isinstance(payload, dict) or payload.get("code") != "OK":
        return {
            "error": f"api error: {payload.get('message') if isinstance(payload, dict) else 'non-JSON response'}",
            "code": payload.get("code") if isinstance(payload, dict) else None,
            "asin": asin,
            "marketplace": marketplace,
        }

    data = payload.get("data") or {}
    if not isinstance(data, dict):
        return {"error": "empty data block", "asin": asin, "marketplace": marketplace}

    bullets = _map_bullets(data.get("features") or [])
    images = _map_images(data, marketplace)
    description = _map_description(data)
    category = _category_from_path(data.get("nodeLabelPath") or "")
    attributes_filled = _map_attributes(data)

    # has_a_plus：badge.ebc == "Y" 视为有 A+ 内容
    badge = data.get("badge") or {}
    has_a_plus = str(badge.get("ebc", "")).upper() == "Y"
    has_video = str(badge.get("video", "")).upper() == "Y"

    language = _MARKET_TO_LANG.get(marketplace, "")

    listing = {
        "market": marketplace,
        "language": language,
        "category": category,
        "brand": data.get("brand") or "",
        "title": data.get("title") or "",
        "bullets": bullets,
        "description": description,
        "images": images,
        "has_a_plus": has_a_plus,
        # attributes → 前台字段（详情页 Product Details 表格可见）
        "attributes_filled": attributes_filled,
        "attributes_top10_expected": [],
        # 后台字段明确留空 + 标注需用户补
        "item_highlights": "",
        "backend_search_terms": "",
        "band_a_critical_6": [],
        "is_parent": bool(data.get("parent") and data["parent"] != asin),
        "is_variation": bool(data.get("variations")),
        # 元信息（标注数据来源，便于诊断）
        "meta": {
            "source": "sellersprite",
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sellersprite": {
                "asin": asin,
                "marketplace": marketplace,
                "price": data.get("price"),
                "prime_price": data.get("primePrice"),
                "rating": data.get("rating"),
                "ratings_count": data.get("ratings"),
                "reviews_count": data.get("reviews"),
                "bsr_rank": data.get("bsrRank"),
                "bsr_label": data.get("bsrLabel"),
                "lqs": data.get("lqs"),
                "parent_asin": data.get("parent"),
                "variation_count": data.get("variations"),
                "has_video": has_video,
                "available_date": data.get("availableDate"),
            },
            "unfetched_backend": [
                "item_highlights",
                "backend_search_terms",
                "attributes_filled / attributes_top10_expected",
                "band_a_critical_6",
                "is_parent / is_variation（粗略推断，建议从 Seller Central 校验）",
                "images 元数据 (width/height/is_white_background/is_square，建议 Claude 视觉分析)",
            ],
            "unfetched_backend_source": "Seller Central 后台导出",
        },
    }
    return listing


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="SellerSprite ASIN 详情 → listing JSON（仅前台字段）")
    p.add_argument("--marketplace", required=True, help="如 US / DE / FR / IT / ES / JP")
    p.add_argument("--asin", required=True, help="10 位 ASIN，如 B0DRVKZHK9")
    p.add_argument("--secret-key", help="覆盖 env SELLERSPRITE_SECRET_KEY")
    args = p.parse_args()

    result = fetch(args.marketplace, args.asin, args.secret_key)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if isinstance(result, dict) and result.get("error"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()