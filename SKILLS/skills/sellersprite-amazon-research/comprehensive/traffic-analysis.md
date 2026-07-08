# 流量结构分析

拆解 ASIN 的流量来源，分析自然/广告/推荐流量结构。

## 使用方式

```
/traffic-analysis [ASIN] [站点]
```

## 工具调用

通过 MCP client 调用：`mcp__sellersprite__<tool_name>`

**响应解析**：`result.content[0].text` 是 JSON 字符串，需二次解析。

## 执行步骤

### 第1步: 获取流量来源

`mcp__sellersprite__traffic_source` — **扁平参数** + `"q": "asin"`

```json
{"marketplace": "US", "asin": "B0XXX", "q": "asin"}
```

> ⚠️ 实测：文档标为 `request` 嵌套对象，但实际 API 要求扁平参数 + `q` 字段。`q` 值固定传 `"asin"`。

### 第2步: 获取关键词流量统计

`mcp__sellersprite__traffic_keyword_stat` — 扁平参数 `{"marketplace":"US", "asin":"B0XXX"}`
- ⚠️ 实际字段：`keywords`(总数)、`ranks`(有排名)、`ads`(有广告)

### 第3步: 获取完整流量词

`mcp__sellersprite__traffic_keyword` — `{"request": {"marketplace":"US", "asin":"B0XXX"}}`

### 第4步: 保存结果 + 生成报告

同时保存原始数据和报告到 `{类别目录}/`。

**报告结构：** 流量总览 → 自然/广告/推荐占比（饼图，0~1×100）→ Top流量词 → 自然排名表现 → 广告投放分析 → 流量缺口 → 优化建议

### 字段注意
- `trafficPercentage/naturalRatio/adRatio` 为 0~1，展示 ×100
- `rankPosition`/`adPosition` 是对象，取 `.position`
