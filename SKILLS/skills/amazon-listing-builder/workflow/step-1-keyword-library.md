# 第一步：关键词分层词库

> 不要把所有词丢在一起，**按意图分层**才能决定每个词放哪里。

## 🚨 必须先调 MCP（禁止浏览器抓 Amazon）

本步核心数据**必须**全部来自卖家精灵 MCP，**禁止**用 web reader 抓 Amazon 搜索建议或关键词页。

### 必须调用的 MCP 工具（按顺序）

```python
# 1. 主力扩词（按种子词扩展）
mcp__sellersprite__keyword_miner({
  "request": {"marketplace":"US", "keyword":"<种子词>"}
})

# 2. 趋势验证（注意：扁平参数；字段是 time/search/chainGrowth/yearlyGrowth）
mcp__sellersprite__keyword_research_trends({
  "marketplace":"US", "keyword":"<种子词>"
})

# 3. 竞品关键词反查（必须传竞品 ASIN）
for asin in competitor_asins:  # 3-5 个竞品
  mcp__sellersprite__traffic_keyword({
    "request": {"marketplace":"US", "asin":asin}
  })

# 4. 竞品真实出单词（用于排序词库优先级）
for asin in competitor_asins:
  mcp__sellersprite__keyword_order({
    "request": {"marketplace":"US", "asin":asin}
  })
```

### ❌ 禁止行为

```javascript
// 错误：用浏览器抓 Amazon 搜词建议
mcp__web_reader__webReader({url:"https://www.amazon.com/s?k=artificial+flowers"})
// 错误：用浏览器抓关键词页
mcp__web_reader__webReader({url:"https://www.amazon.com/s?k=..."})
```

### ✅ 浏览器补充（仅限）

- 自己的广告搜索词报告：从卖家后台手动下载（MCP 无）
- 自己的客服记录：从卖家后台导出（MCP 无）

详见 `reference/mcp-mandatory-protocol.md`。

---

## 一、为什么要分层

旧方法：把 uv resistant artificial outdoor plants、outdoor artificial flowers、fake flowers outdoor 全塞标题，结果标题像词库垃圾桶。

新方法：按用户搜索意图把词分成 5 层，每层放在不同位置（标题 / 五点 / 描述 / ST / QA），让系统理解关系，让买家读得下去。

---

## 二、五层词库结构

| 层级 | 名称 | 示例（抗 UV 户外仿真植物） | 建议位置 |
|------|------|--------------------------|---------|
| 1 | 核心品类词 | artificial flowers / artificial plants / fake flowers / faux plants | 标题开头 + 五点 + 描述 |
| 2 | 功能属性词 | UV resistant / fade resistant / weather resistant / waterproof / maintenance free | 标题 + 五点 1 |
| 3 | 场景词 | outdoor / patio / garden / porch / planter / front door / cemetery / balcony | 标题 + 五点 3 + A+ |
| 4 | 问题词 | won't fade in sun / for outdoor planters / looks real / no watering / full sun | 五点 + QA + A+ |
| 5 | 规格词 | 12 bundles / plastic stems / 16 inch / flowers for pots | 标题 + 五点 4 |

---

## 三、字段定义（每个关键词都要标注）

| 字段 | 说明 |
|------|------|
| `keyword` | 关键词原文 |
| `layer` | 1-5（按上表） |
| `intent` | 搜索意图（如"功能+场景"） |
| `search_volume` | 月搜索量（来自卖家精灵 keyword_miner） |
| `trend` | 趋势（chainGrowth / yearlyGrowth，来自 keyword_research_trends） |
| `ppc` | 广告建议价 |
| `click_concentration` | 点击集中度（0~1） |
| `conversion_concentration` | 转化集中度（0~1） |
| `suggested_position` | 标题 / 五点 / 描述 / ST / QA |
| `must_frontend` | 是否必须前台（true/false） |
| `priority` | P0（必放）/ P1（推荐）/ P2（补充） |

---

## 四、数据来源

| 来源 | 卖家精灵工具 | 备注 |
|------|------------|------|
| 种子词扩展 | `keyword_miner` | 主力扩词工具 |
| 全球热词参照 | `keyword_research` | 注意会忽略 keyword 参数，仅作趋势参照 |
| 趋势验证 | `keyword_research_trends` | 字段：`time` / `search` / `chainGrowth` / `yearlyGrowth` |
| 竞品反查 | `traffic_keyword` + `keyword_order` | 找出竞品真实出单词 |
| 广告搜索词报告 | 后台下载 | 真实转化数据 |
| 评论高频词 | `review` + 自定义 NLP | 注意 review 工具仅返回 20 条 |
| 站外内容词 | TikTok / Reddit / Pinterest | 手动补充 |

---

## 五、合并去重与意图分类规则

1. 全部词合并到一张表，按 `keyword` 文本去重
2. 用关键词本身判断层级：
   - 含 brand/product 类名词 → 第 1 层
   - 含 `resistant`/`proof`/`free`/`material` → 第 2 层
   - 含场景名词（patio/garden/porch/...） → 第 3 层
   - 含问题句式（won't / how to / can I / for ...） → 第 4 层
   - 含数量/尺寸/规格 → 第 5 层
3. 一个词可能跨多层（如 `uv resistant outdoor flowers` 同时属 2+3），按主意图归类

---

## 六、输出模板

```markdown
# 关键词分层词库 — {产品名}

## L1 核心品类词（必须前台）
| 关键词 | 月搜索量 | 趋势 | PPC | 建议位置 |
|--------|---------|------|-----|---------|
| artificial flowers | 95,000 | ↑12% | $0.85 | 标题 |
| ...  | ... | ... | ... | ... |

## L2 功能属性词
...

## L3 场景词
...

## L4 问题词
...

## L5 规格词
...

## 后台补充候选（同义词/变体/错拼）
...
```

---

## 七、给 Codex 的提示词（本步专用）

详见 `prompts/layered-keyword-prompt.md`。精简版：

> 输入：种子词、产品核心卖点、卖家精灵关键词数据、竞品 ASIN、广告搜索词报告、评论高频词。
>
> 任务：
> 1. 合并所有关键词并去重
> 2. 按上述 5 层结构分类，标注每个字段
> 3. 标记 must_frontend（核心词、功能词、主场景词默认必前台）
> 4. 输出 Markdown 表格 + JSON 结构化数据
> 5. 标注缺失数据字段（如某词 PPC 缺失），不要编造

---

## 八、检查清单

- [ ] 五层词库都至少有 5 个词
- [ ] 每个核心词都标注了 must_frontend=true
- [ ] 没有把同一个词重复放在不同层级
- [ ] 没有把竞品品牌词（如其他卖家品牌）混进来
- [ ] 数据缺失字段已标注，未编造
