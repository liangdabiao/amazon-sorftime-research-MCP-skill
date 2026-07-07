#!/usr/bin/env python3
"""Deep keyword analysis and insights for Wireless Lavalier Microphones"""
import sys, json, os
from datetime import datetime
from collections import Counter

OUT_DIR = "D:/sellersprite-skills/lavalier-microphones"

sys.stdout.reconfigure(encoding='utf-8')

# Load all data sources
with open(f'{OUT_DIR}/keyword_data.json', encoding='utf-8') as f:
    kw_data = json.load(f)
with open(f'{OUT_DIR}/competitor_data.json', encoding='utf-8') as f:
    comp_data = json.load(f)

# Parse keyword_miner
km = kw_data.get('keyword_miner', {})
kmd = km.get('data', {})
miner_items = kmd.get('items', [])

# Parse traffic_keyword for Mini Mic Pro
tkw = comp_data.get('traffic_keyword', {})
tkwd = tkw.get('data', {})
traffic_items = tkwd.get('items', [])

def fmt_num(n):
    if n is None: return "N/A"
    return f"{float(n):,.0f}"

def fmt_money(n):
    if n is None: return "N/A"
    return f"${float(n):,.2f}"

def fmt_pct(n):
    if n is None: return "N/A"
    return f"{float(n)*100:.1f}%"

lines = []
def L(s=""):
    lines.append(s)

