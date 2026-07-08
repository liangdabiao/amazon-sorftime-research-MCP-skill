# 第二步：用户问题库

> 新算法语境下，**问题库比关键词库更重要**。因为 Alexa/Rufus/对话式购物的本质是：买家不搜短词，而是问问题。

## 🚨 必须先调 MCP（核心数据禁止浏览器抓 Amazon）

本步的**竞品评论和竞品 Listing 结构**必须用 MCP，**严禁**用 web reader 抓 `amazon.com/product-reviews/` 或 `amazon.com/dp/` 页面。

### 必须调用的 MCP 工具

```python
# 1. 竞品差评（用户问题库最核心来源）
for asin in competitor_asins:  # 3-5 个竞品
  mcp__sellersprite__review({
    "marketplace":"US", "asin":asin  # 注意：扁平参数
  })
  # ⚠️ 每次最多返回 20 条，是样本数据，需多次调用或多 ASIN 取并集

# 2. 竞品 Listing（拿标题/五点/描述/A+ 结构参考）
for asin in competitor_asins:
  mcp__sellersprite__asin_detail({
    "marketplace":"US", "asin":asin
  })

# 3. 竞品流量结构（看主力出单词反映的需求）
for asin in competitor_asins:
  mcp__sellersprite__traffic_keyword({
    "request": {"marketplace":"US", "asin":asin}
  })
```

### ❌ 严禁的错误做法

```javascript
// 错误：用浏览器抓 Amazon 评论页
mcp__web_reader__webReader({
  url:"https://www.amazon.com/product-reviews/B07PQFT83F?filterByStar=critical&pageNumber=1"
})
// 错误：用浏览器抓商品详情页
mcp__web_reader__webReader({url:"https://www.amazon.com/dp/B07XXX..."})
```

### ✅ 浏览器补充（MCP 无对应工具，允许）

```javascript
// 1. 竞品 QA 板块（MCP 无 QA 工具）
mcp__web_reader__webReader({
  url:"https://www.amazon.com/ask-questions/B07XXX...",
  return_format:"text",
  retain_images:false
})

// 2. 站外买家真实反馈
mcp__web_reader__webReader({url:"https://www.reddit.com/r/..."})
mcp__web_reader__webReader({url:"https://www.tiktok.com/..."})
```

详见 `reference/mcp-mandatory-protocol.md`。

---

## 一、为什么要建问题库

如果用户问 "Will these flowers fade in direct sunlight?"，你的 Listing 没有回答这个问题 → 系统不会推荐你。

问题库的作用：
1. **QA 内容来源** — 直接把高频问题做成 QA
2. **五点描述的"答案"逻辑** — 每一点回答一个用户疑虑
3. **A+ 模块结构** — 用一屏回答一个大问题
4. **语义覆盖校验** — 检查 Listing 是否覆盖了所有高频问题

---

## 二、问题来源

| 来源 | 工具/方法 | 优先级 |
|------|----------|--------|
| 竞品 1-3 星差评 | `review` + ASIN 反查 | ⭐⭐⭐ |
| 竞品 QA 板块 | 亚马逊前台手动抓取 | ⭐⭐⭐ |
| 自己客服记录 | 后台 Customer Q&A | ⭐⭐⭐ |
| Reddit / TikTok 评论 | 站外搜产品类目 | ⭐⭐ |
| 广告搜索词报告 | 后台下载，找问句式 | ⭐⭐ |
| 买家退货原因 | 后台 Return Report | ⭐⭐ |
| 5W1H 推演 | 见下方"问题框架" | ⭐ |

---

## 三、问题框架（5W1H + 决策链）

按购买决策阶段拆分问题：

### 阶段 1：是否适合我？（场景适配）
- Can I use these in [场景]?
- Will it work for [用途]?
- Is this suitable for [人群]?

### 阶段 2：会不会有 XX 问题？（痛点担忧）
- Will it [褪色/变形/损坏]?
- Does it really [效果承诺]?
- Is it [真实/耐用/安全]?

### 阶段 3：规格对吗？（参数确认）
- What size is it?
- How many [bundles/pieces]?
- Will it fit my [容器/位置]?

### 阶段 4：怎么用？（使用成本）
- How do I install/setup?
- Do I need [额外配件]?
- Is it easy to [维护/清洁]?

### 阶段 5：出了问题怎么办？（信任）
- What if I don't like it?
- Is there a warranty?
- How is the packaging?

---

## 四、抗 UV 户外仿真植物案例

| # | 问题 | 高频来源 | 对应卖点 | Listing 位置 |
|---|------|---------|---------|------------|
| 1 | Will these flowers fade in direct sunlight? | 差评 + QA | 抗 UV 材料 | 五点 1 + QA |
| 2 | Can I use them in outdoor planters? | QA | 灵活枝干 | 五点 3 + QA |
| 3 | Are the stems flexible enough to bend? | QA | 可塑枝干 | 五点 5 |
| 4 | How many bundles do I need for a medium planter? | QA | 数量建议 | 五点 4 + QA |
| 5 | Do they look realistic up close? | 差评 | 花瓣层次 | 五点 2 + A+ |
| 6 | Will they fall apart or shed? | 差评 | 加固工艺 | 五点 5 |
| 7 | Can I leave them outside in rain? | QA | 防水 | QA |
| 8 | How tall are they? | QA | 规格 | 五点 4 |
| 9 | Will the color look fake? | 差评 | 自然色差 | 五点 2 + A+ |
| 10 | Is the packaging protective? | 差评 | 加固包装 | 五点 5 + A+ |

---

## 五、字段定义

| 字段 | 说明 |
|------|------|
| `question` | 问题原文（英文） |
| `frequency_source` | 来源（差评/QA/Reddit/客服） |
| `frequency_score` | 出现频次（1-5） |
| `corresponding_feature` | 对应卖点 |
| `corresponding_keyword` | 对应可埋关键词 |
| `listing_position` | 五点 N / QA / A+ 第 N 屏 |
| `natural_language_form` | 自然语言搜索变体（Alexa 可能问的） |

---

## 六、给 Codex 的提示词（本步专用）

> 输入：竞品 ASIN 列表、产品核心卖点、产品规格、客户评论数据、客服记录（如有）。
>
> 任务：
> 1. 从评论差评提取 30+ 个用户问题
> 2. 从竞品 QA 板块提取 20+ 个用户问题
> 3. 用 5W1H 框架补全所有决策环节
> 4. 按频次打分（1-5），保留 Top 20
> 5. 标注每个问题对应的卖点、关键词、Listing 位置
> 6. 生成 Alexa/Rufus 可能问的自然语言变体（问题型搜索）

---

## 七、输出模板

```markdown
# 用户问题库 — {产品名}

## Top 10 高频问题（必须覆盖）

### Q1: Will these flowers fade in direct sunlight?
- 频次：⭐⭐⭐⭐⭐
- 来源：差评（出现 18 次）+ QA（出现 12 次）
- 对应卖点：抗 UV 材料
- 对应关键词：UV resistant / fade resistant / won't fade in sun
- 建议位置：五点 1 + QA + A+ 第 2 屏
- Alexa 变体："Which artificial flowers won't fade in full sun?"

## Q2-Q10: ...

## 次高频问题（11-20）
...
```

---

## 八、检查清单

- [ ] 至少覆盖 20 个问题
- [ ] 5 个决策阶段都有问题
- [ ] 每个问题都标注了对应卖点
- [ ] Alexa 自然语言变体已生成
- [ ] 差评高频问题已 100% 覆盖（差评 = 痛点真相）
