# 第六步：产品描述 + A+ 内容

> **描述和 A+ 不是重复五点，而是用来讲完整场景**。把买家代入"使用前痛点 → 使用场景 → 产品解决方案 → 细节对比 → 使用步骤 → 适合人群 → 注意事项"的叙事流。

## 🚨 本步不调 MCP（可选浏览器补充）

本步基于**第二步问题库 + 第三步卖点证据库 + 第五步五点描述**生成，不再调用 MCP 工具。

### ✅ 浏览器补充（可选）

```javascript
// 1. 品牌官网（拿品牌定位语言、品牌故事）
mcp__web_reader__webReader({url:"https://yourbrand.com/about"})
mcp__web_reader__webReader({url:"https://yourbrand.com/story"})

// 2. 竞品 A+ 模块（如需结构参考，可选）
mcp__web_reader__webReader({
  url:"https://www.amazon.com/dp/B07XXX...",  // 仅看 A+ 模块结构
  retain_images:false
})
```

### ❌ 禁止行为

不要用浏览器抓竞品描述凑内容，竞品描述已在第二步通过 `asin_detail` MCP 拿到。

---

## 一、描述 vs A+ 的分工

| 内容 | 作用 | 重点 |
|------|------|------|
| 产品描述 | 文字版故事 | 移动端阅读、文本索引 |
| A+ 内容 | 图文模块叙事 | 桌面端阅读、视觉信任、语义关联 |

> A+ 是承接 Cosmo 语义算法的**最强载体**，因为它可以用图片和模块把"产品-场景-属性-问题"完整连接起来。

---

## 二、产品描述结构（7 段式）

```
1. 开头痛点共鸣（用户的真实困境）
2. 使用场景代入（让用户想象拥有后的样子）
3. 产品解决方案（核心卖点串讲）
4. 细节对比（与普通款的差异）
5. 使用步骤（降低使用门槛）
6. 适合人群（精准定位）
7. 注意事项（预期管理，减少差评）
```

### 案例：抗 UV 户外仿真植物

> **Want a Colorful Porch Without the Maintenance?**
>
> If you love the look of fresh flowers but don't have time to water, trim, and replant every season, these UV-resistant artificial flowers are designed for low-maintenance outdoor decor.
>
> **Built for Outdoor Use**
>
> Made with UV-resistant materials to help reduce fading, these faux plants are suited for patio, porch, and garden arrangements. The flexible stems insert directly into planters, baskets, and window boxes — no tools required.
>
> **Realistic Look That Lasts**
>
> Natural color variation and layered petals create a lifelike look from a distance. Unlike thin plastic florals that look flat, each bundle is shaped to mimic real blooms.
>
> **How to Use**
>
> 1. Unbox and gently fluff each bundle.
> 2. Insert stems into your planter or window box.
> 3. Arrange 4-6 bundles per medium planter for full coverage.
>
> **Who It's For**
>
> Homeowners, renters, and decorators who want lasting curb appeal without weekly upkeep.
>
> **Please Note**
>
> Like all outdoor decor, long-term extreme sun and weather exposure may gradually affect color. For longest life, shelter during severe storms.

---

## 三、A+ 内容模块结构（标准 6-7 屏）

| 屏 | 内容 | 目的 |
|----|------|------|
| 1 | 户外场景大图 + 品牌定位 | 第一眼代入 |
| 2 | 抗 UV 材料示意 | 痛点证据（褪色） |
| 3 | 花瓣细节图 | 痛点证据（真实感） |
| 4 | 适用场景拼图（patio/porch/garden/balcony） | 语义覆盖场景 |
| 5 | 数量与规格对比 | 决策辅助 |
| 6 | 包装与运输加固 | 信任建立 |
| 7 | 普通款 vs 抗 UV 款对比 | 差异化价值 |

---

## 四、A+ 模块语义覆盖矩阵

确保 A+ 视觉模块**覆盖核心语义关系**：

