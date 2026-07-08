# `keyword_miner` — 关键词挖掘 / 种子词扩展

对应网页：关键词优化 → 关键词挖掘（`POST /v3/api/keyword-miner`）

## 用途
输入种子词（或 ASIN），挖掘相关长尾词及需求/竞争指标。

## 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `marketplace` | string | 站点（1=US,2=CA,...见下文） |
| `keyword` | string | 种子词或 ASIN |
| `month` / `historyDate` | string | yyyyMM |
| `page/size` | int | 分页 |
| `order.field` / `order.desc` | string/bool | 默认 searches |
| `filterRootWord` | int | 0=全部 1=仅词根 |
| `includeKeywords/excludeKeywords` | string | 包含/排除关键词 |
| `keywordList` | string | 批量精确查询 |
| `minRelevancy/minSearchRank/minSearch` | 区间筛选 | 服务端直名参数 |
| `minPurchases/minPurchasesRate/minSPR` | 区间筛选 | |
| `minTitleDensity/minProducts` | 区间筛选 | |
| `minSupplyDemandRatio/minAdProducts` | 区间筛选 | |
| `minMonopolyClickRate/minBid/minWordCount` | 区间筛选 | |

### 市场编码
1=US 2=CA 3=UK 4=DE 5=FR 6=IT 7=ES 8=JP 9=IN 10=MX 11=BR 12=AU 13=AE

### 客户端兜底筛选（MCP 无对应区间参数）
`impressions`、`clicks`、`cvsShareRate`：在客户端对响应过滤

## 响应字段

| 字段 | 说明 | 刻度 |
|------|------|------|
| `keyword` | 关键词 | |
| `searches/purchases` | 搜索量/购买量 | |
| `purchaseRate` | 购买率 | **0~1，展示×100** |
| `products/adProducts` | 商品数/广告商品数 | |
| `supplyDemandRatio` | 供需比 | **真实比值** |
| `avgPrice/avgRating` | 均价/平均评分 | |
| `bid/bidMin/bidMax` | PPC 竞价 | |
| `cvsShareRate` | 转化份额 | **0~1，展示×100** |
| `titleDensity` | 标题密度 | |
| `spr` | SPR 值 | |
| `monopolyClickRate` | 点击集中度 | **0~1，展示×100** |
| `clicks/impressions` | 点击/曝光 | |
| `wordCount` | 词数 | |
| `departments` | 所属类目 | |

## 陷阱
1. `purchaseRate/cvsShareRate/monopolyClickRate` 为 0~1，展示 ×100
2. `supplyDemandRatio` 真实比值不换算
3. 种子词扩展用 `keyword_miner`；类目关键词选品用 `keyword_research`
