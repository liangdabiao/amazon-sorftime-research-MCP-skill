---
name: "keyword-research"
description: "亚马逊关键词深度调研与智能分类分析。基于 Sorftime MCP 数据采集 2000+ 关键词，通过 LLM Agent 按 8 维度智能分类（否定词、品牌词、材质词、场景词、属性词、功能词、核心词、其他），生成 Markdown 报告、CSV 词库和 HTML 仪表板。触发方式：/keyword-research {ASIN} {SITE}"
---

# 关键词调研分析 Skill

## 快速参考

| 步骤 | Sorftime API | 用途 | 数据量 |
|------|--------------|------|--------|
| 1 | `product_traffic_terms` | 产品流量关键词 | 50-200 |
| 2 | `competitor_product_keywords` | 竞品布局关键词 | 100-500 |
| 3 | `category_keywords` | 类目核心关键词 | 100-500 |
| 4 | `keyword_related_words` | 长尾词扩展 | 1000-2000 |
| 5 | **LLM Agent** | 8 维智能分类 | 全量 |

**一键执行**:
```bash
# 在 Claude Code 环境中运行（自动触发 LLM 分类）
python .claude/skills/keyword-research/scripts/workflow.py B07PWTJ4H1 US --claude-code-env
```

**其他选项**:
```bash
# 跳过分类，仅采集数据（后续可手动LLM分类）
python .claude/skills/keyword-research/scripts/workflow.py B07PWTJ4H1 US --skip-classification

# 禁用LLM分类，使用规则分类
python .claude/skills/keyword-research/scripts/workflow.py B07PWTJ4H1 US --disable-llm-classification
```

## 触发条件

当用户使用以下方式请求时启动此分析流程：
- **命令**: `/keyword-research {ASIN} {站点}`
- **示例**: `/keyword-research B07PWTJ4H1 US`
- **自然语言**: "分析这个产品的关键词词库"、"调研 B07PWTJ4H1 的关键词"

---

## 角色设定

你是一位拥有 10 年经验的"亚马逊 PPC 广告专家"和"关键词策略分析师"。你精通亚马逊 A9 算法和关键词布局策略，能够从海量关键词中识别出高价值词和需要排除的词。

---

## 数据采集策略：方案 A（基于 ASIN 的深度分析）

```
输入: ASIN + 站点 + (可选) 产品信息
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 1: 基础数据采集                                         │
├─────────────────────────────────────────────────────────────┤
│ 1. product_traffic_terms      → 产品流量词 (50-200个)       │
│ 2. competitor_product_keywords → 竞品布局词 (100-500个)     │
│ 3. category_keywords           → 类目核心词 (100-500个)      │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: 长尾词扩展                                          │
├─────────────────────────────────────────────────────────────┤
│ 从基础词中选择 Top 30 核心词                                 │
│ → 对每个调用 keyword_related_words (50-100个延伸词)         │
│ → 预计获取 1000-2000 个长尾词                               │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: 数据清洗                                            │
├─────────────────────────────────────────────────────────────┤
│ 1. 去重（归一化：小写、去除特殊字符）                        │
│ 2. 过滤无效词（过短、非英文、乱码）                          │
│ 3. 合并搜索量/CPC 等指标                                    │
└─────────────────────────────────────────────────────────────┘
  ↓
最终词库: 2000+ 关键词
```

---

## 关键词分类：8 维智能分类模型

### 分类维度

| 维度 | 标识 | 识别规则 | 应用策略 |
|------|------|----------|----------|
| **否定/敏感词** | NEGATIVE | 与产品不相关、描述不符的词 | 直接添加为否定关键词 |
| **品牌词** | BRAND | 竞品品牌名称 | 竞品打法或否定 |
| **材质词** | MATERIAL | 产品材质相关词 | 精准词组匹配 |
| **场景词** | SCENARIO | 使用场景/位置词 | 按场景拆分广告组 |
| **属性修饰词** | ATTRIBUTE | 产品属性/特性词 | 长尾精准匹配 |
| **功能词** | FUNCTION | 产品功能相关词 | 广泛匹配扩流 |
| **核心产品词** | CORE | 产品核心名称 | 大词投放占领坑位 |
| **其他** | OTHER | 未分类、拼写错误、其他语言 | 补充埋词 |

### 分类识别示例（以 Coat Rack 为例）

```
产品信息: Coat Rack Wall Mount, Wood, 5 Hooks, Entryway

否定词: freestanding, over door, floor, tree, shoe
品牌词: umbra, simplehuman, mDesign, household essentials
材质词: wood, wooden, metal, aluminum, bamboo
场景词: entryway, bathroom, mudroom, garage, bedroom
属性词: wall mount, heavy duty, rustic, vintage, expandable, 5 hook
功能词: hanging, storage, organizer, display
核心词: coat rack, hook, hanger, hat rack, towel rack
其他: coatrac (拼写错误), perchero (西语)
```

---

## 执行流程

### 阶段一：数据采集

#### Step 1.1: 获取产品流量词

```bash
curl -s -X POST "https://mcp.sorftime.com?key={API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"product_traffic_terms","arguments":{"amzSite":"US","asin":"ASIN"}}}'
```

