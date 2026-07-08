#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词调研分析主工作流 v1.1

用法:
    python workflow.py B07PWTJ4H1 US
    python workflow.py B07PWTJ4H1 US --product-info product.json
    python workflow.py B07PWTJ4H1 US --long-tail-limit 20
    python workflow.py B07PWTJ4H1 US --skip-long-tail  # 跳过长尾词扩展
"""

import os
import sys
import json
import re
from datetime import datetime
from collections import Counter

# 导入本地模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from keyword_collector import KeywordCollector
from csv_generator import generate_csv_files
from generate_markdown_report import generate_markdown_report
from generate_html_dashboard import generate_html_dashboard


def get_project_root():
    """获取项目根目录"""
    path = os.path.abspath(__file__)
    while path != os.path.dirname(path):
        if os.path.basename(path) == '.claude':
            return os.path.dirname(path)
        path = os.path.dirname(path)
    return os.getcwd()


PROJECT_ROOT = get_project_root()


class KeywordResearchWorkflow:
    """关键词调研分析工作流"""

    def __init__(self, asin: str, site: str = 'US', product_info: dict = None,
                 long_tail_limit: int = 30, skip_classification: bool = False,
                 enable_llm_classification: bool = True, claude_code_env: bool = None):
        self.asin = asin.upper()
        self.site = site.upper()
        self.product_info = product_info or {}
        self.long_tail_limit = long_tail_limit
        self.skip_classification = skip_classification  # 跳过分类，仅保存数据
        self.enable_llm_classification = enable_llm_classification  # 启用 LLM 分类
        self.output_dir = ''
        self.all_keywords = []          # 所有采集的关键词
        self.categorized_keywords = {}  # 分类后的关键词
        self.execution_log = []         # 执行日志

        # 检测运行环境（优先使用手动指定的值）
        if claude_code_env is not None:
            self.is_claude_code_env = claude_code_env
        else:
            self.is_claude_code_env = self._detect_claude_code_environment()  # 自动检测

    def log(self, message: str, level: str = 'INFO'):
        """记录日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.execution_log.append(log_entry)
        print(f"  {message}")

    def _detect_claude_code_environment(self) -> bool:
        """
        检测是否在 Claude Code 环境中运行

        Returns:
            bool: 是否在 Claude Code 环境中
        """
        # 方法1: 检查环境变量
        if os.environ.get('CLAUDE_CODE') or os.environ.get('CLAUDE_CODE_VERSION'):
            return True

        # 方法2: 检查特定环境标识
        # Claude Code 通过 Skill 调用时，父进程通常是特殊的
        if os.environ.get('SKILL_NAME') or os.environ.get('SKILL_MODE'):
            return True

        # 方法3: 检查工作目录特征
        cwd = os.getcwd()
        if '.claude' in cwd or 'skills' in cwd:
            # 进一步验证：检查是否在 .claude/skills 下运行
            script_path = os.path.abspath(__file__)
            if '.claude' in script_path and 'skills' in script_path:
                return True

        # 方法4: 检查命令行参数特征（通过 Skill 调用会有特定模式）
        if len(sys.argv) > 1 and any(arg.upper().startswith('B') for arg in sys.argv[1:3]):
            # 可能是通过 keyword-research skill 调用（ASIN 参数特征）
            # 额外检查：如果是通过 Bash 工具从 Skill 调用
            pass

        # 方法5: 检查 sys 模块
        try:
            if 'claude' in sys.modules or 'anthropic' in sys.modules:
                return True
            # 检查是否有特殊的模块加载路径
            site_packages = [p for p in sys.path if 'site-packages' in p]
            if site_packages and 'anthropic' in str(site_packages):
                return True
        except:
            pass

        return False

    def setup_output_dir(self):
        """设置输出目录"""
        date_str = datetime.now().strftime('%Y%m%d')
        output_base = os.path.join(PROJECT_ROOT, 'keyword-reports')
        os.makedirs(output_base, exist_ok=True)

        dir_name = f"{self.asin}_{self.site}_{date_str}"
        self.output_dir = os.path.join(output_base, dir_name)
        os.makedirs(self.output_dir, exist_ok=True)

        print(f"\n输出目录: {self.output_dir}")

    def step1_collect_keywords(self) -> bool:
        """步骤1: 数据采集"""
        print(f"\n{'='*70}")
        print("步骤 1/4: 采集关键词数据")
        print('='*70)

        try:
            collector = KeywordCollector(self.asin, self.site, verbose=False)
            keywords, fetched_product_info = collector.collect_all(
                long_tail_limit=self.long_tail_limit
            )

            if not keywords:
                self.log("未采集到任何关键词", "ERROR")
                return False

            self.all_keywords = keywords

            # 合并产品信息（优先使用用户提供的，补充自动获取的）
            if fetched_product_info:
                self._merge_product_info(fetched_product_info)
                self.log(f"✓ 产品信息: {self.product_info.get('product_name', 'Unknown')}")

            self.log(f"✓ 采集到 {len(self.all_keywords)} 个关键词")
            return True

        except Exception as e:
            self.log(f"数据采集失败: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    def _merge_product_info(self, fetched_info: dict):
        """
        合并产品信息（用户提供的优先级更高）

        Args:
            fetched_info: 从 API 自动获取的产品信息
        """
        # 如果用户没有提供产品信息，直接使用自动获取的
        if not self.product_info:
            self.product_info = fetched_info
            return

        # 用户提供了产品信息，仅补充缺失的字段
        for key, value in fetched_info.items():
            if not self.product_info.get(key):
                self.product_info[key] = value
            # 对于列表类型字段，合并去重
            elif isinstance(value, list) and value:
                existing = self.product_info.get(key, [])
                if isinstance(existing, list):
                    combined = list(set(existing + value))
                    self.product_info[key] = combined

    def step2_classify_keywords(self) -> bool:
        """步骤2: LLM 智能分类"""
        print(f"\n{'='*70}")
        print("步骤 2/4: LLM 智能分类（8 维度）")
        print('='*70)

        # 如果跳过分类，直接使用智能规则分类
        if self.skip_classification:
            self.log("跳过 LLM 分类，使用智能规则分类", "INFO")
            self.categorized_keywords = self._smart_classify()
            self._log_classification_summary()
            return True

        try:
            # 准备关键词列表（仅关键词字符串）
            keyword_list = [kw['keyword'] for kw in self.all_keywords]

            # 构建分类 prompt
            classification_prompt = self._build_classification_prompt(
                keyword_list, self.product_info
            )

            # 保存 prompt 用于调试
            prompt_file = os.path.join(self.output_dir, 'classification_prompt.txt')
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(classification_prompt)
            self.log(f"分类提示词已保存: {prompt_file}")

            # 检测运行环境
            if self.is_claude_code_env and self.enable_llm_classification:
                # 在 Claude Code 环境中，输出标记让 Agent 执行 LLM 分类
                print(f"\n" + "="*70)
                print("🤖 Claude Code 环境 - 触发 LLM 分类")
                print("="*70)

                # 先尝试加载已存在的分类结果
                self.categorized_keywords = self._load_categorized_result()

                if self.categorized_keywords:
                    self.log("✓ 使用已有分类结果", "INFO")
                else:
                    # 输出特殊标记，让 Skill 系统知道需要执行 LLM 分类
                    print(f"\n>>> LLM_CLASSIFICATION_NEEDED <<<")
                    print(f">>> PROMPT_FILE: {prompt_file} <<<")
                    print(f">>> OUTPUT_FILE: {os.path.join(self.output_dir, 'categorized_result.json')} <<<")
                    print("\n📋 分类提示词内容:")
                    print("-" * 70)
                    # 输出完整提示词的前1000字符作为预览
                    preview = classification_prompt[:3000] if len(classification_prompt) > 3000 else classification_prompt
                    print(preview)
                    if len(classification_prompt) > 3000:
                        print(f"\n... (省略 {len(classification_prompt) - 3000} 字符，完整内容见 {prompt_file})")
                    print("-" * 70)

                    # 暂时使用规则分类作为后备
                    self.log("⏳ 等待 LLM 分类结果...", "INFO")
                    self.categorized_keywords = self._smart_classify()

                    # 记录这是临时分类结果
                    self.log("⚠ 使用规则分类作为临时结果，可重新执行 LLM 分类", "WARN")
            else:
                # 非 Claude Code 环境，优先加载已有分类结果
                reason = "已跳过分类" if self.skip_classification else "非 Claude Code 环境"
                self.log(f"{reason}，尝试加载已有分类结果", "INFO")
                
                # 尝试加载已存在的分类结果
                self.categorized_keywords = self._load_categorized_result()
                
                if self.categorized_keywords:
                    self.log("✓ 使用已有 LLM 分类结果", "INFO")
                else:
                    self.log("⚠ 无已有分类结果，使用智能规则分类", "WARN")
                    self.categorized_keywords = self._smart_classify()

            self._log_classification_summary()
            return True

        except Exception as e:
            self.log(f"分类失败: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            # 异常情况下使用规则分类
            self.categorized_keywords = self._smart_classify()
            self._log_classification_summary()
            return True

    def _log_classification_summary(self):
        """记录分类摘要"""
        total_categorized = sum(len(v) for v in self.categorized_keywords.values())
        self.log(f"✓ 分类完成，共 {total_categorized} 个关键词已分类")

        for category, keywords in self.categorized_keywords.items():
            if keywords:
                cat_name = self._get_category_display_name(category)
                self.log(f"  - {cat_name}: {len(keywords)} 个")

        # 记录分类方法到摘要
        if hasattr(self, 'is_claude_code_env') and self.is_claude_code_env:
            method = "LLM (Claude Code)" if self.enable_llm_classification and not self.skip_classification else "规则"
        else:
            method = "规则"
        self.log(f"分类方法: {method}", "INFO")

    def _smart_classify(self) -> dict:
        """
        智能规则分类（备用方案）

        基于关键词模式和产品信息进行智能分类
        """
        # 构建产品上下文
        product_context = self._build_product_context()

        # 获取产品名称和核心属性
        product_name = self.product_info.get('product_name', '')
        if not product_name:
            # 从关键词中推断
            core_keywords = sorted(self.all_keywords,
                                 key=lambda x: x.get('search_volume', 0),
                                 reverse=True)[:5]
            product_name = core_keywords[0]['keyword'] if core_keywords else ''

        categorized = {
            'NEGATIVE': [],
            'BRAND': [],
            'MATERIAL': [],
            'SCENARIO': [],
            'ATTRIBUTE': [],
            'FUNCTION': [],
            'CORE': [],
            'OTHER': []
        }

        # 常见否定词模式（根据产品类型动态调整）
        negative_patterns = self._get_negative_patterns(product_context)
        brand_patterns = self._get_brand_patterns()
        material_patterns = self._get_material_patterns(product_context)
        scenario_patterns = self._get_scenario_patterns(product_context)
        attribute_patterns = self._get_attribute_patterns()
        function_patterns = self._get_function_patterns()

        for kw in self.all_keywords:
            keyword = kw['keyword'].lower()
            assigned = False

            # 1. 检查否定词
            for pattern, reason in negative_patterns:
                if pattern in keyword and reason:
                    categorized['NEGATIVE'].append(kw['keyword'])
                    assigned = True
                    break

            if not assigned:
                # 2. 检查品牌词
                for brand in brand_patterns:
                    if brand in keyword:
                        categorized['BRAND'].append(kw['keyword'])
                        assigned = True
                        break

            if not assigned:
                # 3. 检查材质词
                for material in material_patterns:
                    if material in keyword:
                        categorized['MATERIAL'].append(kw['keyword'])
                        assigned = True
                        break

            if not assigned:
                # 4. 检查场景词
                for scenario in scenario_patterns:
                    if scenario in keyword:
                        categorized['SCENARIO'].append(kw['keyword'])
                        assigned = True
                        break

            if not assigned:
                # 5. 检查属性词
                for attr in attribute_patterns:
                    if attr in keyword:
                        categorized['ATTRIBUTE'].append(kw['keyword'])
                        assigned = True
                        break

            if not assigned:
                # 6. 检查功能词
                for func in function_patterns:
                    if func in keyword:
                        categorized['FUNCTION'].append(kw['keyword'])
                        assigned = True
                        break

            if not assigned:
                # 7. 检查核心词（包含产品名称的）
                if product_name and product_name.lower() in keyword:
                    categorized['CORE'].append(kw['keyword'])
                    assigned = True

            if not assigned:
                # 默认放到核心词（如果是短词）或其他（如果是长词）
                if len(kw['keyword'].split()) <= 3:
                    categorized['CORE'].append(kw['keyword'])
                else:
                    categorized['OTHER'].append(kw['keyword'])

        return categorized

    def _build_product_context(self) -> dict:
        """构建产品上下文信息"""
        context = {
            'product_name': '',
            'materials': [],
            'use_cases': [],
            'negative_features': []
        }

        if self.product_info:
            context['product_name'] = self.product_info.get('product_name', '')
            context['materials'] = self.product_info.get('materials', self.product_info.get('material', []))
            context['use_cases'] = self.product_info.get('use_cases', [])
            context['negative_features'] = self.product_info.get('negative_features', [])

        # 如果没有产品信息，从关键词推断
        if not context['product_name'] and self.all_keywords:
            top_keywords = sorted(self.all_keywords,
                                key=lambda x: x.get('search_volume', 0),
                                reverse=True)[:10]
            # 简单推断：最常见的词根
            word_counter = Counter()
            for kw in top_keywords:
                words = kw['keyword'].lower().split()
                word_counter.update(words)

            if word_counter:
                most_common = word_counter.most_common(1)[0][0]
                context['product_name'] = most_common

        return context

    def _get_negative_patterns(self, context: dict) -> list:
        """获取否定词模式"""
        # 基础否定词
        base_patterns = [
            ('freestanding', '与壁挂式不符'),
            ('floor', '与壁挂式不符'),
            ('door', '与墙面不符'),
            ('over door', '与墙面不符'),
            ('tree', '与墙面不符'),
            ('shoe', '不同产品类别'),
        ]

        # 根据产品上下文添加特定否定词
        if context.get('negative_features'):
            for feature in context['negative_features']:
                base_patterns.append((feature.lower(), f'与产品特性不符: {feature}'))

        return base_patterns

    def _get_brand_patterns(self) -> list:
        """获取品牌词模式（包含IP品牌）"""
        # 家居品牌
        home_brands = [
            'umbra', 'simplehuman', 'mdesign', 'mDesign',
            'household essentials', 'colonial candle',
            'melissa & doug', 'crayola'
        ]

        # IP品牌（玩具/娱乐）
        ip_brands = [
            # 电影/电视
            'star wars', 'stranger things', 'lord of the rings', 'game of thrones',
            'marvel', 'dc comics', 'harry potter', 'pixar', 'disney',
            # 游戏
            'minecraft', 'fortnite', 'roblox', 'pokemon', 'zelda',
            'dungeons and dragons', 'dnd', 'dragon age', 'skyrim',
            # 动画/系列
            'ninjago', 'monkie kid', 'hidden side', 'bionicle', 'nexo knights',
            'angry birds', 'avatar', 'how to train your dragon',
            # 其他玩具品牌
            'playmobil', 'barbie', 'hot wheels', 'nerf', 'hasbro'
        ]

        return home_brands + ip_brands

    def _get_material_patterns(self, context: dict) -> list:
        """获取材质词模式"""
        materials = ['wooden', 'wood', 'metal', 'aluminum', 'bamboo',
                    'plastic', 'steel', 'iron', 'ceramic', 'glass',
                    'fabric', 'leather', 'canvas', 'paper']

        # 添加产品特定材质
        if context.get('materials'):
            materials.extend([m.lower() for m in context['materials']])

        return materials

    def _get_scenario_patterns(self, context: dict) -> list:
        """获取场景词模式"""
        scenarios = ['entryway', 'bathroom', 'mudroom', 'garage',
                    'bedroom', 'kitchen', 'living room', 'office',
                    'outdoor', 'indoor', 'patio', 'deck']

        # 添加产品特定场景
        if context.get('use_cases'):
            scenarios.extend([s.lower() for s in context['use_cases']])

        return scenarios

    def _get_attribute_patterns(self) -> list:
        """获取属性词模式"""
        return [
            # 安装方式
            'mount', 'wall mount', 'freestanding', 'over door',
            # 特性
            'heavy duty', 'rustic', 'vintage', 'expandable', 'folding',
            # 组件
            'hook', 'shelf', 'rack', 'holder', 'organizer', 'storage', 'container',
            # 尺寸
            'large', 'small', 'medium', 'mini', 'giant', 'big',
            # 主题/风格（玩具/套装常用）
            'medieval', 'castle', 'knight', 'viking', 'fantasy', 'dragon',
            'minifigure', 'set', 'building', 'construction'
        ]

    def _get_function_patterns(self) -> list:
        """获取功能词模式"""
        return [
            'hanging', 'display', 'organizer', 'storage',
            'holder', 'stand', 'rack', 'shelf'
        ]

    def _build_classification_prompt(self, keywords: list, product_info: dict) -> str:
        """构建分类提示词"""
        # 格式化产品信息
        product_desc = self._format_product_info(product_info)

        # 准备关键词 JSON（前500个作为示例）
        sample_keywords = json.dumps(keywords[:500], ensure_ascii=False)

        prompt = f"""你是一位亚马逊关键词分类专家。请根据以下产品信息，将关键词列表按 8 个维度分类。

{product_desc}

【分类维度说明】
1. **NEGATIVE (否定/敏感词)**: 与产品不相关、描述不符的词，需直接否定
   - 例：freestanding（落地式）vs wall mount（壁挂式）
   - 例：over door（门后）vs wall（墙面）

2. **BRAND (品牌词)**: 竞品品牌名称
   - 例：umbra, simplehuman, mDesign, household essentials

3. **MATERIAL (材质词)**: 描述产品材质的词
   - 例：wooden, metal, aluminum, bamboo, plastic

4. **SCENARIO (使用场景词)**: 产品使用的位置/场景
   - 例：entryway, bathroom, mudroom, garage, bedroom

5. **ATTRIBUTE (属性修饰词)**: 描述产品属性/特性的词
   - 例：wall mount, heavy duty, rustic, vintage, expandable

6. **FUNCTION (功能词)**: 描述产品功能的词
   - 例：hanging, storage, organizer, display

7. **CORE (核心产品词)**: 产品核心名称
   - 例：coat rack, hook, hanger, hat rack, towel rack

8. **OTHER (其他)**: 未分类、拼写错误、其他语言等
   - 例：coatrac（拼写错误）, perchero（西语）

【待分类关键词】（共 {len(keywords)} 个，前500个示例）
{sample_keywords}

【输出格式】
请严格按照以下 JSON 格式输出，不要包含任何其他内容：
```json
{{
  "NEGATIVE": ["keyword1", "keyword2", ...],
  "BRAND": ["keyword1", "keyword2", ...],
  "MATERIAL": ["keyword1", "keyword2", ...],
  "SCENARIO": ["keyword1", "keyword2", ...],
  "ATTRIBUTE": ["keyword1", "keyword2", ...],
  "FUNCTION": ["keyword1", "keyword2", ...],
  "CORE": ["keyword1", "keyword2", ...],
  "OTHER": ["keyword1", "keyword2", ...]
}}
```

注意：每个关键词只能属于一个分类，请根据最相关的特征进行分类。如果关键词超过500个，请按相同规则处理剩余关键词。

【产品信息参考】
ASIN: {self.asin}
站点: {self.site}
"""

        return prompt

    def _format_product_info(self, product_info: dict) -> str:
        """格式化产品信息"""
        if not product_info:
            return "【产品信息】未提供（请根据 ASIN 推断）"

        info_parts = ["【产品信息】"]
        for key, value in product_info.items():
            if isinstance(value, list):
                info_parts.append(f"{key}: {', '.join(str(v) for v in value)}")
            else:
                info_parts.append(f"{key}: {value}")

        return '\n'.join(info_parts)

    def _load_categorized_result(self) -> dict:
        """加载分类结果（从文件或通过其他方式）"""
        result_file = os.path.join(self.output_dir, 'categorized_result.json')

        # 尝试读取已存在的分类结果
        if os.path.exists(result_file):
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.log(f"读取分类结果失败: {e}", 'WARN')

        # 如果没有文件，返回空字典（需要 Agent 填充）
        return {}

    def _get_category_display_name(self, category: str) -> str:
        """获取分类显示名称"""
        names = {
            'NEGATIVE': '否定/敏感词',
            'BRAND': '品牌词',
            'MATERIAL': '材质词',
            'SCENARIO': '使用场景词',
            'ATTRIBUTE': '属性修饰词',
            'FUNCTION': '功能词',
            'CORE': '核心产品词',
            'OTHER': '其他',
            'CHARACTER': '角色词'  # 特殊分类
        }
        return names.get(category, category)

    def step3_generate_reports(self) -> bool:
        """步骤3: 生成报告"""
        print(f"\n{'='*70}")
        print("步骤 3/4: 生成分析报告")
        print('='*70)

        try:
            # 生成 CSV 文件
            print("  生成 CSV 词库...")
            csv_files = generate_csv_files(
                self.all_keywords,
                self.categorized_keywords,
                self.output_dir
            )
            for file in csv_files:
                print(f"    ✓ {os.path.basename(file)}")

            # 生成 Markdown 报告
            print("  生成 Markdown 分析报告...")
            report_file = generate_markdown_report(
                self.asin,
                self.site,
                self.all_keywords,
                self.categorized_keywords,
                self.output_dir,
                self.product_info
            )
            print(f"    ✓ {os.path.basename(report_file)}")

            # 生成 HTML 仪表板
            print("  生成 HTML 可视化仪表板...")
            dashboard_file = generate_html_dashboard(
                self.asin,
                self.site,
                self.all_keywords,
                self.categorized_keywords,
                self.output_dir,
                self.product_info
            )
            print(f"    ✓ {os.path.basename(dashboard_file)}")

            # 保存原始数据
            data_file = os.path.join(self.output_dir, 'keywords_raw.json')
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_keywords, f, ensure_ascii=False, indent=2)
            print(f"    ✓ keywords_raw.json")

            return True

        except Exception as e:
            self.log(f"报告生成失败: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    def step4_save_summary(self) -> bool:
        """步骤4: 保存执行摘要"""
        try:
            # 保存执行日志
            log_file = os.path.join(self.output_dir, 'execution.log')
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.execution_log))

            # 保存分类摘要
            summary_file = os.path.join(self.output_dir, 'summary.json')
            summary = {
                'asin': self.asin,
                'site': self.site,
                'generated_at': datetime.now().isoformat(),
                'total_keywords': len(self.all_keywords),
                'categorized': {
                    cat: len(kws) for cat, kws in self.categorized_keywords.items()
                },
                'output_directory': self.output_dir,
                'long_tail_limit': self.long_tail_limit
            }
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            self.log(f"保存摘要失败: {e}", "ERROR")
            return False

    def run(self) -> bool:
        """执行完整工作流"""
        print("\n" + "="*70)
        print(f"关键词调研分析: {self.asin} ({self.site})")
        print("="*70)

        # 设置输出目录
        self.setup_output_dir()

        # 执行工作流
        success = True

        if not self.step1_collect_keywords():
            self.log("数据采集失败", "ERROR")
            success = False

        # 注意：步骤2需要 Agent 介入执行分类
        # 如果使用命令行直接运行，会提示用户手动分类
        if success and not self.categorized_keywords:
            if not self.step2_classify_keywords():
                success = False

        if success and self.categorized_keywords:
            if not self.step3_generate_reports():
                self.log("报告生成失败", "ERROR")
                success = False

        if success:
            self.step4_save_summary()

        # 打印总结
        print("\n" + "="*70)
        if success:
            print("✓ 分析完成!")
            print(f"报告位置: {self.output_dir}")
            print("\n生成的文件:")
            for file in sorted(os.listdir(self.output_dir)):
                print(f"  - {file}")
        else:
            print("✗ 分析失败，请查看错误信息")
        print("="*70)

        return success


