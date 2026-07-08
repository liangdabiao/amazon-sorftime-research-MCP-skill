# 低品牌垄断类目

找品牌集中度低的类目（新品牌友好）。

## 工具
`mcp__sellersprite__market_research` — `{"request": {...}}`

## 筛选
- 客户端过滤 `topBrandCrn <= 0.45`（品牌集中度≤45%）

## 输出
低垄断类目列表 + 市场规模/增长/竞争格局

## 注意
`topBrandCrn` 为 0~1，过滤比较 ≤ 0.45
