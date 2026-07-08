#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 Sorftime 评论 SSE 响应并生成差评分析"""

import json
import codecs
from datetime import datetime
from collections import defaultdict

# 读取原始 SSE 文件
sse_file = "D:/amazon-mcp/review-analysis-reports/B0DZCBYCNY_US_20260315/data/raw_reviews_sse.txt"

with open(sse_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取 SSE 数据中的 JSON
start_idx = content.find('data: ')
if start_idx == -1:
    print("错误: 未找到 SSE 数据格式")
    exit(1)

json_str = content[start_idx + 6:]  # 跳过 "data: "
try:
    data = json.loads(json_str)
except json.JSONDecodeError:
    # 如果第一个解析失败，尝试找到完整的 JSON 结束
    end_idx = json_str.find('}\n\n')
    if end_idx != -1:
        json_str = json_str[:end_idx + 1]
        data = json.loads(json_str)
    else:
        print("错误: 无法解析 JSON")
        exit(1)

# 提取评论文本
text = data['result']['content'][0]['text']

# 查找评论数组起始位置
reviews_start = text.find('[{')
if reviews_start == -1:
    print("错误: 未找到评论数组")
    exit(1)

reviews_json = text[reviews_start:]
reviews = json.loads(reviews_json)

print(f"总评论数: {len(reviews)}")

# 过滤 1-3 星评论
negative_reviews = [r for r in reviews if float(r.get('评星', 5)) <= 3.0]
print(f"差评数 (1-3星): {len(negative_reviews)}")

# 打印前5条评论以便检查
print("\n前5条差评:")
for i, review in enumerate(negative_reviews[:5]):
    print(f"\n[{i+1}] {review.get('评星', 'N/A')}星 - {review.get('标题', 'N/A')}")
    print(f"评论: {review.get('评论', 'N/A')[:200]}...")

# 保存解析后的评论
with open("D:/amazon-mcp/review-analysis-reports/B0DZCBYCNY_US_20260315/data/parsed_reviews.json", 'w', encoding='utf-8') as f:
    json.dump(negative_reviews, f, ensure_ascii=False, indent=2)

print(f"\n解析后的评论已保存到 parsed_reviews.json")
