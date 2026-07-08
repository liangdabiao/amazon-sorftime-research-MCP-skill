# 第八步：QA 设计

> QA 在 Alexa/Rufus 对话式购物时代会越来越重要，**因为它天然就是问题和答案结构**。它是 Listing 的"答案型内容补丁"。

## 🚨 本步基于第二步数据，可选浏览器补充

本步主要基于**第二步问题库 Top 10 + 第三步卖点证据库**生成，不再调用 MCP 工具。

### ✅ 浏览器补充（MCP 无 QA 工具，允许）

```javascript
// 1. 竞品 QA 板块（补充 MCP 拿不到的问题）
mcp__web_reader__webReader({
  url:"https://www.amazon.com/ask-questions/B07XXX...",
  return_format:"text",
  retain_images:false
})

// 2. Reddit 真实买家提问（可选）
mcp__web_reader__webReader({url:"https://www.reddit.com/r/..."})
```

### ❌ 禁止行为

不要用浏览器抓竞品评论凑问题，所有竞品评论已在第二步通过 `review` MCP 拿到。

---

## 一、QA 的双重作用

1. **承接自然语言搜索** — 当用户用完整问题提问时，QA 直接匹配
2. **补 Listing 没讲透的地方** — 标题五点不能太长，QA 可以补规格、适配、使用、维护、场景边界

---

## 二、QA 来源

| 来源 | 优先级 |
|------|--------|
| 第二步用户问题库 Top 10 | ⭐⭐⭐ |
| 竞品 QA 板块高频问题 | ⭐⭐⭐ |
| 客服记录 | ⭐⭐⭐ |
| 差评反馈的疑虑 | ⭐⭐⭐ |
| 5W1H 推演 | ⭐⭐ |

---

## 三、QA 写法两大原则

### 原则 1：回答要具体，不要只说 yes

✅ **好回答**：
> **Q: Will these artificial flowers fade in direct sunlight?**
> A: They are made with UV-resistant materials to help reduce fading during outdoor use, but like all outdoor decor, long-term extreme sun exposure may gradually affect color. For best longevity, shelter during severe weather.

✗ **差回答**：
> **Q: Will these fade?**
> A: Yes, they are fade-resistant.

### 原则 2：QA 补 Listing 没讲透的地方

| 类型 | 示例 QA |
|------|---------|
| 规格 | How many bundles do I need for a medium planter? |
| 适配 | Will these fit a 12-inch window box? |
| 使用 | Do I need to assemble anything? |
| 维护 | How do I clean them? |
| 场景边界 | Can I use them in a bathroom with high humidity? |
| 风险 | Are they waterproof? Can they stay out in rain? |

---

## 四、抗 UV 户外仿真植物 QA 完整示例

### Q1: Will these artificial flowers fade in direct sunlight?
**A**: They are made with UV-resistant materials to help reduce fading during outdoor use, but like all outdoor decor, long-term extreme sun exposure may gradually affect color. For best longevity, shelter during severe weather.
**埋入**：UV-resistant, fade, outdoor, sunlight

### Q2: Can I use them in outdoor planters?
**A**: Yes, the flexible stems can be inserted directly into planters, pots, baskets and porch boxes. Each bundle is shaped to mimic real blooms.
**埋入**：outdoor planters, flexible stems, planters, baskets

### Q3: Are the stems flexible enough to bend?
**A**: Yes, the stems are made of durable plastic with internal wire, allowing you to shape them naturally and fit different planter sizes.
**埋入**：flexible stems, plastic, planter

### Q4: How many bundles do I need for a medium planter?
**A**: For a 12-inch medium planter, 4-6 bundles create full coverage. The 12-bundle set fills 2-3 medium planters or one long window box.
**埋入**：12 bundles, medium planter, window box

### Q5: Do they look realistic up close?
**A**: Natural color variation and layered petals create a lifelike look from a distance. For very close inspection, the petals may feel slightly plastic to the touch.
**埋入**：realistic, natural color, layered petals, lifelike

### Q6: Are they waterproof? Can I leave them out in rain?
**A**: Yes, the materials are water-resistant and suitable for outdoor use in normal weather. For longest life, we recommend sheltering during heavy storms or extreme winds.
**埋入**：waterproof, water-resistant, outdoor, weather

### Q7: How tall are they?
**A**: Each bundle measures approximately 14-16 inches tall, suitable for medium and large planters.
**埋入**：size, inches, planters

### Q8: Will the color look fake or too bright?
**A**: The petals use natural color variation to avoid the over-saturated look common in cheap faux florals. Colors are designed to mimic real garden blooms.
**埋入**：color, natural, realistic, faux florals

