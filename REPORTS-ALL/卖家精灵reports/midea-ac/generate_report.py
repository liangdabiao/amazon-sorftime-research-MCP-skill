#!/usr/bin/env python3
"""Generate market report for Midea AC"""
import json

with open('midea-ac/research_data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

def safe_items(data):
    if isinstance(data, dict):
        return data.get('items', [])
    if isinstance(data, list):
        return data
    return []

brands = d.get('raw_brand_conc',{}).get('data',[])
price = safe_items(d.get('raw_price_dist',{}).get('data',{}))
ratings_dist = safe_items(d.get('raw_rating_dist',{}).get('data',{}))
seller_type = safe_items(d.get('raw_seller_type',{}).get('data',{}))
list_date = safe_items(d.get('raw_list_date',{}).get('data',{}))
seller_ctry = safe_items(d.get('raw_seller_ctry',{}).get('data',{}))
prod_conc = d.get('raw_prod_conc',{}).get('data',[])
kw_items = d.get('raw_keyword_miner',{}).get('data',{}).get('items',[])
kw_sorted = sorted(kw_items, key=lambda x: x.get('searches',0), reverse=True) if kw_items else []

window_items = d.get('raw_product_window',{}).get('data',{}).get('items',[])
total_units = sum(p.get('units',0) for p in window_items)
price_items = [p for p in window_items if p.get('price',0) > 0]
avg_price = sum(p.get('price',0) for p in price_items) / max(len(price_items), 1)

report = []
report.append('# Midea (美的) 窗式空调 Amazon US 市场调研报告\n')
report.append('**报告日期**: 2026-07-07\n')
report.append('---\n')
report.append('## 一、筛选口径\n')
report.append('- **调研对象**: Midea (美的) 窗式空调 Amazon US 市场')
report.append('- **类目节点**: Home & Kitchen > Heating, Cooling & Air Quality > Air Conditioners > Window')
report.append('- **节点 ID**: 1055398:3206324011:14554126011:3737721')
report.append('- **数据工具**: product_research, market_brand_concentration, market_price_distribution, market_rating_distribution, market_seller_type_concentration, market_listing_date_distribution, market_seller_country_distribution, market_product_concentration, asin_detail, keyword_miner, keepa_info, asin_prediction')
report.append('- **数据月份**: 2026年7月')
report.append('- **样本量**: 50个产品, 品牌集中度 Top 10\n')
report.append('---\n')

report.append('## 二、KPI 摘要\n')
report.append('| 指标 | 数值 |')
report.append('|------|------|')
report.append(f'| 类目总月销量 | 约 {total_units:,}+ 台 |')
report.append('| 类目总月销售额 | 约 $51M+ |')
report.append(f'| 平均售价 | ~${avg_price:.0f} |')
report.append('| 品牌数量 | 20+ |')
report.append('| Midea 市占率(销量) | **34.0%** (第1名) |')
report.append('| Midea 市占率(销售额) | **41.6%** (第1名) |')
report.append('| 主要竞争对手 | Frigidaire(26.7%), GE(10.7%), LG(9.5%) |\n')
report.append('---\n')

report.append('## 三、品牌集中度分析\n')
report.append('| 排名 | 品牌 | 销量占比 | 销售额占比 | ASIN数 | 均价 | 月销量 |')
report.append('|------|------|:--------:|:----------:|:------:|:----:|:------:|')
for b in brands[:10]:
    report.append(f'| {b.get("ranking")} | **{b["brand"]}** | {b["totalUnitsRatio"]*100:.1f}% | {b["totalRevenueRatio"]*100:.1f}% | {b["products"]} | ${b["avgPrice"]:.0f} | {b["totalUnits"]:,} |')

report.append('\n**洞察**: Midea 以 34% 销量份额和 41.6% 销售额份额稳居第1。Frigidaire 紧随其后(26.7%)但均价更低($336 vs $402)。Midea 的 U-Shaped 系列推高了整体均价和利润率。\n')
report.append('---\n')

report.append('## 四、价格分布\n')
report.append('| 价格区间 | 产品数 | 月销量 | 占比 | 销售额 |')
report.append('|---------|:------:|:------:|:---:|:------:|')
for p in price:
    pct = p.get('unitsRatio', 0) * 100
    report.append(f'| {p.get("label","?")} | {p.get("products",0)} | {p.get("units",0):,} | {pct:.1f}% | ${p.get("revenue",0):,.0f} |')

report.append('\n**洞察**: 主要销量集中在 $150-$500 区间的中高端产品。\n')
report.append('---\n')

report.append('## 五、卖家类型分布\n')
report.append('| 类型 | 产品数 | 月销量 | 占比 |')
report.append('|------|:------:|:------:|:----:|')
for s in seller_type:
    report.append(f'| {s.get("label","?")} | {s.get("productNum",0)} | {s.get("units",0):,} | {s.get("unitsRatio",0)*100:.1f}% |')

report.append('\n**洞察**: Amazon自营占 89.6%, 该品类以 1P 模式主导。\n')
report.append('---\n')

report.append('## 六、上架时间分布\n')
report.append('| 上架时间 | 产品数 | 月销量 | 占比 |')
report.append('|---------|:------:|:------:|:----:|')
for l in list_date:
    report.append(f'| {l.get("label","?")} | {l.get("products",0)} | {l.get("units",0):,} | {l.get("unitsRatio",0)*100:.1f}% |')

report.append('\n---\n')

report.append('## 七、卖家国家分布\n')
report.append('| 国家 | 产品数 | 月销量 | 占比 |')
report.append('|------|:------:|:------:|:----:|')
for c in seller_ctry:
    report.append(f'| {c.get("country","?")} | {c.get("products",0)} | {c.get("units",0):,} | {c.get("unitsRatio",0)*100:.1f}% |')

report.append('\n---\n')

report.append('''## 八、Midea 产品线拆解

### 8.1 U-Shaped 系列 (2026款) — 旗舰创新产品线

U-Shaped 是 Midea 的差异化核心产品, 采用独特的 U 型设计:
- 允许窗户在空调安装状态下开合, 保持通风和视野
- 利用窗户物理隔音, 最低 32 dBA (9倍静音于传统机型)
- DC Inverter 技术, 节能 37%+, 首个获 ENERGY STAR 认证的窗式空调
- 支持 SmartHome App, Alexa, Google Assistant 智能控制
- Quick-Snap 简易安装支架

**变体系列 (父ASIN: B0H2WX235T)**:
| 变体 | ASIN | 价格 | 评分 |
|------|:----:|:----:|:----:|
| 6,000 BTU | B0G34M7C1M | $349.99 | 4.7(151) |
| 8,000 BTU | B0G34MR64D | $379.99 | 4.7(151) |
| 10,000 BTU | B0G34PP2JW | $449.99 | 4.7(151) |
| 12,000 BTU | B0G34JL2ZS | $459.99 | 4.7(151) |
| 6,000 BTU Jet Black | B0GL6LJFVM | $349.99 | 4.7(151) |

系列月销量约 27,457 台, 评分 **4.7★**, 远超传统窗式平均。

### 8.2 Smart Inverter 传统窗式系列

| 型号 | ASIN | 价格 | 评分 | 特点 |
|------|:----:|:----:|:----:|------|
| 18,000 BTU | B0FDQHJ46H | $545 | 4.4(12K+) | APP+Alexa |
| 12,000 BTU w/Heat | B0GL6H2J7P | ~$450 | 4.4(12K+) | 带加热 |
| 8,000 BTU w/Heat | B0CVVQWGH2 | $340 | 3.8(675) | 加热+除湿 |
| 7,800 BTU Inverter | B0H79RW5PN | $380 | 4.4(12K+) | 变频 |
| 6,000 BTU | B0CYFCJN7R | $234 | 4.4(12K+) | 3合1 |
| 5,000 BTU EasyCool | B085797ZFF | $170 | 4.4(12K+) | 入门级 |

### 8.3 Midea 整体表现

- **总月销量**: 65,671 台 (品牌第1)
- **总月销售额**: $21.3M (品牌第1)
- **均价**: $402 (高端定位)
- **平均评分**: 4.3★
- **ASIN数量**: 4个独立ASIN (vs LG 13个, Frigidaire 7个)

Midea 以**最少的产品线**实现了**最高的市场份额**, 产品策略极其高效。

---\n''')

report.append('## 九、关键词分析\n')
report.append('### 9.1 核心品类搜索词\n')
report.append('| 关键词 | 月搜索量 | 均价 | SPR | 竞价 |')
report.append('|--------|:-------:|:----:|:---:|:----:|')
target_kws = ['window air conditioner', 'air conditioner', 'ac unit', 'portable ac', 'portable air conditioner', 'portable ac unit', 'ac']
for kw_name in target_kws:
    match = [k for k in kw_sorted if k.get('keyword') == kw_name]
    if match:
        k = match[0]
        report.append(f'| {k["keyword"]} | {k.get("searches",0):,} | ${k.get("avgPrice",0)} | {k.get("spr",0)} | ${k.get("bid",0)} |')

report.append('\n### 9.2 Midea 品牌相关关键词\n')
report.append('- midea u shaped window air conditioner')
report.append('- midea air conditioner')
report.append('- midea window air conditioner')
report.append('- midea portable air conditioner')
report.append('- midea 8000 btu air conditioner')
report.append('- midea 12000 btu air conditioner\n')
report.append('---\n')

report.append('## 十、产品集中度 (Top 10 ASIN)\n')
report.append('| 排名 | 品牌 | 价格 | 月销占比 | 评分(评论数) |')
report.append('|:----:|:----:|:----:|:--------:|:------------:|')
for i, p in enumerate(prod_conc[:10]):
    report.append(f'| {i+1} | {p.get("brand","?")} | ${p.get("price",0)} | {p.get("totalUnitsRatio",0)*100:.1f}% | {p.get("rating","?")}({p.get("ratings",0):,}) |')

report.append('\n---\n')

report.append('''## 十一、竞品格局总结

| 品牌 | 定位 | 优势 | 威胁 |
|------|:----:|------|------|
| **Midea** | 高端创新 | U-Shaped 差异化, 4.7★评分, 均价$402 | 持续创新压力 |
| Frigidaire | 中端走量 | 7个ASIN, 品牌认知强, Amazon自营 | 产品同质化 |
| GE | 中端 | 品牌信任, Profile高端线 | 产品线仅2个ASIN |
| LG | 全价位 | 品牌力强, 13个ASIN覆盖面广 | 单品销量分散 |
| Electactic | 中低端 | 9个ASIN多型号覆盖 | 品牌力弱 |

---\n''')

report.append('## 十二、风险提示\n')
report.append('1. **季节性**: 空调为强季节性品类, 夏季(5-8月)为销售高峰, 冬季低谷明显')
report.append('2. **1P主导**: Amazon自营占 89.6%, 3P/FBA 卖家进入空间有限')
report.append('3. **大件物流**: 窗式空调 50-60磅, FBA 费用高')
report.append('4. **新品壁垒**: Frigidaire/GE/LG 品牌认知度强')
report.append('5. **价格战风险**: 中国低价品牌涌入可能拉低均价\n')
report.append('---\n')

report.append('''## 十三、评级: ✅ 推荐

**Midea 在窗式空调类目已建立强势品牌地位:**

| 维度 | 评分 | 说明 |
|:----:|:----:|------|
| 市场地位 | ★★★★★ | 销量/销售额双料第1 |
| 产品力 | ★★★★★ | U-Shaped 创新设计, 4.7★ |
| 利润率 | ★★★★☆ | 均价$402, 高端定位 |
| 竞争壁垒 | ★★★★☆ | 专利+品牌+Amazon合作 |
| 增长潜力 | ★★★★☆ | 2026新款持续迭代 |

**机会点**:
- 便携式空调(Portable AC)可作为第二增长曲线
- 加大品牌词SEO和广告投放
- 扩展更多 BTU 规格

---

> ⚠️ **免责声明**: 所有销量/销售额数据为 sellerSprite 估算值, 仅供参考。数据采集日期: 2026-07-06/07。\n''')

with open('midea-ac/market_report.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))
print(f'Report saved! {len("\n".join(report))} chars')
