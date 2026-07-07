#!/usr/bin/env python3
"""Keyword research for Wireless Lavalier Microphones category"""
import sys, json, urllib.request, time, os
from datetime import datetime

SECRET_KEY = ""
URL = "https://mcp.sellersprite.com/mcp"
OUT_DIR = "D:/sellersprite-skills/lavalier-microphones"

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

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

def safe_items(data):
    if isinstance(data, dict):
        if data.get('code') == 'OK':
            d = data.get('data', {})
            if isinstance(d, list): return d
            items = d.get('items', d.get('data', []))
            if isinstance(items, list): return items
        inner = data.get('data', data)
        if isinstance(inner, list): return inner
        if isinstance(inner, dict):
            return inner.get('items', inner.get('data', []))
        return []
    if isinstance(data, list): return data
    return []

# Phase 1: keyword_miner
print("=== Phase 1: Keyword Mining ===")
kw_miner = call_tool("keyword_miner", {
    "request": {"marketplace": "US", "keyword": "lavalier microphone wireless", "size": 100}
})
print(f"  Status: {kw_miner.get('code', 'ERROR')}")

# Phase 2: keyword_research
print("\n=== Phase 2: Keyword Research ===")
kw_research = call_tool("keyword_research", {
    "request": {"marketplace": "US", "keyword": "lavalier microphone", "size": 100}
})
print(f"  Status: {kw_research.get('code', 'ERROR')}")

# Phase 3: ABA trends for top keywords
print("\n=== Phase 3: ABA Trends ===")
aba_results = {}
research_items = safe_items(kw_research)
print(f"  Found {len(research_items)} keywords")
for kw in research_items[:3]:
    keyword = kw.get('keyword', '')
    if keyword:
        print(f"  Fetching ABA trend for '{keyword}'...")
        time.sleep(0.3)
        aba = call_tool("aba_research_trend", {"marketplace": "US", "keyword": keyword})
        aba_results[keyword] = aba
        print(f"    -> {aba.get('code', 'ERROR')}")