| 语义关系 | A+ 屏 | 对应关键词 |
|---------|------|----------|
| 产品 → 场景（patio） | 第 1 屏 + 第 4 屏 | patio, outdoor |
| 产品 → 属性（UV resistant） | 第 2 屏 | UV resistant, fade resistant |
| 产品 → 属性（realistic） | 第 3 屏 | realistic, natural look |
| 产品 → 规格（12 bundles） | 第 5 屏 | 12 bundles, bulk |
| 产品 → 信任（packaging） | 第 6 屏 | protective packaging |
| 产品 → 差异化 | 第 7 屏 | vs standard faux flowers |

---

## 五、给美工的图片需求清单

A+ 的成败在图片。每个模块都要给美工一份清晰的需求文档：

```markdown
## A+ 第 2 屏：抗 UV 材料示意
- 主体：产品近景，标出花瓣材质
- 配色：温暖自然，避免过艳
- 文案：UV Resistant Material — Help Reduce Fading
- 标注：阳光照射示意 + "Tested for Outdoor Use"
- 尺寸：970 x 600
- 风格参考：[附竞品 A+ 链接]
```

---

## 六、给 Codex 的提示词（本步专用）

> 输入：痛点-证据映射表、用户问题库、五点描述（来自第五步）、品牌定位、产品规格、合规限制。
>
> 任务：
>
> **A. 产品描述**
> 1. 按 7 段式生成英文描述
> 2. 每段 60-100 字
> 3. 自然融入 L1-L4 关键词（不堆砌）
> 4. 移动端友好（短段落、加粗标题）
> 5. 包含"使用步骤"和"注意事项"降低差评
>
> **B. A+ 模块结构**
> 1. 设计 6-7 屏布局，每屏对应一个语义关系
> 2. 每屏给出：标题、正文、图片需求、关键词
> 3. 标注每屏对应哪个用户问题
> 4. 给出对比模块（普通款 vs 升级款）
> 5. 不重复五点描述的原话

---

## 七、字符与字数规范

### 产品描述
| 站点 | 字数上限 | 建议 |
|------|---------|------|
| 美国站 | 2000 字符 | 800-1200 字符（移动端友好） |

### A+ 内容
| 模块类型 | 文字字数 | 图片尺寸 |
|---------|---------|---------|
| Standard Image + Text | ≤100 字 | 970 x 600 |
| Standard Image Text Overlay | ≤50 字 | 970 x 600 |
| Standard Single Image | 无文字 | 970 x 600 |
| Comparison | ≤200 字 | 970 x 600 |

---

## 八、常见错误

| 错误 | 修正 |
|------|------|
| 描述只是五点的复述 | 用叙事流代替卖点罗列 |
| A+ 全是产品特写，没有场景图 | 至少 3 个场景模块 |
| 没有"使用步骤"模块 | 降低使用门槛 |
| 没有"注意事项"模块 | 减少差评（预期管理） |
| 没有对比模块 | 用普通款 vs 升级款凸显差异 |
| 关键词堆砌 | 自然融入叙事 |

---

## 九、输出模板

```markdown
# 产品描述 + A+ 内容 — {产品名}

## 产品描述
[7 段式英文文案]

## A+ 模块结构

### 第 1 屏：户外场景大图
- 标题：[品牌] UV-Resistant Outdoor Florals
- 正文：Built for outdoor living
- 图片需求：[详细描述]
- 关键词：outdoor, patio, UV resistant

### 第 2-7 屏：...

## 图片需求清单（给美工）
| 屏 | 尺寸 | 需求 | 文案 |
|----|------|------|------|
| 1 | 970x600 | 户外场景大图 | [品牌] UV-Resistant Outdoor Florals |
| ... | ... | ... | ... |
```

---

## 十、检查清单

- [ ] 描述按 7 段式结构
- [ ] 描述含"使用步骤"和"注意事项"
- [ ] A+ 6-7 屏，每屏对应一个语义关系
- [ ] A+ 包含对比模块
- [ ] 图片需求清单完整
- [ ] 不重复五点原话
- [ ] 字数符合规范
- [ ] 关键词自然融入
