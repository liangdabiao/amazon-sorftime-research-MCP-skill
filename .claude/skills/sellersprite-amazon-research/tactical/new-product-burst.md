# 新品快速爆发

找上架不久但销量已快速攀升的新品。

## 工具
`mcp__sellersprite__product_research` — `{"request": {...}}`

## 筛选参数
- `minUnits`: 300, `maxRatings`: 100, `minUnitsCr`: 正增长
- 按 `units` 降序

## 逻辑
上架≤2月 + 月销量≥300 + Review≤100 → 已验证市场需求，评论门槛低。

## 输出
新品 ASIN 列表 + 销量/价格/评分/BSR 对比 + 进入可行性分析

## 注意
响应字段用 `units`(销量)、`revenue`(销售额)、`ratings`(评分)
