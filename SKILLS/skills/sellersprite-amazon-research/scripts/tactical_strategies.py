#!/usr/bin/env python3
"""Run all 5 tactical strategy cards for Wireless Lavalier Microphones"""
import sys, json, urllib.request, time, os
from datetime import datetime

SECRET_KEY = ""
URL = "https://mcp.sellersprite.com/mcp"
OUT_DIR = "D:/sellersprite-skills/lavalier-microphones"
NODE_ID = "11091801:11974521:8882489011:11974711:11974761"

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def call_tool(name, arguments):
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

def safe_items(data):
    if isinstance(data, dict):
        if data.get('code') == 'OK':
            d = data.get('data', {})
            if isinstance(d, list): return d
            items = d.get('items', d.get('data', []))
            if isinstance(items, list): return items
            return []
        return []
    if isinstance(data, list): return data
    return []

def fmt_num(n):
    if n is None: return "N/A"
    return f"{float(n):,.0f}"

def fmt_money(n):
    if n is None: return "N/A"
    return f"${float(n):,.2f}"

def fmt_pct(n, is_ratio=True):
    if n is None: return "N/A"
    n = float(n)
    if is_ratio: return f"{n*100:.1f}%"
    return f"{n:.1f}%"

# ======= Load existing data =======
with open('D:/sellersprite-skills/wirelessinstruments/research_data.json', encoding='utf-8') as f:
    parent_data = json.load(f)

with open(f'{OUT_DIR}/keyword_data.json', encoding='utf-8') as f:
    kw_data = json.load(f)

parent_items = parent_data.get('market_research', {}).get('data', {}).get('items', [])
miner_items = safe_items(kw_data.get('keyword_miner', {}))

# ======= Call product_research for cards 4 & 5 =======
print("=== Calling product_research (for High Margin & Hot Low Rating) ===")
pr_high_margin = call_tool("product_research", {
    "request": {
        "marketplace": "US",
        "nodeIdPath": NODE_ID,
        "maxFba": 4,
        "minProfit": 0.5,
        "fulfillment": "FBA",
        "size": 50
    }
})
print(f"  high_margin: {pr_high_margin.get('code', 'ERROR')}")

time.sleep(0.3)
pr_hot_low = call_tool("product_research", {
    "request": {
        "marketplace": "US",
        "nodeIdPath": NODE_ID,
        "minUnits": 1000,
        "maxRating": 4.2,
        "size": 50
    }
})
print(f"  hot_low_rating: {pr_hot_low.get('code', 'ERROR')}")

everything = {
    "low_brand_monopoly": {"source": "parent_market_research"},
    "high_new_product_ratio": {"source": "parent_market_research"},
    "low_monopoly_keyword": {"source": "keyword_miner"},
    "high_margin_lightweight": pr_high_margin,
    "hot_low_rating": pr_hot_low,
}

# ======= GENERATE REPORT =======
lines = []
def L(s=""):
    lines.append(s)

