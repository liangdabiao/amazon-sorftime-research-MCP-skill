# `traffic_keyword` — 关键词反查 / ASIN 流量词

对应网页：关键词优化 → 关键词反查（`POST /v3/api/relation/reversing`）

## 用途
输入 ASIN，返回其实际获得曝光/流量的关键词列表。

## 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `marketplace` | string | 站点 |
| `asin` | string | ASIN（单值） |
| `month` | string | yyyyMM |
| `keyword` | string | 关键词过滤 |
| `size/page` | int | 分页 |
| `badges` | string | 多选，大小写不敏感 |
| `order.field` / `order.desc` | string/bool | 排序，默认 trafficPercentage |

### 配套工具
- `traffic_extend`：支持区间筛选，但字段不全
- 推荐做法：`traffic_keyword` 全字段取数，客户端过滤

## 响应字段（零改名）

| 字段 | 说明 | 刻度 |
|------|------|------|
| `keyword` | 关键词 | |
| `searches` | 搜索量 | |
| `purchases` | 购买量 | |
| `purchaseRate` | 购买率 | **0~1，展示×100** |
| `bid/bidMin/bidMax` | PPC 竞价 | |
| `rankPosition` | 自然排名对象 `{page,index,position}` | 取 `.position` |
| `adPosition` | 广告排名对象 | 取 `.position` |
| `supplyDemandRatio` | 供需比 | **真实比值** |
| `trafficPercentage` | 流量占比 | **0~1，展示×100** |
| `naturalRatio/adRatio` | 自然/广告占比 | **0~1，展示×100** |
| `monopolyClickRate` | 点击集中度 | **0~1，展示×100** |
| `top3ClickingRate/top3ConversionRate` | Top3 点击/转化率 | **0~1，展示×100** |
| `clicks/impressions` | 点击/曝光 | |
| `products` | 商品数 | |
| `calculatedWeeklySearches` | 周均搜索量 | |

## 陷阱
1. `purchaseRate/trafficPercentage/naturalRatio/adRatio` 为 0~1，展示 ×100
2. `supplyDemandRatio` 真实比值不换算
3. `rankPosition`/`adPosition` 是对象，取 `.position` 展示
4. 别用 `keyword_order` 当反查全集（字段少）