def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        print("用法: python workflow.py <ASIN> <站点> [选项]")
        print("\n选项:")
        print("  --product-info <json文件>   产品信息文件")
        print("  --long-tail-limit <数量>    长尾词扩展数量（默认30，0表示跳过）")
        print("  --skip-long-tail            跳过长尾词扩展")
        print("  --skip-classification       跳过LLM分类，仅保存数据（可后续手动分类）")
        print("  --enable-llm-classification 启用LLM分类（默认启用）")
        print("  --disable-llm-classification 禁用LLM分类，使用规则分类")
        print("  --claude-code-env           指定在Claude Code环境中运行（触发LLM分类）")
        print("\n示例:")
        print("  python workflow.py B07PWTJ4H1 US")
        print("  python workflow.py B07PWTJ4H1 US --product-info product.json")
        print("  python workflow.py B07PWTJ4H1 US --long-tail-limit 20")
        print("  python workflow.py B07PWTJ4H1 US --skip-long-tail")
        print("  python workflow.py B07PWTJ4H1 US --skip-classification")
        print("  python workflow.py B07PWTJ4H1 US --claude-code-env")
        print("\n注意:")
        print("  - 在 Claude Code 环境中，默认自动使用 LLM 分类")
        print("  - 在命令行环境中，默认使用规则分类")
        print("  - 使用 --claude-code-env 可强制启用 LLM 分类模式")
        print("  - 使用 --skip-classification 可仅采集数据，稍后手动分类")
        sys.exit(1)

    asin = sys.argv[1]
    site = sys.argv[2]
    product_info = None
    long_tail_limit = 30
    skip_classification = False
    enable_llm_classification = True
    claude_code_env = None  # None=自动检测，True=强制启用，False=强制禁用

    # 解析参数
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--product-info' and i + 1 < len(sys.argv):
            with open(sys.argv[i + 1], 'r', encoding='utf-8') as f:
                product_info = json.load(f)
            i += 2
        elif sys.argv[i] == '--long-tail-limit' and i + 1 < len(sys.argv):
            long_tail_limit = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--skip-long-tail':
            long_tail_limit = 0
            i += 1
        elif sys.argv[i] == '--skip-classification':
            skip_classification = True
            i += 1
        elif sys.argv[i] == '--disable-llm-classification':
            enable_llm_classification = False
            i += 1
        elif sys.argv[i] == '--enable-llm-classification':
            enable_llm_classification = True
            i += 1
        elif sys.argv[i] == '--claude-code-env':
            claude_code_env = True
            i += 1
        elif sys.argv[i] == '--no-claude-code-env':
            claude_code_env = False
            i += 1
        else:
            i += 1

    # 运行工作流
    workflow = KeywordResearchWorkflow(
        asin, site, product_info, long_tail_limit,
        skip_classification, enable_llm_classification, claude_code_env
    )
    success = workflow.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
