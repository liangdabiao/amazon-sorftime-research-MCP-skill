# 第五步：五点描述

> **五点不是参数表，而是购买决策链**。每一点回答一个用户疑虑，推动买家做决策。

## 🚨 本步不调 MCP

本步基于**第一步词库 + 第二步问题库 Top 5 + 第三步痛点-证据映射表**生成五点，不再调用 MCP 工具。

### 数据来源
- 每点对应的卖点：第三步证据库
- 每点埋入的关键词：第一步词库
- 每点回答的用户疑虑：第二步问题库
- 字符限制：基于目标站点规范

### ❌ 禁止行为

不要用浏览器抓竞品五点凑内容，所有竞品五点参考已在第二步通过 `asin_detail` MCP 拿到。

---

## 一、五点 = 五个决策环节

| 点位 | 决策环节 | 回答的问题 | 示例（抗 UV 户外仿真植物） |
|------|---------|----------|---------------------------|
| 1 | 核心价值 | 为什么这个产品适合 XX 场景？ | Designed for Outdoor Sunlight（抗 UV） |
| 2 | 痛点解决 | 会不会有 XX 问题？ | Realistic Color and Layered Petals（真实感） |
| 3 | 使用场景 | 适合哪些具体场景？ | Perfect for Porch, Patio and Garden Planters |
| 4 | 规格使用 | 数量多少？怎么用？ | 12 Bundles, Flexible Stems for Direct Insertion |
| 5 | 信任风险 | 包装/维护/售后？ | Protective Packaging and Maintenance-Free |

---

## 二、写法原则

### 原则 1：每一点一句话承诺 + 一句证据

✅ **第 1 点示例**：
> **Designed for Outdoor Sunlight** — Made with UV-resistant materials to help reduce fading in patio, porch and garden use.

✗ **错误示例（堆词无证据）**：
> **Premium Quality**：High quality material, perfect for any occasion, great for home and garden.

### 原则 2：关键词自然融入，不堆砌

把 L2 功能词、L3 场景词、L4 问题词自然融入，不是塞进去。

✅ `Made with UV-resistant materials to help reduce fading in patio, porch and garden use.`
- 含 UV-resistant（L2）、fading（L4）、patio/porch/garden（L3）

### 原则 3：禁用空泛词

| 禁用 | 用具体卖点替代 |
|------|--------------|
| Premium quality | 写具体材料 / 工艺 |
| Perfect for any occasion | 写具体场景 |
| Easy to use | 写具体怎么用 |
| Great gift | 写适合什么人送礼 |
| High performance | 写具体数据 |

---

## 三、抗 UV 户外仿真植物完整示例

### Point 1: Designed for Outdoor Sunlight
Made with UV-resistant materials to help reduce fading in patio, porch and garden use.

**埋入**：UV-resistant（L2）、outdoor、sunlight、fading（L4）、patio、porch、garden（L3）

### Point 2: Realistic Color and Layered Petals
Natural color variation and fuller flower heads create a more lifelike look from a distance.

**埋入**：realistic、lifelike（L2）、natural color（L4 变体）

### Point 3: Perfect for Porch, Patio and Garden Planters
Flexible stems can be directly inserted into planters, baskets and porch boxes for instant outdoor decor.

**埋入**：porch、patio、garden、planters（L3）、flexible stems、direct insertion（L4）

### Point 4: 12 Bundles for Full Arrangements
Each set includes 12 bundles of faux plants, enough to fill 2-3 medium planters or one long window box.

**埋入**：12 bundles（L5）、planters、window box（L3）

### Point 5: Protective Packaging and Maintenance-Free
Shipped with reinforced packaging to reduce transit damage. No watering, no trimming — keeps outdoor spaces colorful all season.

**埋入**：protective packaging（L4）、maintenance-free、no watering（L2/L4）

---

## 四、字符规范

| 站点 | 单点字符上限 | 建议范围 |
|------|------------|---------|
| 美国站 | 500 | 200-300 |
| 欧洲站 | 500 | 200-300 |
| 日本站 | 250（字节） | 150-200 |

每点结构：**加粗卖点标题（5-8 词）+ 短句承诺 + 长句证据**。

---

## 五、给 Codex 的提示词（本步专用）

> 输入：痛点-证据映射表（第三步）、关键词分层词库（第一步）、用户问题库 Top 5（第二步）、产品规格、合规限制。
>
> 任务：
> 1. 严格按 5 个决策环节生成五点
> 2. 每点结构：加粗卖点标题 + 1 句承诺 + 1-2 句证据
> 3. 每点埋入至少 3 个关键词（来自不同层级）
> 4. 禁用空泛词清单（premium / perfect / easy / great gift / high performance）
> 5. 字符控制在 200-300 之间
> 6. 每点对应一个用户问题（来自问题库 Top 5）
> 7. 不夸大，不绝对化

---

## 六、给 Codex 的禁忌词清单

直接传给 AI：

```
禁用词清单（绝对不能出现在五点中）：
- Premium quality / High quality
- Perfect for any occasion / Perfect for everyone
- Great gift / Best gift
- 100% / Lifetime / Never / Always
- Eco-friendly（无认证）
- FDA approved（无认证）
- Cures / Treats / Heals（医疗）
- Best / Number 1 / Top rated
- Cheap / Lowest price

替换规则：
- premium quality → 写具体材料（如 PE plastic / stainless steel）
- perfect for any occasion → 写具体 2-3 个场景
- great gift → 写具体适合什么人（如 for housewarmings, for Mother's Day）
- 100% no fade → help reduce fading
```

---

## 七、输出模板

```markdown
# 五点描述草稿 — {产品名}

## Point 1: Designed for Outdoor Sunlight
**加粗卖点标题**：Designed for Outdoor Sunlight
**正文**：Made with UV-resistant materials to help reduce fading in patio, porch and garden use.
**字符数**：118
**埋入关键词**：UV-resistant（L2）、outdoor、sunlight、fading（L4）、patio、porch、garden（L3）
**对应问题**：Q1 - Will these flowers fade in direct sunlight?
**合规检查**：✅ 用 "help reduce" 而非 "no fade"

## Point 2-5: ...

## 检查结果
- [x] 5 个决策环节全覆盖
- [x] 每点埋入 3+ 关键词
- [x] 无禁用词
- [x] 无绝对化表达
- [x] 字符数 200-300 之间
```

---

## 八、检查清单

- [ ] 5 个决策环节全覆盖（核心价值 / 痛点 / 场景 / 规格 / 信任）
- [ ] 每点都有具体证据，无空话
- [ ] 禁用词全部规避
- [ ] 每点埋入 3+ 关键词
- [ ] 每点对应一个用户问题
- [ ] 合规检查通过
- [ ] 字符数符合规范