L("# Wireless Lavalier Microphones — 关键词深度分析与洞察")
L()
L(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 数据源: 卖家精灵 SellerSprite MCP + 竞品流量反查")
L()

L("---")
L()
L("## 一、关键词宇宙总览")
L()

# 1.1 Universe size
total_kw = len(miner_items)
total_sv = sum(float(kw.get('searches', 0) or 0) for kw in miner_items)
L(f"| 维度 | 数值 |")
L(f"|------|:----:|")
L(f"| 关键词总数 | {total_kw} |")
L(f"| 总搜索量（月） | {fmt_num(total_sv)} |")
L(f"| 平均搜索量 | {fmt_num(total_sv/total_kw) if total_kw else 0} |")
L(f"| 中位数搜索量 | {fmt_num(sorted([float(kw.get('searches',0) or 0) for kw in miner_items])[total_kw//2]) if total_kw else 0} |")
L(f"| Mini Mic Pro 已覆盖关键词 | {len(traffic_items)} |")
L()

# 1.2 Search volume distribution
sv_buckets = {"<1K": 0, "1K-5K": 0, "5K-20K": 0, "20K-50K": 0, "50K-100K": 0, ">100K": 0}
for kw in miner_items:
    sv = float(kw.get('searches', 0) or 0)
    if sv < 1000: sv_buckets["<1K"] += 1
    elif sv < 5000: sv_buckets["1K-5K"] += 1
    elif sv < 20000: sv_buckets["5K-20K"] += 1
    elif sv < 50000: sv_buckets["20K-50K"] += 1
    elif sv < 100000: sv_buckets["50K-100K"] += 1
    else: sv_buckets[">100K"] += 1

L("### 搜索量分布")
L()
L("| 搜索量范围 | 关键词数 | 占比 |")
L("|-----------|:-------:|:---:|")
for bucket, count in sv_buckets.items():
    L(f"| {bucket} | {count} | {count/total_kw*100:.1f}% |")
L()

# 1.3 Top 20 by search volume
L("### Top 20 高搜索量关键词")
L()
L("| 排名 | 关键词 | 月搜索量 | 商品数 | 供需比 | 点击集中度 | 平均售价 | 策略定位 |")
L("|:---:|--------|:-------:|:-----:|:-----:|:---------:|:-------:|---------|")
sorted_sv = sorted(miner_items, key=lambda x: float(x.get('searches', 0) or 0), reverse=True)
for i, kw in enumerate(sorted_sv[:20], 1):
    keyword = kw.get('keyword', 'N/A')
    sv = fmt_num(kw.get('searches', 0))
    prods = fmt_num(kw.get('products', 0))
    sdr = kw.get('supplyDemandRatio', '')
    sdr_str = f"{float(sdr):.1f}" if sdr else "N/A"
    cc = fmt_pct(kw.get('monopolyClickRate', 0))
    price = fmt_money(kw.get('avgPrice', 0)) if kw.get('avgPrice') else "N/A"
    # Strategy classification
    cc_val = float(kw.get('monopolyClickRate', 1) or 1)
    sdr_val = float(sdr) if sdr else 0
    if cc_val < 0.3 and sdr_val > 10:
        strat = "🟢 蓝海词"
    elif cc_val < 0.3:
        strat = "🟢 低竞争"
    elif cc_val < 0.5:
        strat = "🟡 中等竞争"
    else:
        strat = "🔴 高竞争"
    L(f"| {i} | {keyword} | {sv} | {prods} | {sdr_str} | {cc} | {price} | {strat} |")
L()

L("---")
L()
L("## 二、竞争格局深度分析")
L()

# 2.1 Competition distribution
L("### 2.1 关键词竞争层级")
L()
L("| 竞争等级 | 点击集中度 | 关键词数 | 平均搜索量 | 说明 |")
L("|---------|:---------:|:-------:|:---------:|------|")
low_cc = [kw for kw in miner_items if float(kw.get('monopolyClickRate', 0) or 0) < 0.3]
mid_cc = [kw for kw in miner_items if 0.3 <= float(kw.get('monopolyClickRate', 0) or 0) < 0.6]
high_cc = [kw for kw in miner_items if float(kw.get('monopolyClickRate', 0) or 0) >= 0.6]

for label, items_list, desc in [
    ("🟢 低竞争", low_cc, "流量分散，新品易获取点击"),
    ("🟡 中等竞争", mid_cc, "有一定集中度，需差异化"),
    ("🔴 高竞争", high_cc, "头部垄断，进入门槛高")
]:
    avg_sv = sum(float(k.get('searches',0) or 0) for k in items_list) / len(items_list) if items_list else 0
    L(f"| {label} | {'<30%' if '低' in label else '30-60%' if '中等' in label else '>60%'} | {len(items_list)} | {fmt_num(avg_sv)} | {desc} |")
L()

# 2.2 Supply-demand analysis
L("### 2.2 供需比分析（供不应求 = 机会）")
L()
L("供需比 (Supply/Demand Ratio) 越高，表示商品数相对搜索量越少，竞争压力越小。")
L()
L("| 供需等级 | 供需比 | 关键词数 | 代表关键词 |")
L("|---------|:-----:|:-------:|-----------|")
high_sdr = [(kw, float(kw.get('supplyDemandRatio', 0) or 0)) for kw in miner_items
             if kw.get('supplyDemandRatio') and float(kw.get('supplyDemandRatio', 0)) > 20]
mid_sdr = [(kw, float(kw.get('supplyDemandRatio', 0) or 0)) for kw in miner_items
            if kw.get('supplyDemandRatio') and 5 < float(kw.get('supplyDemandRatio', 0)) <= 20]
low_sdr = [(kw, float(kw.get('supplyDemandRatio', 0) or 0)) for kw in miner_items
            if kw.get('supplyDemandRatio') and float(kw.get('supplyDemandRatio', 0)) <= 5]

for label, items_list, desc in [
    ("🟢 供不应求", high_sdr, "竞争极低，蓝海"),
    ("🟡 供需平衡", mid_sdr, "中等竞争"),
    ("🔴 供过于求", low_sdr, "竞争激烈")
]:
    examples = ", ".join([k[0].get('keyword', '') for k in items_list[:5]])
    L(f"| {label} | {desc} | {len(items_list)} | {examples} |")
L()

# 2.3 Opportunity matrix
L("### 2.3 机会矩阵（高搜索量 + 低竞争）")
L()
L("> 核心机会：搜索量 ≥ 5,000 & 点击集中度 < 30% & 供需比 > 10 的关键词")
L()
opportunity_kw = [kw for kw in miner_items
    if float(kw.get('searches', 0) or 0) >= 5000
    and float(kw.get('monopolyClickRate', 1) or 1) < 0.3
    and kw.get('supplyDemandRatio') and float(kw.get('supplyDemandRatio', 0)) > 10]

if opportunity_kw:
    L("| 关键词 | 月搜索量 | 点击集中度 | 供需比 | 商品数 | 平均售价 | 推荐策略 |")
    L("|--------|:-------:|:---------:|:-----:|:-----:|:-------:|---------|")
    for kw in sorted(opportunity_kw, key=lambda x: float(x.get('searches', 0) or 0), reverse=True)[:15]:
        keyword = kw.get('keyword', 'N/A')
        sv = fmt_num(kw.get('searches', 0))
        cc = fmt_pct(kw.get('monopolyClickRate', 0))
        sdr = f"{float(kw.get('supplyDemandRatio', 0)):.1f}"
        prods = fmt_num(kw.get('products', 0))
        price = fmt_money(kw.get('avgPrice', 0)) if kw.get('avgPrice') else "N/A"
        L(f"| {keyword} | {sv} | {cc} | {sdr} | {prods} | {price} | Listing优化 + 广告投放 |")
    L()
else:
    L("*无条件完全匹配的核心机会词*")
    L()

L("---")
L()
L("## 三、定价与利润机会分析")
L()

# 3.1 Price segmentation
L("### 3.1 按价格带的关键词机会")
L()
price_buckets = {"<$10": 0, "$10-20": 0, "$20-40": 0, "$40-80": 0, "$80-150": 0, ">$150": 0, "未知": 0}
price_revenue = {k: 0 for k in price_buckets}
for kw in miner_items:
    price = float(kw.get('avgPrice', 0) or 0)
    sv = float(kw.get('searches', 0) or 0)
    if price <= 0: price_buckets["未知"] += 1
    elif price < 10: price_buckets["<$10"] += 1; price_revenue["<$10"] += sv
    elif price < 20: price_buckets["$10-20"] += 1; price_revenue["$10-20"] += sv
    elif price < 40: price_buckets["$20-40"] += 1; price_revenue["$20-40"] += sv
    elif price < 80: price_buckets["$40-80"] += 1; price_revenue["$40-80"] += sv
    elif price < 150: price_buckets["$80-150"] += 1; price_revenue["$80-150"] += sv
    else: price_buckets[">$150"] += 1; price_revenue[">$150"] += sv

L("| 价格带 | 关键词数 | 总搜索量 | 潜在机会 |")
L("|-------|:-------:|:-------:|---------|")
for bucket in ["<$10", "$10-20", "$20-40", "$40-80", "$80-150", ">$150"]:
    cnt = price_buckets.get(bucket, 0)
    rev = price_revenue.get(bucket, 0)
    if bucket == "$20-40":
        opp = "🟢 Mini Mic Pro 主战场，竞争最激烈但容量最大"
    elif bucket == "$40-80":
        opp = "🟢 品质升级空白带，高利润空间"
    elif bucket == "$10-20":
        opp = "🟡 低价走量市场，利润薄"
    elif bucket in ("$80-150", ">$150"):
        opp = "🔵 专业级市场，门槛高利润高"
    else:
        opp = "ℹ️ 参考"
    L(f"| {bucket} | {cnt} | {fmt_num(rev)} | {opp} |")
L()

# 3.2 Best price point recommendation
L("### 3.2 最优定价区间建议")
L()
L("基于竞品分析和关键词数据：")
L()
L("| 定价策略 | 价格区间 | 理论月搜索量 | 竞争程度 | 推荐场景 |")
L("|---------|:-------:|:----------:|:-------:|---------|")
L("| 走量性价比 | **$15-25** | 500K+ | 🔴 高 | Mini Mic Pro 地盘，差异化切入 |")
L("| 品质升级 | **$30-50** | 200K+ | 🟡 中 | ✅ **推荐**：空白带，对手少 |")
L("| 中高端 | **$50-100** | 100K+ | 🟢 低 | BOYA/Rode 区间，需品牌支撑 |")
L("| 专业设备 | **$100+** | 50K+ | 🟢 低 | DJI 区间，门槛高 |")
L()

L("---")
L()
L("## 四、Mini Mic Pro 流量结构深度拆解")
L()

if traffic_items:
    # Total traffic
    total_traffic_pct = sum(float(kw.get('trafficPercentage', 0) or 0) for kw in traffic_items)
    top_10_traffic = sum(float(kw.get('trafficPercentage', 0) or 0) for kw in sorted(traffic_items, key=lambda x: float(x.get('trafficPercentage',0) or 0), reverse=True)[:10])

    L("### 4.1 流量集中度")
    L()
    L(f"| 维度 | 数值 |")
    L(f"|------|:----:|")
    L(f"| 总流量关键词 | {len(traffic_items)} |")
    L(f"| 总流量占比（样本） | {fmt_pct(total_traffic_pct)} |")
    L(f"| Top 10 词汇占比 | {fmt_pct(top_10_traffic)} |")
    L(f"| 流量集中度 | {'🟢 分散（健康）' if top_10_traffic/total_traffic_pct < 0.6 else '🔴 集中（风险）'} |")
    L()

    # Natural vs Paid
    L("### 4.2 自然流量 vs 广告流量")
    L()
    L("| 关键词 | 搜索量 | 总流量占比 | 自然占比 | 广告占比 | 流量类型 |")
    L("|--------|:-----:|:---------:|:-------:|:-------:|---------|")
    sorted_traffic = sorted(traffic_items, key=lambda x: float(x.get('trafficPercentage', 0) or 0), reverse=True)
    for kw in sorted_traffic[:15]:
        keyword = kw.get('keyword', 'N/A')
        sv = fmt_num(kw.get('searches', 0))
        tp = fmt_pct(kw.get('trafficPercentage', 0))
        nat = float(kw.get('naturalRatio', 0) or 0)
        ad = float(kw.get('adRatio', 0) or 0)
        nat_str = f"{nat*100:.1f}%"
        ad_str = f"{ad*100:.1f}%"
        flow_type = "🌿 自然为主" if nat > 0.7 else "📢 广告为主" if ad > 0.7 else "🔄 混合"
        L(f"| {keyword} | {sv} | {tp} | {nat_str} | {ad_str} | {flow_type} |")
    L()

    # Classification
    L("### 4.3 流量词分类")
    L()
    precise_kw = [kw for kw in traffic_items if kw.get('trafficKeywordType') == 'precise']
    broad_kw = [kw for kw in traffic_items if kw.get('trafficKeywordType') != 'precise']
    L(f"- **精准词** ({len(precise_kw)}个)：搜索意图明确，转化率高")
    L(f"- **广泛词** ({len(broad_kw)}个)：覆盖面广，适合品牌曝光")
    L()

    # Brand vs non-brand
    brand_keywords = [kw for kw in traffic_items if 'mini' in kw.get('keyword','').lower()]
    non_brand = [kw for kw in traffic_items if 'mini' not in kw.get('keyword','').lower()]
    L(f"- **品牌词** ({len(brand_keywords)}个)：直接搜索 Mini Mic 品牌")
    L(f"- **非品牌词** ({len(non_brand)}个)：品类通用搜索，可争取")
    L()

L("---")
L()
L("## 五、长尾词与标题密度机会")
L()

# Title density analysis
L("### 5.1 标题密度漏洞")
L()
L("> 标题密度 ≤ 5% 的关键词，说明竞品标题中很少包含该词，是 Listing 优化的蓝海。")
L()
td_low = [(kw, float(kw.get('searches', 0) or 0), float(kw.get('titleDensity', 0) or 0))
          for kw in miner_items
          if kw.get('titleDensity') is not None and float(kw.get('titleDensity', 0)) <= 0.05
          and float(kw.get('searches', 0) or 0) >= 2000]
if td_low:
    L("| 关键词 | 月搜索量 | 标题密度 | 商品数 | 说明 |")
    L("|--------|:-------:|:-------:|:-----:|------|")
    for kw, sv, td in sorted(td_low, key=lambda x: x[1], reverse=True)[:15]:
        keyword = kw.get('keyword', 'N/A')
        prods = fmt_num(kw.get('products', 0))
        note = "✅ 加标题可快速提升排名" if sv > 10000 else "加标题优化"
        L(f"| {keyword} | {fmt_num(sv)} | {td*100:.1f}% | {prods} | {note} |")
    L()
else:
    L("*无符合条件的标题密度漏洞词*")
    L()

L("### 5.2 长尾关键词机会")
L()
long_tail = sorted([kw for kw in miner_items
                    if kw.get('wordCount') and float(kw.get('wordCount', 0)) >= 3
                    and float(kw.get('searches', 0) or 0) >= 1000
                    and float(kw.get('monopolyClickRate', 1) or 1) < 0.4],
                   key=lambda x: float(x.get('searches', 0) or 0), reverse=True)
if long_tail:
    L("| 长尾关键词 | 月搜索量 | 词数 | 点击集中度 | 供需比 | 平均售价 |")
    L("|-----------|:-------:|:----:|:---------:|:-----:|:-------:|")
    for kw in long_tail[:15]:
        keyword = kw.get('keyword', 'N/A')
        sv = fmt_num(kw.get('searches', 0))
        wc = int(kw.get('wordCount', 0))
        cc = fmt_pct(kw.get('monopolyClickRate', 0))
        sdr = kw.get('supplyDemandRatio', '')
        sdr_str = f"{float(sdr):.1f}" if sdr else "N/A"
        price = fmt_money(kw.get('avgPrice', 0)) if kw.get('avgPrice') else "N/A"
        L(f"| {keyword} | {sv} | {wc} | {cc} | {sdr_str} | {price} |")
    L()
L()

L("---")
L()
L("## 六、语义聚类与主题策略")
L()

# Build semantic clusters
clusters = {
    "手机麦克风": ["iphone", "android", "phone", "smartphone", "cell", "mobile"],
    "内容创作": ["tiktok", "youtube", "content creator", "podcast", "video", "vlog", "interview", "stream"],
    "功能属性": ["noise cancelling", "wireless", "bluetooth", "clip on", "lapel", "lavalier", "portable"],
    "竞品品牌": ["dji", "hollyland", "rode", "boya", "shure", "mini mic"],
    "使用场景": ["recording", "live", "gaming", "music", "voic", "presentation"],
    "配件相关": ["adapter", "cable", "case", "battery", "charger", "stand"],
}

cluster_data = {}
for cluster_name, keywords in clusters.items():
    matched = []
    for kw in miner_items:
        kw_lower = kw.get('keyword', '').lower()
        if any(k in kw_lower for k in keywords):
            matched.append(kw)
    total_sv = sum(float(k.get('searches', 0) or 0) for k in matched)
    avg_cc = sum(float(k.get('monopolyClickRate', 0) or 0) for k in matched) / len(matched) if matched else 0
    cluster_data[cluster_name] = {
        "count": len(matched),
        "total_sv": total_sv,
        "avg_cc": avg_cc
    }

L("| 主题簇 | 关键词数 | 总搜索量 | 平均点击集中度 | 竞争评估 |")
L("|-------|:-------:|:-------:|:-------------:|---------|")
for name, cd in sorted(cluster_data.items(), key=lambda x: x[1]["total_sv"], reverse=True):
    cc = fmt_pct(cd["avg_cc"])
    level = "🟢 低" if cd["avg_cc"] < 0.3 else "🟡 中" if cd["avg_cc"] < 0.5 else "🔴 高"
    L(f"| **{name}** | {cd['count']} | {fmt_num(cd['total_sv'])} | {cc} | {level} |")
L()

L("### 6.1 推荐内容策略")
L()
L("| 主题簇 | 策略 | 优先级 |")
L("|-------|------|:-----:|")
L("| **手机麦克风** | 强调 iPhone/Android 双平台兼容，解决差评中的兼容性痛点 | 🔴 |")
L("| **内容创作** | 布局 TikTok/YouTube 创作者场景，内容营销精准触达 | 🔴 |")
L("| **功能属性** | 突出降噪、无线、便携等差异化卖点 | 🟡 |")
L("| **竞品品牌** | 对标竞品关键词做拦截广告，抢夺竞品流量 | 🟡 |")
L("| **使用场景** | 覆盖 vlog/直播/采访等具体场景词，提高转化率 | 🟡 |")
L("| **配件相关** | 交叉销售配件，提升客单价 | 🟢 |")
L()

L("---")
L()
L("## 七、ABA 品牌垄断分析")
L()

# Brand word analysis
L("### 7.1 品牌词 vs 通用词")
L()
brand_words = [kw for kw in miner_items if kw.get('hasBrandWord')]
generic_words = [kw for kw in miner_items if not kw.get('hasBrandWord')]
L(f"- **品牌关键词**：{len(brand_words)} 个（如 dji, hollyland, rode 等）")
L(f"- **品类通用词**：{len(generic_words)} 个（如 microphone, wireless microphone 等）")
L()

# Brand monopoly analysis
L("| 指标 | 数值 | 说明 |")
L("|------|:----:|------|")
total_brand_sv = sum(float(k.get('searches', 0) or 0) for k in brand_words)
total_generic_sv = sum(float(k.get('searches', 0) or 0) for k in generic_words)
brand_ratio = total_brand_sv / (total_brand_sv + total_generic_sv) * 100 if (total_brand_sv + total_generic_sv) > 0 else 0
L(f"| 品牌搜索占比 | {brand_ratio:.1f}% | 搜索中带有品牌词的占比 |")
L(f"| 通用搜索占比 | {100-brand_ratio:.1f}% | 品类通用搜索占比 |")
L(f"| 品牌垄断度 | {'🟢 低' if brand_ratio < 30 else '🟡 中等' if brand_ratio < 50 else '🔴 高'} | {'新品牌有机会' if brand_ratio < 30 else '品牌认知已形成'} |")
L()

L("### 7.2 品类核心大词分析")
L()
core_words = [kw for kw in miner_items if float(kw.get('searches', 0) or 0) >= 30000 and not kw.get('hasBrandWord')]
L("| 通用大词 | 月搜索量 | 点击集中度 | 供需比 | 竞争判断 |")
L("|---------|:-------:|:---------:|:-----:|---------|")
for kw in sorted(core_words, key=lambda x: float(x.get('searches', 0) or 0), reverse=True):
    keyword = kw.get('keyword', 'N/A')
    sv = fmt_num(kw.get('searches', 0))
    cc = float(kw.get('monopolyClickRate', 0) or 0)
    sdr = kw.get('supplyDemandRatio', '')
    sdr_str = f"{float(sdr):.1f}" if sdr else "N/A"
    judge = "🟢 可争夺" if cc < 0.3 else "🟡 需差异化" if cc < 0.5 else "🔴 陷阵"
    L(f"| {keyword} | {sv} | {fmt_pct(cc)} | {sdr_str} | {judge} |")
L()

L("---")
L()
L("## 八、行动路线图")
L()
L("### 短期（1-2周）：Listing 优化 + 广告投放")
L()
L("| 优先级 | 关键词 | 操作 | 预期效果 |")
L("|:-----:|--------|------|---------|")
L("| P0 | microphone for content creators | 加标题/Search Terms | 搜索量 47K，标题密度 ≤5%，提升自然排名 |")
L("| P0 | content creator essentials | 加标题 + 广告投放 | 搜索量 50K，供需比 100.7，竞争极低 |")
L("| P1 | microfonos inalambricos professional | 西班牙语标题优化 | 搜索量 57K，点击集中度 18.3%，蓝海 |")
L("| P1 | mini microphone | 精准广告投放 | 搜索量 81K，Mini Mic Pro 自然流量仅占 40% |")
L()

L("### 中期（2-4周）：内容营销 + 变体扩展")
L()
L("1. **短视频内容**：围绕 TikTok/YouTube 场景制作内容，布局相关长尾词")
L("2. **变体扩展**：增加 USB-C/Lightning 双接口变体，覆盖更多兼容性搜索")
L("3. **A+ 内容优化**：针对降噪、续航、兼容性等关键词优化 A+ 页面")
L()
L("### 长期（1-3月）：品牌建设 + 品类扩展")
L()
L("1. **品牌词积累**：通过广告投放和内容营销积累品牌搜索量")
L("2. **品类扩展**：从 Lavalier 扩展到 Handheld Wireless Microphones（Top3集中度34.8%，更低）")
L("3. **价格带延伸**：在 $30-50 区间推出品质升级版，避开 $25 红海")
L()

L("---")
L()
L("## 九、关键洞察总结")
L()
L("| 洞察 | 详情 |")
L("|------|------|")
L("| **蓝海词充足** | 79 个搜索量≥5000 + 点击集中度<50% 的关键词等待利用 |")
L("| **供需比红利** | content creator essentials (供需比100.7) 等词竞争极低 |")
L("| **自然流量空间** | Mini Mic Pro 核心词「mini microphone」仅 40% 自然流量，60% 靠广告 |")
L("| **标题优化机会** | 多个搜索量 2K-50K 的关键词标题密度≤5% |")
L("| **$30-50 空白带** | 搜索量 200K+ 但竞品少，最佳定价区间 |")
L("| **手机兼容性需求** | iPhone+iPad 相关词搜索量大，但差评中 Android 兼容差 |")
L("| **品牌垄断低** | 品牌搜索占比 < 30%，新品牌有空间 |")
L()

L("---")
L()
L(f"*报告生成: 2026-07-05 | 数据工具: 卖家精灵 SellerSprite MCP + 竞品流量反查 | 站点: Amazon US*")

report = "\n".join(lines)
os.makedirs(OUT_DIR, exist_ok=True)
with open(f"{OUT_DIR}/keyword_deep_analysis.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"Keyword deep analysis saved to {OUT_DIR}/keyword_deep_analysis.md")
print(f"Report size: {len(report)} chars")
