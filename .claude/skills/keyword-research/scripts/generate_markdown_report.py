#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 报告生成器
"""

import os
from datetime import datetime


def generate_markdown_report(asin: str, site: str, keywords: list,
                            categorized: dict, output_dir: str,
                            product_info: dict = None) -> str:
    """
    生成 Markdown 分析报告

    Args:
        asin: 产品 ASIN
        site: 站点
        keywords: 完整关键词列表
        categorized: 分类后的关键词
        output_dir: 输出目录
        product_info: 产品信息（可选）

    Returns:
        str: 报告文件路径
    """
    report_file = os.path.join(output_dir, 'report.md')

    # 计算统计数据
    stats = calculate_statistics(keywords, categorized)

    # 生成报告内容
    content = build_report_content(asin, site, keywords, categorized,
                                   stats, product_info)

    # 写入文件
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return report_file


def calculate_statistics(keywords: list, categorized: dict) -> dict:
    """计算统计数据"""
    total_keywords = len(keywords)
    total_search_volume = sum(kw.get('search_volume', 0) for kw in keywords)
    total_cpc = sum(kw.get('cpc', 0) for kw in keywords)

    # 计算分类后的总关键词数（用于占比计算）
    total_categorized = sum(len(kw_list) for kw_list in categorized.values())

    # 分类统计
    category_stats = {}
    for category, kw_list in categorized.items():
        search_volumes = []
        for kw in kw_list:
            if isinstance(kw, dict):
                search_volumes.append(kw.get('search_volume', 0))
            elif isinstance(kw, str):
                # 在 keywords 中查找
                for original_kw in keywords:
                    if original_kw['keyword'].lower() == kw.lower():
                        search_volumes.append(original_kw.get('search_volume', 0))
                        break

        # 使用分类后的总数计算占比
        category_stats[category] = {
            'count': len(kw_list),
            'percentage': round(len(kw_list) / total_categorized * 100, 1) if total_categorized > 0 else 0,
            'total_search_volume': sum(search_volumes),
            'avg_search_volume': round(sum(search_volumes) / len(search_volumes), 0) if search_volumes else 0
        }

    return {
        'total_keywords': total_keywords,
        'total_search_volume': total_search_volume,
        'avg_cpc': round(total_cpc / total_keywords, 2) if total_keywords > 0 else 0,
        'category_stats': category_stats,
        'total_categorized': total_categorized
    }


def build_report_content(asin: str, site: str, keywords: list,
                        categorized: dict, stats: dict,
                        product_info: dict = None) -> str:
    """构建报告内容"""

    # 获取产品名称
    product_name = product_info.get('product_name', '') if product_info else ''
    if not product_name:
        # 从关键词中推断产品名称
        core_keywords = categorized.get('CORE', [])[:10]
        product_name = infer_product_name(core_keywords)

    content = f"""# 关键词调研分析报告

## 分析概览

