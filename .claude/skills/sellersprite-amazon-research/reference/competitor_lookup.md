# `competitor_lookup` — 查竞品 / 商品列表查询

对应网页：大数据选品 → 查竞品（`POST /v3/api/competing-lookup`）

## 用途
按 ASIN / 关键词 / 品牌 / 卖家 / 类目 查询 Amazon 商品列表。

## 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `marketplace` | string | 站点 |
| `asins` | array | ASIN 数组，最多 40 |
| `keyword` | string | 关键词 |
| `month` | string | yyyyMM |
| `brand` | string | 品牌名 |
| `sellerName` | string | 卖家名 |
| `nodeIdPath/nodeIdPaths` | string/array | 类目节点 |
| `matchType` | int | 1=词组 2=模糊 3=精准 |
| `page/size` | int | 分页 |
| `variation` | string | "Y" 去重 |
| `order.field` / `order.desc` | string/bool | 排序 |

## 响应字段改名

| 网页 API | MCP 字段 |
|----------|----------|
| `totalUnits` | **`units`** |
| `totalAmount` | **`revenue`** |
| `reviews` | **`ratings`** |
| `bsrRank` | **`bsr`** |
| `sellerType` | **`fulfillment`** |

## 陷阱
1. ASIN 须真实存在，否则 `total=0`
2. 响应读 MCP 名（units/revenue/ratings/bsr）
3. 注意：这是列表查询，与单 ASIN 深度分析（asin_detail）不同