**返回数据**: 关键词列表，包含搜索量、CPC 等指标

#### Step 1.2: 获取竞品布局词

```bash
curl -s -X POST "https://mcp.sorftime.com?key={API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"competitor_product_keywords","arguments":{"amzSite":"US","asin":"ASIN"}}}'
```

**返回数据**: 竞品在各关键词下的排名位置

#### Step 1.3: 获取类目核心词

```bash
# 首先获取产品详情以获取 NodeID
curl -s -X POST "https://mcp.sorftime.com?key={API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"product_detail","arguments":{"amzSite":"US","asin":"ASIN"}}}'

# 然后获取类目关键词
curl -s -X POST "https://mcp.sorftime.com?key={API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"category_keywords","arguments":{"amzSite":"US","nodeId":"NODE_ID"}}}'
```

#### Step 1.4: 长尾词扩展

从基础词中选择 Top 30 核心，对每个调用：

```bash
curl -s -X POST "https://mcp.sorftime.com?key={API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":N,"method":"tools/call","params":{"name":"keyword_related_words","arguments":{"amzSite":"US","searchKeyword":"KEYWORD"}}}'
```

---

### 阶段二：LLM 智能分类

#### 分类提示词模板

```
你是一位亚马逊关键词分类专家。请根据以下产品信息，将关键词列表按 8 个维度分类。

【产品信息】
产品名称: {product_name}
材质: {material}
核心属性: {features}
使用场景: {use_cases}
否定特征: {negative_features}

【分类维度】
1. NEGATIVE: 不相关的词，需直接否定
2. BRAND: 竞品品牌名称
3. MATERIAL: 材质相关词 (wood, metal, aluminum...)
4. SCENARIO: 使用场景词 (entryway, bathroom...)
5. ATTRIBUTE: 属性修饰词 (wall mount, heavy duty...)
6. FUNCTION: 功能词 (hanging, storage...)
7. CORE: 核心产品词 (coat rack, hook...)
8. OTHER: 其他（拼写错误、其他语言等）

【待分类关键词】
{keywords_json}

【输出格式】
请以 JSON 格式输出：
{
  "NEGATIVE": ["word1", "word2", ...],
  "BRAND": [...],
  ...
}
```

#### 批量处理策略

- **批次大小**: 每批 150 个关键词
- **并行处理**: 可并发多个批次
- **结果合并**: 统计各分类数量，汇总关键词

---

### 阶段三：报告生成

#### 输出文件结构

```
keyword-reports/
└── {ASIN}_{Site}_{YYYYMMDD}/
    ├── report.md                    # Markdown 分析报告
    ├── keywords.csv                 # 完整关键词词库（分类后）
    ├── negative_words.txt           # 否定词清单
    ├── brand_words.txt              # 品牌词清单
    ├── categorized_summary.json     # 分类统计
    └── dashboard.html               # HTML 可视化仪表板
```

#### keywords.csv 格式

```csv
keyword,category,search_volume,cpc,competition,application,relevance_score
coat rack,CORE,54000,1.85,high,广泛匹配,1.00
wooden coat rack,MATERIAL,12000,1.25,medium,精准匹配,0.95
freestanding coat rack,NEGATIVE,4500,0.85,low,直接否定,0.00
...
```

---

## 产品信息支持（可选）

为提高分类准确性，支持用户提供产品信息：

### 输入方式

**方式 1**: 命令行参数
```bash
python workflow.py B07PWTJ4H1 US --product-info product.json
```

**方式 2**: 交互式收集
```bash
请输入产品核心属性（用逗号分隔）:
> Wall Mount, 5 Hooks, 16.5 inches, Heavy Duty
```

### 产品信息 JSON 格式

```json
{
  "product_name": "Coat Rack Wall Mount",
  "material": "Wood",
  "features": ["Wall Mount", "5 Hooks", "16.5 inches", "Heavy Duty"],
  "use_cases": ["Entryway", "Bathroom", "Mudroom", "Garage"],
  "negative_features": ["Freestanding", "Over Door", "Floor"]
}
```

---

## Sorftime API 参考

### 关键词相关接口

| 接口 | 调用消耗 | 参数 | 返回 |
|------|----------|------|------|
| `product_traffic_terms` | 1 | asin, site | 产品流量词 |
| `competitor_product_keywords` | 1 | asin, site | 竞品布局词 |
| `category_keywords` | 1 | nodeId, site | 类目核心词 |
| `keyword_related_words` | 1 | searchKeyword, site | 延伸长尾词 |
| `keyword_detail` | 1 | keyword, site | 关键词详情 |
| `product_detail` | 1 | asin, site | 产品详情 |

### 调用格式

```bash
curl -s -X POST "https://mcp.sorftime.com?key={API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":N,"method":"tools/call","params":{"name":"TOOL_NAME","arguments":{"amzSite":"US","KEY":"VALUE"}}}'
```

---

## 支持的站点

**Amazon**: US, GB, DE, FR, IN, CA, JP, ES, IT, MX, AE, AU, BR, SA

