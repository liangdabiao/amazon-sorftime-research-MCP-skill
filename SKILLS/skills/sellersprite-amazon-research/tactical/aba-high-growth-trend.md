# ABA 高增长趋势词

通过 ABA 数据发现近 3 月持续增长的关键词。

## 工具
`mcp__sellersprite__keyword_research` — `{"request": {...}}`
`mcp__sellersprite__keyword_research_trends` — 扁平参数 `{"marketplace":"US", "keyword":"..."}`

## 筛选逻辑
- 近 3 月搜索排名持续上升
- `monopolyClickRate` < 50%（0~1 比较 < 0.5）
- `supplyDemandRatio` 20-80

## 输出
高增长关键词表 + 搜索量趋势 + 竞争度 + PPC 竞价

## 注意
`keyword_research_trends` 字段：`time`/`search`/`chainGrowth`(环比)
