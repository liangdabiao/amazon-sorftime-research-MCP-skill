from .base import BaseScenario
from typing import Dict, List, Any


class AdBudgetScenario(BaseScenario):
    """透视竞品广告策略和预算"""

    NAME = "ad_budget"
    DESCRIPTION = "透视竞品广告策略和预算"
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
                    'intent_summary': f'广告预算分析：获取{asin}基础信息'
                }
            },
            {
                'tool_name': 'get_asin_variations',
                'arguments': {
                    'asin': asin,
                    'country': site,
                    'intent_summary': f'广告预算分析：获取{asin}变体关系'
                }
            },
            {
                'tool_name': 'get_asin_ad_change_trends',
                'arguments': {
                    'asin': asin,
                    'country': site,
                    'start_date': start_date,
                    'end_date': end_date,
                    'intent_summary': f'广告预算分析：获取{asin}广告活动变化'
                }
            },
            {
                'tool_name': 'get_asin_traffic',
                'arguments': {
                    'asins': [asin],
                    'country': site,
                    'intent_summary': f'广告预算分析：获取{asin}流量得分'
                }
            },
            {
                'tool_name': 'get_asin_traffic_trends',
                'arguments': {
                    'asin': asin,
                    'country': site,
                    'start_date': start_date,
                    'end_date': end_date,
                    'intent_summary': f'广告预算分析：获取{asin}流量趋势'
                }
            },
            {
                'tool_name': 'get_asin_keywords',
                'arguments': {
                    'asin': asin,
                    'country': site,
                    'page': 1,
                    'page_size': 50,
                    'sort_field': 'traffic',
                    'sort_order': 'desc',
                    'intent_summary': f'广告预算分析：获取{asin}关键词列表'
                }
            }
        ]

        return tools

    def aggregate_data(self, raw_data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        asin = params['asin']
        site = params['site']

        data = {
            'title': f'广告策略与预算分析 - {asin}',
            'target': asin,
            'site': site,
            'scenario': '广告预算'
        }

        if raw_data.get('get_asin_info'):
            data['asin_info'] = self._process_asin_info(raw_data['get_asin_info'])

        if raw_data.get('get_asin_variations'):
            data['variations'] = self._process_variations(raw_data['get_asin_variations'], asin)

        if raw_data.get('get_asin_traffic'):
            data['traffic'] = self._process_traffic(raw_data['get_asin_traffic'])
            data['overview'] = self._build_overview(data['traffic'])

        if raw_data.get('get_asin_traffic_trends'):
            data['traffic_trends'] = self._process_traffic_trends(raw_data['get_asin_traffic_trends'], asin)

        if raw_data.get('get_asin_ad_change_trends'):
            data['ad_trends'] = self._process_ad_trends(raw_data['get_asin_ad_change_trends'], asin)

        if raw_data.get('get_asin_keywords'):
            data['keywords'] = self._process_keywords(raw_data['get_asin_keywords'], asin)

            asin_keywords = data['keywords'].get(asin, [])
            ad_keywords = [kw for kw in asin_keywords if kw.get('ad_rank', 999) <= 20]
            ad_keywords.sort(key=lambda x: x.get('traffic', 0), reverse=True)
            data['core_keywords'] = ad_keywords[:15]

        if data.get('traffic') and data.get('keywords'):
            traffic_data = data['traffic'].get(asin, {})
            ad_traffic_share = traffic_data.get('ad_traffic_share', 0)
            natural_traffic_share = traffic_data.get('natural_traffic_share', 0)

            data['ad_type_share'] = {
                '自然流量': natural_traffic_share,
                '广告流量': ad_traffic_share
            }

        if data.get('ad_trends'):
            ad_trends_data = data['ad_trends'].get(asin, {})
            daily_changes = ad_trends_data.get('daily_changes', [])
            summary = ad_trends_data.get('summary', {})

            budget_inference = self._infer_budget(daily_changes, summary, data.get('traffic_trends', {}).get(asin, []))
            data['budget_inference'] = budget_inference

        return data

    def generate_insights(self, data: Dict[str, Any]) -> List[str]:
        insights = []

        ad_type_share = data.get('ad_type_share', {})
        if ad_type_share:
            ad_share = ad_type_share.get('广告流量', 0)
            if ad_share > 50:
                insights.append(f"广告流量占比{ad_share}%，竞品高度依赖广告投放")
            elif ad_share > 30:
                insights.append(f"广告流量占比{ad_share}%，竞品保持适度的广告投入")
            else:
                insights.append(f"广告流量占比{ad_share}%，竞品以自然流量为主")

        core_keywords = data.get('core_keywords', [])
        if core_keywords:
            insights.append(f"识别出{len(core_keywords)}个核心广告关键词")
            top_kw = core_keywords[0]
            insights.append(f"最核心广告关键词：'{top_kw['keyword']}'，流量{top_kw['traffic']}")

        budget_inference = data.get('budget_inference', {})
        trend = budget_inference.get('trend', '')
        if trend == 'increasing':
            insights.append("竞品广告预算呈上升趋势，可能正在扩大市场份额")
        elif trend == 'decreasing':
            insights.append("竞品广告预算呈下降趋势，可能在收缩或调整策略")
        else:
            insights.append("竞品广告预算保持稳定，策略较为保守")

        estimated_monthly = budget_inference.get('estimated_monthly', 0)
        if estimated_monthly > 0:
            insights.append(f"预估月广告预算约${estimated_monthly}")

        return insights

    def _infer_budget(self, daily_changes: List[Dict[str, Any]], summary: Dict[str, Any],
                      traffic_trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_added = summary.get('total_added', 0)
        total_removed = summary.get('total_removed', 0)
        net_change = summary.get('net_change', total_added - total_removed)

        if net_change > 5:
            trend = 'increasing'
        elif net_change < -5:
            trend = 'decreasing'
        else:
            trend = 'stable'

        peak_days = []
        if traffic_trends:
            avg_traffic = sum(t['total_traffic'] for t in traffic_trends) / len(traffic_trends)
            for day in traffic_trends:
                if day['total_traffic'] > avg_traffic * 1.2:
                    peak_days.append(day['date'])

        estimated_monthly = 0
        if traffic_trends and len(traffic_trends) >= 7:
            avg_ad_traffic = sum(t['ad_traffic'] for t in traffic_trends[-7:]) / 7
            if avg_ad_traffic > 0:
                estimated_monthly = int(avg_ad_traffic * 30 * 2)

        return {
            'trend': trend,
            'peak_hours': '推测为美国时间上午10点-下午4点',
            'adjustment_dates': peak_days[:5],
            'estimated_monthly': estimated_monthly
        }

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

    def _process_variations(self, result: Dict[str, Any], asin: str) -> Dict[str, Any]:
        data = result.get('data', result.get('result', result))
        return {
            asin: {
                'parent_asin': data.get('parent_asin', data.get('parentASIN', '')),
                'children': data.get('children', data.get('childASINs', [])),
                'variation_data': {}
            }
        }

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

    def _process_ad_trends(self, result: Dict[str, Any], asin: str) -> Dict[str, Any]:
        data = result.get('data', result.get('result', result))
        daily_changes = data.get('daily_changes', data.get('dailyChanges', []))
        summary = data.get('summary', {})

        processed_changes = []
        for day in daily_changes[-7:]:
            processed_changes.append({
                'date': day.get('date', day.get('Date', '')),
                'added': day.get('added', day.get('addedCount', 0)),
                'removed': day.get('removed', day.get('removedCount', 0))
            })

        return {
            asin: {
                'daily_changes': processed_changes,
                'summary': {
                    'total_added': summary.get('total_added', 0),
                    'total_removed': summary.get('total_removed', 0),
                    'net_change': summary.get('net_change', summary.get('total_added', 0) - summary.get('total_removed', 0))
                }
            }
        }

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
                'search_volume': kw.get('search_volume', kw.get('searchVolume', 0)),
                'cpc': kw.get('cpc', kw.get('costPerClick', 0))
            })

        return {asin: keywords}

    def _build_overview(self, traffic: Dict[str, Any]) -> Dict[str, Any]:
        overview = {}
        for asin, data in traffic.items():
            overview[f"{asin} - 总流量"] = data['total_traffic']
            overview[f"{asin} - 广告流量占比"] = f"{data['ad_traffic_share']}%"
        return overview
