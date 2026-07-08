#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 词库生成器
"""

import os
import csv
from datetime import datetime


def generate_csv_files(keywords: list, categorized: dict, output_dir: str) -> list:
    """
    生成所有 CSV 文件

    Args:
        keywords: 完整关键词列表，每个包含分类信息
        categorized: 分类后的关键词字典 {category: [keywords...]}
        output_dir: 输出目录

    Returns:
        list: 生成的文件路径列表
    """
    generated_files = []

    # 1. 生成完整关键词词库 CSV
    full_csv = os.path.join(output_dir, 'keywords.csv')
    generate_full_csv(keywords, categorized, full_csv)
    generated_files.append(full_csv)

    # 2. 生成分类 CSV 文件
    for category, kw_list in categorized.items():
        if not kw_list:
            continue

        category_name = category.lower()
        category_csv = os.path.join(output_dir, f'keywords_{category_name}.csv')
        generate_category_csv(kw_list, category_csv, keywords)
        generated_files.append(category_csv)

    # 3. 生成否定词清单（可直接复制）
    negative_txt = os.path.join(output_dir, 'negative_words.txt')
    generate_negative_list(categorized.get('NEGATIVE', []), negative_txt)
    generated_files.append(negative_txt)

    # 4. 生成品牌词清单
    brand_txt = os.path.join(output_dir, 'brand_words.txt')
    generate_simple_list(categorized.get('BRAND', []), brand_txt)
    generated_files.append(brand_txt)

    # 5. 生成分类统计 JSON
    stats_json = os.path.join(output_dir, 'categorized_summary.json')
    generate_category_stats(keywords, categorized, stats_json)
    generated_files.append(stats_json)

    return generated_files


def generate_full_csv(keywords: list, categorized: dict, output_file: str):
    """
    生成完整关键词 CSV 文件

    CSV 格式:
    keyword,category,subcategory,search_volume,cpc,competition,application
    """
    # 建立分类映射
    category_map = {}
    for category, kw_list in categorized.items():
        for kw in kw_list:
            normalized = kw.lower().strip() if isinstance(kw, str) else kw.get('keyword', '').lower().strip()
            category_map[normalized] = category

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'keyword',
            'category',
            'subcategory',
            'search_volume',
            'cpc',
            'competition',
            'application'
        ])

        for kw_data in keywords:
            keyword = kw_data.get('keyword', '')
            normalized = keyword.lower().strip()

            category = category_map.get(normalized, 'UNCATEGORIZED')
            subcategory = get_subcategory_name(category)
            application = get_application_strategy(category)

            writer.writerow([
                keyword,
                category,
                subcategory,
                kw_data.get('search_volume', 0),
                kw_data.get('cpc', 0),
                kw_data.get('competition', 'unknown'),
                application
            ])

    print(f"  ✓ 完整词库: {output_file}")


def generate_category_csv(keywords: list, output_file: str, all_keywords: list = None):
    """生成单个分类的 CSV 文件"""
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['keyword', 'search_volume', 'cpc', 'competition'])

        for kw in keywords:
            if isinstance(kw, str):
                # 从 all_keywords 中查找数据
                if all_keywords:
                    for original_kw in all_keywords:
                        if original_kw['keyword'].lower() == kw.lower():
                            writer.writerow([
                                kw,
                                original_kw.get('search_volume', 0),
                                original_kw.get('cpc', 0),
                                original_kw.get('competition', 'unknown')
                            ])
                            break
                    else:
                        writer.writerow([kw, 0, 0, 'unknown'])
                else:
                    writer.writerow([kw, 0, 0, 'unknown'])
            elif isinstance(kw, dict):
                writer.writerow([
                    kw.get('keyword', ''),
                    kw.get('search_volume', 0),
                    kw.get('cpc', 0),
                    kw.get('competition', 'unknown')
                ])


def generate_negative_list(negative_keywords: list, output_file: str):
    """生成否定词清单（每行一个，可直接复制）"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for kw in negative_keywords:
            if isinstance(kw, str):
                f.write(f"{kw}\n")
            elif isinstance(kw, dict):
                kw_str = kw.get('keyword', kw)
                f.write(f"{kw_str}\n")

    count = len(negative_keywords)
    print(f"  ✓ 否定词清单: {output_file} ({count} 个)")


def generate_simple_list(keywords: list, output_file: str):
    """生成简单词列表（每行一个）"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for kw in keywords:
            if isinstance(kw, str):
                f.write(f"{kw}\n")
            elif isinstance(kw, dict):
                kw_str = kw.get('keyword', kw)
                f.write(f"{kw_str}\n")


def generate_category_stats(all_keywords: list, categorized: dict, output_file: str):
    """生成分类统计 JSON"""
    stats = {
        'generated_at': datetime.now().isoformat(),
        'total_keywords': sum(len(v) for v in categorized.values()),
        'categories': {}
    }

    # 构建搜索量映射
    search_map = {kw['keyword'].lower(): kw.get('search_volume', 0)
                 for kw in all_keywords}

    for category, keywords in categorized.items():
        # 计算搜索量统计
        search_volumes = []
        for kw in keywords:
            if isinstance(kw, dict):
                search_volumes.append(kw.get('search_volume', 0))
            elif isinstance(kw, str):
                search_volumes.append(search_map.get(kw.lower(), 0))

        total_volume = sum(search_volumes)
        avg_volume = round(total_volume / len(search_volumes), 0) if search_volumes else 0

        stats['categories'][category] = {
            'count': len(keywords),
            'percentage': round(len(keywords) / stats['total_keywords'] * 100, 1) if stats['total_keywords'] > 0 else 0,
            'total_search_volume': total_volume,
            'avg_search_volume': avg_volume
        }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"  ✓ 分类统计: {output_file}")


def get_subcategory_name(category: str) -> str:
    """获取分类的中文名称"""
    names = {
        'NEGATIVE': '否定/敏感词',
        'BRAND': '品牌词',
        'MATERIAL': '材质词',
        'SCENARIO': '使用场景词',
        'ATTRIBUTE': '属性修饰词',
        'FUNCTION': '功能词',
        'CORE': '核心产品词',
        'OTHER': '其他',
        'CHARACTER': '角色词',
        'UNCATEGORIZED': '未分类'
    }
    return names.get(category, category)


def get_application_strategy(category: str) -> str:
    """获取分类的应用策略"""
    strategies = {
        'NEGATIVE': '直接添加为否定关键词',
        'BRAND': '竞品打法或添加为否定词',
        'MATERIAL': '精准词组匹配',
        'SCENARIO': '按场景拆分广告组',
        'ATTRIBUTE': '长尾精准匹配',
        'FUNCTION': '广泛匹配扩流',
        'CORE': '大词投放占领坑位',
        'OTHER': '补充埋词',
        'CHARACTER': '角色相关投放',
        'UNCATEGORIZED': '需人工复核'
    }
    return strategies.get(category, '')


# 导入 json 模块
import json


def main():
    """测试入口"""
    import sys

    if len(sys.argv) < 4:
        print("用法: python csv_generator.py <output_dir> <keywords.json> <categorized.json>")
        sys.exit(1)

    output_dir = sys.argv[1]
    keywords_file = sys.argv[2]
    categorized_file = sys.argv[3]

    with open(keywords_file, 'r', encoding='utf-8') as f:
        keywords = json.load(f)

    with open(categorized_file, 'r', encoding='utf-8') as f:
        categorized = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    files = generate_csv_files(keywords, categorized, output_dir)

    print(f"\n生成的文件:")
    for f in files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
