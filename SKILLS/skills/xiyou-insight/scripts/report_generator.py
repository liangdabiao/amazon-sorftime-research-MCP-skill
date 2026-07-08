#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西柚洞察报告生成器

将MCP获取的数据聚合为Markdown报告

使用方式:
    from scripts.report_generator import ReportGenerator
    generator = ReportGenerator()
    report = generator.generate(data, scenario, asin, site)
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class ReportGenerator:
    """报告生成器"""

    def generate(self, data: Dict[str, Any], scenario: str, 
                 target: str, site: str, output_dir: str = None) -> str:
        """
        生成报告

        Args:
            data: 结构化数据
            scenario: 场景名称
            target: ASIN或关键词
            site: 站点
            output_dir: 输出目录

        Returns:
            str: 报告内容
        """
        report_content = self._build_report(data, scenario, target, site)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            report_file = os.path.join(output_dir, 'report.md')
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            return report_file

        return report_content

    def _build_report(self, data: Dict[str, Any], scenario: str, 
                      target: str, site: str) -> str:
        """构建报告内容"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        scenario_titles = {
            '广告监控': '实时监控广告投放效果分析报告',
            '流量缺口': '高性价比流量缺口分析报告',
            '竞品拆解': '对标竞对打法拆解报告',
            '新品推广': '新品推广效率分析报告',
            '流量广告策略': '竞品流量及广告策略深度分析报告',
            '广告预算': '竞品广告策略和预算分析报告',
            '关键词库': '关键词库搭建报告'
        }

        title = scenario_titles.get(scenario, f'{scenario}分析报告')

        content = f"""# {title}

## 分析概览

| 项目 | 详情 |
|------|------|
| 分析场景 | {scenario} |
| 分析对象 | {target} |
| 目标站点 | {site} |
| 生成时间 | {timestamp} |

