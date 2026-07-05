from .base import BaseScenario
from typing import Dict, List, Any


class TrafficGapScenario(BaseScenario):
    """快速找到高性价比流量缺口"""

    NAME = "traffic_gap"
    DESCRIPTION = "快速找到高性价比流量缺口"
    REQUIRED_PARAMS = ['own_asin', 'competitor_asins', 'site']

    def get_mcp_tools(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        own_asin = params['own_asin']
        competitor_asins = params['competitor_asins']
        if isinstance(competitor_asins, str):
            competitor_asins = [competitor_asins]
        site = params['site']

        all_asins = [own_asin] + competitor_asins

        tools = [
            {
                'tool_name': 'get_asin_info',
                'arguments': {
                    'asins': all_asins,
                    'country': site,
                    'intent_summary': f'流量缺口分析：获取ASIN基础信息'
                }
            },
            {
                'tool_name': 'get_asin_traffic',
                'arguments': {
                    'asins': all_asins,
                    'country': site,
                    'intent_summary': f'流量缺口分析：获取ASIN流量得分'
                }
            }
        ]

        for asin in all_asins:
            tools.append({
                'tool_name': 'get_asin_keywords',
                'arguments': {
                    'asin': asin,
                    'country': site,
                    'page': 1,
                    'page_size': 100,
                    'sort_field': 'traffic',
                    'sort_order': 'desc',
                    'intent_summary': f'流量缺口分析：获取{asin}关键词列表'
                }
            })

        return tools

    def aggregate_data(self, raw_data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        own_asin = params['own_asin']
        competitor_asins = params['competitor_asins']
        if isinstance(competitor_asins, str):
            competitor_asins = [competitor_asins]
        site = params['site']

        data = {
            'title': f'流量缺口分析 - {own_asin}',
            'target': own_asin,
            'site': site,
            'scenario': '流量缺口',
            'competitors': competitor_asins
        }

        if raw_data.get('get_asin_info'):
            data['asin_info'] = self._process_asin_info(raw_data['get_asin_info'])

        if raw_data.get('get_asin_traffic'):
            data['traffic'] = self._process_traffic(raw_data['get_asin_traffic'])
            data['overview'] = self._build_overview(data['traffic'])

        if raw_data.get('get_asin_keywords'):
            all_keywords = raw_data['get_asin_keywords']
            if not isinstance(all_keywords, list):
                all_keywords = [all_keywords]

            keywords_map = {}
            for i, asin in enumerate([own_asin] + competitor_asins):
                if i < len(all_keywords):
                    keywords_map[asin] = self._extract_keywords(all_keywords[i])

            data['keywords'] = keywords_map

            own_keywords = set(kw.get('keyword', '').lower() for kw in keywords_map.get(own_asin, []))
            gap_keywords = []

            for competitor in competitor_asins:
                for kw in keywords_map.get(competitor, []):
                    keyword = kw.get('keyword', '').lower()
                    if keyword not in own_keywords and keyword not in [g['keyword'] for g in gap_keywords]:
                        gap_keywords.append({
                            'keyword': keyword,
                            'competitor': competitor,
                            'competitor_rank': kw.get('natural_rank', kw.get('ad_rank', '')),
                            'own_rank': '-',
                            'traffic': kw.get('traffic', 0),
                            'traffic_share': kw.get('traffic_share', ''),
                            'search_volume': kw.get('search_volume', 0),
                            'competitive_difficulty': kw.get('competitive_difficulty', 0),
                            'cpc': kw.get('cpc', 0),
                            'priority': self._calculate_priority(kw)
                        })

            gap_keywords.sort(key=lambda x: (-x['traffic'], x['competitive_difficulty']))
            data['traffic_gaps'] = gap_keywords[:30]

        return data

    def generate_insights(self, data: Dict[str, Any]) -> List[str]:
        insights = []

        gaps = data.get('traffic_gaps', [])
        if gaps:
            high_priority = sum(1 for g in gaps if g.get('priority') == 'high')
            medium_priority = sum(1 for g in gaps if g.get('priority') == 'medium')

            insights.append(f"共发现{len(gaps)}个流量缺口关键词")
            if high_priority > 0:
                insights.append(f"其中{high_priority}个高优先级关键词建议优先投放")
            if medium_priority > 0:
                insights.append(f"{medium_priority}个中优先级关键词可作为补充流量")

            top_gap = gaps[0]
            insights.append(f"最大流量缺口：'{top_gap['keyword']}'，竞品流量{top_gap['traffic']}")

        if data.get('traffic'):
            own_traffic = data['traffic'].get(data['target'], {})
            competitor_traffic = []
            for competitor in data.get('competitors', []):
                ct = data['traffic'].get(competitor, {})
                if ct:
                    competitor_traffic.append(ct)

            if competitor_traffic:
                avg_competitor_total = sum(ct.get('total_traffic', 0) for ct in competitor_traffic) / len(competitor_traffic)
                own_total = own_traffic.get('total_traffic', 0)

                if own_total < avg_competitor_total * 0.7:
                    insights.append("自身流量低于竞品平均水平，需要加大广告投放")
                elif own_total < avg_competitor_total:
                    insights.append("自身流量略低于竞品，有提升空间")
                else:
                    insights.append("自身流量表现良好，继续保持")

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
                'currency': item.get('currency', item.get('Currency', '')),
                'stars': item.get('stars', item.get('Stars', '')),
                'ratings': item.get('ratings', item.get('Ratings', '')),
                'url': item.get('url', item.get('Url', '')),
                'image': item.get('image', item.get('Image', ''))
            }
        return result_dict

    def _process_traffic(self, result: Dict[str, Any]) -> Dict[str, Any]:
        items = result.get('data', result.get('result', result))
        if isinstance(items, dict):
            items = [items]

        result_dict = {}
        for item in items:
            asin = item.get('asin', item.get('ASIN', 'unknown'))
            result_dict[asin] = {
                'natural_traffic': item.get('natural_traffic', item.get('naturalTraffic', 0)),
                'ad_traffic': item.get('ad_traffic', item.get('adTraffic', 0)),
                'total_traffic': item.get('total_traffic', item.get('totalTraffic', 0)),
                'keyword_count': item.get('keyword_count', item.get('keywordCount', 0)),
                'natural_traffic_share': item.get('natural_traffic_share', item.get('naturalTrafficShare', 0)),
                'ad_traffic_share': item.get('ad_traffic_share', item.get('adTrafficShare', 0))
            }
        return result_dict

    def _extract_keywords(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
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

    def _calculate_priority(self, keyword: Dict[str, Any]) -> str:
        search_volume = keyword.get('search_volume', 0)
        difficulty = keyword.get('competitive_difficulty', 100)
        traffic = keyword.get('traffic', 0)

        if search_volume > 50000 and difficulty < 60:
            return 'high'
        elif search_volume > 10000 and difficulty < 70:
            return 'medium'
        elif traffic > 1000:
            return 'medium'
        else:
            return 'low'

    def _build_overview(self, traffic: Dict[str, Any]) -> Dict[str, Any]:
        overview = {}
        for asin, data in traffic.items():
            overview[f"{asin} - 总流量"] = data['total_traffic']
            overview[f"{asin} - 关键词数"] = data['keyword_count']
        return overview
