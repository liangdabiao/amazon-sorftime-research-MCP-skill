#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sorftime SSE 响应解析器 - 关键词专用版本
复用 category-selection 的解析逻辑，适配关键词数据格式
"""

import json
import codecs
import re


def fix_mojibake(text):
    """
    修复 Mojibake 编码问题 (UTF-8/Latin-1 双重编码)
    """
    if isinstance(text, str):
        try:
            return text.encode('latin-1').decode('utf-8')
        except:
            return text
    elif isinstance(text, dict):
        return {fix_mojibake(k): fix_mojibake(v) for k, v in text.items()}
    elif isinstance(text, list):
        return [fix_mojibake(item) for item in text]
    return text


def escape_control_chars_in_json(json_str):
    """Escape control characters only within JSON string values"""
    result = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(json_str):
        c = json_str[i]

        if escape_next:
            result.append(c)
            escape_next = False
            i += 1
            continue

        if c == '\\':
            result.append(c)
            escape_next = True
            i += 1
            continue

        if c == '"':
            in_string = not in_string
            result.append(c)
            i += 1
            continue

        if in_string:
            # Within a string, escape control characters
            if c == '\r':
                result.append('\\r')
            elif c == '\n':
                result.append('\\n')
            elif c == '\t':
                result.append('\\t')
            elif ord(c) < 32:
                # Other control chars - replace with space
                result.append(' ')
            else:
                result.append(c)
        else:
            result.append(c)

        i += 1

    return ''.join(result)


def escape_control_chars_in_json_strings(json_str):
    """转义 JSON 字符串值中的控制字符"""
    result = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(json_str):
        c = json_str[i]

        if escape_next:
            result.append(c)
            escape_next = False
            i += 1
            continue

        if c == '\\':
            result.append(c)
            escape_next = True
            i += 1
            continue

        if c == '"':
            in_string = not in_string
            result.append(c)
            i += 1
            continue

        if in_string:
            if c == '\n':
                result.append('\\n')
            elif c == '\r':
                result.append('\\r')
            elif c == '\t':
                result.append('\\t')
            elif ord(c) < 32:
                result.append(' ')
            else:
                result.append(c)
        else:
            result.append(c)

        i += 1

    return ''.join(result)


def parse_sse_response(response: str) -> dict:
    """
    解析 Sorftime SSE 响应

    Args:
        response: curl 返回的 SSE 格式响应

    Returns:
        dict: 解析后的数据
    """
    result = {'text': '', 'data': None, 'has_error': False, 'error': None}

    # 提取 SSE data 行
    for line in response.split('\n'):
        if line.startswith('data: '):
            json_text = line[6:]
            try:
                # 先转义控制字符，再解析 JSON
                escaped_json = escape_control_chars_in_json(json_text)
                data = json.loads(escaped_json)
                result_text = data.get('result', {}).get('content', [{}])[0].get('text', '')
                if result_text:
                    # 解码 Unicode 转义
                    decoded = codecs.decode(result_text, 'unicode-escape')
                    # 修复 Mojibake
                    decoded = fix_mojibake(decoded)
                    result['text'] = decoded

                    # 尝试解析为 JSON 数据
                    try:
                        result['data'] = parse_json_data(decoded)
                    except:
                        pass

                    return result
            except json.JSONDecodeError as e:
                result['error'] = str(e)
                result['has_error'] = True

    # 检查错误响应
    if 'error' in response.lower() or 'Authentication required' in response:
        result['has_error'] = True
        result['error'] = response

    return result


def parse_json_data(text: str):
    """
    从文本中提取并解析 JSON 数据

    Args:
        text: 可能包含 JSON 的文本

    Returns:
        dict or list: 解析后的数据（数组或对象）
    """
    # 转义控制字符
    text = escape_control_chars_in_json_strings(text)

    # 找到 JSON 开始位置（优先查找数组，因为 Sorftime 返回数组）
    json_start = text.find('[')
    if json_start == -1:
        # 尝试查找对象开始
        json_start = text.find('{')
        if json_start == -1:
            return {}

    # 使用括号匹配提取完整内容
    bracket_start = text[json_start]
    depth = 0
    in_string = False
    escape_next = False
    end = -1

    for i in range(json_start, len(text)):
        c = text[i]

        if escape_next:
            escape_next = False
            continue

        if c == '\\':
            escape_next = True
            continue

        if c == '"':
            in_string = not in_string
            continue

        if not in_string:
            if c == bracket_start:
                depth += 1
            elif c == ('}' if bracket_start == '{' else ']'):
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

    if end == -1:
        return {}

    json_str = text[json_start:end]

    # 尝试解析
    try:
        data = json.loads(json_str)
        return fix_mojibake(data)
    except json.JSONDecodeError:
        return {}


def safe_int(value, default=0):
    """安全地转换为整数"""
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        cleaned = re.sub(r'[^\d.-]', '', value)
        try:
            return int(float(cleaned)) if cleaned else default
        except ValueError:
            return default
    return default


def safe_float(value, default=0.0):
    """安全地转换为浮点数"""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r'[^\d.-]', '', value)
        try:
            return float(cleaned) if cleaned else default
        except ValueError:
            return default
    return default


def extract_keywords_from_response(response_data: dict) -> list:
    """
    从 API 响应中提取关键词列表

    支持多种可能的响应格式:
    1. {"关键词": [...]}  - 中文键名
    2. {"keywords": [...]} - 英文键名
    3. 直接是数组
    """
    if not response_data:
        return []

    # 如果是数组，直接返回
    if isinstance(response_data, list):
        return response_data

    # 查找关键词列表
    keywords = []

    # 可能的键名
    possible_keys = [
        '关键词', 'keywords', 'Keywords', '流量词', 'traffic_terms',
        'related_words', '延伸词', 'result', 'data', 'items'
    ]

    for key in possible_keys:
        if key in response_data:
            value = response_data[key]
            if isinstance(value, list):
                keywords = value
                break

    return keywords


def normalize_keyword_data(raw_keyword: dict or str) -> dict:
    """
    标准化关键词数据格式

    Args:
        raw_keyword: 原始关键词数据（可能是字符串或字典）

    Returns:
        dict: 标准化的关键词数据
    """
    if isinstance(raw_keyword, str):
        return {
            'keyword': raw_keyword.strip(),
            'search_volume': 0,
            'cpc': 0,
            'competition': 'unknown'
        }

    if isinstance(raw_keyword, dict):
        # 标准化键名
        keyword = (
            raw_keyword.get('关键词') or
            raw_keyword.get('keyword') or
            raw_keyword.get('Keyword') or
            raw_keyword.get('text') or
            ''
        ).strip()

        # 搜索量可能的键名
        search_volume = 0
        for key in ['月搜索量', 'monthlySearchVolume', 'search_volume', '搜索量', 'volume']:
            if key in raw_keyword:
                search_volume = safe_int(raw_keyword[key])
                break

        # CPC 可能的键名
        cpc = 0
        for key in ['推荐竞价', 'CPC竞价', 'cpc', 'CPC', 'cpc_bid', 'suggested_bid']:
            if key in raw_keyword:
                cpc = safe_float(raw_keyword[key])
                break

        # 竞争度
        competition = raw_keyword.get('competition', raw_keyword.get('竞争度', 'unknown'))

        return {
            'keyword': keyword,
            'search_volume': search_volume,
            'cpc': cpc,
            'competition': competition
        }

    return {
        'keyword': '',
        'search_volume': 0,
        'cpc': 0,
        'competition': 'unknown'
    }
