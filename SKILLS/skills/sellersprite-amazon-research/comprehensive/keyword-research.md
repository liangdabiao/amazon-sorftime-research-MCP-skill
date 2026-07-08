# 关键词选品研究

基于关键词进行市场需求分析，挖掘高潜力关键词。

## 使用方式

```
/keyword-research [种子词] [站点]
```

## 工具调用

通过 MCP client 调用：`mcp__sellersprite__<tool_name>`

**参数模式**：`keyword_miner`/`keyword_research` 使用 `request` 嵌套对象；`keyword_research_trends` 使用扁平参数。

**响应解析**：`result.content[0].text` 是 JSON 字符串，需二次解析。

## 执行步骤

### 第1步: 关键词挖掘

调用 `mcp__sellersprite__keyword_miner`：
- 参数：`{"request": {"marketplace":"US", "keyword":"种子词"}}`

### 第2步: 关键词研究

调用 `mcp__sellersprite__keyword_research`：
- 参数：`{"request": {"marketplace":"US", "keyword":"种子词"}}`

### 第3步: 关键词趋势

调用 `mcp__sellersprite__keyword_research_trends`：
- 扁平参数：`{"marketplace":"US", "keyword":"种子词"}`
- ⚠️ 实际字段：`time`（非 `month`）、`search`（非 `searches`）、`chainGrowth`（环比）、`yearlyGrowth`（同比）

### 第4步: 保存结果

同时保存两份文件：
1. **原始数据** → `{类别目录}/research_data.json`
2. **分析报告** → `{类别目录}/keyword_report.md`

### 第5步: 生成报告

**报告结构：** 关键词总览 → 高潜力词表 → 趋势分析 → 竞争分析 → 长尾词机会 → 广告建议

### 字段注意
- `purchaseRate/cvsShareRate/monopolyClickRate` 为 0~1，展示 ×100
- `supplyDemandRatio` 真实比值不换算
- `keyword_research_trends` 用 `time`/`search`/`chainGrowth` 字段，非文档名
