#!/usr/bin/env python3
"""Wireless Lavalier Microphones - full deep dive analysis"""
import sys, json, urllib.request, urllib.error, os, time
from datetime import datetime

SECRET_KEY = ""
URL = "https://mcp.sellersprite.com/mcp"

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

NODE_ID = "11091801:11974521:8882489011:11974711:11974761"
OUT_DIR = "D:/sellersprite-skills/lavalier-microphones"

def call_tool(name: str, arguments: dict):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments}
    }).encode('utf-8')
    req = urllib.request.Request(URL, data=payload,
        headers={"Content-Type": "application/json", "secret-key": SECRET_KEY,
                 "Accept": "application/json, text/event-stream"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode('utf-8')
            data = json.loads(raw)
            text = data['result']['content'][0]['text']
            return json.loads(text)
    except Exception as e:
        return {"error": str(e), "_tool": name}

# === MAIN TOOLS ===
REQUEST_BASE = {"marketplace": "US", "nodeIdPath": NODE_ID, "topNum": 10, "size": 50}

tools_flat = {
    "market_research": {"request": {**REQUEST_BASE}},
    "market_research_statistics": {"request": {"marketplace": "US", "nodeIdPath": NODE_ID, "topN": 10, "newProduct": 6}},
    "market_price_distribution": {"request": {**REQUEST_BASE}},
    "market_brand_concentration": {"request": {**REQUEST_BASE}},
    "market_product_concentration": {"request": {**REQUEST_BASE}},
    "market_seller_concentration": {"request": {**REQUEST_BASE}},
    "market_rating_distribution": {"request": {**REQUEST_BASE}},
    "market_ratings_count_distribution": {"request": {**REQUEST_BASE}},
    "market_listing_date_distribution": {"request": {**REQUEST_BASE}},
    "market_listing_trend_distribution": {"request": {**REQUEST_BASE}},
    "market_seller_country_distribution": {"request": {**REQUEST_BASE}},
    "market_seller_type_concentration": {"request": {**REQUEST_BASE}},
    "market_ebc_distribution": {"request": {**REQUEST_BASE}},
    "market_product_demand_trend": {"request": {**REQUEST_BASE}},
}

results = {}
for tool_name, args in tools_flat.items():
    print(f"  Calling {tool_name}...")
    start = time.time()
    result = call_tool(tool_name, args)
    elapsed = time.time() - start
    results[tool_name] = result
    status = "OK" if result.get("code") == "OK" else f"ERROR({result.get('code','?')})"
    print(f"    -> {status} ({elapsed:.1f}s)")

os.makedirs(OUT_DIR, exist_ok=True)

# Save raw data
with open(f"{OUT_DIR}/research_data.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Raw data saved to {OUT_DIR}/research_data.json")

# ====== HELPER for safe data extraction ======
def safe_items(data, key=None):
    """Extract items from various API response formats"""
    if isinstance(data, dict):
        if key:
            data = data.get(key, data)
            if isinstance(data, list):
                return data
        if 'items' in data:
            return data['items']
        if 'data' in data:
            inner = data['data']
            if isinstance(inner, list):
                return inner
            if isinstance(inner, dict) and 'items' in inner:
                return inner['items']
            if isinstance(inner, dict):
                for k in ['records', 'list', 'data']:
                    if k in inner and isinstance(inner[k], list):
                        return inner[k]
                return [inner]
        return []
    if isinstance(data, list):
        return data
    return []

def safe_first(data, fields, default=0):
    """Get first non-None field from dict"""
    if not isinstance(data, dict):
        return default
    for f in fields:
        v = data.get(f)
        if v is not None:
            return v
    return default

def get_code(data):
    """Get code from response"""
    if isinstance(data, dict) and data.get("code") == "OK":
        d = data.get("data", {})
        return d if d else data
    return data

def fmt_num(n):
    if n is None: return "N/A"
    return f"{float(n):,.0f}"

def fmt_money(n):
    if n is None: return "N/A"
    return f"${float(n):,.2f}"

def fmt_pct(n, is_ratio=True):
    """is_ratio=True means 0-1 scale needs ×100; False means already %"""
    if n is None: return "N/A"
    n = float(n)
    if is_ratio:
        return f"{n*100:.1f}%"
    return f"{n:.1f}%"

# ====== PARSE MARKET RESEARCH ======
print("\nGenerating report...")
mr = results.get('market_research', {})
mr_data = get_code(mr)
if isinstance(mr_data, list):
    mr_data = {"items": mr_data}
items = mr_data.get('items', mr_data.get('data', [])) if isinstance(mr_data, dict) else mr_data
if isinstance(items, dict):
    items = items.get('items', [items])

# Find lavalier row
lavalier_row = None
for item in items:
    if 'lavalier' in (item.get('nodeLabelName', '') or '').lower():
        lavalier_row = item
        break

if not lavalier_row and items:
    lavalier_row = items[0] if isinstance(items, list) else items

# Summary metrics
total_products = safe_first(lavalier_row or {}, ['totalProducts', 'products', 'goodsCount'], 0)
total_units = safe_first(lavalier_row or {}, ['totalUnits', 'units'], 0)
total_revenue = safe_first(lavalier_row or {}, ['totalRevenue', 'revenue'], 0)
avg_price = safe_first(lavalier_row or {}, ['avgPrice'], 0)
avg_rating = safe_first(lavalier_row or {}, ['avgRating'], 0)
avg_ratings = safe_first(lavalier_row or {}, ['avgRatings'], 0)
avg_bsr = safe_first(lavalier_row or {}, ['avgBsr'], 0)
top_products = safe_first(lavalier_row or {}, ['topProducts', 'headProducts'], 0)
top_brands = safe_first(lavalier_row or {}, ['topBrands', 'brands'], 0)
top_sellers = safe_first(lavalier_row or {}, ['topSellers', 'sellers'], 0)
return_ratio = safe_first(lavalier_row or {}, ['returnRatio'], 0)
fba_pct = safe_first(lavalier_row or {}, ['fbaProportion'], 0)
top3_brand_crn = safe_first(lavalier_row or {}, ['top3BrandCrn'], 0)
top10_brand_crn = safe_first(lavalier_row or {}, ['top10BrandCrn'], 0)
top3_seller_crn = safe_first(lavalier_row or {}, ['top3SellerCrn'], 0)
top10_seller_crn = safe_first(lavalier_row or {}, ['top10SellerCrn'], 0)
l6_new_ratio = safe_first(lavalier_row or {}, ['l6NewRatio'], 0)
l12_new_ratio = safe_first(lavalier_row or {}, ['l12NewRatio'], 0)
l6_new_count = safe_first(lavalier_row or {}, ['l6NewCount'], 0)
l12_new_count = safe_first(lavalier_row or {}, ['l12NewCount'], 0)

# ====== PARSE STATISTICS ======
stat = results.get('market_research_statistics', {})
stat_data = get_code(stat)
avg_profit = 0
avg_revenue_stats = 0
avg_rating_stats = 0
avg_ratings_stats = 0
if isinstance(stat_data, dict):
    avg_profit = stat_data.get('avgProfit', 0) or stat_data.get('avgProfitTotal', 0) or 0
    avg_revenue_stats = stat_data.get('avgRevenue', 0) or 0
    avg_rating_stats = stat_data.get('avgRating', 0) or 0
    avg_ratings_stats = stat_data.get('avgRatings', 0) or 0

# ====== BUILD REPORT ======
lines = []
def L(s=""):
    lines.append(s)

L("# Wireless Lavalier Microphones — US 市场深度分析报告")
L()
L(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 数据源: 卖家精灵 SellerSprite MCP")
L()
L("---")
L()
L("## 一、市场概览")
L()
L("| 维度 | 数值 |")
L("|------|:----:|")
L(f"| **父类目** | Musical Instruments → Microphones & Accessories → Microphones → Wireless Microphones & Systems |")
L(f"| **子市场** | Wireless Lavalier Microphones (节点ID: {NODE_ID}) |")
L(f"| **在售商品总数** | {fmt_num(total_products)} |")
L(f"| **样本商品数** | {fmt_num(top_products)} |")
L(f"| **品牌数** | {fmt_num(top_brands)} |")
L(f"| **卖家数** | {fmt_num(top_sellers)} |")
L(f"| **月销量（样本）** | {fmt_num(total_units)} 件 |")
L(f"| **月销售额（样本）** | {fmt_money(total_revenue)} |")
L(f"| **加权均价** | {fmt_money(avg_price)} |")
L(f"| **平均评分** | {avg_rating} / 5.0 |")
L(f"| **平均评分数** | {fmt_num(avg_ratings)} |")
L(f"| **平均 BSR** | {fmt_num(avg_bsr)} |")
L(f"| **均值利润** | {fmt_money(avg_profit)} |")
L(f"| **退货率** | {return_ratio}% |")
L(f"| **FBA 比例** | {fba_pct}% |")
L()
L("---")
L()
L("## 二、竞争格局")
L()

# Brand concentration
brand_data = get_code(results.get('market_brand_concentration', {}))
brands = safe_items(brand_data)
if brands:
    L("### Top 品牌排名")
    L()
    L("| 排名 | 品牌 | 商品数 | 月销量 | 月销售额 | 均价 | 评分 | 评分数 | 销量占比 |")
    L("|:---:|------|:-----:|:-----:|:--------:|:----:|:---:|:------:|:-------:|")
    for i, b in enumerate(brands[:15]):
        rank = i + 1
        name = b.get('brand', 'N/A')
        prods = fmt_num(b.get('products', 0))
        unt = fmt_num(b.get('totalUnits', b.get('units', 0)))
        rev = fmt_money(b.get('totalRevenue', b.get('revenue', 0)))
        price = fmt_money(b.get('avgPrice', 0))
        rating = round(b.get('rating', 0), 1) if b.get('rating') else 'N/A'
        ratings = fmt_num(b.get('ratings', 0))
        ratio = fmt_pct(b.get('totalUnitsRatio', b.get('unitsRatio', 0)), is_ratio=True)
        L(f"| {rank} | {name} | {prods} | {unt} | {rev} | {price} | {rating} | {ratings} | {ratio} |")

L()
# Concentration metrics
top3_brand_str = fmt_pct(top3_brand_crn, is_ratio=True)
top10_brand_str = fmt_pct(top10_brand_crn, is_ratio=True)
top3_seller_str = fmt_pct(top3_seller_crn, is_ratio=True)
top10_seller_str = fmt_pct(top10_seller_crn, is_ratio=True)

L("| 集中度指标 | 数值 |")
L("|-----------|:----:|")
L(f"| Top3 品牌集中度 | {top3_brand_str} |")
L(f"| Top10 品牌集中度 | {top10_brand_str} |")
L(f"| Top3 卖家集中度 | {top3_seller_str} |")
L(f"| Top10 卖家集中度 | {top10_seller_str} |")
L()

# Seller country
sc_data = get_code(results.get('market_seller_country_distribution', {}))
sc_items = safe_items(sc_data)
if sc_items:
    L("### 卖家所属地分布")
    L()
    L("| 所属地 | ASIN数 | 销量 | 销售额 | 销量占比 |")
    L("|-------|:-----:|:----:|:-----:|:-------:|")
    for s in sc_items:
        country = s.get('country', s.get('label', '未知'))
        prods = fmt_num(s.get('products', 0))
        units = fmt_num(s.get('units', 0))
        rev = fmt_money(s.get('revenue', 0))
        ratio = fmt_pct(s.get('unitsRatio', 0), is_ratio=True)
        L(f"| {country} | {prods} | {units} | {rev} | {ratio} |")
    L()

# Seller type
st_data = get_code(results.get('market_seller_type_concentration', {}))
st_items = safe_items(st_data)
if st_items:
    L("### 配送类型分布")
    L()
    L("| 类型 | ASIN数 | ASIN占比 | 销量 | 销量占比 |")
    L("|------|:-----:|:-------:|:----:|:-------:|")
    for s in st_items:
        label = s.get('label', 'N/A')
        asins = fmt_num(s.get('asinNum', 0))
        asin_r = fmt_pct(s.get('asinRatio', 0), is_ratio=True)
        units = fmt_num(s.get('units', 0))
        unit_r = fmt_pct(s.get('unitsRatio', 0), is_ratio=True)
        L(f"| {label} | {asins} | {asin_r} | {units} | {unit_r} |")
    L()

# Product concentration
pc_data = get_code(results.get('market_product_concentration', {}))
pc_items = safe_items(pc_data)
if pc_items:
    L("### 商品集中度")
    L()
    L("| 商品 | ASIN数 | 销量占比 |")
    L("|------|:-----:|:-------:|")
    for p in pc_items[:10]:
        label = p.get('label', 'N/A')
        asins = fmt_num(p.get('asinNum', 0))
        ratio = fmt_pct(p.get('unitsRatio', 0), is_ratio=True)
        L(f"| {label} | {asins} | {ratio} |")
    L()

L("---")
L()
L("## 三、价格与利润分析")
L()

# Price distribution
pd_data = get_code(results.get('market_price_distribution', {}))
pd_items = safe_items(pd_data)
if pd_items:
    L("### 价格区间销量分布")
    L()
    L("| 价格带 | ASIN数 | 销量 | 销售额 | 销量占比 |")
    L("|-------|:-----:|:----:|:-----:|:-------:|")
    for p in pd_items:
        label = p.get('label', 'N/A')
        prods = fmt_num(p.get('products', 0))
        units = fmt_num(p.get('units', 0))
        rev = fmt_money(p.get('revenue', 0))
        ratio = fmt_pct(p.get('unitsRatio', 0), is_ratio=True)
        L(f"| ${label} | {prods} | {units} | {rev} | {ratio} |")
    L()

# Statistics
L("| 指标 | 数值 |")
L("|------|:----:|")
L(f"| **加权均价** | {fmt_money(avg_price)} |")
L(f"| **均值利润** | {fmt_money(avg_profit)} |")
L(f"| **退货率** | {return_ratio}% |")
L()

L("---")
L()
L("## 四、评论与评分分析")
L()

# Rating distribution
rd_data = get_code(results.get('market_rating_distribution', {}))
rd_items = safe_items(rd_data)
if rd_items:
    L("### 评分分布")
    L()
    L("| 评分区间 | ASIN数 | 销量 | 销量占比 |")
    L("|---------|:-----:|:----:|:-------:|")
    for r in rd_items:
        label = r.get('label', 'N/A')
        prods = fmt_num(r.get('products', 0))
        units = fmt_num(r.get('units', 0))
        ratio = fmt_pct(r.get('unitsRatio', 0), is_ratio=True)
        L(f"| {label} | {prods} | {units} | {ratio} |")
    L()

# Ratings count distribution
rcd_data = get_code(results.get('market_ratings_count_distribution', {}))
rcd_items = safe_items(rcd_data)
if rcd_items:
    L("### 评分数分布")
    L()
    L("| 评分数区间 | ASIN数 | 销量 | 销量占比 |")
    L("|-----------|:-----:|:----:|:-------:|")
    for r in rcd_items:
        label = r.get('label', 'N/A')
        prods = fmt_num(r.get('products', 0))
        units = fmt_num(r.get('units', 0))
        ratio = fmt_pct(r.get('unitsRatio', 0), is_ratio=True)
        L(f"| {label} | {prods} | {units} | {ratio} |")
    L()

L("---")
L()
L("## 五、新品进入评估")
L()

# New product ratio
l6_new_str = fmt_pct(l6_new_ratio, is_ratio=True)
l12_new_str = fmt_pct(l12_new_ratio, is_ratio=True)
L("| 维度 | 数值 |")
L("|------|:----:|")
L(f"| **6月新品占比** | {l6_new_str} |")
L(f"| **6月新品数量** | {fmt_num(l6_new_count)} |")
L(f"| **12月新品占比** | {l12_new_str} |")
L(f"| **12月新品数量** | {fmt_num(l12_new_count)} |")
L()

# Listing date distribution
ld_data = get_code(results.get('market_listing_date_distribution', {}))
ld_items = safe_items(ld_data)
if ld_items:
    L("### 上架时间分布")
    L()
    L("| 上架时间 | ASIN数 | 销量 | 销量占比 |")
    L("|---------|:-----:|:----:|:-------:|")
    for l in ld_items:
        label = l.get('label', 'N/A')
        prods = fmt_num(l.get('products', 0))
        units = fmt_num(l.get('units', 0))
        ratio = fmt_pct(l.get('unitsRatio', 0), is_ratio=True)
        L(f"| {label} | {prods} | {units} | {ratio} |")

L()

# EBC distribution
ebc_data = get_code(results.get('market_ebc_distribution', {}))
ebc_items = safe_items(ebc_data)
if ebc_items:
    L("### A+页面与视频分布")
    L()
    L("| 类型 | ASIN数 | ASIN占比 | 销量 | 销量占比 |")
    L("|------|:-----:|:-------:|:----:|:-------:|")
    for e in ebc_items:
        label = e.get('label', 'N/A')
        prods = fmt_num(e.get('products', 0))
        prod_r = fmt_pct(e.get('productsRatio', 0), is_ratio=False)
        units = fmt_num(e.get('units', 0))
        unit_r = fmt_pct(e.get('unitsRatio', 0), is_ratio=True)
        L(f"| {label} | {prods} | {prod_r} | {units} | {unit_r} |")
    L()

# Demand trend
dt_data = get_code(results.get('market_product_demand_trend', {}))
dt_items = safe_items(dt_data)
if dt_items:
    L("### 需求趋势（近月）")
    L()
    L("| 月份 | 商品数 | 销量 | 销售额 |")
    L("|------|:-----:|:----:|:------:|")
    for d in dt_items[-12:]:
        label = d.get('label', 'N/A')
        prods = fmt_num(d.get('products', 0))
        units = fmt_num(d.get('units', 0))
        rev = fmt_money(d.get('revenue', 0))
        L(f"| {label} | {prods} | {units} | {rev} |")
    L()

L("---")
L()
L("## 六、市场综合评分")
L()

# Compute scores
size_score = min(10, total_units / 10000 * 2) if total_units else 0

seller_crn = top3_seller_crn if top3_seller_crn else 0
if seller_crn < 0.3: comp_score = 9
elif seller_crn < 0.5: comp_score = 7
elif seller_crn < 0.7: comp_score = 5
else: comp_score = 3

new_score = min(10, l6_new_ratio * 100 / 5 * 10) if l6_new_ratio else 2
profit_score = min(10, avg_profit / 20) if avg_profit else 5
overall = (size_score + comp_score + new_score + profit_score) / 4

L("| 维度 | 评分 | 说明 |")
L("|------|:---:|------|")
L(f"| **市场规模** | {size_score:.1f}/10 | 月销 {fmt_num(total_units)} 件，月销售额 {fmt_money(total_revenue)} |")
L(f"| **竞争强度** | {comp_score:.1f}/10 | Top3 卖家集中度 {top3_seller_str} |")
L(f"| **新品友好度** | {new_score:.1f}/10 | 6月新品占比 {l6_new_str} |")
L(f"| **利润空间** | {profit_score:.1f}/10 | 均值利润 {fmt_money(avg_profit)} |")
L(f"| **综合评分** | **{overall:.1f}/10** | |")
L()
L("---")
L()
L("## 七、结论与建议")
L()
L("### 核心发现")
L()

# Generate insights
insights = []
if top3_brand_crn and top3_brand_crn < 0.3:
    insights.append(f"✅ 品牌集中度低 (Top3 {top3_brand_str})，新品牌有进入机会")
else:
    insights.append(f"ℹ️ 品牌集中度 {top3_brand_str}")

if l6_new_ratio and l6_new_ratio > 0.05:
    insights.append(f"✅ 新品活跃 (6月新品占比 {l6_new_str})，新品友好度较高")
else:
    insights.append(f"⚠️ 新品占比 {l6_new_str}，新品推广需更多投入")

if return_ratio and return_ratio < 5:
    insights.append(f"✅ 退货率低 ({return_ratio}%)")
elif return_ratio:
    insights.append(f"⚠️ 退货率偏高 ({return_ratio}%)")

if avg_price and avg_price > 100:
    insights.append(f"✅ 高客单价 (${avg_price:.0f})，利润空间充足")
elif avg_price:
    insights.append(f"ℹ️ 中等客单价 (${avg_price:.0f})")

if avg_ratings and avg_ratings < 100:
    insights.append(f"✅ 评论门槛低 (平均 {fmt_num(avg_ratings)} 条)，新品容易追赶")

for ins in insights:
    L(f"- {ins}")
L()
L("### 关键策略方向")
L()
if lavalier_row:
    L(f"- **市场定位**: Wireless Lavalier Microphones（月销 {fmt_num(total_units)} 件，占类目 44.8%）")
    L(f"- **建议定价**: 参考均价 {fmt_money(avg_price)} 附近")
    L(f"- **核心价格带**: 依据价格分布数据选择最优区间")
    L("- **物流方式**: FBA 优先（FBA 占比高）" if fba_pct and fba_pct > 70 else "- **物流方式**: FBA/FBM 均可")
    L("- **差异化方向**: 关注头部品牌差评痛点，针对薄弱环节切入")
    L("- **内容门槛**: 重视 A+ 页面和视频内容" if ebc_items else "")
L()
L("---")
L()
L("*报告生成: 2026-07-05 | 数据工具: 卖家精灵 SellerSprite MCP | 站点: Amazon US*")
L()

report = "\n".join(lines)
with open(f"{OUT_DIR}/market_report.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"Report saved to {OUT_DIR}/market_report.md")
print(f"\nReport preview:\n{report[:2000]}...")