# Save raw data
os.makedirs(OUT_DIR, exist_ok=True)
all_results = {
    "keyword_miner": kw_miner,
    "keyword_research": kw_research,
    "aba_trends": aba_results,
    "generated_at": datetime.now().isoformat()
}
with open(f"{OUT_DIR}/keyword_data.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
print(f"\nData saved to {OUT_DIR}/keyword_data.json")

# ====== Generate keyword report ======
print("\n=== Generating Keyword Report ===")

def fmt_num(n):
    if n is None: return "N/A"
    return f"{float(n):,.0f}"

def fmt_pct(n, is_ratio=True):
    if n is None: return "N/A"
    n = float(n)
    if is_ratio: return f"{n*100:.1f}%"
    return f"{n:.1f}%"

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

# ----- Keyword Miner -----
L("## 一、关键词挖掘（Keyword Miner）")
L()
miner_items = safe_items(kw_miner)
if miner_items:
    L("| 关键词 | 月搜索量 | 商品数 | 供需比 | 标题密度 | 平均售价 |")
    L("|--------|:-------:|:-----:|:------:|:--------:|:-------:|")
    sorted_miner = sorted(miner_items, key=lambda x: float(x.get('searchVolume', 0) or 0), reverse=True)
    for kw in sorted_miner[:30]:
        keyword = kw.get('keyword', 'N/A')
        sv = fmt_num(kw.get('searchVolume', 0))
        prods = fmt_num(kw.get('products', 0))
        sdr = kw.get('supplyDemandRatio', '')
        sdr_str = f"{float(sdr):.1f}" if sdr else "N/A"
        td = fmt_pct(kw.get('titleDensity', 0), is_ratio=True) if kw.get('titleDensity') else "N/A"
        price = fmt_money(kw.get('avgPrice', 0)) if kw.get('avgPrice') else "N/A"
        L(f"| {keyword} | {sv} | {prods} | {sdr_str} | {td} | {price} |")
    L()

L("---")
L()

# ----- Keyword Research -----
L("## 二、关键词研究（Keyword Research）")
L()
if research_items:
    L("| 关键词 | 月搜索量 | 月销量 | 周趋势 | 月趋势 | 3月趋势 | 点击集中度 | 品牌集中度 |")
    L("|--------|:-------:|:-----:|:-----:|:------:|:-------:|:---------:|:---------:|")
    sorted_research = sorted(research_items, key=lambda x: float(x.get('searchVolume', 0) or 0), reverse=True)
    for kw in sorted_research[:30]:
        keyword = kw.get('keyword', 'N/A')
        sv = fmt_num(kw.get('searchVolume', 0))
        units = fmt_num(kw.get('units', 0))
        w_t = fmt_pct(kw.get('weekTrend', 0)) if kw.get('weekTrend') is not None else "N/A"
        m_t = fmt_pct(kw.get('monthTrend', 0)) if kw.get('monthTrend') is not None else "N/A"
        m3_t = fmt_pct(kw.get('threeMonthTrend', 0)) if kw.get('threeMonthTrend') is not None else "N/A"
        cc = fmt_pct(kw.get('clickConcentration', kw.get('monopolyClickRate', 0)))
        bc = fmt_pct(kw.get('brandConcentration', kw.get('brandMonopolyRate', 0)))
        L(f"| {keyword} | {sv} | {units} | {w_t} | {m_t} | {m3_t} | {cc} | {bc} |")
    L()

L("---")
L()

# ----- ABA Trends -----
L("## 三、ABA 趋势分析")
L()
for keyword, aba_data in aba_results.items():
    L(f"### 「{keyword}」ABA 趋势")
    L()
    aba_items = safe_items(aba_data)
    if aba_items:
        L("| 时间 | 搜索频率排名 | 点击份额 | 转化份额 |")
        L("|------|:----------:|:--------:|:--------:|")
        for item in aba_items[-12:]:
            time_label = item.get('label', item.get('time', 'N/A'))
            rank = item.get('rank', item.get('searchRank', ''))
            cs = fmt_pct(item.get('clickShareRate', item.get('clickShare', 0)))
            cvs = fmt_pct(item.get('conversionShareRate', item.get('conversionShare', 0)))
            L(f"| {time_label} | {rank} | {cs} | {cvs} |")
    L()

L("---")
L()

# ----- Low-competition opportunities -----
L("## 四、低竞争高潜力关键词推荐")
L()
if research_items:
    opportunities = []
    for kw in research_items:
        sv = float(kw.get('searchVolume', 0) or 0)
        click_conc = float(kw.get('clickConcentration', kw.get('monopolyClickRate', 1) or 1))
        brand_conc = float(kw.get('brandConcentration', kw.get('brandMonopolyRate', 1) or 1))
        if sv >= 300 and click_conc < 0.5 and brand_conc < 0.5:
            opportunities.append(kw)
    if opportunities:
        L("| 关键词 | 月搜索量 | 点击集中度 | 品牌集中度 | 策略 |")
        L("|--------|:-------:|:---------:|:---------:|------|")
        for kw in sorted(opportunities, key=lambda x: float(x.get('searchVolume', 0) or 0), reverse=True)[:15]:
            keyword = kw.get('keyword', 'N/A')
            sv = fmt_num(kw.get('searchVolume', 0))
            cc = fmt_pct(kw.get('clickConcentration', 0))
            bc = fmt_pct(kw.get('brandConcentration', 0))
            L(f"| {keyword} | {sv} | {cc} | {bc} | 广告投放 + Listing 优化 |")
    else:
        L("*暂无符合条件的低竞争高潜力关键词*")
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
L()

report = "\n".join(lines)
with open(f"{OUT_DIR}/keyword_report.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"\nKeyword report saved to {OUT_DIR}/keyword_report.md")