"""

        if scenario == '流量广告策略' or scenario == '竞品拆解':
            content += self._build_competitor_analysis(data)
        elif scenario == '广告监控':
            content += self._build_ad_monitoring(data)
        elif scenario == '流量缺口':
            content += self._build_traffic_gap(data)
        elif scenario == '新品推广':
            content += self._build_new_product(data)
        elif scenario == '广告预算':
            content += self._build_ad_budget(data)
        elif scenario == '关键词库':
            content += self._build_keyword_database(data)
        else:
            content += self._build_general_analysis(data)

        return content

    def _build_competitor_analysis(self, data: Dict[str, Any]) -> str:
        """构建竞品分析报告"""
        content = ""

        if data.get('asin_info'):
            content += "## 竞品基础信息\n\n"
            for asin, info in data['asin_info'].items():
                content += f"### {asin}\n\n"
                content += f"- **标题**: {info.get('title', '-')}\n"
                content += f"- **价格**: {info.get('price', '-')} {info.get('currency', '')}\n"
                content += f"- **评分**: {info.get('stars', '-')} ({info.get('ratings', '-')}条评论)\n"
                content += f"- **链接**: [Amazon]({info.get('url', '#')})\n\n"

        if data.get('variations'):
            content += "## 变体关系分析\n\n"
            for asin, var in data['variations'].items():
                content += f"### {asin} 变体结构\n\n"
                content += f"- **父体**: {var.get('parent_asin', '-')}\n"
                content += f"- **子体数量**: {len(var.get('children', []))}\n"
                content += "- **子体列表**: " + ", ".join(var.get('children', [])) + "\n\n"

        if data.get('traffic'):
            content += "## 流量分析\n\n"
            content += "### 流量得分对比\n\n"
            content += "| ASIN | 自然流量 | 广告流量 | 总流量 | 关键词数量 |\n"
            content += "|------|----------|----------|--------|------------|\n"
            for asin, traffic in data['traffic'].items():
                content += f"| {asin} | {traffic.get('natural_traffic', '-')} | {traffic.get('ad_traffic', '-')} | {traffic.get('total_traffic', '-')} | {traffic.get('keyword_count', '-')} |\n"
            content += "\n"

        if data.get('keywords'):
            content += "## 关键词布局分析\n\n"
            for asin, keywords in data['keywords'].items():
                content += f"### {asin} 关键词分布\n\n"
                if keywords:
                    content += "| 关键词 | 自然排名 | 广告排名 | 流量 | 流量占比 |\n"
                    content += "|--------|----------|----------|------|----------|\n"
                    for kw in keywords[:10]:
                        content += f"| {kw.get('keyword', '-')} | {kw.get('natural_rank', '-')} | {kw.get('ad_rank', '-')} | {kw.get('traffic', '-')} | {kw.get('traffic_share', '-')} |\n"
                    content += f"\n*显示前10个关键词，共{len(keywords)}个*\n\n"

        if data.get('ad_trends'):
            content += "## 广告策略分析\n\n"
            for asin, trends in data['ad_trends'].items():
                content += f"### {asin} 广告活动变化\n\n"
                if trends.get('daily_changes'):
                    content += "| 日期 | 新增活动 | 移除活动 |\n"
                    content += "|------|----------|----------|\n"
                    for day in trends['daily_changes'][-7:]:
                        content += f"| {day.get('date', '-')} | {day.get('added', 0)} | {day.get('removed', 0)} |\n"
                    content += "\n"

        if data.get('insights'):
            content += "## 关键洞察\n\n"
            for insight in data['insights']:
                content += f"- {insight}\n"
            content += "\n"

        return content

    def _build_ad_monitoring(self, data: Dict[str, Any]) -> str:
        """构建广告监控报告"""
        content = ""

        if data.get('hourly_rank'):
            content += "## 小时级排名监控\n\n"
            content += f"### {data.get('keyword', '')} 小时级排名变化\n\n"
            content += "| 时间 | 自然排名 | 广告排名 |\n"
            content += "|------|----------|----------|\n"
            for hour in data['hourly_rank']:
                content += f"| {hour.get('hour', '-')}:00 | {hour.get('natural_rank', '-')} | {hour.get('ad_rank', '-')} |\n"
            content += "\n"

        if data.get('rank_trends'):
            content += "## 日排名趋势\n\n"
            content += "| 日期 | 自然排名 | 广告排名 |\n"
            content += "|------|----------|----------|\n"
            for day in data['rank_trends'][-14:]:
                content += f"| {day.get('date', '-')} | {day.get('natural_rank', '-')} | {day.get('ad_rank', '-')} |\n"
            content += "\n"

        if data.get('ad_changes'):
            content += "## 广告活动变化\n\n"
            content += "| 日期 | 新增活动 | 移除活动 |\n"
            content += "|------|----------|----------|\n"
            for day in data['ad_changes'][-7:]:
                content += f"| {day.get('date', '-')} | {day.get('added', 0)} | {day.get('removed', 0)} |\n"
            content += "\n"

        if data.get('effect_evaluation'):
            content += "## 广告效果评估\n\n"
            eval_data = data['effect_evaluation']
            content += f"- **评估结果**: {eval_data.get('result', '-')}\n"
            content += f"- **自然排名变化**: {eval_data.get('natural_rank_change', '-')}\n"
            content += f"- **广告排名变化**: {eval_data.get('ad_rank_change', '-')}\n"
            content += f"- **评估理由**: {eval_data.get('reason', '-')}\n\n"

        return content

    def _build_traffic_gap(self, data: Dict[str, Any]) -> str:
        """构建流量缺口分析报告"""
        content = ""

        if data.get('keyword_comparison'):
            content += "## 关键词覆盖对比\n\n"
            content += "| 关键词 | 自身排名 | 竞品A排名 | 竞品B排名 | 搜索量 | 竞争难度 |\n"
            content += "|--------|----------|-----------|-----------|--------|----------|\n"
            for kw in data['keyword_comparison'][:20]:
                content += f"| {kw.get('keyword', '-')} | {kw.get('own_rank', '-')} | {kw.get('competitor_a_rank', '-')} | {kw.get('competitor_b_rank', '-')} | {kw.get('search_volume', '-')} | {kw.get('competitive_difficulty', '-')} |\n"
            content += "\n"

        if data.get('traffic_gaps'):
            content += "## 流量缺口分析\n\n"
            content += f"共发现 **{len(data['traffic_gaps'])}** 个流量缺口关键词\n\n"
            content += "| 优先级 | 关键词 | 竞品排名 | 自身排名 | 搜索量 | 竞争难度 | 建议竞价 |\n"
            content += "|--------|--------|----------|----------|--------|----------|----------|\n"
            for gap in data['traffic_gaps'][:15]:
                priority = '🔴高' if gap.get('priority') == 'high' else '🟡中' if gap.get('priority') == 'medium' else '🟢低'
                content += f"| {priority} | {gap.get('keyword', '-')} | {gap.get('competitor_rank', '-')} | {gap.get('own_rank', '-')} | {gap.get('search_volume', '-')} | {gap.get('competitive_difficulty', '-')} | ${gap.get('cpc', '-')} |\n"
            content += "\n"

        if data.get('recommendations'):
            content += "## 优化建议\n\n"
            for rec in data['recommendations']:
                content += f"- {rec}\n"
            content += "\n"

        return content

    def _build_new_product(self, data: Dict[str, Any]) -> str:
        """构建新品推广分析报告"""
        content = ""

        if data.get('traffic_stage'):
            content += "## 流量分配阶段判断\n\n"
            stage = data['traffic_stage']
            stage_name = {'sparse': '稀疏期', 'oscillating': '震荡期', 'stable': '稳定期'}.get(stage.get('stage', ''), '未知')
            content += f"### 当前阶段: **{stage_name}**\n\n"
            content += f"- **判断依据**: {stage.get('reason', '-')}\n"
            content += f"- **流量得分**: {stage.get('traffic_score', '-')}\n"
            content += f"- **关键词数量**: {stage.get('keyword_count', '-')}\n\n"

        if data.get('traffic_trends'):
            content += "## 流量趋势\n\n"
            content += "| 日期 | 自然流量 | 广告流量 | 总流量 |\n"
            content += "|------|----------|----------|--------|\n"
            traffic_trends = data['traffic_trends']
            if isinstance(traffic_trends, dict):
                for asin, trends in traffic_trends.items():
                    for day in trends[-14:] if isinstance(trends, list) else []:
                        content += f"| {day.get('date', '-')} | {day.get('natural_traffic', '-')} | {day.get('ad_traffic', '-')} | {day.get('total_traffic', '-')} |\n"
            elif isinstance(traffic_trends, list):
                for day in traffic_trends[-14:]:
                    content += f"| {day.get('date', '-')} | {day.get('natural_traffic', '-')} | {day.get('ad_traffic', '-')} | {day.get('total_traffic', '-')} |\n"
            content += "\n"

        if data.get('异动关键词'):
            content += "## 异动关键词分析\n\n"
            
            if data['异动关键词'].get('新增'):
                content += "### 📈 新增关键词\n\n"
                content += "| 关键词 | 自然排名 | 搜索量 |\n"
                content += "|--------|----------|--------|\n"
                for kw in data['异动关键词']['新增'][:10]:
                    content += f"| {kw.get('keyword', '-')} | {kw.get('natural_rank', '-')} | {kw.get('search_volume', '-')} |\n"
                content += "\n"

            if data['异动关键词'].get('流失'):
                content += "### 📉 流失关键词\n\n"
                content += "| 关键词 | 搜索量 |\n"
                content += "|--------|--------|\n"
                for kw in data['异动关键词']['流失'][:10]:
                    content += f"| {kw.get('keyword', '-')} | {kw.get('search_volume', '-')} |\n"
                content += "\n"

            if data['异动关键词'].get('流量升档'):
                content += "### 🚀 流量升档\n\n"
                content += "| 关键词 | 档位变化 | 搜索量 |\n"
                content += "|--------|----------|--------|\n"
                for kw in data['异动关键词']['流量升档'][:10]:
                    content += f"| {kw.get('keyword', '-')} | {kw.get('change', '-')} | {kw.get('search_volume', '-')} |\n"
                content += "\n"

        if data.get('recommendations'):
            content += "## 优化建议\n\n"
            for rec in data['recommendations']:
                content += f"- {rec}\n"
            content += "\n"

        return content

    def _build_ad_budget(self, data: Dict[str, Any]) -> str:
        """构建广告预算分析报告"""
        content = ""

        if data.get('ad_type_share'):
            content += "## 广告类型分布\n\n"
            content += "| 广告类型 | 流量占比 |\n"
            content += "|----------|----------|\n"
            for ad_type, share in data['ad_type_share'].items():
                content += f"| {ad_type} | {share}% |\n"
            content += "\n"

        if data.get('ad_activities'):
            content += "## 广告活动分析\n\n"
            content += "| 活动ID | 流量贡献 | 展示时长趋势 |\n"
            content += "|--------|----------|--------------|\n"
            for activity in data['ad_activities'][:10]:
                content += f"| {activity.get('id', '-')} | {activity.get('traffic_share', '-')} | {activity.get('duration_trend', '-')} |\n"
            content += "\n"

        if data.get('core_keywords'):
            content += "## 核心广告关键词\n\n"
            content += "| 关键词 | 流量占比 | 搜索量 | 建议竞价 |\n"
            content += "|--------|----------|--------|----------|\n"
            for kw in data['core_keywords'][:15]:
                content += f"| {kw.get('keyword', '-')} | {kw.get('traffic_share', '-')} | {kw.get('search_volume', '-')} | ${kw.get('cpc', '-')} |\n"
            content += "\n"

        if data.get('budget_inference'):
            content += "## 预算推断\n\n"
            budget = data['budget_inference']
            content += f"- **预算趋势**: {budget.get('trend', '-')}\n"
            content += f"- **主要投放时段**: {budget.get('peak_hours', '-')}\n"
            content += f"- **预算调整节点**: {budget.get('adjustment_dates', '-')}\n"
            content += f"- **预估月预算**: ${budget.get('estimated_monthly', '-')}\n\n"

        return content

    def _build_keyword_database(self, data: Dict[str, Any]) -> str:
        """构建关键词库报告"""
        content = ""

        if data.get('keyword_stats'):
            stats = data['keyword_stats']
            content += "## 关键词统计\n\n"
            content += f"- **总关键词数**: {stats.get('total', 0)}\n"
            content += f"- **强相关**: {stats.get('strong', 0)} ({round(stats.get('strong', 0)/stats.get('total', 1)*100, 1)}%)\n"
            content += f"- **高相关**: {stats.get('high', 0)} ({round(stats.get('high', 0)/stats.get('total', 1)*100, 1)}%)\n"
            content += f"- **中相关**: {stats.get('medium', 0)} ({round(stats.get('medium', 0)/stats.get('total', 1)*100, 1)}%)\n"
            content += f"- **低相关**: {stats.get('low', 0)} ({round(stats.get('low', 0)/stats.get('total', 1)*100, 1)}%)\n\n"

        if data.get('categorized_keywords'):
            content += "## 关键词分类\n\n"
            for category, keywords in data['categorized_keywords'].items():
                content += f"### {category} ({len(keywords)}个)\n\n"
                content += "| 关键词 | 搜索量 | 竞争难度 | 建议竞价 |\n"
                content += "|--------|--------|----------|----------|\n"
                for kw in keywords[:10]:
                    content += f"| {kw.get('keyword', '-')} | {kw.get('search_volume', '-')} | {kw.get('competitive_difficulty', '-')} | ${kw.get('cpc', '-')} |\n"
                if len(keywords) > 10:
                    content += f"\n*显示前10个，共{len(keywords)}个*\n"
                content += "\n"

        if data.get('negative_keywords'):
            content += "## 否定词库\n\n"
            content += f"共 **{len(data['negative_keywords'])}** 个否定关键词\n\n"
            content += "| 关键词 | 相关性 | 原因 |\n"
            content += "|--------|--------|------|\n"
            for kw in data['negative_keywords'][:20]:
                content += f"| {kw.get('keyword', '-')} | {kw.get('relevance', '-')} | {kw.get('reason', '-')} |\n"
            content += "\n"

        return content

    def _build_general_analysis(self, data: Dict[str, Any]) -> str:
        """构建通用分析报告"""
        content = ""

        if data.get('summary'):
            content += "## 分析摘要\n\n"
            content += data['summary'] + "\n\n"

        if data.get('details'):
            content += "## 详细数据\n\n"
            for key, value in data['details'].items():
                content += f"### {key}\n\n"
                if isinstance(value, list):
                    for item in value[:20]:
                        if isinstance(item, dict):
                            content += "- " + ", ".join(f"{k}: {v}" for k, v in item.items()) + "\n"
                        else:
                            content += f"- {item}\n"
                    if len(value) > 20:
                        content += f"\n*显示前20条，共{len(value)}条*\n"
                elif isinstance(value, dict):
                    content += "| 字段 | 值 |\n"
                    content += "|------|------|\n"
                    for k, v in value.items():
                        content += f"| {k} | {v} |\n"
                else:
                    content += f"{value}\n"
                content += "\n"

        return content


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python report_generator.py <data_json_path>")
        sys.exit(1)

    data_path = sys.argv[1]
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenario = data.get('scenario', '通用分析')
    target = data.get('target', '')
    site = data.get('site', '')

    generator = ReportGenerator()
    output_dir = os.path.dirname(data_path)
    report_file = generator.generate(data, scenario, target, site, output_dir)

    print(f"✅ 报告已生成: {report_file}")
