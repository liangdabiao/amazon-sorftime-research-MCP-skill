#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成报告，使用已有的分类结果

使用方式:
1. 从报告目录内运行（自动检测）:
   python regenerate_reports.py

2. 指定 ASIN 和站点:
   python regenerate_reports.py --asin B0FG6QG8C8 --site US

3. 指定完整输出目录:
   python regenerate_reports.py --dir "D:\\amazon-mcp\\keyword-reports\\B0FG6QG8C8_US_20260314"

4. 列出所有可用的报告目录:
   python regenerate_reports.py --list
"""
import os
import sys
import json
import argparse
import re
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from workflow import KeywordResearchWorkflow
from csv_generator import generate_csv_files
from generate_markdown_report import generate_markdown_report
from generate_html_dashboard import generate_html_dashboard


def list_available_reports(base_dir=None):
    """列出所有可用的报告目录"""
    if base_dir is None:
        # 从当前目录向上查找 keyword-reports 目录
        current_dir = os.path.abspath(os.getcwd())
        if 'keyword-reports' in current_dir:
            base_dir = current_dir
        else:
            # 尝试相对路径
            base_dir = os.path.join(os.path.dirname(SCRIPT_DIR), '..', '..', '..', 'keyword-reports')
            base_dir = os.path.abspath(base_dir)

    if not os.path.exists(base_dir):
        print(f"❌ 报告目录不存在: {base_dir}")
        return

    print(f"📂 可用的报告目录: {base_dir}\n")

    # 列出所有 ASIN_开头的目录
    dirs = []
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path) and '_' in item:
            # 检查是否有 keywords_raw.json
            if os.path.exists(os.path.join(item_path, 'keywords_raw.json')):
                dirs.append(item)

    if not dirs:
        print("  没有找到任何报告目录")
        return

    # 按修改时间排序
    dirs_with_time = []
    for d in dirs:
        d_path = os.path.join(base_dir, d)
        mtime = os.path.getmtime(d_path)
        dirs_with_time.append((d, mtime))

    dirs_with_time.sort(key=lambda x: x[1], reverse=True)

    for d, mtime in dirs_with_time:
        # 解析 ASIN 和站点
        parts = d.split('_')
        if len(parts) >= 2:
            asin = parts[0]
            site = parts[1]
            # 检查分类文件
            d_path = os.path.join(base_dir, d)
            has_categorized = os.path.exists(os.path.join(d_path, 'categorized_result.json'))
            status = "✓ LLM分类" if has_categorized else "○ 规则分类"
            mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            print(f"  {d:40s} | {status:10s} | {mtime_str}")

    print(f"\n使用方法:")
    print(f"  python regenerate_reports.py --asin <ASIN> --site <SITE>")
    print(f"  cd {base_dir}\\<目录名> && python ..\\..\\..\\.claude\\skills\\keyword-research\\scripts\\regenerate_reports.py")


def parse_output_dir(output_dir):
    """从输出目录路径解析 ASIN 和站点"""
    basename = os.path.basename(output_dir)
    # 格式: ASIN_SITE_YYYYMMDD
    parts = basename.split('_')
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None, None


def find_output_dir_from_cwd():
    """从当前工作目录查找输出目录"""
    cwd = os.path.abspath(os.getcwd())

    # 检查当前目录是否有 keywords_raw.json
    if os.path.exists(os.path.join(cwd, 'keywords_raw.json')):
        return cwd

    # 检查是否在 keyword-reports 目录下
    if 'keyword-reports' in cwd:
        # 可能在某个报告目录的子目录中
        parts = cwd.split('keyword-reports')
        if len(parts) > 1:
            base_path = parts[0] + 'keyword-reports'
            remainder = parts[1].lstrip(os.sep)
            # 尝试找到包含 keywords_raw.json 的目录
            current = remainder
            while current:
                test_path = os.path.join(base_path, current)
                if os.path.exists(os.path.join(test_path, 'keywords_raw.json')):
                    return test_path
                # 向上移动
                parts = current.split(os.sep)
                parts.pop()
                current = os.sep.join(parts) if parts else ''
                if not current or current == remainder:
                    break

    return None


def main():
    parser = argparse.ArgumentParser(
        description='重新生成关键词报告',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python regenerate_reports.py --list                          # 列出所有报告
  python regenerate_reports.py --asin B0FG6QG8C8 --site US    # 指定 ASIN
  python regenerate_reports.py --dir "path\\to\\report"       # 指定目录
  cd report_dir && python regenerate_reports.py               # 从报告目录运行
        """
    )
    parser.add_argument('--asin', help='ASIN')
    parser.add_argument('--site', default='US', help='Amazon 站点 (默认: US)')
    parser.add_argument('--dir', help='输出目录路径')
    parser.add_argument('--list', action='store_true', help='列出所有可用的报告目录')
    parser.add_argument('--base-dir', help='报告根目录 (用于 --list)')

    args = parser.parse_args()

    # 列出所有报告
    if args.list:
        list_available_reports(args.base_dir)
        return 0

    # 确定输出目录
    output_dir = None
    asin = None
    site = args.site

    if args.dir:
        # 直接指定目录
        output_dir = args.dir
        asin, site = parse_output_dir(output_dir)
        if not asin:
            print(f"❌ 无法从目录名解析 ASIN: {output_dir}")
            return 1
    elif args.asin:
        # 指定 ASIN
        asin = args.asin
        site = args.site
        # 查找匹配的目录
        base_dir = os.path.join(os.path.dirname(SCRIPT_DIR), '..', '..', '..', 'keyword-reports')
        base_dir = os.path.abspath(base_dir)
        for item in os.listdir(base_dir):
            if item.startswith(f"{asin}_{site}"):
                output_dir = os.path.join(base_dir, item)
                break
        if not output_dir:
            print(f"❌ 未找到 ASIN {asin} ({site}) 的报告目录")
            print(f"   搜索路径: {base_dir}")
            print(f"   使用 --list 查看所有可用报告")
            return 1
    else:
        # 尝试从当前目录检测
        output_dir = find_output_dir_from_cwd()
        if not output_dir:
            print("❌ 无法确定输出目录")
            print("\n请使用以下方式之一:")
            print("  1. 从报告目录内运行此脚本")
            print("  2. 使用 --asis <ASIN> --site <SITE> 指定")
            print("  3. 使用 --dir <路径> 指定完整目录")
            print("  4. 使用 --list 查看所有可用报告")
            return 1
        asin, site = parse_output_dir(output_dir)
        if not asin:
            print(f"❌ 无法从目录名解析 ASIN: {output_dir}")
            return 1
        print(f"📂 自动检测到输出目录: {output_dir}")

    # 验证目录存在
    if not os.path.exists(output_dir):
        print(f"❌ 输出目录不存在: {output_dir}")
        return 1

    # 验证必要文件存在
    keywords_file = os.path.join(output_dir, 'keywords_raw.json')
    if not os.path.exists(keywords_file):
        print(f"❌ 关键词文件不存在: {keywords_file}")
        return 1

    # 创建工作流
    workflow = KeywordResearchWorkflow(asin, site, None, 0)
    workflow.output_dir = output_dir

    # 加载关键词
    with open(os.path.join(workflow.output_dir, 'keywords_raw.json'), 'r', encoding='utf-8') as f:
        workflow.all_keywords = json.load(f)

    # 加载产品信息
    product_info_file = os.path.join(workflow.output_dir, 'product_info.json')
    if os.path.exists(product_info_file):
        with open(product_info_file, 'r', encoding='utf-8') as f:
            workflow.product_info = json.load(f)

    print(f"\n{'='*60}")
    print(f"重新生成报告: {asin} ({site})")
    print(f"{'='*60}")
    print(f"输出目录: {workflow.output_dir}")
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

    # 生成 CSV
    print("\n生成 CSV 文件...")
    csv_files = generate_csv_files(
        workflow.all_keywords,
        workflow.categorized_keywords,
        workflow.output_dir
    )
    print(f"✓ 生成 {len(csv_files)} 个 CSV 文件")

    # 生成 Markdown 报告
    print("\n生成 Markdown 报告...")
    report_file = generate_markdown_report(
        workflow.asin,
        workflow.site,
        workflow.all_keywords,
        workflow.categorized_keywords,
        workflow.output_dir,
        workflow.product_info
    )
    print(f"✓ 报告已生成：{report_file}")

    # 生成 HTML 仪表板
    print("\n生成 HTML 仪表板...")
    dashboard_file = generate_html_dashboard(
        workflow.asin,
        workflow.site,
        workflow.all_keywords,
        workflow.categorized_keywords,
        workflow.output_dir,
        workflow.product_info
    )
    print(f"✓ 仪表板已生成：{dashboard_file}")

    print("\n" + "="*60)
    print("✓ 所有报告生成完成!")
    print("="*60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
