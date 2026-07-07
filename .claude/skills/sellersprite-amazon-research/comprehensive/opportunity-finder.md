# 蓝海机会挖掘

通过 ABA 趋势发现飙升/增长/潜力关键词。

## 使用方式

```
/opportunity-finder [关键词或类目] [站点]
```

## 工具调用

通过 MCP client 调用：`mcp__sellersprite__<tool_name>`

**响应解析**：`result.content[0].text` 是 JSON 字符串，需二次解析。

## 执行步骤

### 第1步-第3步: ABA 数据获取

1. `mcp__sellersprite__aba_research_weekly` — `{"request": {"marketplace":"US", "keyword":"..."}}`
2. `mcp__sellersprite__aba_research_monthly` — `{"request": {"marketplace":"US", "keyword":"..."}}`
3. `mcp__sellersprite__aba_research_trend` — 扁平参数 `{"marketplace":"US", "keyword":"..."}`
   - ⚠️ 实际字段：`label`(月份)、`date`、`searches`、`rank`（无 `clickShareRate`/`conversionShareRate`）

### 第4步: Google 趋势（可选）

`mcp__sellersprite__google_trend` — `{"request": {"marketplace":"US", "keyword":"..."}}`

### 第5步: 保存结果 + 生成报告

同时保存原始数据和报告到 `{类别目录}/`。

**报告结构：** 飙升关键词 → 持续增长词 → 季节性机会 → 蓝海词筛选 → Google趋势验证 → 行动建议
