# 第四步：标题结构设计

> **标题不是越长越好，也不是关键词越多越好**。标题是 Listing 的"定位声明"，要让系统快速理解、让买家快速决策。

## 🚨 本步不调 MCP

本步基于**第一步词库 + 第三步卖点证据库**生成 3 版标题对比，不再调用 MCP 工具。

### 数据来源
- 关键词优先级：来自第一步 MCP `keyword_miner` / `keyword_research_trends` / `traffic_keyword` 的输出
- 差异化属性：来自第三步痛点-证据映射表
- 品牌名、规格：用户提供

### ✅ 浏览器补充（可选）

```javascript
// 品牌官网（拿品牌定位词）
mcp__web_reader__webReader({url:"https://yourbrand.com/about"})
```

---

## 一、黄金结构

```
[品牌] + [核心品类词] + [关键差异化属性] + [主使用场景] + [规格/数量] + [差异化价值（可选）]
```

### 案例：抗 UV 户外仿真植物

```
Brand UV Resistant Artificial Flowers for Outdoors, 12 Bundles Realistic Faux Plants for Patio Garden Porch Planters, Fade Resistant Outdoor Decor
```

拆解：
- Brand = 品牌
- UV Resistant = 关键差异化属性（L2 功能词）
- Artificial Flowers = 核心品类词（L1）
- for Outdoors = 主使用场景（L3）
- 12 Bundles = 规格（L5）
- Realistic Faux Plants = 同义词扩展（L1 变体）
- for Patio Garden Porch Planters = 详细场景（L3）
- Fade Resistant = 差异化价值（L2）
- Outdoor Decor = 类目定位（L1）

---

## 二、三大原则

### 原则 1：主词靠前
系统从左到右理解权重，核心品类词必须在前 5 个词内出现。

✅ `Brand UV Resistant Artificial Flowers for Outdoors`
❌ `Brand Premium Quality Decor for Home Garden Patio - 12 Bundles UV Resistant Artificial Flowers`

### 原则 2：差异化属性明确
不要用通用形容词（premium / high quality / best），用具体功能词（UV resistant / fade resistant / realistic）。

### 原则 3：场景精准，不要全塞
你的主场景是 patio / garden / porch，标题就讲这三个，**不要把 cemetery / wedding / office / home 全塞进去**。

---

## 三、生成 3 个版本对比

| 版本 | 特点 | 适用场景 |
|------|------|---------|
| 关键词覆盖版 | 多埋词，结构紧凑 | 广告冷启动、强竞价品类 |
| 转化表达版 | 可读性优先，价值前置 | 自然排名沉淀、移动端 |
| 简洁合规版 | 字数克制，无夸大表达 | 高合规风险品类、新账号 |

### 案例（抗 UV 户外仿真植物）

| 版本 | 标题 | 优缺点 |
|------|------|--------|
| 关键词覆盖版 | Brand UV Resistant Artificial Flowers for Outdoors, 12 Bundles Realistic Faux Plants for Patio Garden Porch Planters, Fade Resistant Outdoor Decor | ✅ 核心词全覆盖；❌ 字数偏长 |
| 转化表达版 | Brand 12-Bundle UV Resistant Artificial Flowers — Fade-Proof Outdoor Faux Plants for Patio & Porch Planters | ✅ 移动端友好；❌ 牺牲了 garden 场景 |
| 简洁合规版 | Brand UV Resistant Artificial Flowers, 12 Bundles Faux Plants for Outdoor Patio Garden Planters | ✅ 安全合规；❌ 差异化弱 |

---

## 四、字数与字符规范

| 站点 | 字符上限 | 建议范围 |
|------|---------|---------|
| 美国站（US） | 200 | 150-180（移动端友好） |
| 欧洲站（UK/DE/FR/IT/ES） | 200 | 150-180 |
| 日本站（JP） | 100（字节） | 80-100 |
| 加拿大站（CA） | 200 | 150-180 |

> ⚠️ 移动端通常只展示前 80 字符，**前 80 字符必须包含核心词 + 主卖点**。

---

## 五、给 Codex 的提示词（本步专用）

详见 `prompts/master-prompt.md` 第 5 步。精简版：

> 输入：词库（L1-L5）、痛点证据映射表、品牌名、规格、合规限制。
>
> 任务：
> 1. 生成 3 版标题（关键词覆盖版 / 转化表达版 / 简洁合规版）
> 2. 每版都遵循"品牌 + 核心词 + 差异化属性 + 主场景 + 规格"结构
> 3. 字符控制在 150-180
> 4. 前 80 字符必须包含核心词 + 主卖点
> 5. 标注每版埋入的关键词清单（对照词库）
> 6. 列出优缺点 + 适用场景
> 7. 推荐一版作为基础版，并说明理由

---

## 六、常见错误（必须避免）

| 错误 | 示例 | 修正 |
|------|------|------|
| 通用形容词堆砌 | Premium Quality Beautiful Artificial Flowers | 用功能词替代 |
| 主词靠后 | Brand Outdoor Decor for Home Garden - UV Resistant Artificial Flowers 12 Bundles | 主词前置 |
| 全场景塞满 | for Patio Garden Porch Cemetery Wedding Office Home Balcony | 只放主场景 |
| 重复关键词 | Artificial Flowers UV Resistant Artificial Plants Outdoor Faux Flowers | 同义词去重 |
| 包含竞品品牌 | Better Than [Other Brand] Artificial Flowers | 移除竞品词 |
| 绝对化表达 | 100% No Fade Lifetime Warranty | 改稳健表达 |

---

## 七、输出模板

```markdown
# 标题草稿对比 — {产品名}

## 版本 1：关键词覆盖版
**标题**：Brand UV Resistant Artificial Flowers for Outdoors, 12 Bundles Realistic Faux Plants for Patio Garden Porch Planters, Fade Resistant Outdoor Decor
**字符数**：178
**前 80 字符**：Brand UV Resistant Artificial Flowers for Outdoors, 12 Bundles Real
**埋入关键词**：
- L1：artificial flowers, faux plants
- L2：UV resistant, fade resistant
- L3：outdoors, patio, garden, porch, planters
- L5：12 bundles

**优点**：核心词全覆盖，符合系统索引
**缺点**：字数偏长，移动端可能截断
**适用**：广告冷启动

## 版本 2：转化表达版
...

## 版本 3：简洁合规版
...

## 推荐基础版
**选择**：版本 1
**理由**：[根据品类、账号阶段、广告策略选择]
```

---

## 八、检查清单

- [ ] 3 个版本已生成
- [ ] 每版都遵循黄金结构
- [ ] 字符数在 150-180 之间
- [ ] 前 80 字符含核心词 + 主卖点
- [ ] 无通用形容词堆砌
- [ ] 无竞品品牌词
- [ ] 无绝对化表达
- [ ] 优缺点对比清晰，推荐理由合理
