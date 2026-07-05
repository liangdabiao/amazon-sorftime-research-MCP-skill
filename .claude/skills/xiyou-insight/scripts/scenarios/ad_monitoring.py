from .base import BaseScenario
from typing import Dict, List, Any


class AdMonitoringScenario(BaseScenario):
    """实时监控广告投放效果"""

    NAME = "ad_monitoring"
    DESCRIPTION = "实时监控广告投放效果"
    REQUIRED_PARAMS = ['asin', 'site', 'keyword']

    def get_mcp_tools(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        asin = params['asin']
        site = params['site']
        keyword = params['keyword']
        date = params.get('date', self.default_end_date)
        end_date = params.get('end_date', self.default_end_date)
        start_date = params.get('start_date', self.default_start_date)

        tools = [
            {
                'tool_name': 'get_asin_info',
                'arguments': {
                    'asins': [asin],
                    'country': site,
                    'intent_summary': f'广告监控：获取{asin}基础信息'
                }
            },
            {
                'tool_name': 'get_asin_keyword_rank_hourly',
                'arguments': {
                    'asin': asin,
                    'keyword': keyword,
                    'country': site,
                    'date': date,
                    'intent_summary': f'广告监控：获取{asin}在关键词{keyword}下的小时级排名'
                }
            },
            {
                'tool_name': 'get_asin_keyword_rank_trends',
                'arguments': {
                    'asin': asin,
                    'keyword': keyword,
                    'country': site,
                    'start_date': start_date,
                    'end_date': end_date,
                    'intent_summary': f'广告监控：获取{asin}在关键词{keyword}下的日排名趋势'
                }
            },
            {
                'tool_name': 'get_asin_ad_change_trends',
                'arguments': {
                    'asin': asin,
                    'country': site,
                    'start_date': start_date,
                    'end_date': end_date,
                    'intent_summary': f'广告监控：获取{asin}广告活动变化趋势'
                }
            },
            {
                'tool_name': 'get_asin_keyword_traffic_trends',
                'arguments': {
                    'asin': asin,
                    'keyword': keyword,
                    'country': site,
                    'start_date': start_date,
                    'end_date': end_date,
                    'intent_summary': f'广告监控：获取{asin}在关键词{keyword}下的流量趋势'
                }
            }
        ]

        return tools

    def aggregate_data(self, raw_data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        asin = params['asin']
        site = params['site']
        keyword = params['keyword']

        data = {
            'title': f'广告投放监控 - {asin} - {keyword}',
            'target': asin,
            'site': site,
            'scenario': '广告监控',
            'keyword': keyword
        }

        if raw_data.get('get_asin_info'):
            data['asin_info'] = self._process_asin_info(raw_data['get_asin_info'])

        if raw_data.get('get_asin_keyword_rank_hourly'):
            data['hourly_rank'] = self._process_hourly_rank(raw_data['get_asin_keyword_rank_hourly'])

        if raw_data.get('get_asin_keyword_rank_trends'):
            data['rank_trends'] = self._process_rank_trends(raw_data['get_asin_keyword_rank_trends'])

        if raw_data.get('get_asin_ad_change_trends'):
            data['ad_changes'] = self._process_ad_changes(raw_data['get_asin_ad_change_trends'])

        if raw_data.get('get_asin_keyword_traffic_trends'):
            data['traffic_trends'] = self._process_keyword_traffic_trends(raw_data['get_asin_keyword_traffic_trends'])

        return data

    def generate_insights(self, data: Dict[str, Any]) -> List[str]:
        insights = []

        if data.get('rank_trends'):
            trends = data['rank_trends']
            if len(trends) >= 7:
                first_natural = trends[0].get('natural_rank', 999)
                last_natural = trends[-1].get('natural_rank', 999)
                first_ad = trends[0].get('ad_rank', 999)
                last_ad = trends[-1].get('ad_rank', 999)

                natural_improved = last_natural < first_natural and last_natural != 0
                ad_improved = last_ad < first_ad and last_ad != 0

                if natural_improved and ad_improved:
                    insights.append("广告投放效果优秀，自然排名和广告排名均有提升")
                elif natural_improved:
                    insights.append("广告投放带动了自然排名上升，属于正向干预")
                elif ad_improved and not natural_improved:
                    insights.append("广告排名有提升但自然排名未上升，需关注广告有效性")
                else:
                    insights.append("广告投放未能有效提升排名，建议调整关键词或竞价策略")

        if data.get('ad_changes'):
            added = sum(day.get('added', 0) for day in data['ad_changes'])
            removed = sum(day.get('removed', 0) for day in data['ad_changes'])
            if added > removed:
                insights.append(f"近期新增{added}个广告活动，广告投放力度在加大")
            elif removed > added:
                insights.append(f"近期移除{removed}个广告活动，广告策略正在调整")

        if data.get('hourly_rank'):
            ad_rank_occurrences = sum(1 for h in data['hourly_rank'] if h.get('ad_rank', 999) <= 10)
            if ad_rank_occurrences >= 18:
                insights.append("广告位置稳定，大部分时间都在首页前10名")
            elif ad_rank_occurrences >= 12:
                insights.append("广告位置尚可，约一半时间在首页")
            else:
                insights.append("广告位置不稳定，需要优化竞价策略")

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

    def _process_hourly_rank(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = result.get('data', result.get('result', result))
        if isinstance(items, dict):
            items = items.get('hours', items.get('data', []))

        hourly_data = []
        for hour in items:
            hourly_data.append({
                'hour': hour.get('hour', hour.get('Hour', '')),
                'natural_rank': hour.get('natural_rank', hour.get('naturalRank', '')),
                'ad_rank': hour.get('ad_rank', hour.get('adRank', ''))
            })
        return hourly_data

    def _process_rank_trends(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = result.get('data', result.get('result', result))
        if isinstance(items, dict):
            items = items.get('trends', items.get('data', []))

        trends = []
        for day in items:
            trends.append({
                'date': day.get('date', day.get('Date', '')),
                'natural_rank': day.get('natural_rank', day.get('naturalRank', '')),
                'ad_rank': day.get('ad_rank', day.get('adRank', ''))
            })
        return trends[-14:] if len(trends) > 14 else trends

    def _process_ad_changes(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        data = result.get('data', result.get('result', result))
        daily_changes = data.get('daily_changes', data.get('dailyChanges', []))

        processed_changes = []
        for day in daily_changes[-7:]:
            processed_changes.append({
                'date': day.get('date', day.get('Date', '')),
                'added': day.get('added', day.get('addedCount', 0)),
                'removed': day.get('removed', day.get('removedCount', 0))
            })
        return processed_changes

    def _process_keyword_traffic_trends(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
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
        return trends[-14:] if len(trends) > 14 else trends
