# 第四步：标题 + 商品亮点分层设计（Item Name + Item Highlights）

> **2026-07-27 起美国站前台标题结构已改为双字段**（图书/音乐/影音等媒介类目除外）：Item Name（75 字符）+ Item Highlights（125 字符）。合计仍是 200 字符，信息量没砍，只是重新分层：**标题管身份识别，亮点管比较辅助**。标题不是越长越好，也不是关键词越多越好。

## 🚨 本步不调 MCP

本步基于**第一步词库 + 第三步卖点证据库**生成 3 版"标题 + 亮点"组合对比，不再调用 MCP 工具。

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

## 一、2026 新规：75 + 125 = 200 双字段结构

| 字段 | 字符上限 | 定位 | 前台位置 | API 字段 |
|------|---------|------|---------|---------|
| **Item Name（标题）** | 75（含空格） | 身份识别：品牌 + 品类 + 核心差异 | 主标题 | `item_name` |
| **Item Highlights（商品亮点）** | 125 | 比较辅助：材质 / 场景 / 兼容 / 规格 / 限制 | 移动端：标题正下方单独一行浅色小字；桌面端：用竖线 `\|` 与标题拼接成一行 | `title_differentiation` |

### 关键属性（必须记住）

1. **可搜索索引**：官方明确 Item Highlights 内容会被搜索抓取，放进去的关键词能带来曝光（具体 ranking 权重官方只确认"可索引"，仍在观察期）
2. **格式**：逗号分隔的短语，**不是完整句子**，也不是五点描述（Bullet Points 仍独立存在，互不替代）
3. **API 提交**：`title_differentiation` 通过 Listings Items API 或 JSON_LISTINGS_FEED 提交；先调 `getDefinitionsProductType` 确认该类目已开放该属性
4. **存量 Listing 不强制立刻改**：超 75 字符的老标题 7-27 后不会被下架；亚马逊 AI 会自动拆分到 `item_name` + `title_differentiation`，品牌所有者有 **14 天审核窗口**（Manage All Inventory → Edit → View enhancements）可驳回/修改再批准
5. **批量迁移**：下载 Category Listings Report，表内已带 Item Highlights 列，填完传回通常 8 小时内生效
6. **提交口径注意**：提交超 75 字符的 `item_name` 时目录会自动拆分；`getListingsItem` 返回的是你的原始提交值，前台展示的是拆分后版本

> ⚠️ 大卖家长尾词如果原来全压在标题里，现在必须主动重新分配到 Highlights——否则 AI 自动拆分可能把转化词切掉。

---

## 二、双字段黄金结构

```
Item Name（≤75 字符）:
[品牌] + [核心品类词] + [关键差异化属性] + [规格/数量]

Item Highlights（≤125 字符，逗号分隔短语）:
[材质/工艺], [主场景], [兼容/适用对象], [包装内容], [限制条件]
```

### 案例 1：抗 UV 户外仿真植物

**旧写法（200 字符长标题，已过时）**：

```
Brand UV Resistant Artificial Flowers for Outdoors, 12 Bundles Realistic Faux Plants for Patio Garden Porch Planters, Fade Resistant Outdoor Decor
```

**新写法**：

- Item Name（49 字符）：`Brand UV Resistant Artificial Flowers, 12 Bundles`
- Item Highlights（约 104 字符）：`UV & Fade Resistant, Realistic Faux Plants, for Patio Garden Porch Planters, Outdoor Decor, No Watering Needed`

拆解：
- Item Name = 品牌（Brand）+ 核心品类词（Artificial Flowers，L1）+ 关键差异（UV Resistant，L2）+ 规格（12 Bundles，L5）→ 身份识别，75 字符内完成
- Item Highlights = 功能（UV & Fade Resistant，L2）+ 同义词（Realistic Faux Plants，L1 变体）+ 详细场景（Patio Garden Porch Planters，L3）+ 类目定位（Outdoor Decor，L1）+ 差异价值（No Watering Needed，L4）→ 帮助比较的信息