| 项目 | 详情 |
|------|------|
| **ASIN** | [{asin}](https://www.amazon.com/dp/{asin}) |
| **产品名称** | {product_name} |
| **亚马逊站点** | {site} |
| **分析时间** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| **词库规模** | {stats.get('total_categorized', stats['total_keywords']):,} 个关键词（原始：{stats['total_keywords']:,}个） |
| **总搜索量** | {stats['total_search_volume']:,} |
| **平均 CPC** | ${stats['avg_cpc']:.2f} |

---

## 分类统计

| 分类 | 数量 | 占比 | 总搜索量 | 平均搜索量 | 应用策略 |
|------|------|------|----------|-----------|----------|
"""

    # 分类统计表格
    category_order = ['NEGATIVE', 'BRAND', 'MATERIAL', 'SCENARIO',
                     'ATTRIBUTE', 'FUNCTION', 'CORE', 'CHARACTER', 'OTHER']

    for cat in category_order:
        if cat not in stats['category_stats']:
            continue
        cat_stat = stats['category_stats'][cat]
        cat_name = get_category_display_name(cat)
        strategy = get_application_strategy(cat)

        content += f"| **{cat_name}** | {cat_stat['count']:,} | {cat_stat['percentage']}% | {cat_stat['total_search_volume']:,} | {cat_stat['avg_search_volume']:,} | {strategy} |\n"

    content += f"""

---

## 各分类 Top 关键词

### 核心产品词 (CORE)

{generate_top_keywords_table(categorized.get('CORE', []), keywords, limit=20)}

**应用建议**: 这些是产品的核心大词，流量大但竞争激烈。建议用于广泛匹配占领坑位，配合高预算和强Listing实力。

---

### 否定/敏感词 (NEGATIVE)

{generate_top_keywords_table(categorized.get('NEGATIVE', []), keywords, limit=30)}

**应用建议**: 以上 {len(categorized.get('NEGATIVE', []))} 个词与产品不相关，请直接添加为否定关键词（词组否定），避免浪费广告费。

---

### 品牌词 (BRAND)

{generate_top_keywords_table(categorized.get('BRAND', []), keywords, limit=20)}

**应用建议**: 竞品品牌词。如果做竞品狙击，可以单独创建广告组；否则直接添加为否定词。

---

### 材质词 (MATERIAL)

{generate_top_keywords_table(categorized.get('MATERIAL', []), keywords, limit=20)}

**应用建议**: 材质词转化率通常较高，建议用于精准匹配或词组匹配。

---

### 使用场景词 (SCENARIO)

{generate_top_keywords_table(categorized.get('SCENARIO', []), keywords, limit=25)}

**应用建议**: 按场景拆分广告组（如：entryway 组、bathroom 组），提高广告相关性。

---

### 属性修饰词 (ATTRIBUTE)

{generate_top_keywords_table(categorized.get('ATTRIBUTE', []), keywords, limit=25)}

**应用建议**: 长尾精准词，竞争小转化率高。建议用于精确匹配或词组匹配。

---

### 功能词 (FUNCTION)

{generate_top_keywords_table(categorized.get('FUNCTION', []), keywords, limit=20)}

**应用建议**: 功能相关词，用于广泛匹配扩流，但需注意过滤不相关的词。

---

## 广告投放策略建议

### 1. 否定关键词策略

直接复制 `negative_words.txt` 文件中的所有词，添加到广告活动的否定关键词列表中。

**否定数量**: {len(categorized.get('NEGATIVE', []))} 个
**操作方式**: 词组否定 (Phrase Match)

### 2. 精准匹配组（高转化）

**组合策略**: 材质词 + 属性修饰词

推荐组合（以产品为核心）:
"""

    # 生成精准组合建议
    material_kws = [get_kw_string(k) for k in categorized.get('MATERIAL', [])[:10]]
    attribute_kws = [get_kw_string(k) for k in categorized.get('ATTRIBUTE', [])[:15]]

    if material_kws and attribute_kws:
        content += f"""
| 材质 | 属性 | 组合示例 |
|------|------|----------|
| {' / '.join(material_kws[:3])} | {' / '.join(attribute_kws[:3])} | 组合使用 |

**投放方式**: 精确匹配 (Exact Match)
**预期**: 高转化率，低 CPC
"""

    content += f"""

### 3. 场景广告组

按使用场景拆分广告组，提高广告相关性:

"""

    # 场景词分组建议
    scenarios = categorized.get('SCENARIO', [])[:10]
    if scenarios:
        for i, scenario in enumerate(scenarios[:5], 1):
            scenario_kw = get_kw_string(scenario)
            content += f"- **场景组 {i}**: 围绕 `{scenario_kw}` 展开投放\n"

    content += f"""

**投放方式**: 词组匹配 (Phrase Match)
**预期**: 中等转化，中等流量

### 4. 广泛匹配组（扩流）

**关键词**: 核心产品词 + 功能词

推荐:
"""
    core_kws = [get_kw_string(k) for k in categorized.get('CORE', [])[:10]]
    function_kws = [get_kw_string(k) for k in categorized.get('FUNCTION', [])[:10]]

    for kw in core_kws[:5]:
        content += f"- `{kw}`\n"

    content += f"""

**投放方式**: 广泛匹配 (Broad Match)
**预期**: 大流量，需密切监控否定词

---

## 词库文件说明

| 文件 | 说明 | 用途 |
|------|------|------|
| `keywords.csv` | 完整词库（含分类、搜索量、CPC） | Excel 打开分析 |
| `keywords_negative.csv` | 否定词专用 | 直接复制到广告后台 |
| `keywords_brand.csv` | 品牌词列表 | 竞品分析或否定 |
| `keywords_material.csv` | 材质词 | 精准组投放 |
| `keywords_scenario.csv` | 场景词 | 场景组投放 |
| `keywords_attribute.csv` | 属性修饰词 | 长尾精准投放 |
| `keywords_function.csv` | 功能词 | 广泛匹配投放 |
| `keywords_core.csv` | 核心产品词 | 大词投放 |
| `negative_words.txt` | 否定词清单（每行一个） | 直接复制使用 |
| `brand_words.txt` | 品牌词清单 | 品牌分析 |

---

## 数据来源

本报告基于 **Sorftime Amazon 数据服务** 生成，数据采集自:
- 产品流量关键词分析
- 竞品关键词布局分析
- 类目核心关键词分析
- 长尾词智能扩展

数据更新频率: 实时更新
数据时效: 约 1-7 天延迟

---

*本报告由 Claude Code 自动生成 | 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    return content


def generate_top_keywords_table(keywords: list, all_keywords: list, limit: int = 20) -> str:
    """生成 Top 关键词表格"""
    if not keywords:
        return "*暂无数据*"

    # 构建搜索量和 CPC 映射
    search_map = {kw['keyword'].lower(): kw.get('search_volume', 0)
                 for kw in all_keywords}
    cpc_map = {kw['keyword'].lower(): kw.get('cpc', 0)
               for kw in all_keywords}

    # 排序
    sorted_kws = sorted(keywords,
                       key=lambda k: search_map.get(k.lower() if isinstance(k, str) else k.get('keyword', '').lower(), 0),
                       reverse=True)[:limit]

    table = "| 排名 | 关键词 | 搜索量 | CPC |\n|------|--------|--------|-----|\n"

    for i, kw in enumerate(sorted_kws, 1):
        if isinstance(kw, str):
            keyword = kw
            search_vol = search_map.get(kw.lower(), 0)
            cpc = cpc_map.get(kw.lower(), 0)
        else:
            keyword = kw.get('keyword', '')
            search_vol = kw.get('search_volume', 0)
            cpc = kw.get('cpc', 0)

        table += f"| {i} | `{keyword}` | {search_vol:,} | ${cpc:.2f} |\n"

    return table


def get_kw_string(kw) -> str:
    """获取关键词字符串"""
    if isinstance(kw, str):
        return kw
    return kw.get('keyword', '')


def get_category_display_name(category: str) -> str:
    """获取分类显示名称"""
    names = {
        'NEGATIVE': '否定/敏感词',
        'BRAND': '品牌词',
        'MATERIAL': '材质词',
        'SCENARIO': '使用场景词',
        'ATTRIBUTE': '属性修饰词',
        'FUNCTION': '功能词',
        'CORE': '核心产品词',
        'CHARACTER': '角色词',
        'OTHER': '其他'
    }
    return names.get(category, category)


def get_application_strategy(category: str) -> str:
    """获取应用策略"""
    strategies = {
        'NEGATIVE': '直接否定',
        'BRAND': '竞品打法/否定',
        'MATERIAL': '精准匹配',
        'SCENARIO': '场景分组',
        'ATTRIBUTE': '长尾精准',
        'FUNCTION': '广泛匹配',
        'CORE': '大词投放',
        'OTHER': '补充埋词'
    }
    return strategies.get(category, '')


def infer_product_name(core_keywords: list) -> str:
    """从核心关键词推断产品名称"""
    if not core_keywords:
        return "Unknown Product"

    # 取第一个核心词
    first_kw = get_kw_string(core_keywords[0])

    # 简单的名称推断
    if first_kw:
        # 首字母大写
        return first_kw.title()

    return "Unknown Product"


def main():
    """测试入口"""
    import sys
    import json

    if len(sys.argv) < 5:
        print("用法: python generate_markdown_report.py <asin> <site> <keywords.json> <categorized.json> [output_dir]")
        sys.exit(1)

    asin = sys.argv[1]
    site = sys.argv[2]
    keywords_file = sys.argv[3]
    categorized_file = sys.argv[4]
    output_dir = sys.argv[5] if len(sys.argv) > 5 else '.'

    with open(keywords_file, 'r', encoding='utf-8') as f:
        keywords = json.load(f)

    with open(categorized_file, 'r', encoding='utf-8') as f:
        categorized = json.load(f)

    report_file = generate_markdown_report(asin, site, keywords, categorized, output_dir)
    print(f"✓ 报告已生成: {report_file}")


if __name__ == "__main__":
    main()
