# 市场全景分析

对指定的 Amazon 类目进行全面分析，评估市场吸引力、竞争强度和进入可行性。

## 使用方式

```
/market-analysis [类目关键词或节点ID] [站点]
```

参数: 第1个为类目关键词/nodeIdPath（必填），第2个为站点（可选，默认US）

## 执行步骤

### 第1步: 获取类目节点

调用 `product_node` 查找类目节点：
- `marketplace`: 指定站点
- `keyword`: 用户输入的关键词（建议用英文，中文翻译 nodeLabelLocale 不可靠）

⚠️ **必须找到叶子节点**（有具体商品数量的节点），根节点统计全 0。

输出示例：
```json
{"nodeIdPath": "11091801:11974521:8882489011:11974711",
 "nodeLabelPath": "Musical Instruments:Microphones & Accessories:Microphones:Wireless Microphones & Systems",
 "products": 8885}
```

### 第2步: 并行获取市场核心数据

**同时调用：**

1. `market_research` — 市场整体数据
   - 参数模式：`request` 嵌套对象
   - `nodeIdPath`: 第1步获取的节点路径
   - `topNum`: 10
   - `size`: 50

2. `market_research_statistics` — 深入统计
   - 参数模式：`request` 嵌套对象
   - `topN`: 10
   - `newProduct`: 默认6

### 第3步: 并行多维分布分析

并行调用以下 12 个工具（无数据依赖）：
1. `market_price_distribution` — 价格区间分布
2. `market_brand_concentration` — 品牌集中度
3. `market_product_concentration` — 商品集中度
4. `market_seller_concentration` — 卖家集中度
5. `market_rating_distribution` — 评分值分布
6. `market_ratings_count_distribution` — 评分数分布
7. `market_listing_date_distribution` — 上架时间分布
8. `market_seller_country_distribution` — 卖家所属地分布
9. `market_seller_type_concentration` — 发货类型分布
10. `market_ebc_distribution` — A+与视频分布
11. `market_product_demand_trend` — 需求趋势
12. `market_listing_trend_distribution` — 上架趋势分布（🆕新增工具）

### 第4步: 生成并保存市场分析报告

**保存两份文件（必须，禁止仅打印到控制台）：**

1. **原始数据** → `{类别目录}/research_data.json`
   - 所有工具调用的原始返回 JSON，方便后续复查
2. **分析报告** → `{类别目录}/market_report.md`
   - 结构化 Markdown 报告

**报告结构：**
1. **市场概览** — 商品总数、品牌数、卖家数、月总销量/销售额、均价、平均评分
2. **市场吸引力评分**（1-10分各维度）：市场规模、增长性、利润空间、竞争强度、新品友好度、进入门槛 → 综合评分
3. **竞争格局** — 头部集中度、品牌/卖家结构
4. **价格与利润分析** — 各价格带分布、最佳定价建议
5. **新品进入评估** — 新品占比、评论门槛、内容投入建议
6. **风险与机会** — 主要风险和差异化方向
7. **结论与建议** — 是否推荐进入、策略建议

### 刻度陷阱
- 集中度 `top*Crn` / 新品占比 `l*NewRatio` 为 0~1，展示 ×100
- `returnRatio`/`fbaProportion` 已是百分数，不再换算
- 根节点统计全 0，必须选叶子节点
- `sellerLocation` 多选需拆单值再并集
- `nodeLabelLocale`（中文翻译）不可靠，以英文 `nodeLabelPath` 为准

### 数据解析要点

`market_research` 返回的 `data.items` 既包含子市场，也可能包含父节点自身汇总行。
可通过 `ranking` 字段排序，过滤 `totalProducts` 数据异常的条目。

分布类工具（market_brand_concentration 等）的 `data` 结构不统一：
- 部分直接返回数组：`data: [{...}]`
- 部分返回对象：`data: { items: [{...}] }`
- 安全取值：先判 `isinstance(data, dict)` 再 `.get('items', [])`