### 案例 2：官方风格示例（USB-C 充电器）

旧标题：USB-C 快充适配器，支持 PPS，适用 MacBook/iPhone/Galaxy…不含线

- 标题只留：`USB-C PPS Charger`
- Highlight：`USB-C, Supports PPS, Cable Not Included, Travel & Office`

---

## 三、双字段三大原则

### 原则 1：主词靠前（Item Name）
系统从左到右理解权重，核心品类词必须在前 5 个词内出现。Item Name 只有 75 字符，就是移动端完整可见的主标题，**必须独立完成身份识别**，不能依赖 Highlights 补词。

✅ `Brand UV Resistant Artificial Flowers, 12 Bundles`
❌ `Brand Premium Quality Decor, 12 Bundles`（核心品类词缺失）

### 原则 2：差异化属性具体，亮点不重复标题
不要用通用形容词（premium / high quality / best），用具体功能词（UV resistant / fade resistant / realistic）。**Highlights 不搬运标题已有的词继续堆**——同一个词写两遍不增加索引价值，浪费 125 字符配额。

### 原则 3：亮点是短语清单，不是第二标题
Highlights 放"帮助比较"的信息：材质、适用场景、兼容型号、包装内容、限制条件。不放促销语（Free Shipping / Best Price / Sale），不写成完整句子，不把五点描述复制进来。

---

## 四、生成 3 个版本对比

| 版本 | 特点 | 适用场景 |
|------|------|---------|
| 关键词覆盖版 | 标题+亮点合计埋词最多，结构紧凑 | 广告冷启动、强竞价品类 |
| 转化表达版 | 可读性优先，价值前置 | 自然排名沉淀、移动端 |
| 简洁合规版 | 字数克制，无夸大表达 | 高合规风险品类、新账号 |

### 案例（抗 UV 户外仿真植物）

| 版本 | Item Name | Item Highlights | 优缺点 |
|------|-----------|-----------------|--------|
| 关键词覆盖版 | Brand UV Resistant Artificial Flowers, 12 Bundles | UV & Fade Resistant, Realistic Faux Plants, for Patio Garden Porch Planters, Outdoor Decor, No Watering Needed | ✅ 核心词全覆盖；❌ 亮点接近满配，后续加词空间小 |
| 转化表达版 | Brand 12-Bundle UV Resistant Fake Plants That Look Real | UV & Fade Proof, Lush & Realistic, for Patio & Porch Planters, Zero Maintenance Outdoor Decor | ✅ 移动端友好；❌ 牺牲了 garden 场景词 |
| 简洁合规版 | Brand UV Resistant Artificial Flowers, 12 Bundles | Fade Resistant, for Outdoor Planters, Plastic Stems, No Watering | ✅ 安全合规、留白多；❌ 差异化弱 |

---

## 五、字数与字符规范

| 站点 | Item Name 上限 | Item Highlights 上限 | 建议组合 |
|------|--------------|---------------------|---------|
| 美国站（US） | 75 字符 | 125 字符 | 标题 60-75 + 亮点 90-125 |
| 欧洲站（UK/DE/FR/IT/ES） | 75 字符 | 125 字符 | 同美国站 |
| 日本站（JP） | 按站点公告执行 | 按站点公告执行 | 以类目 schema 为准 |
| 加拿大站（CA） | 75 字符 | 125 字符 | 同美国站 |

> ⚠️ 本 Skill 以美国站为基准。其他站点上线前先调 `getDefinitionsProductType` 拿 schema，确认该类目 `title_differentiation` 属性与字符上限。
> ⚠️ 媒介类目（图书/音乐/影音）不适用本次改革，仍按原 200 字符单标题处理。

---

## 六、给 Codex 的提示词（本步专用）

详见 `prompts/master-prompt.md` 第 4 步。精简版：