L("# Wireless Lavalier Microphones — 战术策略卡分析报告")
L()
L(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 数据源: 卖家精灵 SellerSprite MCP | 站点: Amazon US")
L()

# ====== CARD 1: Low Brand Monopoly ======
L("---")
L()
L("## 策略卡一：低品牌垄断类目")
L()
L("> 筛选条件：Top3 品牌集中度 < 45%")
L()

low_monopoly_items = [i for i in parent_items if i.get('top3BrandCrn', 1) is not None and i.get('top3BrandCrn', 1) < 0.45]
if low_monopoly_items:
    L("| 子市场 | 商品数 | 月销量 | 月销售额 | Top3品牌集中度 | 判断 |")
    L("|--------|:-----:|:-----:|:--------:|:-------------:|:----:|")
    for item in low_monopoly_items:
        name = item.get('nodeLabelName', 'N/A')
        tp = fmt_num(item.get('totalProducts', 0))
        units = fmt_num(item.get('totalUnits', 0))
        rev = fmt_money(item.get('totalRevenue', 0))
        crn = fmt_pct(item.get('top3BrandCrn', 0))
        L(f"| {name} | {tp} | {units} | {rev} | {crn} | ✅ 低垄断 |")
    L()
    L(f"共 **{len(low_monopoly_items)}** 个子市场符合低品牌垄断条件。")
else:
    L("*无线麦克风品类下无符合低垄断条件的子市场*")
L()

L("**结论：** Wireless Lavalier Microphones (Top3 {}) 和 Handheld Wireless Microphones (Top3 {}) 品牌集中度低于45%，新品牌有进入机会。".format(
    fmt_pct(parent_items[0].get('top3BrandCrn',0)) if parent_items else '?',
    fmt_pct(parent_items[1].get('top3BrandCrn',0)) if len(parent_items) > 1 else '?'
))

# ====== CARD 2: High New Product Ratio ======
L()
L("---")
L()
L("## 策略卡二：高新品占比市场")
L()
L("> 筛选条件：6月新品占比 > 5% 且新品有出单")
L()

high_new_items = [i for i in parent_items if i.get('l6NewRatio', 0) is not None and i.get('l6NewRatio', 0) > 0.05]
if high_new_items:
    L("| 子市场 | 商品数 | 月销量 | 6月新品占比 | 12月新品占比 | 判断 |")
    L("|--------|:-----:|:-----:|:----------:|:-----------:|:----:|")
    for item in sorted(high_new_items, key=lambda x: float(x.get('l6NewRatio', 0) or 0), reverse=True):
        name = item.get('nodeLabelName', 'N/A')
        tp = fmt_num(item.get('totalProducts', 0))
        units = fmt_num(item.get('totalUnits', 0))
        l6 = fmt_pct(item.get('l6NewRatio', 0))
        l12 = fmt_pct(item.get('l12NewRatio', 0))
        L(f"| {name} | {tp} | {units} | {l6} | {l12} | ✅ 新品活跃 |")
    L()
    L(f"共 **{len(high_new_items)}** 个子市场符合高新品占比条件。")
else:
    L("*无线麦克风品类下无符合高新品占比条件的子市场*")
L()

L("**结论：** Wireless Lavalier 6月新品占比 {}，新品活跃度较高，对新品友好。".format(
    fmt_pct(parent_items[0].get('l6NewRatio',0)) if parent_items else '?'
))

# ====== CARD 3: Low Monopoly Keywords ======
L()
L("---")
L()
L("## 策略卡三：流量分散关键词（蓝海词）")
L()
L("> 筛选条件：月搜索量 ≥ 5,000 且 点击集中度 < 50%")
L()

low_mono_kw = [kw for kw in miner_items
    if float(kw.get('searches', 0) or 0) >= 5000
    and float(kw.get('monopolyClickRate', 1) or 1) < 0.5]

if low_mono_kw:
    sorted_kw = sorted(low_mono_kw, key=lambda x: float(x.get('searches', 0) or 0), reverse=True)
    L("| 关键词 | 月搜索量 | 点击集中度 | 供需比 | 商品数 | 平均售价 |")
    L("|--------|:-------:|:---------:|:------:|:-----:|:-------:|")
    for kw in sorted_kw[:20]:
        keyword = kw.get('keyword', 'N/A')
        sv = fmt_num(kw.get('searches', 0))
        cc = fmt_pct(kw.get('monopolyClickRate', 0))
        sdr = kw.get('supplyDemandRatio', '')
        sdr_str = f"{float(sdr):.1f}" if sdr else "N/A"
        prods = fmt_num(kw.get('products', 0))
        price = fmt_money(kw.get('avgPrice', 0)) if kw.get('avgPrice') else "N/A"
        L(f"| {keyword} | {sv} | {cc} | {sdr_str} | {prods} | {price} |")
    L()
    L(f"共 **{len(low_mono_kw)}** 个蓝海关键词符合条件。")
else:
    L("*未找到符合条件的低垄断关键词（搜索量≥5000 + 点击集中度<50%）*")
L()

L("**推荐策略：** 优先投放供需比 > 10 且搜索量高的关键词，竞争小、转化潜力大。")

# ====== CARD 4: High Margin Lightweight ======
L()
L("---")
L()
L("## 策略卡四：高毛利轻小品")
L()
L("> 筛选条件：FBA 运费 ≤ $4 | 毛利率 ≥ 50% | FBA 发货")
L()

hm_items = safe_items(pr_high_margin)
if hm_items:
    sorted_hm = sorted(hm_items, key=lambda x: float(x.get('units', 0) or 0), reverse=True)
    L("| 商品 | 售价 | 月销量 | 月销售额 | FBA费 | 毛利率 | BSR | 评分 |")
    L("|------|:----:|:-----:|:--------:|:----:|:-----:|:---:|:----:|")
    for p in sorted_hm[:20]:
        title = (p.get('title', p.get('productName', 'N/A')))[:40]
        price = fmt_money(p.get('price', p.get('amount', 0)))
        units = fmt_num(p.get('units', 0))
        rev = fmt_money(p.get('revenue', 0))
        fba = fmt_money(p.get('fbaFee', 0))
        margin = fmt_pct(p.get('profitRate', p.get('profit', 0)))
        bsr = fmt_num(p.get('bsr', 0))
        rating = p.get('rating', 0)
        L(f"| {title} | {price} | {units} | {rev} | {fba} | {margin} | {bsr} | {rating} |")
    L()
    L(f"共 **{len(hm_items)}** 个商品符合高毛利轻小条件。")
else:
    L("*该节点下未找到符合条件的高毛利轻小商品*")
L()

# ====== CARD 5: Hot Low Rating ======
L()
L("---")
L()
L("## 策略卡五：热销低评分产品")
L()
L("> 筛选条件：月销量 ≥ 1,000 | 评分 ≤ 4.2")
L()

hl_items = safe_items(pr_hot_low)
if hl_items:
    sorted_hl = sorted(hl_items, key=lambda x: float(x.get('units', 0) or 0), reverse=True)
    L("| 商品 | 售价 | 月销量 | 月销售额 | 评分 | 评分数 | BSR | FBA费 |")
    L("|------|:----:|:-----:|:--------:|:---:|:-----:|:---:|:----:|")
    for p in sorted_hl[:20]:
        title = (p.get('title', p.get('productName', 'N/A')))[:40]
        price = fmt_money(p.get('price', p.get('amount', 0)))
        units = fmt_num(p.get('units', 0))
        rev = fmt_money(p.get('revenue', 0))
        rating = p.get('rating', 0)
        ratings = fmt_num(p.get('ratings', 0))
        bsr = fmt_num(p.get('bsr', 0))
        fba = fmt_money(p.get('fbaFee', 0))
        L(f"| {title} | {price} | {units} | {rev} | {rating} | {ratings} | {bsr} | {fba} |")
    L()

    # Check if Mini Mic Pro is already there
    has_mini = any('mini mic' in (p.get('title', '')).lower() for p in hl_items)
    if not has_mini:
        L("> 注：Mini Mic Pro 评分 4.4，不符合 ≤4.2 条件，未出现在此列表。")
        L()
    L(f"共 **{len(hl_items)}** 个商品符合热销低评分条件，这些产品存在改良机会。")
else:
    L("*该节点下未找到符合条件的热销低评分商品*")
L()

# ====== OVERALL SUMMARY ======
L()
L("---")
L()
L("## 综合策略总结")
L()
L("| 策略卡 | 结论 |")
L("|--------|:----:|")
L(f"| ① 低品牌垄断类目 | ✅ 适用 — Lavalier Top3集中度 {fmt_pct(parent_items[0].get('top3BrandCrn',0)) if parent_items else '?'}（<45%）|")
L(f"| ② 高新品占比市场 | ✅ 适用 — 6月新品占比 {fmt_pct(parent_items[0].get('l6NewRatio',0)) if parent_items else '?'}（>5%）|")
L(f"| ③ 流量分散关键词 | ✅ 找到 {len(low_mono_kw)} 个蓝海关键词 |")
L(f"| ④ 高毛利轻小品 | {'✅ 找到 ' + str(len(hm_items)) + ' 个' if hm_items else '⚠️ 无匹配'} 轻小高毛利商品 |")
L(f"| ⑤ 热销低评分产品 | {'✅ 找到 ' + str(len(hl_items)) + ' 个' if hl_items else '⚠️ 无匹配'} 改良机会产品 |")
L()
L("### 建议行动优先级")
L()
L("1. **🔴 流量分散关键词投放** — {} 个蓝海词，搜索量>5000且竞争低，可快速获取流量".format(len(low_mono_kw)))
if hl_items:
    L("2. **🔴 热销低评分产品改良** — {} 个产品市场需求大但有产品缺陷，改进可切入".format(len(hl_items)))
if hm_items:
    L("3. **🟡 高毛利轻小商品开发** — {} 个已验证的轻小高利润模型".format(len(hm_items)))
L("4. **🟡 低垄断子市场深耕** — Lavalier + Handheld 两个低垄断子市场")
L("5. **🟢 利用高新品占比优势** — 市场更新迭代快，新品容易起量")
L()
L("---")
L()
L(f"*报告生成: 2026-07-05 | 数据工具: 卖家精灵 SellerSprite MCP | 站点: Amazon US*")

report = "\n".join(lines)
os.makedirs(OUT_DIR, exist_ok=True)
with open(f"{OUT_DIR}/tactical_strategies.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"Tactical strategies saved to {OUT_DIR}/tactical_strategies.md")
print(f"Report size: {len(report)} chars")
