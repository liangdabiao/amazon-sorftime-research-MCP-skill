#!/usr/bin/env python3
"""Fix keyword report - correct field names"""
import sys, json
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
OUT_DIR = "D:/sellersprite-skills/lavalier-microphones"

with open(f"{OUT_DIR}/keyword_data.json", encoding='utf-8') as f:
    data = json.load(f)

def safe_items(api_result):
    if isinstance(api_result, dict):
        if api_result.get('code') != 'OK':
            return []
        d = api_result.get('data', {})
        if isinstance(d, list): return d
        items = d.get('items', d.get('data', []))
        if isinstance(items, list): return items
        return []
    return []

def fmt_num(n):
    if n is None: return "N/A"
    return f"{float(n):,.0f}"

def fmt_pct(n):
    if n is None: return "N/A"
    n = float(n)
    return f"{n*100:.1f}%"

def fmt_money(n):
    if n is None: return "N/A"
    return f"${float(n):,.2f}"

lines = []
def L(s=""):
    lines.append(s)

L("# Wireless Lavalier Microphones — 关键词研究报告")
L()
L(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 数据源: 卖家精灵 SellerSprite MCP")
L()
L("---")
L()

# ====== Keyword Miner ======
L("## 一、关键词挖掘（Keyword Miner）")
L()
L("关键词挖掘从种子词「lavalier microphone wireless」扩展，返回相关关键词的搜索量、竞争度和供需关系。")
L()
miner_items = sorted(safe_items(data.get('keyword_miner', {})),
                     key=lambda x: float(x.get('searches', 0) or 0), reverse=True)

if miner_items:
    L("| 关键词 | 月搜索量 | 商品数 | 供需比 | 点击集中度 | 标题密度 | 平均售价 | 平均评分 |")
    L("|--------|:-------:|:-----:|:------:|:---------:|:--------:|:-------:|:-------:|")
    for kw in miner_items[:40]:
        keyword = kw.get('keyword', 'N/A')
        sv = fmt_num(kw.get('searches', 0))
        prods = fmt_num(kw.get('products', 0))
        sdr = kw.get('supplyDemandRatio', '')
        sdr_str = f"{float(sdr):.1f}" if sdr else "N/A"
        click_crn = fmt_pct(kw.get('monopolyClickRate', 0))
        td = kw.get('titleDensity', 0)
        td_str = f"{float(td):.1f}%" if td else "N/A"
        price = fmt_money(kw.get('avgPrice', 0)) if kw.get('avgPrice') else "N/A"
        rating = round(kw.get('avgRating', 0), 1) if kw.get('avgRating') else "N/A"
        L(f"| {keyword} | {sv} | {prods} | {sdr_str} | {click_crn} | {td_str} | {price} | {rating} |")
    L()

L("---")
L()

# ====== Keyword Research ======
L("## 二、关键词研究（Keyword Research）")
L()
L("> 注意：Keyword Research 返回类目级别相关关键词，使用父类目数据。")
L()
research_items = safe_items(data.get('keyword_research', {}))
if research_items:
    L("| 关键词 | 月搜索量 | 月销量 | 搜索增长率 | 供需比 | 点击集中度 | 平均售价 | 平均评分 |")
    L("|--------|:-------:|:-----:|:---------:|:------:|:---------:|:-------:|:-------:|")
    for kw in sorted(research_items, key=lambda x: float(x.get('searches', 0) or 0), reverse=True)[:40]:
        keyword = kw.get('keywords', kw.get('keyword', 'N/A'))
        sv = fmt_num(kw.get('searches', 0))
        purchases = fmt_num(kw.get('purchases', 0))
        growth = kw.get('growth', '')
        growth_str = f"{float(growth):.1f}%" if growth != '' else "N/A"
        sdr = kw.get('supplyDemandRatio', '')
        sdr_str = f"{float(sdr):.1f}" if sdr else "N/A"
        click_crn = fmt_pct(kw.get('araClickRate', kw.get('monopolyClickRate', 0)))
        price = fmt_money(kw.get('avgPrice', 0)) if kw.get('avgPrice') else "N/A"
        rating = round(kw.get('avgRating', 0), 1) if kw.get('avgRating') else "N/A"
        L(f"| {keyword} | {sv} | {purchases} | {growth_str} | {sdr_str} | {click_crn} | {price} | {rating} |")
    L()

L("---")
L()

# ====== ABA Trends ======
L("## 三、ABA 趋势分析")
L()
aba_results = data.get('aba_trends', {})
if aba_results:
    for keyword, aba_data in aba_results.items():
        L(f"### 「{keyword}」ABA 趋势")
        L()
        aba_items = safe_items(aba_data)
        if aba_items:
            L("| 时间 | 搜索频率排名 | 点击份额 | 转化份额 |")
            L("|------|:----------:|:--------:|:--------:|")
            for item in aba_items[-12:]:
                time_label = item.get('label', item.get('month', 'N/A'))
                rank = item.get('rank', '')
                cs = fmt_pct(item.get('clickShareRate', item.get('clickShare', 0)))
                cvs = fmt_pct(item.get('conversionShareRate', item.get('conversionShare', 0)))
                L(f"| {time_label} | {rank} | {cs} | {cvs} |")
        else:
            L("*暂无 ABA 趋势数据*")
        L()
else:
    L("*ABA 趋势数据未获取到*")
    L()

L("---")
L()

# ====== Opportunities ======
L("## 四、低竞争高潜力关键词推荐")
L()
opportunities = []
for kw in miner_items:
    sv = float(kw.get('searches', 0) or 0)
    click_crn = float(kw.get('monopolyClickRate', 1) or 1)
    if sv >= 300 and click_crn < 0.5:
        opportunities.append(kw)

if opportunities:
    L("| 关键词 | 月搜索量 | 供需比 | 点击集中度 | 平均售价 | 策略 |")
    L("|--------|:-------:|:------:|:---------:|:-------:|------|")
    for kw in sorted(opportunities, key=lambda x: float(x.get('searches', 0) or 0), reverse=True)[:15]:
        keyword = kw.get('keyword', 'N/A')
        sv = fmt_num(kw.get('searches', 0))
        sdr = kw.get('supplyDemandRatio', '')
        sdr_str = f"{float(sdr):.1f}" if sdr else "N/A"
        cc = fmt_pct(kw.get('monopolyClickRate', 0))
        price = fmt_money(kw.get('avgPrice', 0)) if kw.get('avgPrice') else "N/A"
        L(f"| {keyword} | {sv} | {sdr_str} | {cc} | {price} | 广告投放 + Listing 优化 |")
    L()
else:
    L("*暂无符合条件的低竞争高潜力关键词（搜索量≥300 且 点击集中度<50%）*")
    L()

L("---")
L()
L("## 五、战术策略推荐")
L()
L("1. **ABA 高增长趋势词** — 近 3 月持续增长的关键词重点投放")
L("2. **流量分散关键词** — 点击集中度 < 50%，竞争分散易于切入")
L("3. **标题密度漏洞** — 标题密度 ≤ 5 的长尾词，优化 Listing 标题")
L("4. **高客单长尾词** — 均价 ≥ $80 且有合理搜索量的关键词")
L()
L("---")
L()
L(f"*报告生成: 2026-07-05 | 数据源: 卖家精灵 SellerSprite MCP | 站点: Amazon US*")

report = "\n".join(lines)
with open(f"{OUT_DIR}/keyword_report.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"Keyword report regenerated to {OUT_DIR}/keyword_report.md")
print(f"Total keywords in miner: {len(miner_items)}")
print(f"Opportunities found: {len(opportunities)}")
print(f"Report size: {len(report)} chars")
