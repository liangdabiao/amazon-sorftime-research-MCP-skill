# `market_research` — 选市场 / 市场全景分析

对应网页：大数据选品 → 选市场（`POST /v2/market-research`）

## 用途
给父类目（节点/关键词）+ 多维筛选，返回细分市场列表及 ~100 个市场级指标。

## 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `marketplace` | string | 站点 |
| `nodeIdPath` | string | 类目节点 `parentId:childId`（优先） |
| `keyword` / `departmentKeyword` | string | 类目关键词 |
| `month` | string | yyyyMM |
| `newProduct` | int | 新品定义月数：1/3/6/12，默认 6 |
| `topNum` | int | 头部商品数，默认 10 |
| `sellerLocation` | string | 卖家所属地（仅单值有效） |
| `size` | int | 返回条数 |

### 筛选参数刻度
- 集中度（`*Crn`）/占比（`*Proportion`）：**0~1 小数**
  - 网页按百分比填则需 ÷100

## 响应字段

| 字段 | 含义 | 刻度 |
|------|------|------|
| `nodeLabelName/path` | 细分市场名/路径 | |
| `topProducts/brands/sellers` | 样本商品/品牌/卖家数 | |
| `totalProducts` | 类目在售商品总数 | |
| `totalUnits/totalRevenue` | 样本月总销量/销售额 | |
| `avgUnits/avgRevenue/avgPrice/avgBsr/avgRating/avgRatings` | 各项均值 | |
| `top{3,5,10,20}{Product,Brand,Seller}Crn` | 分层集中度 | **0~1，展示×100** |
| `fbaProportion/fbmProportion/amazonSelfProportion` | 卖家结构 | **已是百分数** |
| `returnRatio` | 退货率 | **已是百分数** |
| `l{1,3,6,12}NewRatio` / `NewCount` | 新品占比/数量 | Ratio **0~1，展示×100** |

## 网页→MCP 改名
`HeadListing*→Top*`、`*Ratio→*Proportion`、`*Sales→*Units`、`*Reviews→*Ratings`、`*TotalProducts→*GoodsCount`、`marketId→marketplace`、`monthName→month`、`topn→topNum`、`newReleaseNum→newProduct`

## 市场分布工具集

| 工具 | 用途 |
|------|------|
| `market_price_distribution` | 价格区间分布 |
| `market_brand_concentration` | 品牌集中度 |
| `market_product_concentration` | 商品集中度 |
| `market_seller_concentration` | 卖家集中度 |
| `market_rating_distribution` | 评分值分布 |
| `market_ratings_count_distribution` | 评分数分布 |
| `market_listing_date_distribution` | 上架时间分布 |
| `market_seller_country_distribution` | 卖家所属地分布 |
| `market_seller_type_concentration` | 发货类型分布 |
| `market_ebc_distribution` | A+页面与视频分布 |
| `market_product_demand_trend` | 需求趋势 |
| `market_research_statistics` | 市场深入统计 |

## 分布工具实际字段名（实测，避开陷阱）

分布工具返回的 `data` 是**直接数组**（非 `{items: [...]}`），字段名与 `market_research` 完全不同。

### 公共字段
大多数分布工具共用以下字段（注意不是 `totalProducts` / `totalProductsProportion`）：

| 工具返回字段 | 含义 | 刻度 |
|------------|------|------|
| `products` / `asinNum` | ASIN/商品数 | 整数 |
| `units` | 样本销量 | 整数 |
| `revenue` | 样本销售额 | float |
| `unitsRatio` | 销量占比 | **0~1 小数**，展示 ×100 |
| `revenueRatio` | 销售额占比 | **0~1 小数**，展示 ×100 |
| `asinRatio` | ASIN占比（配送类型专用） | **0~1 小数**，展示 ×100 |
| `productsRatio` | ASIN占比（A+专用） | **已是百分数**，不换算 |

### 各工具独有字段

| 工具 | 独有字段 | 说明 |
|------|---------|------|
| `market_price_distribution` | `label`(价格带如"0-150"), `products`, `units`, `revenue`, `unitsRatio` | label 是价格区间字符串 |
| `market_brand_concentration` | `brand`, `ranking`, `products`, `newProducts`, `avgPrice`, `ratings`, `rating`, `totalUnits`, `totalRevenue`, `totalUnitsRatio` | **`totalUnits` 不是 `units`** |
| `market_seller_concentration` | `sellerName`, `sellerId`, `totalUnits`, `totalRevenue`, `totalUnitsRatio` | 与品牌结构类似 |
| `market_seller_country_distribution` | `country`(=label), `products`, `units`, `revenue`, `unitsRatio` | 用 `country` 字段 |
| `market_seller_type_concentration` | `asinNum`, `asinRatio`, `units`, `unitsRatio`, `productNum` | 用 `asinNum` 非 `products` |
| `market_rating_distribution` | `label`(评分区间), `products`, `units`, `unitsRatio` | |
| `market_ratings_count_distribution` | `label`(评分数区间), `products`, `units`, `unitsRatio` | |
| `market_listing_date_distribution` | `label`(时间), `products`, `units`, `unitsRatio` | 样本较小时可能全 0 |
| `market_ebc_distribution` | `label`, `products`, `productsRatio`, `units`, `unitsRatio` | `productsRatio` 已是 % |
| `market_product_demand_trend` | `label`(月份), `products`, `units`, `revenue` | |
| `market_product_concentration` | `label`, `asinNum`, `unitsRatio` | |

## 陷阱
1. 根节点统计全 0，必须选叶子节点
2. 集中度 0~1 展示 ×100；`returnRatio`/`*Proportion` 不换算
3. `sellerLocation` 多选无效，需拆单值再并集
4. 月份未就绪取最近自然月