### Q9: Is the packaging protective? Will they arrive deformed?
**A**: Each set is shipped with reinforced packaging to reduce transit damage. If any bundle arrives misshapen, gentle fluffing restores the shape.
**埋入**：packaging, reinforced, transit

### Q10: Can I use them for indoor decoration too?
**A**: Yes, while designed for outdoor use, they work well in indoor planters, vases, and centerpieces. The UV-resistant materials do not affect indoor use.
**埋入**：indoor, planters, vases, centerpieces

---

## 五、down filled pillows QA 示例（来自需求文档）

> 用户输入示例：产品特性 24x24 / bulk / fluffy；核心卖点 24x24；关键词 down filled pillows / feather down pillow / down feather pillow / goose down pillows

### Q1: Are these pillows machine washable, or do they need dry cleaning?
**A**: These 24 x 24 down filled pillows are best maintained with spot cleaning or professional dry cleaning to preserve the fluffy feather down filling. Frequent machine washing may reduce the loft of the goose down fill over time.
**埋入**：24 x 24, down filled pillows, fluffy, feather down, goose down

### Q2: How fluffy are these pillows right out of the package?
**A**: Each 24 x 24 feather down pillow ships compressed. Allow 24-48 hours for the goose down fill to fully expand — the bulk down fill will reach maximum fluffy loft after a few hours of air exposure and gentle fluffing.
**埋入**：24 x 24, feather down pillow, goose down, bulk, fluffy

### Q3: Are these genuine goose down or a blend?
**A**: These down feather pillows use a feather down blend designed for balanced support and fluffy bulk. The 24 x 24 size provides medium-firm support suitable for side and back sleepers.
**埋入**：down feather pillow, goose down pillows, 24 x 24, fluffy, bulk

### Q4: What size pillow cover fits these?
**A**: Standard 24 x 24 inch pillow covers fit perfectly. The bulk filling holds shape well inside shams and decorative covers, making them ideal for couches, beds, and reading nooks.
**埋入**：24 x 24, bulk, down filled pillows

---

## 六、给 Codex 的提示词（本步专用）

详见 `prompts/master-prompt.md` 第 9 步。精简版：

> 输入：用户问题库 Top 10、产品规格、卖点证据库、产品关键词列表（必须埋入）。
>
> 任务：
> 1. 生成 10 个 QA，覆盖 5 个决策环节（场景适配 / 痛点担忧 / 规格确认 / 使用成本 / 信任）
> 2. 每个回答具体（不只用 yes/no），含场景边界和注意事项
> 3. 每个回答自然埋入 2-3 个指定关键词
> 4. 答案稳健，不夸大（如医疗/环保承诺）
> 5. 涵盖至少 2 个"边界问题"（如某场景是否适合、极端使用情况）
> 6. 模拟 Alexa/Rufus 可能问的自然语言变体

---

## 七、Alexa/Rufus 风格问题模板

对话式购物的问题特征：
- 用完整句子问，不是短词
- 含具体场景和约束（"for my front porch that gets full sun"）
- 含比较（"better than X for Y"）

### 模板
- "Which [product type] won't [problem] in [scenario]?"
- "Can I use [product] for [specific scenario]?"
- "Is [product] suitable for [user type] with [specific concern]?"
- "How does [product] compare to [alternative] for [use case]?"

---

## 八、输出模板

```markdown
# QA 草稿 — {产品名}

## Q1: Will these artificial flowers fade in direct sunlight?
**A**: They are made with UV-resistant materials to help reduce fading during outdoor use, but like all outdoor decor, long-term extreme sun exposure may gradually affect color. For best longevity, shelter during severe weather.
**埋入关键词**：UV-resistant, fade, outdoor, sunlight
**对应问题库**：Q1
**对应卖点**：抗 UV
**Alexa 变体**："Which artificial flowers won't fade in full sun?"

## Q2-Q10: ...

## 检查清单
- [x] 10 个 QA
- [x] 5 个决策环节覆盖
- [x] 每个回答具体
- [x] 关键词自然埋入
- [x] 无夸大承诺
- [x] 含至少 2 个边界问题
```

---

## 九、检查清单

- [ ] 至少 10 个 QA
- [ ] 5 个决策环节全覆盖
- [ ] 每个回答具体（不只 yes/no）
- [ ] 每个回答埋入 2-3 个关键词
- [ ] 无夸大承诺
- [ ] 至少 2 个边界问题（极端场景）
- [ ] Alexa 自然语言变体已生成
- [ ] 与五点描述互补（不重复，补缺口）
