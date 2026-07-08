# 智能选品助手

按多维条件筛选潜力商品，评估进入可行性。

## 使用方式

```
/product-research [关键词] [站点] [筛选条件]
```

## 工具调用

通过 MCP client 调用：`mcp__sellersprite__product_research`

**参数模式**：`request` 嵌套对象 — 所有参数包裹在 `request` 键下。

**响应解析**：`result.content[0].text` 是 JSON 字符串，需二次解析：
```python
raw = json.loads(result['content'][0]['text'])
data = raw.get('data', [])
```

## 执行步骤

### 第1步: 获取类目节点（如需）

调用 `mcp__sellersprite__product_node`：
- 参数：`{"request": {"marketplace": "US", "keyword": "yoga mat"}}`
- ⚠️ `nodeLabelLocale`（中文翻译）不可靠，以英文 `nodeLabelPath` 为准

### 第2步: 执行商品筛选

调用 `mcp__sellersprite__product_research`：
- 参数：`{"request": {"marketplace":"US", "keyword":"...", "minUnits":100, ...}}`

**常用筛选维度：** `keyword`, `marketplace`, `month`, `minUnits/maxUnits`, `minRevenue/maxRevenue`, `minPrice/maxPrice`, `minRating`, `minSubBsrRank`, `fulfillment`("FBA,FBM,AMZ"), `sellerNation`, `minLqs`, `minProfit`

### 第3步: 保存结果

同时保存两份文件：
1. **原始数据** → `{类别目录}/research_data.json`
2. **分析报告** → `{类别目录}/product_report.md`

### 第4步: 生成报告

**报告结构：** 筛选口径 → KPI概览 → 商品候选表（units/revenue/ratings/bsr）→ 进入建议

### 字段注意
- `units`=月销量、`revenue`=月销售额、`ratings`=评分数、`bsr`=BSR
- 多值参数传逗号字符串，当前月数据可能为 None
- HTML 实体解码：`html.unescape(title)`
