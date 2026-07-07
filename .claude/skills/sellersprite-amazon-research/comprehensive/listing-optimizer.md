# Listing 优化诊断

诊断 Listing 质量，发现关键词覆盖缺口。

## 使用方式

```
/listing-optimizer [ASIN] [站点]
```

## 工具调用

通过 MCP client 调用：`mcp__sellersprite__<tool_name>`

**响应解析**：`result.content[0].text` 是 JSON 字符串，需二次解析。

## 执行步骤

### 第1步: 获取 Listing 基本信息

`mcp__sellersprite__asin_detail` — 扁平参数 `{"marketplace":"US", "asin":"B0XXX"}`

### 第2步: 获取 Listing 流量数据

`mcp__sellersprite__traffic_listing` — `{"request": {"marketplace":"US", "asin":"B0XXX"}}`

### 第3步: 获取关键词表现

`mcp__sellersprite__keyword_order` — `{"request": {"marketplace":"US", "asin":"B0XXX"}}`

`mcp__sellersprite__traffic_keyword` — `{"request": {"marketplace":"US", "asin":"B0XXX"}}`

### 第4步: 保存结果 + 生成报告

同时保存原始数据和报告到 `{类别目录}/`。

**报告结构：** Listing概览 → 关键词覆盖分析（自然/广告排名）→ 标题优化 → 搜索词埋词 → 图片内容诊断 → 评分评论诊断 → 行动优先级

### 字段注意
- `traffic_keyword` 中 `rankPosition` 取 `.position`
- `naturalRatio/adRatio` 为 0~1，展示 ×100
- HTML 实体解码：`html.unescape(title)`
