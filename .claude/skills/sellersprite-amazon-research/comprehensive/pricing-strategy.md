# 定价策略分析

分析市场价格带分布，制定最优定价策略。

## 使用方式

```
/pricing-strategy [类目关键词或节点ID] [站点]
```

## 工具调用

通过 MCP client 调用：`mcp__sellersprite__<tool_name>`，均使用 `request` 嵌套参数。

**响应解析**：`result.content[0].text` 是 JSON 字符串，需二次解析。

## 执行步骤

### 第1步: 获取类目节点

`mcp__sellersprite__product_node` — `{"request": {"marketplace":"US", "keyword":"..."}}`

### 第2步: 获取价格分布

`mcp__sellersprite__market_price_distribution` — `{"request": {"marketplace":"US", "nodeIdPath":"..."}}`
- 返回 `data` 是直接数组（非 `{items: [...]}`），字段：`label`(价格带)、`products`、`units`、`unitsRatio`(0~1)

### 第3步: 获取竞品价格

`mcp__sellersprite__competitor_lookup` — `{"request": {"marketplace":"US", "nodeIdPath":"..."}}`

### 第4步: 保存结果 + 生成报告

同时保存原始数据和报告到 `{类别目录}/`。

**报告结构：** 市场价格带总览 → 最佳定价带 → Top竞品定价 → 利润空间 → 推荐定价策略 → 促销策略建议
