#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 workflow 加载已有分类结果
"""
import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from workflow import KeywordResearchWorkflow

# 创建工作流
workflow = KeywordResearchWorkflow('B09QSGWCLG', 'US', None, 0)
workflow.output_dir = r'D:\amazon-mcp\keyword-reports\B09QSGWCLG_US_20260314'

# 加载关键词
with open(os.path.join(workflow.output_dir, 'keywords_raw.json'), 'r', encoding='utf-8') as f:
    workflow.all_keywords = json.load(f)

# 尝试加载分类结果
workflow.categorized_keywords = workflow._load_categorized_result()

if workflow.categorized_keywords:
    print("✓ 成功加载分类结果")
    total = sum(len(v) for v in workflow.categorized_keywords.values())
    print(f"  总关键词数：{total}")
    for cat, kws in workflow.categorized_keywords.items():
        print(f"  - {cat}: {len(kws)} 个")
else:
    print("✗ 未找到分类结果")
