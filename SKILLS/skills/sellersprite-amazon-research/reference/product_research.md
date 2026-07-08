# `product_research` — 选产品 / 高级商品筛选

对应网页：大数据选品 → 选产品（`POST /v3/api/product-research`）

## 用途
按关键词 + 多维条件（销量/价格/BSR/评分/利润/配送/卖家等）筛选 Amazon 商品。

## 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `marketplace` | string | 站点（US/JP/UK/DE/FR/IT/ES/CA/IN） |
| `keyword` | string | 搜索关键词 |
| `matchType` | int | 1=词组 2=模糊 3=精准 |
| `month` | string | yyyyMM |
| `minUnits/maxUnits` | int | 月销量区间 |
| `minRevenue/maxRevenue` | float | 月销售额区间 |
| `minPrice/maxPrice` | float | 价格区间 |
| `minSubBsrRank/maxSubBsrRank` | int | 子类 BSR 排名 |
| `minRating/maxRating` | float | 评分区间 |
| `minRatings/maxRatings` | int | 评分数区间 |
| `minRatingsCv` | int | 月新增评分数 |
| `minUnitsCr` | float | 月销量增长率 |
| `minFba` | float | 最低 FBA 运费 |
| `minLqs` | int | Listing 质量分 |
| `minProfit/maxProfit` | float | 利润区间 |
| `fulfillment` | string | FBA,FBM,AMZ（逗号字符串） |
| `includeBrands/excludeBrands` | string | 品牌白/黑名单（逗号字符串） |
| `includeSellers/excludeSellers` | string | 卖家白/黑名单（逗号字符串） |
| `sellerNation` | string | 卖家所属地 |
| `badgeAC/badgeBS/badgeNR` | string | "Y" 过滤 |
| `page/size` | int | 分页，size 默认 50 最大 100 |
| `order.field` / `order.desc` | string/bool | 排序字段和方向 |

## 响应字段改名

| 网页 API | MCP 字段 | 说明 |
|----------|----------|------|
| `totalUnits` | **`units`** | 月销量 |
| `totalAmount` | **`revenue`** | 月销售额 |
| `reviews` | **`ratings`** | 评分数 |
| `bsrRank` | **`bsr`** | BSR 排名 |
| `sellerType` | **`fulfillment`** | FBA/FBM/AMZ |
| `averagePrice` | `averagePrice` | 均价 |
| `amzUnit` | `amzUnit` | 亚马逊自营销量 |

## 陷阱
1. 响应字段读 MCP 名（units/revenue/ratings/bsr），不用网页 API 名
2. 当前月 `units/revenue` 可能为 None，取最近自然月
3. 黑白名单/配送方式传逗号字符串；badges 传 "Y"