---

## 注意事项

1. **API Key 配置**: 自动从 `.mcp.json` 读取
2. **数据去重**: 归一化处理（小写、去除特殊字符）
3. **LLM 分类**: 批量处理，每批 150 个关键词
4. **输出编码**: UTF-8，支持中文和特殊字符
5. **报告命名**: `{ASIN}_{Site}_{YYYYMMDD}` 格式

---

## 故障排查

### 问题 1: API 返回 "未查询到对应产品"
**原因**: ASIN 不存在于 Sorftime 数据库
**解决**:
1. 使用 `product_search` 验证 ASIN
2. 检查站点是否正确

### 问题 2: 分类结果不准确
**原因**: 缺少产品信息上下文或使用了规则分类
**解决**:
1. 提供产品信息 JSON 文件
2. 在 Claude Code 环境中运行以使用 LLM 分类
3. 手动执行 LLM 分类后保存到 `categorized_result.json`

### 问题 3: 长尾词扩展数量不足
**原因**: 核心词选择不准确或 API 限流
**解决**:
1. 调整核心词选择策略，增加搜索量权重
2. 降低 `--long-tail-limit` 数量避免 API 限流
3. 使用 `--skip-long-tail` 跳过长尾扩展

### 问题 4: 分类显示 "分类失败或未提供结果" 或 使用了规则分类
**原因**: 在命令行环境中运行，没有触发 LLM 分类
**解决**:
1. 使用 `--claude-code-env` 参数强制启用 LLM 分类模式：
   ```bash
   python workflow.py B07PWTJ4H1 US --claude-code-env
   ```
2. 系统会输出分类提示词，复制提示词发送给 Claude 执行分类
3. 将分类结果保存为 `categorized_result.json`
4. 重新运行 workflow.py 会自动加载分类结果并重新生成报告

### 问题 5: 如何手动进行 LLM 分类
**场景**: 采集了数据但分类不准确
**解决**:
1. 查看输出目录中的 `classification_prompt.txt`
2. 将提示词发送给 Claude 执行分类
3. 将分类结果保存为 `categorized_result.json`
4. 运行报告重新生成脚本

---

## 参考文档

- [Sorftime API 文档](references/sorftime-keyword-api.md)
- [分类规则说明](references/classification-rules.md)

---

## 手动 LLM 分类流程

如果规则分类结果不准确，可以手动执行 LLM 分类：

### 步骤 1: 查看分类提示词
```bash
cat keyword-reports/{ASIN}_{Site}_{YYYYMMDD}/classification_prompt.txt
```

### 步骤 2: 将提示词发送给 Claude
复制整个提示词内容，发送给 Claude 执行分类

### 步骤 3: 保存分类结果
将 Claude 返回的 JSON 保存到：
```bash
keyword-reports/{ASIN}_{Site}_{YYYYMMDD}/categorized_result.json
```

### 步骤 4: 重新生成报告

`regenerate_reports.py` 支持多种使用方式：

#### 方式 1: 从报告目录内运行（自动检测）
```bash
cd keyword-reports/{ASIN}_{Site}_{YYYYMMDD}/
python ../../.claude/skills/keyword-research/scripts/regenerate_reports.py
```

#### 方式 2: 指定 ASIN 和站点
```bash
python .claude/skills/keyword-research/scripts/regenerate_reports.py --asin B0FG6QG8C8 --site US
```

#### 方式 3: 指定完整输出目录
```bash
python .claude/skills/keyword-research/scripts/regenerate_reports.py --dir "keyword-reports\B0FG6QG8C8_US_20260314"
```

#### 方式 4: 列出所有可用的报告目录
```bash
python .claude/skills/keyword-research/scripts/regenerate_reports.py --list
```

---

## 版本更新记录

### v1.3 (2026-03-14)
- ✅ **优化 regenerate_reports.py**: 移除硬编码 ASIN
- ✅ **支持多种使用方式**:
  - 从报告目录内运行（自动检测）
  - 使用 `--asis` 和 `--site` 参数指定
  - 使用 `--dir` 参数指定完整目录
  - 使用 `--list` 列出所有可用报告
- ✅ **改进错误提示**: 更友好的错误信息和帮助文档

### v1.2 (2026-03-14)
- ✅ 修复 LLM 分类触发问题
- ✅ 添加 `--claude-code-env` 参数强制启用 LLM 分类
- ✅ 改进环境检测逻辑
- ✅ 在 Claude Code 环境中自动触发 LLM 分类
- ✅ 分类完成后自动使用 LLM 结果重新生成报告

### v1.1 (2026-03-14)
- ✅ 添加 Claude Code 环境检测
- ✅ 添加 `--skip-classification` 选项
- ✅ 改进规则分类：扩展 IP 品牌词识别
- ✅ 改进规则分类：添加主题属性词
- ✅ 更新故障排查文档

### v1.0 (2026-03-13)
- 初始版本
- 支持 Sorftime API 数据采集
- 支持 8 维智能分类
- 生成 Markdown/CSV/HTML 报告

---

*本技能版本: v1.3 | 最后更新: 2026-03-14*
