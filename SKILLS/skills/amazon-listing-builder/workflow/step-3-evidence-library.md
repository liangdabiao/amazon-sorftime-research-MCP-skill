# 第三步：卖点证据库

> **每一个卖点都要有证据**。否则 AI 写出来的全是空话："premium quality / perfect for any occasion / easy to use / great gift"。

## 🚨 MCP 调用 + 浏览器补充

本步主数据来自**人工供应链信息**（MCP 不提供产品内部数据），但可通过 MCP 拿到**竞品好评中的客户认可证据**。

### 必须调用的 MCP 工具

```python
# 1. 竞品好评（提取客户认可的卖点 = 可信证据）
for asin in competitor_asins:
  mcp__sellersprite__review({
    "marketplace":"US", "asin":asin
  })
  # 用好评主题作为"客户认可的证据"

# 2. 自己 ASIN 的好评（如有）
mcp__sellersprite__review({
  "marketplace":"US", "asin":"<自己的ASIN>"
})
```

### ✅ 浏览器补充（验证材料 / 认证）

```javascript
// 1. 认证机构官网（验证 CPSIA / FDA / RoHS 等证书真实性）
mcp__web_reader__webReader({url:"https://www.fda.gov/..."})
mcp__web_reader__webReader({url:"https://www.cpsc.gov/..."})

// 2. 品牌官网（拿品牌定位语言）
mcp__web_reader__webReader({url:"https://brand.com/about"})
```

### ❌ 禁止行为

不能用浏览器抓 Amazon 商品页凑"证据"，所有竞品数据必须走 MCP。

详见 `reference/mcp-mandatory-protocol.md`。

---

## 一、为什么需要证据库

| 卖点（空话版） | 卖点（证据版） |
|--------------|--------------|
| UV resistant | Made with UV-resistant materials to help reduce fading during outdoor sunlight exposure |
| Realistic | Natural color variation and fuller flower heads create a lifelike look from a distance |
| Easy to use | Flexible stems can be directly inserted into planters, baskets and porch boxes |
| Durable | Reinforced plastic stems resist bending and shedding during shipping |

证据库的本质：**让 AI 写出来的每一句话都有事实支撑，避免合规风险和差评反噬**。

---

## 二、证据类型

| 证据类型 | 示例 | 可信度 |
|---------|------|--------|
| 材料证据 | "Made with UV-resistant PE plastic" | ⭐⭐⭐ |
| 工艺证据 | "Reinforced stems resist bending" | ⭐⭐⭐ |
| 规格证据 | "12 bundles, 16 inches tall" | ⭐⭐⭐ |
| 场景证据 | "Tested for patio and porch use" | ⭐⭐ |
| 对比证据 | "Compared with standard faux flowers" | ⭐⭐ |
| 客户反馈证据 | "Buyers praise the natural look"（来自好评） | ⭐⭐ |
| 数据证据 | "Tested for 200+ hours UV exposure"（如有） | ⭐⭐⭐ |
| 认证证据 | "Meets CPSIA / RoHS / FDA standard"（如有） | ⭐⭐⭐ |

> ⚠️ **关键原则**：没有的证据不要写。AI 很会编，必须人工审核，否则违规风险。

---

## 三、痛点 → 解决方案 → 证据 → 关键词 → 图片 映射表

这是核心产出。每个痛点都要拉成一条完整的链：

| 痛点 | 解决方案 | 证据 | 对应关键词 | 对应图片 | Listing 位置 |
|------|---------|------|----------|---------|------------|
| 会褪色 | 抗 UV 材料 | "UV-resistant materials, suitable for outdoor sun" | UV resistant / fade resistant / won't fade | 户外暴晒场景图 | 五点 1 + A+ 第 2 屏 |
| 看起来假 | 自然色差 + 层次花瓣 | "Natural color variation + layered petals" | realistic / lifelike / natural look | 近景细节图 + 远景布置图 | 五点 2 + A+ 第 3 屏 |
| 不会用 | 直接插入花盆 | "Flexible stems for direct insertion" | easy to use / for planters | 花盆使用图 | 五点 3 + A+ 第 4 屏 |
| 收到变形 | 加固包装 | "Protective packaging to reduce transit damage" | protective packaging | 包装示意图 | 五点 5 + A+ 第 5 屏 |
| 不知道买多少 | 数量建议 | "12 bundles fill a medium planter" | 12 bundles / for planters | 数量对照图 | 五点 4 + QA |

---

## 四、字段定义（卖点证据库）

| 字段 | 说明 |
|------|------|
| `feature` | 卖点名称（如 "UV Resistant"） |
| `painpoint` | 对应用户痛点 |
| `evidence` | 证据描述（具体材料/工艺/数据） |
| `keywords` | 对应关键词列表 |
| `image_brief` | 图片需求简述（给美工的需求文档） |
| `aplus_module` | A+ 模块对应位置 |
| `bullet_point_n` | 五点第几条 |
| `qa_n` | QA 第几题 |
| `compliance_risk` | 合规风险（high/medium/low） |
| `verification_status` | 验证状态（已验证/待验证/无证据） |

---

## 五、给 Codex 的提示词（本步专用）

详见 `prompts/painpoint-mapping-prompt.md`。精简版：

> 输入：产品规格、供应链信息（材料/工艺/认证）、产品功能列表、问题库（来自第二步）、关键词分层词库（来自第一步）。
>
> 任务：
> 1. 列出产品所有可能的卖点（不少于 10 个）
> 2. 为每个卖点找到 1-3 条具体证据（材料/工艺/数据）
> 3. 建立痛点 → 解决方案 → 证据 → 关键词 → 图片 的完整映射表
> 4. 标注无证据支撑的卖点（这些必须从 Listing 删除或补证据）
> 5. 标注合规风险（医疗/环保/绝对化用语风险）
> 6. 输出图片需求清单（给美工）

---

## 六、输出模板

```markdown
# 卖点证据库 — {产品名}

## 卖点 1: UV Resistant Design
- **痛点**：户外暴晒容易褪色
- **证据**：采用抗 UV 处理的 PE 塑料花瓣，适合户外长时间摆放
- **对应关键词**：UV resistant / fade resistant / outdoor sunlight
- **图片需求**：户外阳光下场景图，标注 "UV Resistant"
- **A+ 位置**：第 2 屏（材料示意）
- **五点位置**：第 1 点
- **QA 位置**：Q1
- **合规风险**：低（不写 "100% no fade"，用 "help reduce fading"）
- **验证状态**：已验证（供应链确认）

## 卖点 2: Realistic Look
...

## 待补充证据的卖点（不要写进 Listing）
- 卖点 X：[某承诺]，但当前无证据支撑，建议删除或补充测试数据
```

---

## 七、合规红线（必须人工审核）

| 类型 | 禁用表达 | 安全表达 |
|------|---------|---------|
| 绝对化 | 100% no fade / never fades | Help reduce fading |
| 医疗 | Cures / treats / heals | Supports / may help |
| 环保 | 100% eco-friendly | Made with recyclable materials |
| 安全 | FDA approved（如无认证） | Meets CPSIA standard（如有认证） |
| 持久 | Lifetime warranty / lasts forever | Designed for long-term outdoor use |

---

## 八、检查清单

- [ ] 每个核心卖点都有至少 1 条证据
- [ ] 无证据支撑的卖点已剔除或标注待补
- [ ] 痛点 → 证据映射完整（5 条以上）
- [ ] 图片需求清单已生成
- [ ] 合规红线词已替换为安全表达
- [ ] 验证状态已标注（供应链/测试/客户反馈来源）
