#!/usr/bin/env python3
"""
亚马逊评论多维度分析脚本 v2.0
增加服务维度分析：售前/售后/物流/退换货
"""

import json
import codecs
import re
from datetime import datetime
from collections import defaultdict

def classify_review_enhanced(review):
    """
    6维度评论分类
    """
    title = review.get('标题', '').lower()
    comment = review.get('评论', '').lower()
    text = f"{title} {comment}"

    # === 服务维度（优先检查）===
    # 服务/物流问题关键词
    service_keywords = {
        # 物流发货
        'shipping': ['shipping', 'delivery', 'arrived', 'package', 'packaging'],
        # 退换货
        'return': ['return', 'refund', 'exchange', 'replace', 'replacement'],
        # 客服
        'service': ['customer service', 'support', 'seller', 'vendor'],
        # 配件问题
        'missing': ['missing', 'no cord', 'no cable', 'no charger', 'no ear tip', 'no foam', 'no accessory'],
        # 二手/瑕疵品
        'used': ['used', 'gross', 'dirty', 'scratch', 'ear wax', 'dirt', 'opened'],
        # 发错货
        'wrong': ['wrong item', 'wrong color', 'wrong size', 'sent wrong'],
    }

    # 检查服务维度
    for category, keywords in service_keywords.items():
        if any(keyword in text for keyword in keywords):
            # 进一步判断是正面还是负面
            if any(word in text for word in ['great service', 'good service', 'helpful', 'quick refund']):
                return "服务-好评"
            return "服务/物流问题"

    # === 产品质量维度（原有5类）===
    # 结构/组装问题
    structure_keywords = [
        'broken', 'broke', 'crack', 'fall apart', 'fell apart',
        'fall out', 'won\'t stay', 'won\'t stay in', 'keep falling',
        'charging prong', 'prong', 'corrode', 'corrosion',
        'missing parts', 'defective', 'doa', 'dead on arrival'
    ]
    if any(word in text for word in structure_keywords):
        return "结构/组装问题"

    # 电子模块故障
    electronic_keywords = [
        'charging', 'charge', 'battery', 'battery life', 'won\'t charge',
        'not charging', 'stop charging', 'drain', 'dead',
        'bluetooth', 'connect', 'disconnect', 'connection', 'pair', 'pairing',
        'mic', 'microphone', 'mic stop', 'people can\'t hear',
        'led', 'power display', 'stop working', 'stopped working',
        'won\'t work', 'doesn\'t work', 'not work', 'defective'
    ]
    if any(word in text for word in electronic_keywords):
        return "电子模块故障"

    # 设计/功能缺陷
    design_keywords = [
        'touch', 'sensor', 'sensitive', 'pause', 'accidental',
        'delay', 'lag', 'audio delay', 'video delay', 'sync',
        'sound quality', 'audio quality', 'sound is', 'bass', 'treble', 'muddy', 'tinny', 'hollow',
        'volume', 'loud', 'quiet', 'can\'t hear',
        'fit', 'comfortable', 'uncomfortable', 'hurt', 'pain', 'ear canal',
        'size', 'too big', 'too small', 'too large',
        'waterproof', 'water', 'swim', 'ipx', 'sweat'
    ]
    if any(word in text for word in design_keywords):
        return "设计/功能缺陷"

    # 外观/材质问题
    appearance_keywords = [
        'scratch', 'scratched', 'dent', 'mark',
        'used', 'dirty', 'gross', 'ear wax', 'dust',
        'smell', 'odor', 'burning', 'chemical smell',
        'cheap', 'flimsy', 'plastic', 'quality feel'
    ]
    if any(word in text for word in appearance_keywords):
        return "外观/材质问题"

    # 描述不符
    description_keywords = [
        'not as described', 'different than', 'different from',
        'expect', 'expected', 'advertised', 'ad',
        '5.0', '5.1', '5.2', '5.3', '5.4', 'bluetooth version',
        '60 hour', '60h', 'battery life claim', 'misleading'
    ]
    if any(word in text for word in description_keywords):
        return "描述不符"

    # 默认归类
    return "其他问题"


