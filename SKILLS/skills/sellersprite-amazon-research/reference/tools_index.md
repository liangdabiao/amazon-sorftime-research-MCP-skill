# SellerSprite MCP 工具清单（43 个）

> 实际工具数 43，文档原标 38。2026-07-05 实测验证。

## ASIN 分析（7）
| 工具名 | 用途 | 必填参数 |
|--------|------|---------|
| `asin_detail` | ASIN 详情查询 | `marketplace`, `asin` |
| `asin_prediction` | 销量预测 | `marketplace`, `asin` |
| `asin_sales_trend` | 销量趋势 | `marketplace`, `asin` |
| `asin_coupon_trend` | 优惠趋势 | `marketplace`, `asin` |
| `asin_detail_with_coupon_trend` | 详情+优惠整合 | `marketplace`, `asin` |
| `keepa_info` | Keepa 历史趋势 | `marketplace`, `asin` |
| `bsr_prediction` | BSR 销量预估 | `marketplace`, `bsr`, `categoryId` |

## 商品与竞品（3）
| 工具名 | 用途 | 必填参数 |
|--------|------|---------|
| `product_research` | 选产品/高级筛选 | `request`（嵌套对象） |
| `competitor_lookup` | 查竞品列表 | `request`（嵌套对象） |
| `product_node` | 类目节点查询 | `request`（嵌套对象） |

## 关键词（4）
| 工具名 | 用途 | 必填参数 |
|--------|------|---------|
| `keyword_miner` | 关键词挖掘（种子词扩展） | `request`（嵌套对象） |
| `keyword_research` | 关键词研究（带增长率） | `request`（嵌套对象） |
| `keyword_research_trends` | 关键词趋势 | `marketplace`, `keyword` |
| `keyword_order` | 关键词排名与转化质量 | `request`（嵌套对象） |

## 流量（6）
| 工具名 | 用途 | 必填参数 |
|--------|------|---------|
| `traffic_keyword` | 关键词反查（ASIN 流量词） | `request`（嵌套对象） |
| `traffic_keyword_stat` | 关键词流量统计 | `marketplace`, `asin` |
| `traffic_source` | 流量来源分析 | `marketplace`, `asin`, **`q`**（扁平参数） |
| `traffic_listing_stat` | Listing 流量统计 | `marketplace`, `asin` |
| `traffic_listing` | Listing 流量详情 | `request`（嵌套对象） |
| `traffic_extend` | 关键词拓展（区间筛选） | `request`（嵌套对象） |

> ⚠️ `traffic_source` 虽然文档标为 `request` 嵌套，但实际需用**扁平参数** + `"q": "asin"`：`{"marketplace":"US","asin":"B0XXX","q":"asin"}`。`q` 值为 `"asin"` 时查询该 ASIN 的流量来源结构。

## 市场研究（15）
| 工具名 | 用途 | 必填参数 |
|--------|------|---------|
| `market_research` | 市场全景数据 | `request`（嵌套对象） |
| `market_research_statistics` | 市场深入统计 | `request`（嵌套对象） |
| `market_price_distribution` | 价格区间分布 | `request`（嵌套对象） |
| `market_brand_concentration` | 品牌集中度 | `request`（嵌套对象） |
| `market_product_concentration` | 商品集中度 | `request`（嵌套对象） |
| `market_seller_concentration` | 卖家集中度 | `request`（嵌套对象） |
| `market_rating_distribution` | 评分值分布 | `request`（嵌套对象） |
| `market_ratings_count_distribution` | 评分数分布 | `request`（嵌套对象） |
| `market_listing_date_distribution` | 上架时间分布 | `request`（嵌套对象） |
| `market_listing_trend_distribution` | 上架趋势分布 | `request`（嵌套对象） |
| `market_seller_country_distribution` | 卖家所属地分布 | `request`（嵌套对象） |
| `market_seller_type_concentration` | 发货类型分布 | `request`（嵌套对象） |
| `market_ebc_distribution` | A+页面与视频分布 | `request`（嵌套对象） |
| `market_product_demand_trend` | 需求趋势 | `request`（嵌套对象） |

## ABA/趋势（4）
| 工具名 | 用途 | 必填参数 |
|--------|------|---------|
| `aba_research_weekly` | ABA 周数据 | `request`（嵌套对象） |
| `aba_research_monthly` | ABA 月数据 | `request`（嵌套对象） |
| `aba_research_trend` | ABA 趋势 | `marketplace`, `keyword` |
| `google_trend` | Google 趋势 | `request`（嵌套对象） |

## 评论（1）
| 工具名 | 用途 | 必填参数 |
|--------|------|---------|
| `review` | 评论数据 | `marketplace`, `asin` |

## 商标（4）🆕
| 工具名 | 用途 | 必填参数 |
|--------|------|---------|
| `trademark_list` | 商标列表查询 | `request`（嵌套对象） |
| `trademark_detail` | 商标详情 | `office`, `brandId` |
| `trademark_stats` | 商标统计 | `request`（嵌套对象） |
| `trademark_country_list` | 商标国家列表 | 无 |

## 参数模式说明

### 模式 A：扁平参数
工具直接在顶层接受 `marketplace`, `asin`, `keyword` 等字段。

### 模式 B：`request` 嵌套对象（最常用）
绝大多数筛选类工具使用 `request` 参数，内部结构如：
```json
{
  "marketplace": "US",
  "nodeIdPath": "11091801:11974521:8882489011:11974711",
  "topNum": 10,
  "size": 50
}
```
调用时将字段全部包裹在 `request` 键下。
