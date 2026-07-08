# ASIN 分析工具集

## `asin_detail` — ASIN 详情

### 用途
获取单个 ASIN 的详细信息：标题、品牌、价格、评分、变体、卖家等。

### 请求参数
- `marketplace`: 站点
- `asin`: ASIN（单值）
- `month`: yyyyMM

### 响应字段
标题、品牌、卖家、价格、评分、评分数、BSR、变体信息、配送方式、上架日期、图片 URL、描述等。

---

## `keepa_info` — Keepa 趋势数据

### 用途
获取 ASIN 的历史价格、排名、销量趋势曲线（Keepa 风格）。

### 请求参数
- `marketplace`: 站点
- `asin`: ASIN（单值）
- `month`: yyyyMM

### 响应字段
价格历史、BSR 历史、销量历史数据点。

---

## `asin_prediction` — 销量预测

### 用途
基于历史数据预测 ASIN 的未来销量。

### 请求参数
- `marketplace`: 站点
- `asin`: ASIN

---

## `asin_coupon_trend` — 优惠趋势

### 用途
ASIN 的 Coupon/促销历史趋势。

---

## `asin_detail_with_coupon_trend` — 详情+优惠

### 用途
一次性获取 ASIN 详情和优惠趋势数据。

---

## `bsr_prediction` — BSR 销量预估

### 用途
根据 BSR 排名估算销量。

### 请求参数
- `category`: 类目 ID
- `rank`: BSR 排名
