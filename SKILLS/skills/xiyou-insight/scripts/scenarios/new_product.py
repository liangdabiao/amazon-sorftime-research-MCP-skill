from .base import BaseScenario
from typing import Dict, List, Any


class NewProductScenario(BaseScenario):
    """提升新品推广效率"""

    NAME = "new_product"
    DESCRIPTION = "提升新品推广效率"
    REQUIRED_PARAMS = ['asin', 'site']

    def get_mcp_tools(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        asin = params['asin']
        site = params['site']
        end_date = params.get('end_date', self.default_end_date)
        start_date = params.get('start_date', self.default_start_date)

        tools = [
            {
                'tool_name': 'get_asin_info',
                'arguments': {
                    'asins': [asin],
                    'country': site,
                    'intent_summary': f'新品推广：获取{asin}基础信息'
                }
            },
            {
                'tool_name': 'get_asin_traffic',
                'arguments': {
                    'asins': [asin],
                    'country': site,
                    'intent_summary': f'新品推广：获取{asin}流量得分'
                }
            },
            {
                'tool_name': 'get_asin_traffic_trends',
                'arguments': {
                    'asin': asin,
                    'country': site,
                    'start_date': start_date,
                    'end_date': end_date,
                    'intent_summary': f'新品推广：获取{asin}流量趋势'
                }
            },
            {
                'tool_name': 'get_asin_keywords',
                'arguments': {
                    'asin': asin,
                    'country': site,
                    'page': 1,
                    'page_size': 100,
                    'sort_field': 'traffic',
                    'sort_order': 'desc',
                    'intent_summary': f'新品推广：获取{asin}关键词列表'
                }
            },
            {
                'tool_name': 'get_asin_bsr_trends',
                'arguments': {
                    'asin': asin,
                    'country': site,
                    'start_date': start_date,
                    'end_date': end_date,
                    'intent_summary': f'新品推广：获取{asin}BSR排名趋势'
                }
            }
        ]

        return tools

    def aggregate_data(self, raw_data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        asin = params['asin']
        site = params['site']

        data = {
            'title': f'新品推广分析 - {asin}',
            'target': asin,
            'site': site,
            'scenario': '新品推广'
        }

        if raw_data.get('get_asin_info'):
            data['asin_info'] = self._process_asin_info(raw_data['get_asin_info'])

        if raw_data.get('get_asin_traffic'):
            data['traffic'] = self._process_traffic(raw_data['get_asin_traffic'])
            data['overview'] = self._build_overview(data['traffic'])

        if raw_data.get('get_asin_traffic_trends'):
            data['traffic_trends'] = self._process_traffic_trends(raw_data['get_asin_traffic_trends'], asin)

            traffic_data = data['traffic_trends'].get(asin, [])
            stage, reason = self._determine_stage(traffic_data, data['traffic'].get(asin, {}))
            data['traffic_stage'] = {
                'stage': stage,
                'stage_name': {'sparse': '稀疏期', 'oscillating': '震荡期', 'stable': '稳定期'}.get(stage, '未知'),
                'reason': reason,
                'traffic_score': data['traffic'].get(asin, {}).get('total_traffic', 0),
                'keyword_count': data['traffic'].get(asin, {}).get('keyword_count', 0)
            }

        if raw_data.get('get_asin_keywords'):
            data['keywords'] = self._process_keywords(raw_data['get_asin_keywords'], asin)

        if raw_data.get('get_asin_bsr_trends'):
            data['bsr_trends'] = self._process_bsr_trends(raw_data['get_asin_bsr_trends'])

        return data

    def generate_insights(self, data: Dict[str, Any]) -> List[str]:
        insights = []

        stage = data.get('traffic_stage', {})
        stage_name = stage.get('stage_name', '')

        if stage_name == '稀疏期':
            insights.append("产品处于稀疏期，亚马逊正在进行小流量测试")
            insights.append("重点关注有效点击和转化，通过考核进入放量测试阶段")
            insights.append("建议优化Listing和主图，提高点击率")
        elif stage_name == '震荡期':
            insights.append("产品处于震荡期，亚马逊正在测试不同位置的表现")
            insights.append("保持稳定的广告投放，争取获得靠前的稳定排名")
            insights.append("注意排名波动，及时调整策略")
        elif stage_name == '稳定期':
            insights.append("产品处于稳定期，已获得稳定的自然流量")
            insights.append("重点维护排名，扩大市场份额")
            insights.append("可以考虑拓展相关关键词")

        if data.get('traffic_trends'):
            asin_trends = data['traffic_trends'].get(data['target'], [])
            if len(asin_trends) >= 7:
                recent_avg = sum(t['total_traffic'] for t in asin_trends[-7:]) / 7
                earlier_avg = sum(t['total_traffic'] for t in asin_trends[:7]) / 7 if len(asin_trends) >= 14 else recent_avg

                if recent_avg > earlier_avg * 1.2:
                    insights.append("流量增长明显，推广效果良好")
                elif recent_avg < earlier_avg * 0.8:
                    insights.append("流量出现下滑，需要分析原因")

        if data.get('keywords'):
            asin_keywords = data['keywords'].get(data['target'], [])
            new_keywords = [kw for kw in asin_keywords if kw.get('traffic_growth', '').startswith('+')]
            if new_keywords:
                insights.append(f"发现{len(new_keywords)}个流量增长的关键词，建议加大投放")

        return insights

    def _determine_stage(self, traffic_trends: List[Dict[str, Any]], traffic_data: Dict[str, Any]) -> tuple[str, str]:
        if not traffic_trends:
            return 'unknown', '数据不足'

        total_traffic = traffic_data.get('total_traffic', 0)
        keyword_count = traffic_data.get('keyword_count', 0)

        if total_traffic < 30 or keyword_count < 10:
            return 'sparse', f'流量得分{total_traffic}较低，关键词数量{keyword_count}较少'

        if total_traffic >= 80 and keyword_count >= 50:
            return 'stable', f'流量得分{total_traffic}较高且稳定，关键词数量{keyword_count}充足'

        volatility = 0
        if len(traffic_trends) >= 7:
            avg_traffic = sum(t['total_traffic'] for t in traffic_trends) / len(traffic_trends)
            if avg_traffic > 0:
                volatility = sum(abs(t['total_traffic'] - avg_traffic) for t in traffic_trends) / (len(traffic_trends) * avg_traffic)

        if volatility > 0.15:
            return 'oscillating', f'流量波动较大({round(volatility*100, 1)}%)，处于放量测试阶段'

        return 'oscillating', '流量处于中等水平，正在向稳定期过渡'

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

    def _process_traffic_trends(self, result: Dict[str, Any], asin: str) -> Dict[str, List[Dict[str, Any]]]:
        items = result.get('data', result.get('result', result))
        if isinstance(items, dict):
            items = items.get('trends', items.get('data', []))

        trends = []
        for day in items:
            trends.append({
                'date': day.get('date', day.get('Date', '')),
                'natural_traffic': day.get('natural_traffic', day.get('naturalTraffic', 0)),
                'ad_traffic': day.get('ad_traffic', day.get('adTraffic', 0)),
                'total_traffic': day.get('total_traffic', day.get('totalTraffic', 0))
            })

        return {asin: trends[-14:] if len(trends) > 14 else trends}

    def _process_keywords(self, result: Dict[str, Any], asin: str) -> Dict[str, List[Dict[str, Any]]]:
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
                'traffic_growth': kw.get('traffic_growth', kw.get('trafficGrowth', ''))
            })

        return {asin: keywords}

    def _process_bsr_trends(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = result.get('data', result.get('result', result))
        if isinstance(items, dict):
            items = items.get('trends', items.get('data', []))

        trends = []
        for day in items:
            trends.append({
                'date': day.get('date', day.get('Date', '')),
                'rank': day.get('rank', day.get('Rank', ''))
            })
        return trends[-14:] if len(trends) > 14 else trends

    def _build_overview(self, traffic: Dict[str, Any]) -> Dict[str, Any]:
        overview = {}
        for asin, data in traffic.items():
            overview[f"{asin} - 总流量"] = data['total_traffic']
            overview[f"{asin} - 自然流量"] = data['natural_traffic']
            overview[f"{asin} - 广告流量"] = data['ad_traffic']
            overview[f"{asin} - 关键词数"] = data['keyword_count']
        return overview
