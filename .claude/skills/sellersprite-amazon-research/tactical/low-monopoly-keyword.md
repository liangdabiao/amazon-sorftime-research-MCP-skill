# 流量分散关键词

找搜索量大但点击集中度低的关键词（蓝海词）。

## 工具
`mcp__sellersprite__keyword_miner` — `{"request": {...}}`

## 筛选参数
- `minSearch`: 5000
- 客户端过滤 `monopolyClickRate < 0.5`（集中度<50%）

## 输出
蓝海关键词表 + 搜索量/购买率/竞价/供需比

## 注意
`monopolyClickRate` 为 0~1，过滤比较 < 0.5