def extract_service_issues(reviews):
    """
    提取服务维度的具体问题统计
    """
    service_issues = {
        '物流延迟/包装差': 0,
        '退换货困难': 0,
        '客服响应慢/态度差': 0,
        '配件缺失': 0,
        '收到二手/瑕疵品': 0,
        '发错货': 0,
        '客服好评': 0
    }

    for review in reviews:
        text = f"{review.get('标题', '').lower()} {review.get('评论', '').lower()}"

        if 'missing' in text or 'no cord' in text or 'no cable' in text or 'no ear tip' in text:
            service_issues['配件缺失'] += 1
        elif 'used' in text or 'ear wax' in text or 'dirty' in text or 'scratch' in text:
            if 'customer service was great' not in text:
                service_issues['收到二手/瑕疵品'] += 1
        elif 'return' in text and ('difficult' in text or 'challenge' in text or 'hard' in text):
            service_issues['退换货困难'] += 1
        elif 'great service' in text or 'good service' in text or 'helpful' in text:
            service_issues['客服好评'] += 1
        elif 'shipping' in text or 'delivery' in text or 'package' in text:
            service_issues['物流延迟/包装差'] += 1
        elif 'wrong' in text and ('item' in text or 'color' in text or 'size' in text):
            service_issues['发错货'] += 1
        elif 'customer service' in text or 'seller' in text:
            service_issues['客服响应慢/态度差'] += 1

    return {k: v for k, v in service_issues.items() if v > 0}


def analyze_reviews(reviews_data_file, output_file):
    """
    主分析函数
    """
    # 读取原始评论数据
    with open(reviews_data_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析 SSE 格式
    start_idx = content.find('data: ') + 6
    json_str = content[start_idx:]
    data = json.loads(json_str)

    # 提取评论文本
    text = data['result']['content'][0]['text']

    # 查找评论数组
    reviews_start = text.find('[{')
    reviews_json = text[reviews_start:]
    reviews = json.loads(reviews_json)

    # 过滤差评
    negative_reviews = [r for r in reviews if float(r.get('评星', 5)) <= 3.0]

    print(f"总评论数: {len(reviews)}")
    print(f"差评数 (1-3星): {len(negative_reviews)}")

    # 6维度分类
    pain_points = {
        "电子模块故障": [],
        "结构/组装问题": [],
        "设计/功能缺陷": [],
        "外观/材质问题": [],
        "描述不符": [],
        "服务/物流问题": [],
        "服务-好评": [],
        "其他问题": []
    }

    # 分类统计
    for review in negative_reviews:
        category = classify_review_enhanced(review)
        pain_points[category].append(review)

    # 输出分类统计
    print("\n" + "="*60)
    print("6维度差评分类统计:")
    print("="*60)

    for category, reviews in sorted(pain_points.items(), key=lambda x: len(x[1]), reverse=True):
        if reviews:
            percentage = len(reviews) / len(negative_reviews) * 100
            severity = "高" if category in ["电子模块故障", "结构/组装问题", "服务/物流问题"] else "中"
            print(f"{category:20s}: {len(reviews):3d}条 ({percentage:5.1f}%) | 严重程度: {severity}")

    # 提取服务维度细分统计
    print("\n" + "="*60)
    print("服务维度细分统计:")
    print("="*60)

    service_details = extract_service_issues(negative_reviews)
    for issue, count in sorted(service_details.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(negative_reviews) * 100
        print(f"{issue:20s}: {count:3d}条 ({percentage:5.1f}%)")

    return pain_points, service_details


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        reviews_file = sys.argv[1]
    else:
        reviews_file = "D:/amazon-mcp/review-analysis-reports/B09DT48V16_US_20260315/data/raw_reviews_sse.txt"

    analyze_reviews(reviews_file, "output.json")
