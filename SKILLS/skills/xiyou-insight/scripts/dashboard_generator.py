#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西柚洞察Dashboard生成器

将数据渲染为可视化HTML看板

使用方式:
    from scripts.dashboard_generator import DashboardGenerator
    generator = DashboardGenerator()
    generator.render(data, output_file)
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class DashboardGenerator:
    """Dashboard生成器"""

    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #1a1a1a; line-height: 1.6; }
        .container { max-width: 1400px; margin: 0 auto; padding: 30px 20px; }
        .header { text-align: center; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 2px solid #e1e8ef; }
        .header h1 { font-size: 24px; font-weight: 700; color: #1a1a1a; margin-bottom: 8px; }
        .header p { color: #666; font-size: 14px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; margin-bottom: 24px; }
        .card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        .card-title { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid #f0f2f5; }
        .stat-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f5f7fa; }
        .stat-label { color: #666; font-size: 14px; }
        .stat-value { font-weight: 600; color: #1a1a1a; font-size: 16px; }
        .chart-container { height: 300px; margin-top: 10px; }
        .table-wrapper { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { padding: 10px 8px; text-align: left; border-bottom: 1px solid #f0f2f5; }
        th { background: #f8f9fa; font-weight: 600; color: #333; }
        .highlight { color: #2563eb; font-weight: 600; }
        .danger { color: #dc2626; }
        .success { color: #16a34a; }
        .warning { color: #ca8a04; }
        .tag { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
        .tag-high { background: #fee2e2; color: #dc2626; }
        .tag-medium { background: #fef3c7; color: #ca8a04; }
        .tag-low { background: #dcfce7; color: #16a34a; }
        .insight-box { background: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; border-radius: 0 8px 8px 0; margin-top: 15px; }
        .insight-title { font-weight: 600; color: #1d4ed8; margin-bottom: 8px; }
        .insight-content { color: #374151; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{TITLE}}</h1>
            <p>分析对象: {{TARGET}} | 站点: {{SITE}} | 生成时间: {{TIMESTAMP}}</p>
        </div>
        {{CONTENT}}
    </div>
</body>
</html>"""

    def render(self, data: Dict[str, Any], output_file: str) -> str:
        """
        渲染Dashboard

        Args:
            data: 结构化数据
            output_file: 输出文件路径

        Returns:
            str: 输出文件路径
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        title = data.get('title', '西柚洞察分析看板')
        target = data.get('target', '')
        site = data.get('site', '')

        content = self._build_content(data)

        html = self.HTML_TEMPLATE.replace('{{TITLE}}', title)\
                                 .replace('{{TARGET}}', target)\
                                 .replace('{{SITE}}', site)\
                                 .replace('{{TIMESTAMP}}', timestamp)\
                                 .replace('{{CONTENT}}', content)

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_file

    def _build_content(self, data: Dict[str, Any]) -> str:
        """构建内容"""
        content = ""

        if data.get('overview'):
            content += self._build_overview(data['overview'])

        if data.get('traffic'):
            content += self._build_traffic_section(data['traffic'])

        if data.get('keywords'):
            content += self._build_keywords_section(data['keywords'])

        if data.get('ad_analysis'):
            content += self._build_ad_section(data['ad_analysis'])

        if data.get('comparison'):
            content += self._build_comparison_section(data['comparison'])

        if data.get('insights'):
            content += self._build_insights_section(data['insights'])

        return content

    def _build_overview(self, overview: Dict[str, Any]) -> str:
        """构建概览卡片"""
        items = []
        for key, value in overview.items():
            items.append(f"""
            <div class="stat-item">
                <span class="stat-label">{key}</span>
                <span class="stat-value">{value}</span>
            </div>
            """)

        return f"""
        <div class="grid">
            <div class="card">
                <div class="card-title">📊 概览数据</div>
                {''.join(items)}
            </div>
        </div>
        """

    def _build_traffic_section(self, traffic: Dict[str, Any]) -> str:
        """构建流量分析部分"""
        content = ""

        if traffic.get('scores'):
            scores = traffic['scores']
            chart_data = [
                {"name": "自然流量", "value": scores.get('natural_traffic', 0), "itemStyle": {"color": "#3b82f6"}},
                {"name": "广告流量", "value": scores.get('ad_traffic', 0), "itemStyle": {"color": "#f59e0b"}}
            ]
            content += f"""
            <div class="grid">
                <div class="card">
                    <div class="card-title">📈 流量构成</div>
                    <div class="chart-container" id="trafficPie"></div>
                </div>
                <div class="card">
                    <div class="card-title">📊 流量得分</div>
                    <div class="stat-item"><span class="stat-label">自然流量</span><span class="stat-value highlight">{scores.get('natural_traffic', '-')}</span></div>
                    <div class="stat-item"><span class="stat-label">广告流量</span><span class="stat-value highlight">{scores.get('ad_traffic', '-')}</span></div>
                    <div class="stat-item"><span class="stat-label">总流量</span><span class="stat-value">{scores.get('total_traffic', '-')}</span></div>
                    <div class="stat-item"><span class="stat-label">关键词数量</span><span class="stat-value">{scores.get('keyword_count', '-')}</span></div>
                </div>
            </div>
            <script>
                var trafficPie = echarts.init(document.getElementById('trafficPie'));
                trafficPie.setOption({{
                    tooltip: {{trigger: 'item'}},
                    series: [{{type: 'pie', radius: ['40%', '70%'], data: {json.dumps(chart_data)}, label: {{show: true, formatter: '{{b}}: {{c}}'}}}}]
                }});
            </script>
            """

        if traffic.get('trends'):
            dates = [d['date'] for d in traffic['trends']]
            natural = [d['natural_traffic'] for d in traffic['trends']]
            ad = [d['ad_traffic'] for d in traffic['trends']]
            content += f"""
            <div class="card">
                <div class="card-title">📉 流量趋势</div>
                <div class="chart-container" id="trafficTrend"></div>
            </div>
            <script>
                var trafficTrend = echarts.init(document.getElementById('trafficTrend'));
                trafficTrend.setOption({{
                    tooltip: {{trigger: 'axis'}},
                    xAxis: {{type: 'category', data: {json.dumps(dates)}}},
                    yAxis: {{type: 'value'}},
                    series: [
                        {{name: '自然流量', type: 'line', data: {json.dumps(natural)}, smooth: true}},
                        {{name: '广告流量', type: 'line', data: {json.dumps(ad)}, smooth: true}}
                    ]
                }});
            </script>
            """

        return content

    def _build_keywords_section(self, keywords: Any) -> str:
        """构建关键词部分"""
        if not keywords:
            return ""

        if isinstance(keywords, dict):
            all_keywords = []
            for asin, kw_list in keywords.items():
                for kw in kw_list:
                    kw['asin'] = asin
                    all_keywords.append(kw)
            all_keywords.sort(key=lambda x: x.get('traffic', 0), reverse=True)
        else:
            all_keywords = keywords

        top_keywords = all_keywords[:10]
        
        table_rows = []
        for kw in top_keywords:
            table_rows.append(f"""
            <tr>
                <td>{kw.get('keyword', '-')}</td>
                <td>{kw.get('natural_rank', '-')}</td>
                <td>{kw.get('ad_rank', '-')}</td>
                <td>{kw.get('traffic', '-')}</td>
                <td>{kw.get('traffic_share', '-')}</td>
            </tr>
            """)
        
        return f"""
        <div class="grid">
            <div class="card">
                <div class="card-title">🔑 Top关键词</div>
                <div class="table-wrapper">
                    <table>
                        <thead><tr><th>关键词</th><th>自然排名</th><th>广告排名</th><th>流量</th><th>流量占比</th></tr></thead>
                        <tbody>{''.join(table_rows)}</tbody>
                    </table>
                </div>
            </div>
            <div class="card">
                <div class="card-title">📊 关键词分布</div>
                <div class="chart-container" id="keywordDist"></div>
            </div>
        </div>
        <script>
            var keywordDist = echarts.init(document.getElementById('keywordDist'));
            keywordDist.setOption({{
                tooltip: {{trigger: 'axis', axisPointer: {{type: 'shadow'}}}},
                xAxis: {{type: 'value'}},
                yAxis: {{type: 'category', data: {json.dumps([kw['keyword'] for kw in top_keywords])}}},
                series: [{{name: '搜索量', type: 'bar', data: {json.dumps([kw.get('search_volume', 0) for kw in top_keywords])}}}]
            }});
        </script>
        """

    def _build_ad_section(self, ad_data: Dict[str, Any]) -> str:
        """构建广告分析部分"""
        content = ""

        if ad_data.get('type_share'):
            chart_data = [{"name": k, "value": v} for k, v in ad_data['type_share'].items()]
            content += f"""
            <div class="grid">
                <div class="card">
                    <div class="card-title">🎯 广告类型分布</div>
                    <div class="chart-container" id="adTypePie"></div>
                </div>
            </div>
            <script>
                var adTypePie = echarts.init(document.getElementById('adTypePie'));
                adTypePie.setOption({{
                    tooltip: {{trigger: 'item'}},
                    series: [{{type: 'pie', data: {json.dumps(chart_data)}, label: {{show: true, formatter: '{{b}}: {{c}}%'}}}}]
                }});
            </script>
            """

        if ad_data.get('core_keywords'):
            keywords = ad_data['core_keywords'][:10]
            table_rows = []
            for kw in keywords:
                table_rows.append(f"""
                <tr>
                    <td>{kw.get('keyword', '-')}</td>
                    <td>{kw.get('traffic_share', '-')}</td>
                    <td>${{kw.get('cpc', '-')}}</td>
                </tr>
                """)
            content += f"""
            <div class="card">
                <div class="card-title">💡 核心广告关键词</div>
                <div class="table-wrapper">
                    <table>
                        <thead><tr><th>关键词</th><th>流量占比</th><th>建议竞价</th></tr></thead>
                        <tbody>{''.join(table_rows)}</tbody>
                    </table>
                </div>
            </div>
            """

        return content

    def _build_comparison_section(self, comparison: Dict[str, Any]) -> str:
        """构建对比部分"""
        if not comparison.get('items'):
            return ""

        items = comparison['items']
        table_rows = []
        for item in items:
            table_rows.append(f"""
            <tr>
                <td>{item.get('asin', '-')}</td>
                <td>{item.get('natural_traffic', '-')}</td>
                <td>{item.get('ad_traffic', '-')}</td>
                <td>{item.get('keyword_count', '-')}</td>
            </tr>
            """)

        return f"""
        <div class="card">
            <div class="card-title">⚖️ ASIN对比</div>
            <div class="table-wrapper">
                <table>
                    <thead><tr><th>ASIN</th><th>自然流量</th><th>广告流量</th><th>关键词数量</th></tr></thead>
                    <tbody>{''.join(table_rows)}</tbody>
                </table>
            </div>
        </div>
        """

    def _build_insights_section(self, insights: List[str]) -> str:
        """构建洞察部分"""
        if not insights:
            return ""

        insight_items = []
        for i, insight in enumerate(insights, 1):
            insight_items.append(f"<li>{insight}</li>")

        return f"""
        <div class="card">
            <div class="card-title">💡 关键洞察</div>
            <ul style="padding-left: 20px; color: #374151;">
                {''.join(insight_items)}
            </ul>
        </div>
        """


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python dashboard_generator.py <data_json_path> <output_html_path>")
        sys.exit(1)

    data_path = sys.argv[1]
    output_file = sys.argv[2]

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    generator = DashboardGenerator()
    result = generator.render(data, output_file)

    print(f"✅ Dashboard已生成: {result}")
