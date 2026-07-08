#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接生成 HTML 仪表板测试
"""
import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from generate_html_dashboard import generate_html_dashboard

# 读取数据
output_dir = r'D:\amazon-mcp\keyword-reports\B09QSGWCLG_US_20260314'

with open(os.path.join(output_dir, 'keywords_raw.json'), 'r', encoding='utf-8') as f:
    keywords = json.load(f)

with open(os.path.join(output_dir, 'categorized_result.json'), 'r', encoding='utf-8') as f:
    categorized = json.load(f)

# 生成 HTML
html_file = generate_html_dashboard(
    'B09QSGWCLG',
    'US',
    keywords,
    categorized,
    output_dir,
    {}
)

print(f"✓ HTML 仪表板已生成：{html_file}")
