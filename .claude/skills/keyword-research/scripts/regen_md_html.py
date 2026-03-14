#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成 Markdown 和 HTML 报告，跳过 CSV
"""
import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from workflow import KeywordResearchWorkflow
from generate_markdown_report import generate_markdown_report
from generate_html_dashboard import generate_html_dashboard

# 创建工作流
workflow = KeywordResearchWorkflow('B09QSGWCLG', 'US', None, 0)
workflow.output_dir = r'D:\amazon-mcp\keyword-reports\B09QSGWCLG_US_20260314'

# 加载关键词
with open(os.path.join(workflow.output_dir, 'keywords_raw.json'), 'r', encoding='utf-8') as f:
    workflow.all_keywords = json.load(f)

print(f"已加载 {len(workflow.all_keywords)} 个关键词")

# 加载分类结果
workflow.categorized_keywords = workflow._load_categorized_result()

if workflow.categorized_keywords:
    total = sum(len(v) for v in workflow.categorized_keywords.values())
    print(f"✓ 成功加载分类结果：{total} 个关键词")
    for cat, kws in workflow.categorized_keywords.items():
        print(f"  - {cat}: {len(kws)} 个")
else:
    print("✗ 未找到分类结果，使用规则分类")
    workflow.categorized_keywords = workflow._smart_classify()

# 生成 Markdown 报告
print("\n生成 Markdown 报告...")
try:
    report_file = generate_markdown_report(
        workflow.asin,
        workflow.site,
        workflow.all_keywords,
        workflow.categorized_keywords,
        workflow.output_dir,
        workflow.product_info
    )
    print(f"✓ 报告已生成：{report_file}")
except Exception as e:
    print(f"✗ Markdown 报告生成失败：{e}")

# 生成 HTML 仪表板
print("\n生成 HTML 仪表板...")
try:
    dashboard_file = generate_html_dashboard(
        workflow.asin,
        workflow.site,
        workflow.all_keywords,
        workflow.categorized_keywords,
        workflow.output_dir,
        workflow.product_info
    )
    print(f"✓ 仪表板已生成：{dashboard_file}")
except Exception as e:
    print(f"✗ HTML 仪表板生成失败：{e}")

print("\n✓ 报告生成完成!")
