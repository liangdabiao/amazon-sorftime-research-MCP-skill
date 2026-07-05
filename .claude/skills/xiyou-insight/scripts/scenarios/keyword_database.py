from .base import BaseScenario
from typing import Dict, List, Any


class KeywordDatabaseScenario(BaseScenario):
    """高效搭建关键词库"""

    NAME = "keyword_database"
    DESCRIPTION = "高效搭建关键词库"
    REQUIRED_PARAMS = ['site']

    def get_mcp_tools(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        site = params['site']
        competitor_asins = params.get('competitor_asins', [])
        core_keywords = params.get('core_keywords', [])

        if isinstance(competitor_asins, str):
            competitor_asins = [competitor_asins]
        if isinstance(core_keywords, str):
            core_keywords = [core_keywords]

        tools = []

        if competitor_asins:
            tools.append({
                'tool_name': 'get_asin_info',
                'arguments': {
                    'asins': competitor_asins,
                    'country': site,
                    'intent_summary': '关键词库搭建：获取竞品ASIN基础信息'
                }
            })

            for asin in competitor_asins[:5]:
                tools.append({
                    'tool_name': 'get_asin_keywords',
                    'arguments': {
                        'asin': asin,
                        'country': site,
                        'page': 1,
                        'page_size': 100,
                        'sort_field': 'traffic',
                        'sort_order': 'desc',
                        'intent_summary': f'关键词库搭建：反查{asin}流量词'
                    }
                })

        if core_keywords:
            tools.append({
                'tool_name': 'get_keyword_info',
                'arguments': {
                    'keywords': core_keywords[:20],
                    'country': site,
                    'intent_summary': '关键词库搭建：获取核心关键词基础指标'
                }
            })

            for keyword in core_keywords[:5]:
                tools.append({
                    'tool_name': 'get_keyword_asin_analysis',
                    'arguments': {
                        'keyword': keyword,
                        'country': site,
                        'page': 1,
                        'page_size': 30,
                        'sort_field': 'traffic',
                        'sort_order': 'desc',
                        'intent_summary': f'关键词库搭建：分析关键词{keyword}竞争格局'
                    }
                })

                tools.append({
                    'tool_name': 'get_keyword_aba_trends',
                    'arguments': {
                        'keywords': [keyword],
                        'country': site,
                        'start_week': (self.current_date - timedelta(days=90)).strftime('%Y-%m-%d'),
                        'end_week': self.default_end_date,
                        'intent_summary': f'关键词库搭建：获取{keyword}搜索量趋势'
                    }
                })

        return tools

    def aggregate_data(self, raw_data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        site = params['site']
        competitor_asins = params.get('competitor_asins', [])
        if isinstance(competitor_asins, str):
            competitor_asins = [competitor_asins]

        data = {
            'title': f'关键词库搭建 - {site}',
            'target': site,
            'site': site,
            'scenario': '关键词库'
        }

        all_keywords = []
        keyword_sources = {}

        if raw_data.get('get_asin_info'):
            data['asin_info'] = self._process_asin_info(raw_data['get_asin_info'])

        if raw_data.get('get_asin_keywords'):
            keyword_results = raw_data['get_asin_keywords']
            if not isinstance(keyword_results, list):
                keyword_results = [keyword_results]

            for i, asin in enumerate(competitor_asins):
                if i < len(keyword_results):
                    keywords = self._extract_asin_keywords(keyword_results[i])
                    keyword_sources[asin] = [kw['keyword'] for kw in keywords]
                    all_keywords.extend(keywords)

        if raw_data.get('get_keyword_info'):
            keyword_info = self._process_keyword_info(raw_data['get_keyword_info'])
            for kw in all_keywords:
                keyword_name = kw['keyword']
                if keyword_name in keyword_info:
                    kw.update(keyword_info[keyword_name])

            for keyword_name, info in keyword_info.items():
                if not any(k['keyword'] == keyword_name for k in all_keywords):
                    all_keywords.append(info)

        if raw_data.get('get_keyword_asin_analysis'):
            competition_data = self._process_keyword_competition(raw_data['get_keyword_asin_analysis'])
            data['keyword_competition'] = competition_data

            for kw in all_keywords:
                keyword_name = kw['keyword']
                if keyword_name in competition_data:
                    kw['competition_count'] = len(competition_data[keyword_name])

        seen_keywords = set()
        dedup_keywords = []
        for kw in all_keywords:
            keyword = kw['keyword'].lower()
            if keyword not in seen_keywords:
                seen_keywords.add(keyword)
                kw['keyword'] = kw['keyword']
                dedup_keywords.append(kw)

        dedup_keywords.sort(key=lambda x: x.get('weekly_search_volume', x.get('traffic', 0)), reverse=True)
        data['all_keywords'] = dedup_keywords[:200]

        categorized = self._categorize_keywords(dedup_keywords[:200])
        data['categorized_keywords'] = categorized

        stats = self._calculate_stats(categorized)
        data['keyword_stats'] = stats

        negative_keywords = self._identify_negative_keywords(dedup_keywords[:200])
        data['negative_keywords'] = negative_keywords

        return data

    def generate_insights(self, data: Dict[str, Any]) -> List[str]:
        insights = []

        stats = data.get('keyword_stats', {})
        total = stats.get('total', 0)
        if total > 0:
            insights.append(f"共收集并去重{total}个关键词")

        strong = stats.get('strong', 0)
        high = stats.get('high', 0)
        if strong + high > total * 0.5:
            insights.append("高质量关键词占比超过50%，关键词库质量良好")
        else:
            insights.append("建议补充更多高相关度关键词")

        negative_count = len(data.get('negative_keywords', []))
        if negative_count > 0:
            insights.append(f"识别出{negative_count}个否定关键词，建议加入否定词库")

        categorized = data.get('categorized_keywords', {})
        for category, keywords in categorized.items():
            if len(keywords) > 0:
                insights.append(f"{category}关键词：{len(keywords)}个")

        return insights

    def _process_asin_info(self, result: Dict[str, Any]) -> Dict[str, Any]:
        items = result.get('data', result.get('result', result))
        if isinstance(items, dict):
            items = [items]

        result_dict = {}
        for item in items:
            asin = item.get('asin', item.get('ASIN', 'unknown'))
            result_dict[asin] = {
                'title': item.get('title', item.get('Title', '')),
                'price': item.get('price', item.get('Price', '')),
                'stars': item.get('stars', item.get('Stars', '')),
                'ratings': item.get('ratings', item.get('Ratings', ''))
            }
        return result_dict

    def _extract_asin_keywords(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = result.get('data', result.get('result', result))
        if isinstance(items, dict):
            items = items.get('keywords', items.get('data', []))

        keywords = []
        for kw in items:
            keywords.append({
                'keyword': kw.get('keyword', kw.get('Keyword', '')),
                'natural_rank': kw.get('natural_rank', kw.get('naturalRank', '')),
                'ad_rank': kw.get('ad_rank', kw.get('adRank', '')),
                'traffic': kw.get('traffic', kw.get('Traffic', 0)),
                'traffic_share': kw.get('traffic_share', kw.get('trafficShare', '')),
                'search_volume': kw.get('search_volume', kw.get('searchVolume', 0)),
                'competitive_difficulty': kw.get('competitive_difficulty', kw.get('competitiveDifficulty', 0)),
                'cpc': kw.get('cpc', kw.get('costPerClick', 0))
            })
        return keywords

    def _process_keyword_info(self, result: Dict[str, Any]) -> Dict[str, Any]:
        items = result.get('data', result.get('result', result))
        if isinstance(items, dict):
            items = [items]

        result_dict = {}
        for item in items:
            keyword = item.get('keyword', item.get('Keyword', 'unknown'))
            result_dict[keyword] = {
                'keyword': keyword,
                'weekly_search_volume': item.get('weekly_search_volume', item.get('weeklySearchVolume', 0)),
                'search_frequency_rank': item.get('search_frequency_rank', item.get('searchFrequencyRank', 0)),
                'competitive_difficulty': item.get('competitive_difficulty', item.get('competitiveDifficulty', 0)),
                'cpc': item.get('cost_per_click', item.get('cpc', 0)),
                'click_conversion_rate': item.get('click_conversion_rate', item.get('clickConversionRate', 0)),
                'natural_scroll_rate': item.get('natural_scroll_rate', item.get('naturalScrollRate', 0))
            }
        return result_dict

    def _process_keyword_competition(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        if not isinstance(results, list):
            results = [results]

        result_dict = {}
        for result in results:
            keyword = result.get('keyword', result.get('Keyword', 'unknown'))
            items = result.get('data', result.get('result', result))
            if isinstance(items, dict):
                items = items.get('asins', items.get('data', []))

            asins = []
            for item in items:
                asins.append({
                    'asin': item.get('asin', item.get('ASIN', '')),
                    'title': item.get('title', item.get('Title', '')),
                    'price': item.get('price', item.get('Price', '')),
                    'stars': item.get('stars', item.get('Stars', '')),
                    'natural_rank': item.get('natural_rank', item.get('naturalRank', '')),
                    'ad_rank': item.get('ad_rank', item.get('adRank', '')),
                    'traffic': item.get('traffic', item.get('Traffic', '')),
                    'traffic_share': item.get('traffic_share', item.get('trafficShare', ''))
                })

            result_dict[keyword] = asins

        return result_dict

    def _categorize_keywords(self, keywords: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        categorized = {
            '强相关': [],
            '高相关': [],
            '中相关': [],
            '低相关': [],
            '极低相关': []
        }

        for kw in keywords:
            difficulty = kw.get('competitive_difficulty', 50)
            search_volume = kw.get('weekly_search_volume', kw.get('search_volume', 0))

            if difficulty < 50 and search_volume > 10000:
                categorized['强相关'].append(kw)
            elif difficulty < 60 and search_volume > 5000:
                categorized['高相关'].append(kw)
            elif difficulty < 75 and search_volume > 1000:
                categorized['中相关'].append(kw)
            elif difficulty < 85:
                categorized['低相关'].append(kw)
            else:
                categorized['极低相关'].append(kw)

        return categorized

    def _calculate_stats(self, categorized: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        stats = {'total': 0}
        for category, keywords in categorized.items():
            stats[category] = len(keywords)
            stats['total'] += len(keywords)
        return stats

    def _identify_negative_keywords(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        negative = []
        for kw in keywords:
            difficulty = kw.get('competitive_difficulty', 100)
            search_volume = kw.get('weekly_search_volume', kw.get('search_volume', 0))

            if difficulty > 90 or search_volume < 100:
                negative.append({
                    'keyword': kw['keyword'],
                    'relevance': '极低相关',
                    'reason': '竞争度过高' if difficulty > 90 else '搜索量过低'
                })
        return negative

    def _build_overview(self, data: Dict[str, Any]) -> Dict[str, Any]:
        stats = data.get('keyword_stats', {})
        return {
            '总关键词数': stats.get('total', 0),
            '强相关': stats.get('strong', 0),
            '高相关': stats.get('high', 0),
            '中相关': stats.get('medium', 0)
        }


from datetime import timedelta
