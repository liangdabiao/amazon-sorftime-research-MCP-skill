#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词采集器 - 使用 Sorftime MCP API
优化版本：更好的错误处理、重试机制和调试输出
"""

import os
import sys
import json
import subprocess
import re
import time
from datetime import datetime
from collections import Counter

# 导入数据解析工具
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from data_parser import (
    parse_sse_response,
    extract_keywords_from_response,
    normalize_keyword_data,
    safe_int,
    safe_float
)


class KeywordCollector:
    """从 Sorftime 采集关键词"""

    # API 请求配置
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # 秒
    REQUEST_TIMEOUT = 120  # 秒

    def __init__(self, asin: str, site: str = 'US', verbose: bool = True):
        self.asin = asin.upper()
        self.site = site.upper()
        self.verbose = verbose
        self.api_url = self._get_api_url()
        self.request_id = 0
        self.collected_keywords = []
        self.errors = []  # 记录错误信息
        self.product_detail = None  # 存储产品详情

    def _log(self, message: str, level: str = 'INFO'):
        """输出日志"""
        if self.verbose:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"  [{timestamp}] [{level}] {message}")

    def _get_api_url(self) -> str:
        """从 .mcp.json 读取 API URL"""
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
        mcp_file = os.path.join(project_root, '.mcp.json')

        if not os.path.exists(mcp_file):
            # 尝试从当前工作目录向上查找
            cwd = os.getcwd()
            while cwd != os.path.dirname(cwd):
                mcp_file = os.path.join(cwd, '.mcp.json')
                if os.path.exists(mcp_file):
                    break
                cwd = os.path.dirname(cwd)

        try:
            with open(mcp_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config['mcpServers']['sorftime']['url']
        except Exception as e:
            self._log(f"无法读取 .mcp.json: {e}", 'ERROR')
            return None

    def _curl_request(self, tool_name: str, arguments: dict, retry: int = 0) -> dict:
        """
        执行 Sorftime API 请求（带重试机制）

        Args:
            tool_name: API 工具名称
            arguments: 请求参数
            retry: 当前重试次数

        Returns:
            dict: 解析后的响应数据
        """
        if not self.api_url:
            return {'has_error': True, 'error': 'API URL 未配置'}

        self.request_id += 1
        args_str = json.dumps(arguments, ensure_ascii=False)

        cmd = [
            'curl', '-s', '-X', 'POST', self.api_url,
            '-H', 'Content-Type: application/json',
            '-d', f'{{"jsonrpc":"2.0","id":{self.request_id},"method":"tools/call","params":{{"name":"{tool_name}","arguments":{args_str}}}}}'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                   timeout=self.REQUEST_TIMEOUT, encoding='utf-8', errors='ignore')
            response = parse_sse_response(result.stdout)

            # 检查是否有错误
            if response.get('has_error'):
                error_msg = response.get('error', 'Unknown error')
                self._log(f"API 返回错误: {error_msg}", 'WARN')

                # 如果是临时错误，尝试重试
                if retry < self.MAX_RETRIES and self._is_retryable_error(error_msg):
                    self._log(f"重试 {retry + 1}/{self.MAX_RETRIES}...", 'WARN')
                    time.sleep(self.RETRY_DELAY)
                    return self._curl_request(tool_name, arguments, retry + 1)

                return response

            # 检查是否有数据
            if not response.get('data'):
                # 有些 API 返回空数据是正常的
                self._log(f"API 无返回数据", 'DEBUG')
                return response

            return response

        except subprocess.TimeoutExpired:
            error_msg = 'Request timeout'
            self._log(f"请求超时", 'ERROR')
            if retry < self.MAX_RETRIES:
                self._log(f"重试 {retry + 1}/{self.MAX_RETRIES}...", 'WARN')
                time.sleep(self.RETRY_DELAY)
                return self._curl_request(tool_name, arguments, retry + 1)
            return {'has_error': True, 'error': error_msg}

        except Exception as e:
            error_msg = str(e)
            self._log(f"请求异常: {error_msg}", 'ERROR')
            if retry < self.MAX_RETRIES and self._is_retryable_error(error_msg):
                self._log(f"重试 {retry + 1}/{self.MAX_RETRIES}...", 'WARN')
                time.sleep(self.RETRY_DELAY)
                return self._curl_request(tool_name, arguments, retry + 1)
            return {'has_error': True, 'error': error_msg}

    def _is_retryable_error(self, error_msg: str) -> bool:
        """判断错误是否可以重试"""
        retryable_patterns = [
            'timeout', 'connection', 'network', 'temporary',
            '503', '502', '500', '429'  # HTTP 状态码
        ]
        error_lower = error_msg.lower()
        return any(pattern in error_lower for pattern in retryable_patterns)

    def collect_traffic_terms(self) -> list:
        """采集产品流量关键词"""
        print(f"  [1/4] 采集产品流量词...")
        response = self._curl_request('product_traffic_terms', {
            'amzSite': self.site,
            'asin': self.asin
        })

        if response.get('has_error'):
            print(f"    ⚠ 流量词采集失败: {response.get('error')}")
            self.errors.append({'step': 'traffic_terms', 'error': response.get('error')})
            return []

        keywords_data = extract_keywords_from_response(response.get('data', {}))
        keywords = [normalize_keyword_data(kw) for kw in keywords_data]
        keywords = [kw for kw in keywords if kw['keyword']]  # 过滤空关键词

        print(f"    ✓ 采集到 {len(keywords)} 个流量词")
        return keywords

    def collect_competitor_keywords(self) -> list:
        """采集竞品布局关键词"""
        print(f"  [2/4] 采集竞品布局词...")
        response = self._curl_request('competitor_product_keywords', {
            'amzSite': self.site,
            'asin': self.asin
        })

        if response.get('has_error'):
            print(f"    ⚠ 竞品词采集失败: {response.get('error')}")
            self.errors.append({'step': 'competitor_keywords', 'error': response.get('error')})
            return []

        keywords_data = extract_keywords_from_response(response.get('data', {}))
        keywords = [normalize_keyword_data(kw) for kw in keywords_data]
        keywords = [kw for kw in keywords if kw['keyword']]

        print(f"    ✓ 采集到 {len(keywords)} 个竞品词")
        return keywords

    def collect_category_keywords(self, node_id: str = None) -> list:
        """采集类目核心关键词"""
        print(f"  [3/4] 采集类目核心词...")

        # 如果没有提供 NodeID，先获取产品详情
        if not node_id:
            node_id = self._get_product_node_id()
            if not node_id:
                print(f"    ⚠ 无法获取产品 NodeID，跳过类目词采集")
                return []

        response = self._curl_request('category_keywords', {
            'amzSite': self.site,
            'nodeId': node_id
        })

        if response.get('has_error'):
            print(f"    ⚠ 类目词采集失败: {response.get('error')}")
            self.errors.append({'step': 'category_keywords', 'error': response.get('error')})
            return []

        keywords_data = extract_keywords_from_response(response.get('data', {}))
        keywords = [normalize_keyword_data(kw) for kw in keywords_data]
        keywords = [kw for kw in keywords if kw['keyword']]

        print(f"    ✓ 采集到 {len(keywords)} 个类目词")
        return keywords

    def collect_long_tail_keywords(self, core_keywords: list, limit: int = 30) -> list:
        """
        通过分页获取更多关键词（使用 product_traffic_terms 和 competitor_product_keywords 的多页数据）

        Args:
            core_keywords: 核心关键词列表（用于确定采集数量）
            limit: 尝试获取的额外页数
        """
        print(f"  [4/4] 扩展长尾词（通过分页）...")

        long_tail = []
        success_count = 0
        fail_count = 0

        # 策略1: 获取 product_traffic_terms 的多页数据
        print(f"    策略1: 获取产品流量词的额外页面...")
        max_pages = limit
        for page in range(2, max_pages + 2):
            print(f"    获取流量词第 {page} 页...", end='', flush=True)

            response = self._curl_request('product_traffic_terms', {
                'amzSite': self.site,
                'asin': self.asin,
                'page': page
            })

            if not response.get('has_error') and response.get('data'):
                keywords_data = extract_keywords_from_response(response.get('data', {}))
                words = [normalize_keyword_data(kw) for kw in keywords_data]
                words = [w for w in words if w['keyword']]

                if words:
                    # 检查是否与已有数据重复
                    unique_words = [w for w in words if w['keyword'].lower() not in [kw['keyword'].lower() for kw in long_tail]]
                    if unique_words:
                        long_tail.extend(unique_words)
                        success_count += 1
                        print(f" ✓ ({len(unique_words)} 个新词)")
                    else:
                        print(f" (全部重复，停止)")
                        break
                else:
                    print(f" (无数据)")
                    break
            else:
                fail_count += 1
                print(f" ✗")
                break

        # 策略2: 获取 competitor_product_keywords 的多页数据
        print(f"    策略2: 获取竞品关键词的额外页面...")
        for page in range(2, max_pages + 2):
            print(f"    获取竞品词第 {page} 页...", end='', flush=True)

            response = self._curl_request('competitor_product_keywords', {
                'amzSite': self.site,
                'asin': self.asin,
                'page': page
            })

            if not response.get('has_error') and response.get('data'):
                keywords_data = extract_keywords_from_response(response.get('data', {}))
                words = [normalize_keyword_data(kw) for kw in keywords_data]
                words = [w for w in words if w['keyword']]

                if words:
                    # 检查是否与已有数据重复
                    unique_words = [w for w in words if w['keyword'].lower() not in [kw['keyword'].lower() for kw in long_tail]]
                    if unique_words:
                        long_tail.extend(unique_words)
                        success_count += 1
                        print(f" ✓ ({len(unique_words)} 个新词)")
                    else:
                        print(f" (全部重复，停止)")
                        break
                else:
                    print(f" (无数据)")
                    break
            else:
                fail_count += 1
                print(f" ✗")
                break

        print(f"    ✓ 扩展完成，共获得 {len(long_tail)} 个长尾词")
        if fail_count > 0:
            print(f"    ⚠ {fail_count} 个请求失败")

        return long_tail

    def _get_product_node_id(self) -> str:
        """从产品详情中获取 NodeID"""
        self._log("获取产品 NodeID...", 'DEBUG')
        response = self._curl_request('product_detail', {
            'amzSite': self.site,
            'asin': self.asin
        })

        if response.get('has_error'):
            self._log(f"获取产品详情失败: {response.get('error')}", 'WARN')
            return None

        data = response.get('data', {})
        if isinstance(data, dict):
            # 查找 NodeID 字段
            for key in ['nodeId', 'NodeID', '类目ID', 'category_id', '所在nodeid']:
                if key in data:
                    node_id = str(data[key])
                    self._log(f"找到 NodeID: {node_id}", 'DEBUG')
                    return node_id

            # 尝试从类目信息中提取
            data_str = str(data)
            if '类目' in data_str or 'category' in data_str.lower():
                # 查找 nodeId 模式
                match = re.search(r'nodeId["\']?\s*:\s*["\']?(\d+)', data_str, re.IGNORECASE)
                if match:
                    node_id = match.group(1)
                    self._log(f"从文本提取 NodeID: {node_id}", 'DEBUG')
                    return node_id

        self._log("未找到 NodeID", 'WARN')
        return None

    def get_product_detail(self) -> dict:
        """
        获取产品详情

        Returns:
            dict: 包含原始响应和解析后的数据
        """
        self._log("获取产品详情...", 'DEBUG')
        response = self._curl_request('product_detail', {
            'amzSite': self.site,
            'asin': self.asin
        })

        if response.get('has_error'):
            self._log(f"获取产品详情失败: {response.get('error')}", 'WARN')
            return None

        # 保存完整的响应（包含 text 和 data 字段）
        self.product_detail = response
        return response

    def collect_all(self, long_tail_limit: int = 30) -> tuple:
        """
        采集所有关键词

        Args:
            long_tail_limit: 长尾词扩展的核心词数量（0 表示跳过长尾词扩展）

        Returns:
            tuple: (去重后的完整关键词列表, 产品信息字典)
        """
        print(f"\n开始采集关键词: {self.asin} ({self.site})")
        print("-" * 50)

        all_keywords = []
        self.errors = []  # 清空错误记录

        # Step 0: 获取产品详情（用于后续分类）
        product_info = self.get_product_detail()
        if product_info:
            print(f"  ✓ 产品名称: {product_info.get('product_name', 'Unknown')}")
            print(f"  ✓ 品牌: {product_info.get('brand', 'Unknown')}")

        # Step 1: 基础采集
        traffic = self.collect_traffic_terms()
        competitor = self.collect_competitor_keywords()
        category = self.collect_category_keywords()

        all_keywords.extend(traffic)
        all_keywords.extend(competitor)
        all_keywords.extend(category)

        # Step 2: 去重并选择核心词
        unique_keywords = self._deduplicate_keywords(all_keywords)
        self._log(f"Step 2 去重后: {len(unique_keywords)} 个关键词", 'INFO')

        # Step 3: 长尾词扩展（如果 limit > 0）
        if long_tail_limit > 0 and unique_keywords:
            core_for_expansion = sorted(unique_keywords,
                                       key=lambda x: x.get('search_volume', 0),
                                       reverse=True)
            long_tail = self.collect_long_tail_keywords(core_for_expansion, long_tail_limit)
            self._log(f"Step 3 获得了 {len(long_tail)} 个长尾词", 'INFO')
            all_keywords.extend(long_tail)
            self._log(f"Step 3 添加长尾词后: {len(all_keywords)} 个关键词（包含重复）", 'INFO')

        # Step 4: 最终去重
        final_keywords = self._deduplicate_keywords(all_keywords)
        self._log(f"Step 4 最终去重后: {len(final_keywords)} 个关键词", 'INFO')

        print("-" * 50)
        print(f"✓ 采集完成: 共 {len(final_keywords)} 个关键词\n")

        # 输出错误摘要
        if self.errors:
            print(f"⚠ 发生 {len(self.errors)} 个错误（已跳过）:")
            for err in self.errors[:3]:  # 只显示前 3 个
                print(f"  - {err.get('step')}: {err.get('error')}")
            if len(self.errors) > 3:
                print(f"  ... 还有 {len(self.errors) - 3} 个错误")
            print()

        # 解析产品信息为结构化格式
        parsed_product_info = self._parse_product_info(product_info) if product_info else {}

        return final_keywords, parsed_product_info

    def _parse_product_info(self, product_detail_response: dict) -> dict:
        """
        解析产品详情为结构化格式

        Args:
            product_detail_response: API 返回的完整响应（parse_sse_response 格式）

        Returns:
            dict: 结构化的产品信息
        """
        parsed = {
            'product_name': '',
            'brand': '',
            'materials': [],
            'features': [],
            'use_cases': [],
            'negative_features': [],
            'description': '',
            'category': ''
        }

        if not product_detail_response:
            return parsed

        # 从响应中提取文本（parse_sse_response 返回的格式）
        raw_text = product_detail_response.get('text', '')

        if not raw_text:
            self._log("产品详情文本为空", 'DEBUG')
            return parsed

        # 文本已经在 parse_sse_response 中解码过了，直接使用
        decoded_text = raw_text
        parsed['description'] = decoded_text

        # 解析键值对（格式：中文键名：值）
        lines = decoded_text.split('\n')
        for line in lines:
            line = line.strip()
            if '：' in line or ': ' in line:
                # 分割键值对（同时支持中文冒号和英文冒号）
                if '：' in line:
                    parts = line.split('：', 1)
                else:
                    parts = line.split(': ', 1)

                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()

                    # 解析各个字段
                    if key in ['标题', 'Title', 'title', '产品名称']:
                        parsed['product_name'] = value
                    elif key in ['品牌', 'Brand', 'brand']:
                        parsed['brand'] = value
                    elif key in ['分类', 'Category', 'category']:
                        parsed['category'] = value
                    elif key in ['产品描述', '描述', 'Description', 'description']:
                        parsed['description'] = value

        # 从产品名称和描述中提取更多信息
        combined_text = (parsed['product_name'] + ' ' + parsed['description']).lower()

        # 材质（从描述中提取常见材质词）
        materials_list = ['wood', 'wooden', 'metal', 'aluminum', 'bamboo',
                         'plastic', 'steel', 'iron', 'ceramic', 'glass',
                         'fabric', 'leather', 'canvas', 'paper', 'cotton',
                         'silicone', 'rubber', 'foam', 'polyester', 'abs',
                         'pvc', 'electronic']
        for material in materials_list:
            if material in combined_text:
                parsed['materials'].append(material.title())

        # 特性（从标题或描述中提取）
        feature_keywords = ['waterproof', 'foldable', 'adjustable', 'portable',
                           'heavy duty', 'rustic', 'vintage', 'expandable',
                           'multi-functional', 'easy to use', 'remote control',
                           'rechargeable', 'battery operated', 'electronic',
                           'interactive', 'realistic', 'imitates', 'walking',
                           'sounds', 'shaking head', 'wagging tail', 'demonstration',
                           'one-touch', 'sing', '2.4g', '8-channel', 'large capacity']
        for feature in feature_keywords:
            if feature in combined_text:
                parsed['features'].append(feature.title())

        # 使用场景（常见场景词）
        scenarios = ['entryway', 'bathroom', 'mudroom', 'garage', 'bedroom',
                    'kitchen', 'living room', 'office', 'outdoor', 'indoor',
                    'patio', 'deck', 'baby', 'kids', 'children', 'toddler',
                    'birthday', 'christmas', 'halloween', 'gift', 'party']
        for scenario in scenarios:
            if scenario in combined_text:
                parsed['use_cases'].append(scenario.title())

        # 否定特征（基于常见不匹配特征推断）
        # 如果产品是 dinosaur/animal toy，排除其他类型的玩具
        if 'dinosaur' in combined_text or 'velociraptor' in combined_text:
            parsed['negative_features'].extend([
                'Car Toys', 'Building Blocks', 'Dolls', 'Stuffed Animals',
                'Board Games', 'Puzzles', 'Art Supplies'
            ])

        # 如果是 remote control，排除非电动玩具
        if 'remote control' in combined_text:
            parsed['negative_features'].extend([
                'Manual', 'Hand Crank', 'Wind Up', 'Pull Back'
            ])

        return parsed

    def _deduplicate_keywords(self, keywords: list) -> list:
        """
        去重并合并数据

        如果有重复关键词，保留搜索量最高的版本
        """
        keyword_map = {}

        for kw in keywords:
            normalized = kw['keyword'].lower().strip()
            if not normalized:
                continue

            # 如果已存在，保留搜索量更高的
            if normalized in keyword_map:
                existing = keyword_map[normalized]
                if kw.get('search_volume', 0) > existing.get('search_volume', 0):
                    keyword_map[normalized] = kw
            else:
                keyword_map[normalized] = kw

        # 转换回列表，恢复原始大小写
        seen = set()
        unique = []
        for kw in keywords:
            normalized = kw['keyword'].lower().strip()
            if normalized in keyword_map and normalized not in seen:
                # 使用去重后数据（可能搜索量更高）
                unique.append(keyword_map[normalized])
                seen.add(normalized)

        return unique


def main():
    """命令行测试入口"""
    if len(sys.argv) < 3:
        print("用法: python keyword_collector.py <ASIN> <站点> [长尾词扩展数量]")
        print("示例: python keyword_collector.py B07PWTJ4H1 US 30")
        print("      python keyword_collector.py B07PWTJ4H1 US 0  # 跳过长尾词扩展")
        sys.exit(1)

    asin = sys.argv[1]
    site = sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    collector = KeywordCollector(asin, site, verbose=True)
    keywords, product_info = collector.collect_all(long_tail_limit=limit)

    # 输出产品信息
    if product_info:
        print(f"\n产品信息:")
        print(f"  名称: {product_info.get('product_name', 'Unknown')}")
        print(f"  品牌: {product_info.get('brand', 'Unknown')}")
        if product_info.get('materials'):
            print(f"  材质: {', '.join(product_info['materials'])}")
        if product_info.get('features'):
            print(f"  特性: {', '.join(product_info['features'])}")

    # 输出统计
    print(f"\n关键词统计:")
    print(f"  总数: {len(keywords)}")
    print(f"  总搜索量: {sum(kw.get('search_volume', 0) for kw in keywords):,}")

    # Top 20 关键词
    print(f"\nTop 20 关键词:")
    print("-" * 80)
    sorted_kw = sorted(keywords, key=lambda x: x.get('search_volume', 0), reverse=True)[:20]
    for i, kw in enumerate(sorted_kw, 1):
        print(f"  {i:2}. {kw['keyword']:<40} | 搜索量: {kw.get('search_volume', 0):,}")
    print("-" * 80)


if __name__ == "__main__":
    main()
