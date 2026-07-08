# Keyword Research Skill

亚马逊关键词深度调研与智能分类分析技能。

## 功能特点

- 基于 **Sorftime MCP** 数据采集 2000+ 关键词
- 通过 **LLM Agent** 按 8 维度智能分类
- 生成 Markdown 报告、CSV 词库和 HTML 仪表板

## 8 维分类模型

| 分类 | 说明 | 应用策略 |
|------|------|----------|
| NEGATIVE | 否定/敏感词 | 直接添加为否定关键词 |
| BRAND | 品牌词 | 竞品打法或否定 |
| MATERIAL | 材质词 | 精准词组匹配 |
| SCENARIO | 使用场景词 | 按场景拆分广告组 |
| ATTRIBUTE | 属性修饰词 | 长尾精准匹配 |
| FUNCTION | 功能词 | 广泛匹配扩流 |
| CORE | 核心产品词 | 大词投放占领坑位 |
| OTHER | 其他 | 补充埋词 |

## 使用方法

### 通过 Skill 触发

```bash
/keyword-research B07PWTJ4H1 US
```

### 命令行直接运行

```bash
# 基础用法
python .claude/skills/keyword-research/scripts/workflow.py B07PWTJ4H1 US

# 带产品信息
python .claude/skills/keyword-research/scripts/workflow.py B07PWTJ4H1 US --product-info product.json

# 指定长尾词扩展数量
python .claude/skills/keyword-research/scripts/workflow.py B07PWTJ4H1 US --long-tail-limit 20
```

## 产品信息文件（可选）

```json
{
  "product_name": "Coat Rack Wall Mount",
  "material": "Wood",
  "features": ["Wall Mount", "5 Hooks", "16.5 inches", "Heavy Duty"],
  "use_cases": ["Entryway", "Bathroom", "Mudroom"],
  "negative_features": ["Freestanding", "Over Door", "Floor"]
}
```

## 输出文件

```
keyword-reports/
└── {ASIN}_{Site}_{YYYYMMDD}/
    ├── report.md                    # Markdown 分析报告
    ├── keywords.csv                 # 完整词库（分类后）
    ├── keywords_negative.csv        # 否定词专用
    ├── negative_words.txt           # 否定词清单
    ├── brand_words.txt              # 品牌词清单
    ├── categorized_summary.json     # 分类统计
    ├── dashboard.html               # HTML 仪表板
    └── execution.log                # 执行日志
```

## 数据采集流程

1. **产品流量词** (product_traffic_terms): 50-200 个
2. **竞品布局词** (competitor_product_keywords): 100-500 个
3. **类目核心词** (category_keywords): 100-500 个
4. **长尾词扩展** (keyword_related_words): 1000-2000 个

## API 依赖

本技能使用 Sorftime MCP 以下接口：

- `product_traffic_terms` - 产品流量关键词
- `competitor_product_keywords` - 竞品布局关键词
- `category_keywords` - 类目核心关键词
- `keyword_related_words` - 长尾词扩展
- `product_detail` - 产品详情（获取 NodeID）

## 注意事项

1. **API Key**: 自动从 `.mcp.json` 读取
2. **分类方式**: 使用 LLM Agent 批量分类（每批 150 个关键词）
3. **数据去重**: 自动归一化处理（小写、去除特殊字符）
4. **编码**: UTF-8，支持中文和特殊字符

## 故障排查

### API 认证失败
```
❌ Authentication required - Invalid API Key
```
**解决**: 检查 `.mcp.json` 中的 API Key 是否正确

### 产品未找到
```
未查询到对应产品
```
**解决**: 确认 ASIN 是否存在于 Sorftime 数据库

### 分类结果不准确
**解决**: 提供产品信息 JSON 文件以提高分类准确性

## 文件结构

```
.claude/skills/keyword-research/
├── SKILL.md                          # 技能定义
├── README.md                         # 本文件
├── scripts/
│   ├── workflow.py                   # 主工作流
│   ├── keyword_collector.py          # 关键词采集
│   ├── data_parser.py                # SSE 数据解析
│   ├── csv_generator.py              # CSV 生成
│   ├── generate_markdown_report.py   # Markdown 报告
│   └── generate_html_dashboard.py    # HTML 仪表板
└── templates/
    └── dashboard_template.html       # HTML 模板
```

## 版本

v1.0 - 2026-03-13
