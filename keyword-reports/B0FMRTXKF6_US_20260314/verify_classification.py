#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证分类映射"""

import json

# 读取原始关键词
with open('keywords_raw.json', 'r', encoding='utf-8') as f:
    keywords = json.load(f)

# 读取分类结果
with open('categorized_result.json', 'r', encoding='utf-8') as f:
    categorized = json.load(f)

# 构建分类映射
category_map = {}
for category, kw_list in categorized.items():
    for kw in kw_list:
        category_map[kw.lower()] = category

# 验证每个关键词是否都被正确分类
print('验证分类映射:')
print('=' * 60)

for kw in keywords:
    keyword = kw['keyword']
    normalized = keyword.lower()
    category = category_map.get(normalized, 'UNCATEGORIZED')

    # 只显示前10个和后10个
    idx = keywords.index(kw)
    if idx < 10 or idx >= len(keywords) - 5:
        print(f'{keyword:45} -> {category}')

# 统计
print('=' * 60)
print('分类统计:')
for cat in categorized:
    print(f'  {cat}: {len(categorized[cat])} 个')

uncategorized_count = sum(1 for kw in keywords if kw['keyword'].lower() not in category_map)
print(f'  UNCATEGORIZED: {uncategorized_count} 个')

# 检查是否有重复分类
print('=' * 60)
print('检查重复分类:')
all_categorized = set()
for cat, kw_list in categorized.items():
    for kw in kw_list:
        if kw.lower() in all_categorized:
            print(f'警告: 关键词 "{kw}" 被重复分类!')
        all_categorized.add(kw.lower())

print('验证完成!')
