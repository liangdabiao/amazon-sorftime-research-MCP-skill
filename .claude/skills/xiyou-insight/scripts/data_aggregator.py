#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西柚洞察数据聚合器

合并多个ASIN/关键词数据，进行数据清洗和格式化

使用方式:
    from scripts.data_aggregator import DataAggregator
    aggregator = DataAggregator()
    aggregated = aggregator.aggregate(raw_data)
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class DataAggregator:
    """数据聚合器"""

    def aggregate(self, raw_data: Dict[str, Any], scenario: str = None) -> Dict[str, Any]:
        """
        聚合数据

        Args:
            raw_data: 原始MCP响应数据
            scenario: 场景名称

        Returns:
            dict: 聚合后的结构化数据
        """
        result = {
            'metadata': {
                'scenario': scenario or 'unknown',
                'aggregated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

        if raw_data.get('asin_info'):
            result['asin_info'] = self._process_asin_info(raw_data['asin_info'])

        if raw_data.get('asin_keywords'):
            result['keywords'] = self._process_keywords(raw_data['asin_keywords'])

        if raw_data.get('asin_traffic'):
            result['traffic'] = self._process_traffic(raw_data['asin_traffic'])

        if raw_data.get('asin_traffic_trends'):
            result['traffic_trends'] = self._process_traffic_trends(raw_data['asin_traffic_trends'])

        if raw_data.get('asin_ad_change_trends'):
            result['ad_trends'] = self._process_ad_trends(raw_data['asin_ad_change_trends'])

        if raw_data.get('asin_variations'):
            result['variations'] = self._process_variations(raw_data['asin_variations'])

        if raw_data.get('keyword_info'):
            result['keyword_info'] = self._process_keyword_info(raw_data['keyword_info'])

        if raw_data.get('keyword_asin_analysis'):
            result['keyword_competition'] = self._process_keyword_competition(raw_data['keyword_asin_analysis'])

        if raw_data.get('insights'):
            result['insights'] = raw_data['insights']

        return result

    def _process_asin_info(self, asin_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理ASIN基础信息"""
        result = {}
        for item in asin_info:
            asin = item.get('asin', 'unknown')
            result[asin] = {
                'title': item.get('title', ''),
                'price': item.get('price', ''),
                'currency': item.get('currency', ''),
                'stars': item.get('stars', ''),
                'ratings': item.get('ratings', ''),
                'url': item.get('url', ''),
                'image': item.get('image', '')
            }
        return result

    def _process_keywords(self, keywords_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """处理关键词数据"""
        result = {}
        for asin, keywords in keywords_data.items():
            processed = []
            for kw in keywords:
                processed.append({
                    'keyword': kw.get('keyword', ''),
                    'natural_rank': kw.get('natural_rank', ''),
                    'ad_rank': kw.get('ad_rank', ''),
                    'traffic': kw.get('traffic', ''),
                    'traffic_share': kw.get('traffic_share', ''),
                    'traffic_growth': kw.get('traffic_growth', ''),
                    'search_volume': kw.get('search_volume', ''),
                    'competitive_difficulty': kw.get('competitive_difficulty', ''),
                    'cpc': kw.get('cpc', '')
                })
            result[asin] = processed
        return result

    def _process_traffic(self, traffic_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理流量数据"""
        result = {}
        for item in traffic_data:
            asin = item.get('asin', 'unknown')
            result[asin] = {
                'natural_traffic': item.get('natural_traffic', 0),
                'ad_traffic': item.get('ad_traffic', 0),
                'total_traffic': item.get('total_traffic', 0),
                'keyword_count': item.get('keyword_count', 0),
                'natural_traffic_share': item.get('natural_traffic_share', 0),
                'ad_traffic_share': item.get('ad_traffic_share', 0),
                'traffic_growth': item.get('traffic_growth', 0)
            }
        return result

    def _process_traffic_trends(self, trends_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """处理流量趋势数据"""
        result = {}
        for asin, trends in trends_data.items():
            processed = []
            for day in trends:
                processed.append({
                    'date': day.get('date', ''),
                    'natural_traffic': day.get('natural_traffic', 0),
                    'ad_traffic': day.get('ad_traffic', 0),
                    'total_traffic': day.get('total_traffic', 0)
                })
            result[asin] = processed
        return result

    def _process_ad_trends(self, ad_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """处理广告趋势数据"""
        result = {}
        for asin, data in ad_data.items():
            result[asin] = {
                'daily_changes': data.get('daily_changes', []),
                'summary': data.get('summary', {})
            }
        return result

    def _process_variations(self, var_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """处理变体数据"""
        result = {}
        for asin, data in var_data.items():
            result[asin] = {
                'parent_asin': data.get('parent_asin', ''),
                'children': data.get('children', []),
                'variation_data': data.get('variation_data', {})
            }
        return result

    def _process_keyword_info(self, keyword_info: Any) -> Dict[str, Any]:
        """处理关键词信息"""
        result = {}
        if isinstance(keyword_info, dict):
            for keyword, item in keyword_info.items():
                result[keyword] = {
                    'keyword': keyword,
                    'weekly_search_volume': item.get('weekly_search_volume', 0),
                    'search_frequency_rank': item.get('search_frequency_rank', 0),
                    'competitive_difficulty': item.get('competitive_difficulty', 0),
                    'cpc': item.get('cost_per_click', item.get('cpc', 0)),
                    'click_conversion_rate': item.get('click_conversion_rate', 0),
                    'natural_scroll_rate': item.get('natural_scroll_rate', 0)
                }
        elif isinstance(keyword_info, list):
            for item in keyword_info:
                keyword = item.get('keyword', 'unknown')
                result[keyword] = {
                    'keyword': keyword,
                    'weekly_search_volume': item.get('weekly_search_volume', 0),
                    'search_frequency_rank': item.get('search_frequency_rank', 0),
                    'competitive_difficulty': item.get('competitive_difficulty', 0),
                    'cpc': item.get('cost_per_click', item.get('cpc', 0)),
                    'click_conversion_rate': item.get('click_conversion_rate', 0),
                    'natural_scroll_rate': item.get('natural_scroll_rate', 0)
                }
        return result

    def _process_keyword_competition(self, competition_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """处理关键词竞争数据"""
        result = {}
        for keyword, asins in competition_data.items():
            processed = []
            for item in asins:
                processed.append({
                    'asin': item.get('asin', ''),
                    'title': item.get('title', ''),
                    'price': item.get('price', ''),
                    'stars': item.get('stars', ''),
                    'natural_rank': item.get('natural_rank', ''),
                    'ad_rank': item.get('ad_rank', ''),
                    'traffic': item.get('traffic', ''),
                    'traffic_share': item.get('traffic_share', '')
                })
            result[keyword] = processed
        return result

    def find_traffic_gaps(self, own_keywords: List[str], competitor_keywords: Dict[str, List[Dict[str, Any]]],
                          keyword_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        找出流量缺口

        Args:
            own_keywords: 自身关键词列表
            competitor_keywords: 竞品关键词数据
            keyword_info: 关键词信息

        Returns:
            list: 流量缺口列表
        """
        own_set = set(k.lower() for k in own_keywords)
        gaps = []

        for competitor, keywords in competitor_keywords.items():
            for kw in keywords:
                keyword = kw.get('keyword', '').lower()
                if keyword not in own_set:
                    info = keyword_info.get(keyword, {})
                    gaps.append({
                        'keyword': keyword,
                        'competitor': competitor,
                        'competitor_rank': kw.get('natural_rank', '-'),
                        'own_rank': '-',
                        'search_volume': info.get('weekly_search_volume', 0),
                        'competitive_difficulty': info.get('competitive_difficulty', 0),
                        'cpc': info.get('cpc', 0),
                        'priority': self._calculate_priority(info)
                    })

        gaps.sort(key=lambda x: (-x['search_volume'], x['competitive_difficulty']))
        return gaps

    def _calculate_priority(self, keyword_info: Dict[str, Any]) -> str:
        """计算优先级"""
        search_volume = keyword_info.get('weekly_search_volume', 0)
        difficulty = keyword_info.get('competitive_difficulty', 0)

        if search_volume > 50000 and difficulty < 60:
            return 'high'
        elif search_volume > 10000 and difficulty < 70:
            return 'medium'
        else:
            return 'low'

    def categorize_keywords(self, keywords: List[Dict[str, Any]], relevance_threshold: float = 0.7) -> Dict[str, List[Dict[str, Any]]]:
        """
        按相关性分类关键词

        Args:
            keywords: 关键词列表
            relevance_threshold: 相关性阈值

        Returns:
            dict: 分类后的关键词
        """
        categorized = {
            '强相关': [],
            '高相关': [],
            '中相关': [],
            '低相关': [],
            '极低相关': []
        }

        for kw in keywords:
            relevance = kw.get('relevance', 0.5)
            if relevance >= 0.9:
                categorized['强相关'].append(kw)
            elif relevance >= 0.7:
                categorized['高相关'].append(kw)
            elif relevance >= 0.5:
                categorized['中相关'].append(kw)
            elif relevance >= 0.3:
                categorized['低相关'].append(kw)
            else:
                categorized['极低相关'].append(kw)

        return categorized

    def save_raw_data(self, raw_data: Dict[str, Any], output_dir: str) -> str:
        """
        保存原始数据

        Args:
            raw_data: 原始数据
            output_dir: 输出目录

        Returns:
            str: 输出目录路径
        """
        raw_dir = os.path.join(output_dir, 'raw')
        os.makedirs(raw_dir, exist_ok=True)

        for key, value in raw_data.items():
            if value:
                filename = f"{key}.json"
                filepath = os.path.join(raw_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(value, f, ensure_ascii=False, indent=2)

        return raw_dir


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python data_aggregator.py <raw_data_json_path> <output_dir>")
        sys.exit(1)

    data_path = sys.argv[1]
    output_dir = sys.argv[2]

    with open(data_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    aggregator = DataAggregator()
    aggregated = aggregator.aggregate(raw_data)

    output_file = os.path.join(output_dir, 'data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(aggregated, f, ensure_ascii=False, indent=2)

    aggregator.save_raw_data(raw_data, output_dir)

    print(f"✅ 数据聚合完成: {output_file}")
