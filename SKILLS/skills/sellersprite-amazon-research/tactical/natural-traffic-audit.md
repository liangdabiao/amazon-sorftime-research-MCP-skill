# 自然流量反查

找自然流量占比高的 ASIN（验证是否为真实需求驱动）。

## 工具
`mcp__sellersprite__traffic_source` — `{"request": {"marketplace":"US", "asin":"B0XXX"}}`

## 过滤标准
- 自然流量占比 > 60%（0~1 比较 > 0.6）

## 输出
流量结构饼图 + 自然/广告/推荐占比 + 验证结论