> 输入：词库（L1-L5）、痛点证据映射表、品牌名、规格、合规限制。
>
> 任务：
> 1. 生成 3 版"Item Name + Item Highlights"组合（关键词覆盖版 / 转化表达版 / 简洁合规版）
> 2. Item Name 遵循"品牌 + 核心词 + 差异化属性 + 规格"结构，≤75 字符
> 3. Item Highlights 为逗号分隔短语（材质/场景/兼容/包装/限制），≤125 字符，**不重复 Item Name 已有词**
> 4. 分别标注两字段的字符数与埋入关键词清单（对照词库）
> 5. 列出优缺点 + 适用场景
> 6. 推荐一版作为基础版，并说明理由

---

## 七、常见错误（必须避免）

| 错误 | 示例 | 修正 |
|------|------|------|
| 通用形容词堆砌 | Premium Quality Beautiful Artificial Flowers | 用功能词替代 |
| 主词靠后 | Brand Outdoor Decor - UV Resistant Artificial Flowers 12 Bundles | 主词前置 |
| 标题超 75 字符仍按旧 200 字符写 | 沿用旧长标题不拆分 | 按 75+125 双字段重写 |
| 亮点重复标题词 | 标题已有 UV Resistant，亮点再写 UV Resistant | 亮点只放标题未覆盖的比较信息 |
| 亮点写成完整句子 / 促销语 | These flowers will never fade! Buy now! | 改逗号分隔短语 |
| 全场景塞满 | for Patio Garden Porch Cemetery Wedding Office Home | 只放主场景（次场景留给五点/A+/QA） |
| 重复关键词 | Artificial Flowers UV Resistant Artificial Plants Outdoor Faux Flowers | 同义词去重 |
| 包含竞品品牌 | Better Than [Other Brand] Artificial Flowers | 移除竞品词 |
| 绝对化表达 | 100% No Fade Lifetime Warranty | 改稳健表达 |

---

## 八、输出模板

```markdown
# 标题 + 亮点草稿对比 — {产品名}

## 版本 1：关键词覆盖版
**Item Name**：Brand UV Resistant Artificial Flowers, 12 Bundles
**Item Name 字符数**：49
**Item Highlights**：UV & Fade Resistant, Realistic Faux Plants, for Patio Garden Porch Planters, Outdoor Decor, No Watering Needed
**Item Highlights 字符数**：111
**埋入关键词**：
- L1：artificial flowers（标题）, faux plants（亮点）
- L2：UV resistant（标题）, fade resistant / no watering（亮点）
- L3：patio, garden, porch, planters, outdoor（亮点）
- L5：12 bundles（标题）

**优点**：核心词全覆盖，标题+亮点两层索引
**缺点**：亮点接近满配，加词空间小
**适用**：广告冷启动

## 版本 2：转化表达版
...

## 版本 3：简洁合规版
...

## 推荐基础版
**选择**：版本 1
**理由**：[根据品类、账号阶段、广告策略选择]

## 存量 Listing 迁移提示（如适用）
- 旧标题是否超 75 字符：是/否
- 建议动作：主动按双字段重写 / 等 AI 自动拆分后 14 天内人工审核
```

---

## 九、检查清单

- [ ] 3 个"标题 + 亮点"组合已生成
- [ ] Item Name ≤ 75 字符，含品牌 + 核心品类词 + 关键差异 + 规格
- [ ] Item Highlights ≤ 125 字符，逗号分隔短语，非完整句子
- [ ] Highlights 不重复 Item Name 已有词
- [ ] Highlights 无促销语、无绝对化表达
- [ ] 核心品类词在 Item Name 前 5 个词内
- [ ] 无通用形容词堆砌
- [ ] 无竞品品牌词
- [ ] 两字段字符数已分别标注
- [ ] 优缺点对比清晰，推荐理由合理
- [ ] （存量 Listing）已给出迁移建议（主动改 / AI 拆分 + 14 天人工审核）
