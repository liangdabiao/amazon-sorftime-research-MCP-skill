# 广告投放优化

基于关键词数据优化 PPC 广告策略。

## 使用方式

```
/ad-optimizer [ASIN或关键词] [站点]
```

## 工具调用

通过 MCP client 调用：`mcp__sellersprite__<tool_name>`。

**响应解析**：`result.content[0].text` 是 JSON 字符串，需二次解析。

## 执行步骤

### 第1步: 关键词排名与转化

`mcp__sellersprite__keyword_order` — `{"request": {"marketplace":"US", "asin":"B0XXX"}}`

### 第2步: 流量关键词

`mcp__sellersprite__traffic_keyword` — `{"request": {"marketplace":"US", "asin":"B0XXX"}}`
- 提取：`searches`、`bid/bidMin/bidMax`、`adPosition`、`rankPosition`

### 第3步: 关键词分类

将关键词分为：高价值词（高转化+合理竞价）、机会词（高搜索+低竞价）、低效词（高竞价+低转化）

### 第4步: 保存结果 + 生成报告

同时保存原始数据和报告到 `{类别目录}/`。

**报告结构：** 投放概览 → 高价值词（建议出价）→ 机会关键词 → 否定词建议 → 竞价优化 → 广告结构建议

### 字段注意
- `bid/bidMin/bidMax` 为 PPC 竞价
- `naturalRatio/adRatio` 为 0~1，展示 ×100
- 区分自然排名(`rankPosition.position`)和广告排名(`adPosition.position`)
