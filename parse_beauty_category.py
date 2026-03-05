#!/usr/bin/env python3
"""
解析 Beauty & Personal Care 品类数据并生成分析报告
"""

import json
import re
from datetime import datetime
from pathlib import Path

# 读取原始数据文件
raw_file = r"D:\amazon-mcp\.claude\skills\category-reports\Beauty_&_Personal_Care_US_20260304\category_report_raw.txt"

with open(raw_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取 JSON 数据部分 - 改进的解析逻辑
# 查找 {"Top100 产品": 开始的部分
# 首先清理 SSE 格式前缀
json_start = content.find('{"Top100 产品')
print(f"查找 ' Top100 产品': {json_start}")

if json_start == -1:
    # 尝试查找其他可能的开始位置
    json_start = content.find('"Top100 产品"')
    print(f"查找 '\"Top100 产品\"': {json_start}")
    if json_start != -1:
        json_start = content.rfind('{', 0, json_start)
        print(f"回溯到 '{{': {json_start}")

if json_start == -1:
    # 尝试直接查找 { 开始
    json_start = content.find('{')
    print(f"使用第一个 '{{': {json_start}")

if json_start != -1:
    json_text = content[json_start:]
    print(f"JSON 文本前 200 字符：{json_text[:200]}")
    
    # 尝试找到完整的 JSON 对象
    # 计算大括号匹配
    brace_count = 0
    json_end = 0
    for i, char in enumerate(json_text):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                json_end = i + 1
                break
    
    if json_end > 0:
        json_text = json_text[:json_end]
    else:
        # 如果没有找到闭合，尝试截取到 "... [truncated" 之前
        trunc_pos = json_text.find('... [truncated]')
        if trunc_pos != -1:
            # 找到最后一个完整的產品对象
            last_asin = json_text.rfind('"ASIN"')
            if last_asin != -1:
                # 找到这个产品对象的结束
                product_end = json_text.find('}', last_asin)
                if product_end != -1:
                    # 找到这个产品后面的逗号或数组结束
                    next_comma = json_text.find(',', product_end)
                    next_bracket = json_text.find(']', product_end)
                    if next_bracket != -1 and (next_comma == -1 or next_bracket < next_comma):
                        json_text = json_text[:next_bracket + 1] + '}'
                    else:
                        json_text = json_text[:product_end + 1] + ']}'
    
    print(f"提取的 JSON 文本长度：{len(json_text)}")
    
    # 尝试解析 JSON
    try:
        data = json.loads(json_text)
        products_raw = data.get('Top100 产品', [])
        print(f"JSON 解析成功，获取 {len(products_raw)} 个产品")
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败：{e}")
        print(f"尝试使用正则表达式解析...")
        products_raw = []
        
        # 使用正则表达式提取产品
        product_pattern = r'\{"ASIN":"([^"]+?)","标题":"(.*?)","月销量":"([^"]+?)","月销额":"([^"]+?)","品牌":"([^"]+?)","所处类目排名":"(.*?)","价格":([\d.]+),"外包装尺寸":"([^"]+?)","产品分类":"([^"]+?)","上线天数":(\d+),"上线日期":"([^"]+?)","评论数":(\d+),"星级":([\d.]+),"卖家来源":"([^"]+?)","卖家":"([^"]+?)"\}'
        
        for match in re.finditer(product_pattern, json_text, re.DOTALL):
            try:
                products_raw.append({
                    "ASIN": match.group(1),
                    "标题": match.group(2),
                    "月销量": match.group(3),
                    "月销额": match.group(4),
                    "品牌": match.group(5),
                    "所处类目排名": match.group(6),
                    "价格": float(match.group(7)),
                    "外包装尺寸": match.group(8),
                    "产品分类": match.group(9),
                    "上线天数": int(match.group(10)),
                    "上线日期": match.group(11),
                    "评论数": int(match.group(12)),
                    "星级": float(match.group(13)),
                    "卖家来源": match.group(14),
                    "卖家": match.group(15)
                })
            except Exception as e:
                print(f"解析单个产品失败：{e}")
                continue
    
    # 转换为标准化格式
    products = []
    for p in products_raw:
        try:
            product = {
                "asin": p.get("ASIN", ""),
                "title": p.get("标题", ""),
                "monthly_sales": int(str(p.get("月销量", "0")).replace(',', '')) if p.get("月销量") else 0,
                "monthly_revenue": float(str(p.get("月销额", "0")).replace(',', '')) if p.get("月销额") else 0,
                "brand": p.get("品牌", ""),
                "category_rank": p.get("所处类目排名", ""),
                "price": float(p.get("价格", 0)) if p.get("价格") else 0,
                "size": p.get("外包装尺寸", ""),
                "product_type": p.get("产品分类", ""),
                "days_online": int(p.get("上线天数", 0)) if p.get("上线天数") else 0,
                "launch_date": p.get("上线日期", ""),
                "review_count": int(p.get("评论数", 0)) if p.get("评论数") else 0,
                "rating": float(p.get("星级", 0)) if p.get("星级") else 0,
                "seller_origin": p.get("卖家来源", ""),
                "seller": p.get("卖家", "")
            }
            products.append(product)
        except Exception as e:
            print(f"转换产品失败：{e}")
            continue
    
    print(f"成功解析 {len(products)} 个产品")
    
    # 保存解析后的数据
    output_dir = Path(r"D:\amazon-mcp\category-reports\Beauty_Personal_Care_US_20260304")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存 JSON 数据
    with open(output_dir / "products.json", 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    # 计算统计数据
    total_monthly_sales = sum(p['monthly_sales'] for p in products)
    total_monthly_revenue = sum(p['monthly_revenue'] for p in products)
    avg_price = sum(p['price'] for p in products) / len(products) if products else 0
    avg_rating = sum(p['rating'] for p in products) / len(products) if products else 0
    avg_reviews = sum(p['review_count'] for p in products) / len(products) if products else 0
    
    # 品牌分析
    brand_sales = {}
    for p in products:
        brand = p['brand']
        if brand not in brand_sales:
            brand_sales[brand] = {'sales': 0, 'revenue': 0, 'count': 0}
        brand_sales[brand]['sales'] += p['monthly_sales']
        brand_sales[brand]['revenue'] += p['monthly_revenue']
        brand_sales[brand]['count'] += 1
    
    # 按销量排序品牌
    top_brands = sorted(brand_sales.items(), key=lambda x: x[1]['sales'], reverse=True)[:10]
    
    # 卖家来源分析
    origin_count = {}
    for p in products:
        origin = p['seller_origin']
        origin_count[origin] = origin_count.get(origin, 0) + 1
    
    # 新品分析 (上线天数 < 90 天)
    new_products = [p for p in products if p['days_online'] < 90]
    new_product_ratio = len(new_products) / len(products) * 100 if products else 0
    
    # 低评论产品分析 (评论数 < 100)
    low_review_products = [p for p in products if p['review_count'] < 100]
    low_review_ratio = len(low_review_products) / len(products) * 100 if products else 0
    
    # 计算 CR3 (前 3 品牌销量占比)
    top3_sales = sum(b[1]['sales'] for b in top_brands[:3])
    cr3 = top3_sales / total_monthly_sales * 100 if total_monthly_sales else 0
    
    # 五维评分
    # 1. 市场规模 (20 分)
    monthly_revenue_total = total_monthly_revenue
    if monthly_revenue_total > 10000000:
        market_size_score = 20
    elif monthly_revenue_total > 5000000:
        market_size_score = 17
    elif monthly_revenue_total > 1000000:
        market_size_score = 14
    else:
        market_size_score = 10
    
    # 2. 增长潜力 (25 分) - 基于低评论产品占比
    if low_review_ratio > 40:
        growth_score = 22
    elif low_review_ratio > 20:
        growth_score = 18
    else:
        growth_score = 14
    
    # 3. 竞争烈度 (20 分) - 基于 CR3
    if cr3 < 30:
        competition_score = 18
    elif cr3 < 50:
        competition_score = 14
    else:
        competition_score = 8
    
    # 4. 进入壁垒 (20 分)
    amazon_count = sum(1 for p in products if p['seller'] == 'Amazon')
    amazon_ratio = amazon_count / len(products) * 100 if products else 0
    
    if amazon_ratio < 20 and new_product_ratio > 40:
        barrier_score = 20
    elif amazon_ratio < 20 or new_product_ratio > 40:
        barrier_score = 14
    else:
        barrier_score = 10
    
    # 5. 利润空间 (15 分)
    if avg_price > 300:
        profit_score = 12
    elif avg_price > 150:
        profit_score = 10
    elif avg_price > 50:
        profit_score = 7
    else:
        profit_score = 4
    
    total_score = market_size_score + growth_score + competition_score + barrier_score + profit_score
    
    # 评级
    if total_score >= 80:
        rating = "优秀"
        recommendation = "强烈推荐进入"
    elif total_score >= 70:
        rating = "良好"
        recommendation = "可以考虑进入"
    elif total_score >= 50:
        rating = "一般"
        recommendation = "谨慎进入"
    else:
        rating = "较差"
        recommendation = "不建议进入"
    
    # 生成 Markdown 报告
    report = f"""# Beauty & Personal Care 品类分析报告 - 美国站

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**数据日期**: {datetime.now().strftime('%Y-%m-%d')}
**分析产品数量**: {len(products)} (Top100)

---

## 一、五维评分总览

| 维度 | 分值 | 得分 | 评分标准 |
|------|------|------|----------|
| 市场规模 | 20 分 | **{market_size_score}分** | 月销额 ${monthly_revenue_total:,.0f} |
| 增长潜力 | 25 分 | **{growth_score}分** | 低评论产品占比 {low_review_ratio:.1f}% |
| 竞争烈度 | 20 分 | **{competition_score}分** | CR3 品牌集中度 {cr3:.1f}% |
| 进入壁垒 | 20 分 | **{barrier_score}分** | Amazon 占比 {amazon_ratio:.1f}%, 新品占比 {new_product_ratio:.1f}% |
| 利润空间 | 15 分 | **{profit_score}分** | 平均价格 ${avg_price:.2f} |
| **总分** | **100 分** | **{total_score}分** | **{rating}** - {recommendation} |

---

## 二、市场概况

### 核心指标

| 指标 | 数值 |
|------|------|
| Top100 月销总量 | {total_monthly_sales:,} 件 |
| Top100 月销总额 | ${total_monthly_revenue:,.2f} |
| 平均产品价格 | ${avg_price:.2f} |
| 平均产品评分 | {avg_rating:.2f} 星 |
| 平均评论数量 | {avg_reviews:,.0f} 条 |
| CR3 品牌集中度 | {cr3:.1f}% |

### 卖家来源分布

| 来源地 | 产品数量 | 占比 |
|--------|----------|------|
"""
    
    for origin, count in sorted(origin_count.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(products) * 100 if products else 0
        report += f"| {origin} | {count} | {pct:.1f}% |\n"
    
    report += f"""
---

## 三、Top 10 品牌分析

| 排名 | 品牌 | 产品数 | 月销量 | 月销额 | 销量占比 |
|------|------|--------|--------|--------|----------|
"""
    
    for i, (brand, data) in enumerate(top_brands, 1):
        sales_pct = data['sales'] / total_monthly_sales * 100 if total_monthly_sales else 0
        report += f"| {i} | {brand} | {data['count']} | {data['sales']:,} | ${data['revenue']:,.2f} | {sales_pct:.1f}% |\n"
    
    report += f"""
---

## 四、Top 20 热销产品

| 排名 | ASIN | 品牌 | 产品标题 | 价格 | 月销量 | 月销额 | 评论数 | 评分 |
|------|------|------|----------|------|--------|--------|--------|------|
"""
    
    for i, p in enumerate(products[:20], 1):
        title_short = p['title'][:40] + "..." if len(p['title']) > 40 else p['title']
        report += f"| {i} | {p['asin']} | {p['brand']} | {title_short} | ${p['price']:.2f} | {p['monthly_sales']:,} | ${p['monthly_revenue']:,.2f} | {p['review_count']:,} | {p['rating']:.1f} |\n"
    
    report += f"""
---

## 五、市场机会分析

### 1. 新品表现
- **新品数量** (上线<90 天): {len(new_products)} 个
- **新品占比**: {new_product_ratio:.1f}%
- **机会评估**: {"新品活跃，市场接受度高" if new_product_ratio > 20 else "新品较少，市场相对成熟"}

### 2. 低评论产品机会
- **低评论产品** (评论<100): {len(low_review_products)} 个
- **占比**: {low_review_ratio:.1f}%
- **机会评估**: {"大量新品有机会突围" if low_review_ratio > 30 else "头部效应明显"}

### 3. 价格区间分析
"""
    
    # 价格区间分析
    price_ranges = [
        (0, 10, "0-10 美元"),
        (10, 20, "10-20 美元"),
        (20, 30, "20-30 美元"),
        (30, 50, "30-50 美元"),
        (50, 100, "50-100 美元"),
        (100, 999999, "100 美元以上")
    ]
    
    report += "\n| 价格区间 | 产品数量 | 占比 | 平均销量 |\n"
    report += "|----------|----------|------|----------|\n"
    
    for low, high, label in price_ranges:
        range_products = [p for p in products if low <= p['price'] < high]
        if range_products:
            count = len(range_products)
            pct = count / len(products) * 100 if products else 0
            avg_sales = sum(p['monthly_sales'] for p in range_products) / count
            report += f"| {label} | {count} | {pct:.1f}% | {avg_sales:,.0f} |\n"
    
    report += f"""
---

## 六、关键发现与建议

### 市场特点
1. **品类规模**: 月销额 ${monthly_revenue_total:,.2f}, 属于 {"超大型" if monthly_revenue_total > 10000000 else "大型" if monthly_revenue_total > 5000000 else "中型"} 市场
2. **竞争格局**: CR3={cr3:.1f}%, {"市场集中度高，头部品牌优势明显" if cr3 > 50 else "市场竞争相对分散，新品牌有机会" if cr3 < 30 else "市场竞争中等"}
3. **价格水平**: 平均价格 ${avg_price:.2f}, {"高端市场" if avg_price > 50 else "中端市场" if avg_price > 20 else "大众市场"}
4. **Amazon 自营**: 占比 {amazon_ratio:.1f}%, {"Amazon 自营占主导，竞争压力大" if amazon_ratio > 30 else "Amazon 自营占比较低，第三方卖家有机会"}

### 进入建议
**综合评级**: {rating} ({total_score}分)
**建议**: {recommendation}

### 选品方向建议
1. **关注细分功能**: 从 Top 产品看，{"精华液 (Serum)" if any('Serum' in p['title'] for p in products[:10]) else "其他"} 是热门品类
2. **价格策略**: 主流价格带在 ${avg_price*0.8:.0f}-${avg_price*1.2:.0f} 区间
3. **品牌建设**: Top 品牌包括 {', '.join([b[0] for b in top_brands[:5]])}
4. **产品差异化**: 关注成分创新、功效细分、包装设计等差异化方向

---

## 七、数据说明

- 数据来源：Sorftime MCP API
- 分析站点：Amazon US
- 类目 NodeId: 7792528011
- 数据时效：可能存在 1-7 天延迟

---

*报告由自动化分析工具生成 | 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # 保存报告
    with open(output_dir / "report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 保存统计数据
    stats = {
        "category": "Beauty & Personal Care",
        "site": "US",
        "node_id": "7792528011",
        "data_date": datetime.now().strftime('%Y-%m-%d'),
        "total_products": len(products),
        "total_monthly_sales": total_monthly_sales,
        "total_monthly_revenue": total_monthly_revenue,
        "avg_price": avg_price,
        "avg_rating": avg_rating,
        "avg_reviews": avg_reviews,
        "cr3": cr3,
        "new_product_ratio": new_product_ratio,
        "low_review_ratio": low_review_ratio,
        "amazon_ratio": amazon_ratio,
        "scores": {
            "market_size": market_size_score,
            "growth": growth_score,
            "competition": competition_score,
            "barrier": barrier_score,
            "profit": profit_score,
            "total": total_score,
            "rating": rating,
            "recommendation": recommendation
        },
        "origin_distribution": origin_count,
        "top_brands": [(b[0], b[1]) for b in top_brands]
    }
    
    with open(output_dir / "statistics.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 分析完成 ===")
    print(f"报告保存至：{output_dir / 'report.md'}")
    print(f"产品数据：{output_dir / 'products.json'}")
    print(f"统计数据：{output_dir / 'statistics.json'}")
    print(f"\n=== 五维评分 ===")
    print(f"市场规模：{market_size_score}/20")
    print(f"增长潜力：{growth_score}/25")
    print(f"竞争烈度：{competition_score}/20")
    print(f"进入壁垒：{barrier_score}/20")
    print(f"利润空间：{profit_score}/15")
    print(f"总分：{total_score}/100 - {rating}")
    print(f"建议：{recommendation}")

else:
    print("无法解析 JSON 数据")
    print(f"文件内容预览：{content[:500]}")
