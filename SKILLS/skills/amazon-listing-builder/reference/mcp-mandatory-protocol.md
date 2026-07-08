# MCP 强制使用协议（核心铁律）

> **数据来源优先级：MCP（卖家精灵）> 浏览器**
>
> 核心数据必须走 MCP；浏览器仅作为 MCP 没有覆盖的数据的补充来源。

---

## 一、铁律（必须遵守）

### 🚨 红线 1：核心数据必须走 MCP

以下数据**禁止用浏览器抓取 Amazon**，必须使用卖家精灵 MCP 工具：

| 数据类型 | 必须使用的 MCP 工具 | 禁止行为 |
|---------|------------------|---------|
| 关键词搜索量 / PPC / 趋势 | `keyword_miner` / `keyword_research_trends` | ❌ 浏览器搜 Amazon Suggest |
| 竞品 ASIN 详情（标题/五点/价格/评分） | `asin_detail` | ❌ 浏览器抓 Amazon 商品页 |
| 竞品关键词反查 | `traffic_keyword` / `keyword_order` | ❌ 浏览器看 Amazon 搜索建议 |
| 竞品评论（含差评主题） | `review` | ❌ ❌ ❌ **浏览器抓 `amazon.com/product-reviews/...`** |
| 竞品流量结构 | `traffic_listing` / `traffic_keyword_stat` | ❌ 浏览器看 BSR |
| 价格历史 / BSR 历史 | `keepa_info` | ❌ 浏览器查 Keepa 网站 |
| 市场价格分布 | `market_price_distribution` | ❌ 浏览器翻列表 |
| 类目节点 | `product_node` | ❌ 浏览器搜 Amazon 类目树 |
| 品牌 / 卖家分析 | `market_brand_concentration` | ❌ 浏览器手动统计 |

### ✅ 红线 2：浏览器仅作必要补充

以下数据**MCP 拿不到**，允许使用浏览器（如 `mcp__web_reader__webReader`）：

| 数据类型 | 浏览器来源 | 说明 |
|---------|----------|------|
| 站外买家真实反馈 | Reddit / TikTok / Pinterest 评论 | MCP 不覆盖站外 |
| 亚马逊前台 QA 板块 | `amazon.com/ask-questions/...` | MCP 无 QA 工具 |
| 自己的客服记录 | 卖家后台 / 客服系统 | 私有数据，MCP 拿不到 |
| 自己的广告搜索词报告 | 卖家后台广告报表 | 私有数据 |
| 自己的退货报告 | 卖家后台 | 私有数据 |
| 品牌官网 / 认证信息 | 品牌官网 / CPSIA / FDA / RoHS 官网 | 验证合规性 |
| Google Trends | `trends.google.com` | MCP 无（但有 `google_trend` 工具，优先用 MCP） |
| 竞品品牌词识别 | 竞品 ASIN 的品牌名 | 先用 `asin_detail` 拿品牌，再人工排除 |

### 🔧 红线 3：数据缺失时正确处理

如果 MCP 调用失败或数据不完整：
1. **先重试 1 次**（可能是网络瞬时问题）
2. **检查参数是否正确**（参考 `reference/sellersprite-mcp-integration.md` 第八节常见陷阱）
3. **如果仍然失败，标注 `DATA_MISSING`**，列出需要人工补充的字段
4. **绝对禁止**用浏览器抓 Amazon 页面来"凑数据"

---

## 二、八步工作流的 MCP 调用顺序

每一步开始前，必须先调 MCP 工具拿真实数据，再让 AI 分析。**顺序不能颠倒**。

### 第一步：关键词分层词库

```python
# 必须按顺序调用以下 MCP 工具
# 1. 关键词挖掘（主力扩词）
mcp__sellersprite__keyword_miner({
  "request": {"marketplace":"US", "keyword":"<种子词>"}
})

# 2. 关键词趋势验证（字段：time/search/chainGrowth/yearlyGrowth）
mcp__sellersprite__keyword_research_trends({
  "marketplace":"US", "keyword":"<种子词>"   # 注意：扁平参数
})

# 3. 竞品关键词反查（找出竞品真实出单词）
for asin in competitor_asins:
  mcp__sellersprite__traffic_keyword({
    "request": {"marketplace":"US", "asin":asin}
  })

# 4. 竞品出单词（用于词库优先级排序）
for asin in competitor_asins:
  mcp__sellersprite__keyword_order({
    "request": {"marketplace":"US", "asin":asin}
  })
```

**浏览器补充**：无（关键词数据 MCP 全覆盖）

---

### 第二步：用户问题库

```python
# 1. 竞品差评（必走 MCP，禁止浏览器抓评论页）
for asin in competitor_asins:
  mcp__sellersprite__review({
    "marketplace":"US", "asin":asin
  })
  # ⚠️ 注意：每次最多返回 20 条，是样本数据

# 2. 竞品 Listing 结构（拿五点和描述参考）
for asin in competitor_asins:
  mcp__sellersprite__asin_detail({
    "marketplace":"US", "asin":asin
  })
```

**浏览器补充**（仅这些场景允许）：
```javascript
// 1. 竞品 QA 板块（MCP 无 QA 工具）
mcp__web_reader__webReader({
  url: "https://www.amazon.com/ask-questions/B0XXXXXXX",
  return_format: "text",
  retain_images: false
})

// 2. Reddit / TikTok 站外买家反馈
mcp__web_reader__webReader({
  url: "https://www.reddit.com/r/.../...",
  return_format: "text"
})

// ❌ 错误示例：抓 Amazon 评论页
// mcp__web_reader__webReader({
//   url: "https://www.amazon.com/product-reviews/B07PQFT83F?filterByStar=critical"
// })
```

