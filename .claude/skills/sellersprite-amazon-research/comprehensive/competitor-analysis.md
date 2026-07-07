# 竞品深度拆解

对竞品 ASIN 进行全面拆解，覆盖产品信息、关键词流量、趋势和变体。

## 使用方式

```
/competitor-analysis [ASIN或关键词] [站点]
```

## 工具调用

所有工具通过 MCP client 调用：`mcp__sellersprite__<tool_name>`

**参数模式**：大部分工具使用 `request` 嵌套对象；少量工具（`asin_detail`, `traffic_keyword_stat`, `keepa_info` 等）使用扁平参数。

**响应解析**：`result.content[0].text` 是 JSON 字符串，需二次解析：
```python
raw = json.loads(result['content'][0]['text'])
data = raw.get('data', [])
```

## 执行步骤

### 第1步: 获取竞品列表（如输入为关键词）

调用 `mcp__sellersprite__competitor_lookup`：
- 参数：`{"request": {"marketplace":"US", "keyword":"..."}}`

若用户直接提供 ASIN，跳过此步。

### 第2步: 并行获取 ASIN 深度数据

1. **`mcp__sellersprite__asin_detail`** — 扁平参数 `{"marketplace":"US", "asin":"B0XXX"}`
2. **`mcp__sellersprite__traffic_keyword`** — `{"request": {"marketplace":"US", "asin":"B0XXX"}}`
3. **`mcp__sellersprite__keepa_info`** — 扁平参数 `{"marketplace":"US", "asin":"B0XXX"}`
   - 返回 `buyBox` 是 `[{timePoint, value}]` 数组，取最后一项为当前价
   - `bsr` 同理取 `[{timePoint, value}]` 格式
4. **`mcp__sellersprite__traffic_source`** — `{"request": {"marketplace":"US", "asin":"B0XXX"}}`

### 第3步: 辅助数据

- `mcp__sellersprite__asin_prediction` — 扁平参数
- `mcp__sellersprite__asin_coupon_trend` — 扁平参数

### 第4步: 保存结果

同时保存两份文件：
1. **原始数据** → `{类别目录}/research_data.json`
2. **分析报告** → `{类别目录}/competitor_report.md`

### 第5步: 生成报告

**报告结构：** 竞品概览 → 销量与趋势 → 流量结构（自然/广告占比 0~1，展示×100）→ 关键词覆盖（rankPosition 取 .position）→ 定价促销 → 变体分析 → SWOT → 应对策略
