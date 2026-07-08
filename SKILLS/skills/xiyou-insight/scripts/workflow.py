#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西柚洞察通用工作流引擎

统一入口，通过--scenario参数区分7个场景

使用方式:
    python workflow.py --scenario <场景名> --asin <ASIN> --site <站点>
    
场景列表:
    ad_monitoring         - 实时监控广告投放效果
    traffic_gap           - 快速找到高性价比流量缺口
    competitor_analysis   - 精准拆解竞品流量以及广告策略
    new_product           - 提升新品推广效率
    ad_budget             - 透视竞品广告策略和预算
    keyword_database      - 高效搭建关键词库

示例:
    python workflow.py --scenario competitor_analysis --asin B07PQFT83F --site US
    python workflow.py --scenario ad_monitoring --asin B07PQFT83F --site US --keyword "bluetooth headphones"
    python workflow.py --scenario traffic_gap --own_asin B07PQFT83F --competitor_asins B08X1Z8K5M,B09XYZ --site US
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.scenarios import get_scenario, list_scenarios
from scripts.data_aggregator import DataAggregator
from scripts.report_generator import ReportGenerator
from scripts.dashboard_generator import DashboardGenerator


class WorkflowEngine:
    """通用工作流引擎"""

    def __init__(self):
        self.data_aggregator = DataAggregator()
        self.report_generator = ReportGenerator()
        self.dashboard_generator = DashboardGenerator()

    def run(self, scenario_name: str, params: Dict[str, Any], output_dir: str = None) -> Dict[str, Any]:
        """
        执行工作流

        Args:
            scenario_name: 场景名称
            params: 用户输入参数
            output_dir: 输出目录

        Returns:
            dict: 分析结果
        """
        scenario_class = get_scenario(scenario_name)
        scenario = scenario_class()

        is_valid, missing = scenario.validate_params(params)
        if not is_valid:
            raise ValueError(f"缺少必要参数: {', '.join(missing)}")

        if not output_dir:
            date_str = datetime.now().strftime('%Y%m%d')
            target = params.get('asin', params.get('own_asin', params.get('site', scenario_name)))
            output_dir = os.path.join('xiyou-insight-reports', f'{scenario_name}_{target}_{params.get("site", "US")}_{date_str}')
        os.makedirs(output_dir, exist_ok=True)

        print(f"🚀 开始执行场景: {scenario.NAME}")
        print(f"📁 输出目录: {output_dir}")

        mcp_tools = scenario.get_mcp_tools(params)
        print(f"\n📋 需要调用的MCP工具 ({len(mcp_tools)}个):")
        for i, tool in enumerate(mcp_tools, 1):
            print(f"   {i}. {tool['tool_name']}")

        raw_data = self._collect_mcp_data(mcp_tools, params)

        aggregated_data = scenario.aggregate_data(raw_data, params)

        insights = scenario.generate_insights(aggregated_data)
        aggregated_data['insights'] = insights

        data_file = os.path.join(output_dir, 'data.json')
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(aggregated_data, f, ensure_ascii=False, indent=2)

        self.data_aggregator.save_raw_data(raw_data, output_dir)

        report_file = self.report_generator.generate(
            aggregated_data,
            scenario=aggregated_data.get('scenario', scenario_name),
            target=aggregated_data.get('target', params.get('asin', '')),
            site=params.get('site', ''),
            output_dir=output_dir
        )

        dashboard_file = os.path.join(output_dir, 'dashboard.html')
        self.dashboard_generator.render(aggregated_data, dashboard_file)

        print(f"\n✅ 分析完成!")
        print(f"   📊 数据文件: {data_file}")
        print(f"   📝 报告文件: {report_file}")
        print(f"   📈 Dashboard: {dashboard_file}")

        return aggregated_data

    def _collect_mcp_data(self, mcp_tools: list, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        收集MCP数据（模拟模式）
        
        注意: 实际使用时，这些数据需要通过LLM调用MCP工具获取
        这里提供模拟数据，用于测试工作流流程
        """
        from datetime import datetime, timedelta

        asin = params.get('asin', params.get('own_asin', 'B07PQFT83F'))
        site = params.get('site', 'US')
        keyword = params.get('keyword', 'bluetooth headphones')
        competitor_asins = params.get('competitor_asins', [])
        if isinstance(competitor_asins, str):
            competitor_asins = [competitor_asins]

        end_date = datetime.now().strftime('%Y-%m-%d')

        raw_data = {}

        for tool in mcp_tools:
            tool_name = tool['tool_name']
            args = tool['arguments']

            if tool_name == 'get_asin_info':
                asins = args.get('asins', [asin])
                raw_data['get_asin_info'] = self._mock_asin_info(asins)

            elif tool_name == 'get_asin_variations':
                raw_data['get_asin_variations'] = self._mock_asin_variations(args.get('asin', asin))

            elif tool_name == 'get_asin_keywords':
                asin_kw = args.get('asin', asin)
                raw_data['get_asin_keywords'] = self._mock_asin_keywords(asin_kw)

            elif tool_name == 'get_asin_traffic':
                asins = args.get('asins', [asin])
                raw_data['get_asin_traffic'] = self._mock_asin_traffic(asins)

            elif tool_name == 'get_asin_traffic_trends':
                raw_data['get_asin_traffic_trends'] = self._mock_asin_traffic_trends(args.get('asin', asin))

            elif tool_name == 'get_asin_ad_change_trends':
                raw_data['get_asin_ad_change_trends'] = self._mock_asin_ad_change_trends(args.get('asin', asin))

            elif tool_name == 'get_asin_keyword_rank_hourly':
                raw_data['get_asin_keyword_rank_hourly'] = self._mock_keyword_rank_hourly()

            elif tool_name == 'get_asin_keyword_rank_trends':
                raw_data['get_asin_keyword_rank_trends'] = self._mock_keyword_rank_trends()

            elif tool_name == 'get_asin_keyword_traffic_trends':
                raw_data['get_asin_keyword_traffic_trends'] = self._mock_keyword_traffic_trends()

            elif tool_name == 'get_keyword_info':
                keywords = args.get('keywords', [keyword])
                raw_data['get_keyword_info'] = self._mock_keyword_info(keywords)

            elif tool_name == 'get_keyword_asin_analysis':
                kw = args.get('keyword', keyword)
                if 'get_keyword_asin_analysis' not in raw_data:
                    raw_data['get_keyword_asin_analysis'] = []
                raw_data['get_keyword_asin_analysis'].append(self._mock_keyword_asin_analysis(kw))

            elif tool_name == 'get_keyword_aba_trends':
                kw = args.get('keywords', [keyword])[0]
                raw_data['get_keyword_aba_trends'] = self._mock_keyword_aba_trends(kw)

            elif tool_name == 'get_asin_bsr_trends':
                raw_data['get_asin_bsr_trends'] = self._mock_bsr_trends()

        return raw_data

    def _mock_asin_info(self, asins: list) -> Dict[str, Any]:
        return {
            'data': [
                {
                    'asin': asin,
                    'title': f'Wireless Bluetooth Headphones {asin[:4]} with Noise Cancelling',
                    'price': '59.99',
                    'currency': 'USD',
                    'stars': 4.5,
                    'ratings': 12580,
                    'url': f'https://www.amazon.com/dp/{asin}',
                    'image': 'https://example.com/image.jpg'
                }
                for asin in asins
            ]
        }

    def _mock_asin_variations(self, asin: str) -> Dict[str, Any]:
        return {
            'data': {
                'parent_asin': asin,
                'children': [asin]
            }
        }

    def _mock_asin_keywords(self, asin: str) -> Dict[str, Any]:
        keywords = [
            {'keyword': 'bluetooth headphones', 'natural_rank': 3, 'ad_rank': 2, 'traffic': 15000, 'traffic_share': '25%', 'traffic_growth': '+12%', 'search_volume': 500000, 'competitive_difficulty': 75, 'cpc': 2.5},
            {'keyword': 'wireless headphones', 'natural_rank': 5, 'ad_rank': 3, 'traffic': 12000, 'traffic_share': '20%', 'traffic_growth': '+8%', 'search_volume': 450000, 'competitive_difficulty': 72, 'cpc': 2.3},
            {'keyword': 'noise cancelling headphones', 'natural_rank': 8, 'ad_rank': 5, 'traffic': 8000, 'traffic_share': '13%', 'traffic_growth': '+15%', 'search_volume': 300000, 'competitive_difficulty': 78, 'cpc': 2.8},
            {'keyword': 'bluetooth earbuds', 'natural_rank': 12, 'ad_rank': 8, 'traffic': 5000, 'traffic_share': '8%', 'traffic_growth': '-3%', 'search_volume': 280000, 'competitive_difficulty': 70, 'cpc': 2.1},
            {'keyword': 'wireless earbuds', 'natural_rank': 15, 'ad_rank': 10, 'traffic': 4000, 'traffic_share': '7%', 'traffic_growth': '+5%', 'search_volume': 250000, 'competitive_difficulty': 68, 'cpc': 1.9}
        ]
        return {'data': {'keywords': keywords}}

    def _mock_asin_traffic(self, asins: list) -> Dict[str, Any]:
        return {
            'data': [
                {
                    'asin': asin,
                    'natural_traffic': 85.5,
                    'ad_traffic': 42.3,
                    'total_traffic': 127.8,
                    'keyword_count': 156,
                    'natural_traffic_share': 66.9,
                    'ad_traffic_share': 33.1,
                    'traffic_growth': 12.5
                }
                for asin in asins
            ]
        }

    def _mock_asin_traffic_trends(self, asin: str) -> Dict[str, Any]:
        from datetime import datetime, timedelta
        trends = []
        for i in range(14):
            date = (datetime.now() - timedelta(days=13 - i)).strftime('%Y-%m-%d')
            natural_traffic = 70 + i * 1.1
            ad_traffic = 35 + i * 0.5
            trends.append({
                'date': date,
                'natural_traffic': round(natural_traffic, 1),
                'ad_traffic': round(ad_traffic, 1),
                'total_traffic': round(natural_traffic + ad_traffic, 1)
            })
        return {'data': {'trends': trends}}

    def _mock_asin_ad_change_trends(self, asin: str) -> Dict[str, Any]:
        from datetime import datetime, timedelta
        daily_changes = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=6 - i)).strftime('%Y-%m-%d')
            daily_changes.append({
                'date': date,
                'added': (i % 3) + 1,
                'removed': i % 2
            })
        return {
            'data': {
                'daily_changes': daily_changes,
                'summary': {'total_added': 12, 'total_removed': 3}
            }
        }

    def _mock_keyword_rank_hourly(self) -> Dict[str, Any]:
        hours = []
        for hour in range(24):
            hours.append({
                'hour': hour,
                'natural_rank': 5 + (hour // 6),
                'ad_rank': 2 + (hour // 8)
            })
        return {'data': {'hours': hours}}

    def _mock_keyword_rank_trends(self) -> Dict[str, Any]:
        from datetime import datetime, timedelta
        trends = []
        for i in range(14):
            date = (datetime.now() - timedelta(days=13 - i)).strftime('%Y-%m-%d')
            trends.append({
                'date': date,
                'natural_rank': max(1, 15 - i),
                'ad_rank': max(1, 10 - i // 2)
            })
        return {'data': {'trends': trends}}

    def _mock_keyword_traffic_trends(self) -> Dict[str, Any]:
        from datetime import datetime, timedelta
        trends = []
        for i in range(14):
            date = (datetime.now() - timedelta(days=13 - i)).strftime('%Y-%m-%d')
            trends.append({
                'date': date,
                'natural_traffic': 50 + i * 2,
                'ad_traffic': 30 + i * 1,
                'total_traffic': 80 + i * 3
            })
        return {'data': {'trends': trends}}

    def _mock_keyword_info(self, keywords: list) -> Dict[str, Any]:
        results = []
        for kw in keywords:
            results.append({
                'keyword': kw,
                'weekly_search_volume': 500000 if 'bluetooth' in kw.lower() else 300000,
                'search_frequency_rank': 50 if 'bluetooth' in kw.lower() else 100,
                'competitive_difficulty': 75 if 'bluetooth' in kw.lower() else 70,
                'cost_per_click': 2.5 if 'bluetooth' in kw.lower() else 2.0,
                'click_conversion_rate': 8.5,
                'natural_scroll_rate': 12
            })
        return {'data': results}

    def _mock_keyword_asin_analysis(self, keyword: str) -> Dict[str, Any]:
        asins = [
            {'asin': 'B0XXXXXXXX1', 'title': 'Competitor A - Premium Headphones', 'price': '79.99', 'stars': 4.7, 'natural_rank': 1, 'ad_rank': 1, 'traffic': 25000, 'traffic_share': '40%'},
            {'asin': 'B0XXXXXXXX2', 'title': 'Competitor B - Wireless Pro', 'price': '69.99', 'stars': 4.6, 'natural_rank': 2, 'ad_rank': 2, 'traffic': 18000, 'traffic_share': '28%'},
            {'asin': 'B07PQFT83F', 'title': 'Target Product', 'price': '59.99', 'stars': 4.5, 'natural_rank': 3, 'ad_rank': 3, 'traffic': 15000, 'traffic_share': '24%'}
        ]
        return {'keyword': keyword, 'data': {'asins': asins}}

    def _mock_keyword_aba_trends(self, keyword: str) -> Dict[str, Any]:
        from datetime import datetime, timedelta
        trends = []
        for i in range(12):
            date = (datetime.now() - timedelta(weeks=11 - i)).strftime('%Y-%m-%d')
            trends.append({
                'week': date,
                'weekly_search_volume': 500000 + (i * 5000),
                'aba_rank': 50 - i
            })
        return {'data': {'trends': trends}}

    def _mock_bsr_trends(self) -> Dict[str, Any]:
        from datetime import datetime, timedelta
        trends = []
        for i in range(14):
            date = (datetime.now() - timedelta(days=13 - i)).strftime('%Y-%m-%d')
            trends.append({
                'date': date,
                'rank': max(100, 500 - i * 30)
            })
        return {'data': {'trends': trends}}


def main():
    parser = argparse.ArgumentParser(description='西柚洞察通用工作流引擎')
    parser.add_argument('--scenario', required=True, choices=list(list_scenarios()), help='场景名称')
    parser.add_argument('--asin', help='目标ASIN')
    parser.add_argument('--own_asin', help='自身ASIN（用于流量缺口分析）')
    parser.add_argument('--competitor_asins', help='竞品ASIN列表，逗号分隔')
    parser.add_argument('--site', default='US', help='站点国家码（默认US）')
    parser.add_argument('--keyword', help='关键词（用于广告监控）')
    parser.add_argument('--core_keywords', help='核心关键词列表，逗号分隔')
    parser.add_argument('--output_dir', help='输出目录')
    parser.add_argument('--start_date', help='开始日期 YYYY-MM-DD')
    parser.add_argument('--end_date', help='结束日期 YYYY-MM-DD')

    args = parser.parse_args()

    params = {}
    if args.asin:
        params['asin'] = args.asin
    if args.own_asin:
        params['own_asin'] = args.own_asin
    if args.competitor_asins:
        params['competitor_asins'] = [a.strip() for a in args.competitor_asins.split(',')]
    if args.site:
        params['site'] = args.site
    if args.keyword:
        params['keyword'] = args.keyword
    if args.core_keywords:
        params['core_keywords'] = [k.strip() for k in args.core_keywords.split(',')]
    if args.start_date:
        params['start_date'] = args.start_date
    if args.end_date:
        params['end_date'] = args.end_date

    engine = WorkflowEngine()
    engine.run(args.scenario, params, args.output_dir)


if __name__ == "__main__":
    main()