---

### 第三步：卖点证据库

**主要靠人工**（供应链信息、测试数据、认证），MCP 不提供产品内部数据。

```python
# 可调用：竞品评论中的好评（提取"客户认可的证据"）
mcp__sellersprite__review({
  "marketplace":"US", "asin":"<自己的ASIN>"
})
```

**浏览器补充**：
- 品牌官网（验证材料承诺）
- 认证机构官网（验证 CPSIA / FDA / RoHS 等证书真实性）

---

### 第四步：标题结构设计

**不再调 MCP**。基于第一、二、三步的数据生成 3 版标题对比。

---

### 第五步：五点描述

**不再调 MCP**。基于痛点-证据映射表生成。

---

### 第六步：描述 + A+ 内容

**不再调 MCP**。基于叙事流生成。

**浏览器补充**：
- 品牌官网（拿品牌定位语言）
- 竞品 A+ 模块（如想参考结构）

---

### 第七步：Search Terms

**不再调 MCP**。基于第一步词库 + 第四步标题，做差集运算（找出未在前台出现的词）。

---

### 第八步：QA 设计

基于第二步问题库生成。

**浏览器补充**（可选）：
- 竞品 QA 板块（补充 MCP 拿不到的问题）
- Reddit 真实买家提问

---

## 三、上线后迭代的 MCP 调用

```python
# 1. 自己 ASIN 的流量诊断
mcp__sellersprite__traffic_listing({
  "request":{"marketplace":"US","asin":"<自己的ASIN>"}
})

# 2. 自己 ASIN 的出单词
mcp__sellersprite__keyword_order({
  "request":{"marketplace":"US","asin":"<自己的ASIN>"}
})

# 3. 价格分布
mcp__sellersprite__market_price_distribution({
  "request":{"marketplace":"US","nodeIdPath":"<类目>"}
})

# 4. 自己 Listing 的评论反馈（监控差评主题）
mcp__sellersprite__review({
  "marketplace":"US","asin":"<自己的ASIN>"
})
```

**自己后台数据（浏览器 / 后台导出）**：
- 广告搜索词报告（后台 Reports → Advertising）
- 客户 QA（后台 Buyer-Seller Messaging）
- 退货报告（后台 Returns）
- BSR 排名历史（用 MCP `keepa_info`）

---

## 四、调用前的检查清单

每次开始八步工作流前，必须确认：

- [ ] `.mcp.json` 配置正确（URL + headers.secret-key）
- [ ] MCP 客户端能成功调用 `mcp__sellersprite__product_node` 测试工具
- [ ] 目标 ASIN 已确认（自己的 + 3-5 个竞品）
- [ ] 类目节点 nodeIdPath 已查到（用 `product_node` 工具）
- [ ] 站点确认（US / UK / DE / JP）

如果 MCP 调用失败，**先排查**，不要用浏览器抓 Amazon 凑数据。

---

## 五、常见错误对比

| 场景 | ❌ 错误做法 | ✅ 正确做法 |
|------|-----------|-----------|
| 抓竞品评论 | `webReader(amazon.com/product-reviews/B07X...)` | `mcp__sellersprite__review({asin:"B07X..."})` |
| 抓竞品标题 | `webReader(amazon.com/dp/B07X...)` | `mcp__sellersprite__asin_detail({asin:"B07X..."})` |
| 拿关键词搜索量 | `webReader(Amazon 搜索建议)` | `mcp__sellersprite__keyword_miner({keyword:"..."})` |
| 看 BSR 历史 | `webReader(keepa.com)` | `mcp__sellersprite__keepa_info({asin:"..."})` |
| 看价格分布 | `webReader(翻 Amazon 列表)` | `mcp__sellersprite__market_price_distribution` |
| 看 Reddit 评论 | ✅ `webReader(reddit.com/r/...)` | MCP 无此数据 |
| 看竞品 QA 板块 | ✅ `webReader(amazon.com/ask-questions/...)` | MCP 无 QA 工具 |
| 验证 FDA 认证 | ✅ `webReader(fda.gov)` | MCP 无认证查询 |

---

## 六、为什么不能用浏览器抓 Amazon

| 问题 | 说明 |
|------|------|
| 反爬虫封锁 | Amazon 会快速封锁抓取 IP，数据不完整 |
| 数据结构易变 | HTML 结构变动导致脚本失效 |
| 评论数据不全 | Amazon 前台评论有分页、筛选、隐藏 |
| 缺少核心字段 | 浏览器抓不到搜索量、PPC、转化集中度等核心数据 |
| 合规风险 | 抓取 Amazon 数据违反其 ToS |
| 效率低 | MCP 一次调用拿全字段，浏览器要多次请求 |
| 数据已结构化 | MCP 返回 JSON，浏览器返回 HTML 需要解析 |

**结论**：MCP 是第一手结构化数据源，浏览器只是"必要补充"，不是"主要通道"。

---

## 七、违规自检

每次跑完 skill，自检以下问题：

- [ ] 第一步是否调用了 `keyword_miner`？（不是浏览器搜 Amazon）
- [ ] 第二步是否调用了 `review`？（不是浏览器抓评论页）
- [ ] 第二步是否调用了 `asin_detail`？（不是浏览器抓商品页）
- [ ] 浏览器调用是否仅限于：Reddit / TikTok / 竞品 QA 板块 / 官网验证？
- [ ] 所有 MCP 失败的字段是否标注 `DATA_MISSING`？

如果以上任何一项不通过，**重新跑**该步骤，不要凑数据。
