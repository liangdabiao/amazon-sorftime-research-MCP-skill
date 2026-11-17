# 2026 标题新规详解（7-27 生效）

> 本文件是 `rules.json` 的规则释义文档，供 `lint_title.py` / `lint_highlights.py` / `compliance_report.py` 引用。
> 所有字段名与数值遵循 `rules.json` 与 `indexability_rules.json`。

---

## 0. 新规时间线一览

| 时间节点 | 核心变化 | 影响层级 |
|---|---|---|
| **2025-01-21** | ≤200 字符从严执行；禁用 9 类特殊字符；词/词组重复 ≤2 次（连字符、单复数视为重复） | 规则层（违规即被搜索抑制） |
| **2026-07-27** | 除媒体类目外全品类 **≤75 字符**；新增 **125 字符「商品亮点 / Item Highlights」**字段；超长标题由 AI 改写，品牌卖家有 14 天审核窗口 | 结构层（标题从「主战场」变「门面」） |
| **持续进行** | A10 算法降低精确匹配权重，提升 CTR、语义相关性、外部流量权重 | 算法层（堆词收益递减） |

> **核心信号**：标题从「堆词迎算法」转向「精简迎买家」。skill 必须按 75 字符新规设计，否则 7-27 后生成的 Listing 会被 AI 强制改写。

---

## 1. 75 字符硬上限（title.max_chars.strict_75 = 75）

### 1.1 规则定义

| 字段 | 值 | 说明 |
|---|---|---|
| `title.max_chars.strict_75` | **75** | 2026-07-27 起全品类硬上限（媒体类目除外），含空格 |
| `title.max_chars.transition_200` | **200** | 过渡期上限（2025-01-21 ~ 2026-07-27） |
| `title.recommended_max` | **60** | 移动端首屏可见，官方推荐 |
| `title.warn_threshold` | **70** | 安全余量，超过即告警 |
| `title.core_keyword_within_chars` | **50** | 品牌 + 产品类型 + 第一核心属性须在前 50 字符内 |

### 1.2 适用范围

- **所有站点**（中东站 ME 暂不执行，`site_overrides.ME.skip_75_rule = true`，**待验证**）
- **所有非媒体类目**（媒体类目豁免，见 `sites-overrides.md`）

### 1.3 违规后果

1. 提交后 **24 小时内**通过邮件 / 卖家平台「推荐」通知卖家。
2. 不合规属性被**抑制**（search suppressed，搜索结果中禁止显示）。
3. 进入「**审核商品信息更新（Review Listing Update）**」页面。
4. 生成式 AI 基于原标题生成推荐版本（保留核心、删除重复、符合字数）。

### 1.4 skill 双模式支持

| 模式 | 上限 | 用途 |
|---|---|---|
| `mode: strict_75`（默认） | ≤75 | 面向 7-27 后，推荐 |
| `mode: transition_200` | ≤200 | 过渡期兼容，但仍执行重复词/符号/促销词规则 |

> 文档应明确告知用户：**过渡期生成的 200 字符标题，7-27 后会被 AI 改写，建议直接按 75 生成**。

---

## 2. 125 字符商品亮点字段（highlights.max_chars = 125）

### 2.1 规则定义

| 字段 | 值 | 说明 |
|---|---|---|
| `highlights.max_chars` | **125** | 商品亮点字段字符上限（含空格） |
| `highlights.min_short_clauses` | **3** | 最少 3 个短语 |
| `highlights.required_separator` | **`,`** | 短语间用**逗号**分隔（官方 FAQ 明确，非分号/竖线/换行） |
| `highlights.phrase_not_sentence` | **true** | 逗号分隔的**短语**，不是完整句子 |
| `highlights.max_clause_chars` | **40** | 单短语启发式上限（超长提示可能写成句子，WARN） |
| `highlights.render_separator` | pipe `U+007C` | 前端渲染层把标题与亮点拼成一行时的分隔符，**非字段内容本身**（详见 2.2） |
| `highlights.display_concatenated` | **true** | 实测：前端把标题与亮点拼成一行显示在标题位（详见 2.2） |
| `highlights.prerequisite_title_within` | **75** | 前提：标题已 ≤75 字符，亮点字段才可填 |
| `highlights.distinct_from_title` | **true** | 不重复标题文本（完全重复则 WARN） |
| `highlights.cross_field_repeat_check` | **true** | 跨字段重复词 WARN（拼接同行后买家会看到堆砌，标 TBD，不计 FAIL） |

### 2.2 展示关系：后台两个字段，前端拼成一行（实测，最关键）

> ⚠️ **本 skill 最关键的认知**：标题和亮点在**后台是两个独立字段**，但**前端实际渲染把两者用竖线拼成一行**显示在标题位。质检必须按"拼接同行"建模，不能当成两个互不相干的字段各查各的。这也是本 skill 此前的原则性错误所在。

**三层事实**（2026-08 联网核实，一手来源：亚马逊官方卖家中心 + 官方论坛 + 真实页面实测）：

| 层面 | 事实 |
|---|---|
| **后台** | `title` 与 `item_highlights` 是两个独立字段，分别填写、分别索引 |
| **前端实测** | **两种形态并存**（不同商品/页面不同）：① 拼接一行——标题位把"标题 竖线 亮点"用 pipe（U+007C，前后带空格）连成一行；② 分行显示——标题字号更大、黑色，亮点在标题下方单独一行、字号更小、偏灰 |
| **官方设计意图** | 亮点应显示在标题"**下方**"分两行（官方 FAQ 原文） |
| **现状** | 拼接行曾是官方承认的展示 bug（卖家论坛确认调查中）；如今两种形态并存，可能为逐步修复/灰度切换——**审计时以该商品实际渲染形态为准**，不预设 |

**实测样本**（ASIN B0CY9PB6P3，PDP 的 `#productTitle` 字段）：

```
RAYMYLO Insulated Water Bottle 87 oz, Triple Wall Vacuum Stainless Steel | (Cold for 48 Hrs), Leak Proof & Non-BPA, Modern Water Flask Jug with Paracord Handle & Straw Spout Lids
```

竖线前 ≈71 字符（item name，≤75），竖线后 ≈100 字符（item highlights，≤125）。

**分隔符细节（极易踩坑）**：
- 渲染拼接用的是 `|`（pipe，**U+007C**，连续竖线）
- 标题禁用字符清单里禁的是 `¦`（**broken bar，U+00A6**，断开的竖线）——两者是**不同字符**
- `|`（U+007C）**不在**标题禁用字符清单内；官方文档对分隔符只字未提（设计意图是分两行，本就没设计拼接逻辑）
- **结论**：卖家**不需要也不应该**在 title 或 highlights 字段里自己手填 `|`——那是系统渲染层自动拼的。若 highlights 内容里出现 `|`，提示移除（会干扰系统拼接）

**格式硬要求**（官方 FAQ 原文）：
- **逗号分隔的短语**，不是完整句子：`(Cold for 48 Hrs), Leak Proof & Non-BPA, ...`
- **前提条件**：只有标题已 ≤75 字符时，亮点字段才可用；标题超限时该字段不可填

**对质检的三个直接影响**：
1. **要有"合并呈现串"视角**：买家实际看到的是"标题 竖线 亮点"一行，质检须有拼接串层（预览 + 合并字符数），不能 title / highlights 各查各的
2. **跨字段重复词**：拼接同行后，某词在标题出现又在亮点出现，买家在一行里连续看到堆砌——给 WARN（官方无跨字段明文，标 TBD，不计 FAIL）
3. **亮点格式**：必须逗号短语、非句子（非逗号分隔符给 WARN；单段过长/含句号提示可能写成句子）

**与五点描述的区别**（确认：完全不同字段）：亮点是 2026 新增、125 字符、逗号短语、显示在标题区；五点是详情页中部 "About this item"、每条独立要点。**亮点 ≠ 五点描述**。

> A9 权重说明：`highlights_weight_note` = "2026 new field, A9 weight unverified (estimated 4), mark TBD"。
> 即 125 字段是 2026 新增字段，A9 实际索引权重尚未官方确认，估算为 4（低于标题 5），**标注 TBD 待验证**。
>
> 数据获取约束：卖家精灵 `asin_detail` **无 `item_highlights` 字段**，且返回的 `title` 仍是旧版长标题（实测 180 字符）——即卖家精灵未跟上 7-27 新规的字段拆分。亮点必须 Seller Central 导出，标题需按 75 字符手动拆分。

### 2.3 关键词分层

```
标题(title)          ← 权重最高 5；核心大词、品类词、品牌词
商品亮点(highlights) ← 权重 4(TBD)；长尾词、场景词
五点描述(bullets)    ← 权重 4；功能展开、场景词
后台(backend)        ← 权重 4；同义词、拼写变体、未覆盖长尾；≤250 字节
```

**铁律**：四层不重复，各有分工。标题已有的词不重复塞进其他三层（重复不加分，浪费字符/字节）。

### 2.4 优秀案例（含合并呈现预览）

```
title:           Anker Soundcore Liberty 4 NC Earbuds, Black
item_highlights: Active Noise Cancellation up to 45dB, Bluetooth 5.3, 50H playtime with case, IPX5 waterproof
```

**前端合并呈现串**（系统自动用 pipe 拼接，卖家无需手填分隔符）：

```
Anker Soundcore Liberty 4 NC Earbuds, Black | Active Noise Cancellation up to 45dB, Bluetooth 5.3, 50H playtime with case, IPX5 waterproof
```

- 标题 47 字符 ≤ 75 ✓
- 亮点用**逗号**分隔 4 个短语（非分号、非完整句子）✓，108 字符 ≤ 125 ✓，4 短语 ≥ 3 ✓
- 4 个差异化卖点（降噪 / 蓝牙 / 续航 / 防水）均为标题未出现的长尾/规格词，跨字段无堆砌 ✓
- 合并串总长 ≈158 字符（47 + 3 + 108），买家在一行内同时看到品牌型号 + 核心规格

---

## 3. 重复词规则（title.word_repeat_max = 2）

### 3.1 规则定义

| 字段 | 值 | 说明 |
|---|---|---|
| `title.word_repeat_max` | **2** | 词/词组出现 ≤2 次（允许 2 次，第 3 次违规） |
| `title.repeat_exempt` | 介词/连词/冠词 18 个 | 不计入重复 |
| `title.repeat_normalization` | strip_hyphen / singularize / lowercase | 归一化后再计数 |

### 3.2 豁免词表（repeat_exempt）

```
介词: in, on, over, with, for, to, of, at, by
连词: and, or, but, nor, so, yet
冠词: the, a, an
```

> 共 18 个，全部小写比对。这些词可多次出现，不计重复。

### 3.3 归一化规则（repeat_normalization）—— 官方最易漏的点

亚马逊官方明确（2025-01-21 公告原文）：**使用连字符或单复数形式的同一词语也会被视为重复**。

| 归一化步骤 | 函数 | 示例 |
|---|---|---|
| 1. 去连字符 | `strip_hyphen`：`word.replace("-","")` | `multi-color` → `multicolor` |
| 2. 单数化 | `singularize`：去末尾 `s`/`es`/`ies` | `apples` → `apple`；`boxes` → `box`；`babies` → `baby` |
| 3. 小写 | `lowercase`：`.lower()` | `Apple` → `apple` |

**官方示例**：
- `apple` 与 `apples` → 归一后均为 `apple` → **计为重复**
- `multi-color` 与 `multicolor` → 归一后均为 `multicolor` → **计为重复**

### 3.4 违规示例

```
❌ Wireless Earbuds Bluetooth Headphones, Noise Cancelling True Wireless
   Earphones in-Ear Bluetooth 5.3 Sport Headphones with Mic
```

| 词 | 出现次数（归一后） | 判定 |
|---|---|---|
| `bluetooth` | 2 | 边缘合规（=2） |
| `wireless` | 2 | 边缘合规（=2） |
| `headphone`（headphones 归一） | 2 | 边缘合规（=2） |
| `earbud`/`earphone` | 各 1 | 合规 |

> 上述虽未超 2 次，但语义堆砌明显，A10 会判定关键词堆砌降权。skill 即使字面合规也应告警。

---

## 4. 禁用字符（title.forbidden_chars / forbidden_non_ascii）

### 4.1 禁用特殊字符（9 类）

```
forbidden_chars: ['!', '$', '?', '_', '{', '}', '^', '¬', '¦']
```

**例外**：品牌名称的固有组成部分除外。例如品牌名 `LEGO!`（假设）中的 `!` 允许。
skill 实现：对 `brand` token 跳过禁用字符校验。

### 4.2 禁用非语言 ASCII

```
forbidden_non_ascii: ['Æ', 'Š', 'Œ', 'Ÿ', 'Ž', 'Ø', 'ß']
```

仅允许标准字母和数字。

### 4.3 允许的标点（allowed_punct）

```
allowed_punct: ['-', '/', ',', '&', '.', '(', ')', '"', "'"]
```

| 标点 | 典型用途 | 示例 |
|---|---|---|
| `-`（连字符） | 复合词、尺寸 | `1/2-Inch`、`multi-color` |
| `/`（斜杠） | 比例、选项 | `1/2`、`men/women` |
| `,`（逗号） | 字段分隔 | `Earbuds, Black` |
| `&`（和号） | 品牌/系列 | `Johnson & Johnson` |
| `.`（句点） | 小数、缩写 | `1.5L`、`3.5mm` |
| `()`（括号） | 包装说明 | `(Pack of 3)` |
| `"`（双引号） | 英寸 | `8"` |
| `'`（撇号） | 所有格 | `Levi's` |

### 4.4 允许的单位缩写（allowed_unit_abbr）

```
allowed_unit_abbr: ['cm', 'oz', 'in', 'kg', 'ml', 'lb', 'ft', 'mm', 'g', 'mg', 'W', 'V', 'Ah', 'Hz']
```

测量单位缩写允许直接出现在标题中，如 `32oz`、`20V`、`50ml`。

---

## 5. 禁用内容（促销词 / 主观词 / 商业信息）

### 5.1 促销词黑名单（forbidden_promo_words，按 language 取）

**英文（en）**：
```
free shipping, best seller, hot item, 100% quality guaranteed, sale,
discount, cheap, bargain, new arrival, top rated, #1, best price,
lowest price, limited time, free gift, guaranteed
```

**中文（zh）**：
```
免运费, 热销, 爆款, 第一, 精品, 优质, 特价, 促销, 降价, 包邮, 赠品, 热卖, 正品
```

> 日文（ja）/ 德文（de）/ 法文（fr）：为空数组，待补充。

### 5.2 主观词（forbidden_subjective）

**英文（en）**：`amazing, incredible, perfect, awesome, stunning, fantastic, unbelievable`
**中文（zh）**：`完美, 惊艳, 极佳, 超强, 顶级`

### 5.3 禁止的商业信息

- **价格**：`$9.99`、`Only ...`
- **公司/卖家信息**：`Sold by ABC`、公司名
- **配送信息**：`Ships from`、`FBA`

---

## 6. 大小写与结构规则

| 规则 | 值 | 说明 |
|---|---|---|
| `title.no_all_caps` | **true** | 不得全大写（品牌缩写、型号除外） |
| `title.title_case` | **true** | 每词首字母大写（介词/连词/冠词除外） |
| `title.numbers_arabic` | **true** | 用阿拉伯数字 `2` 而非 `two` |
| `title.brand_first` | **true** | 品牌名置首 |
| `title.must_contain` | `["brand", "product_type"]` | 标题必备要素 |

### 官方词序（structure_formula）

```
品牌 → 口味/款式 → 产品类型 → 关键属性（USP） → 颜色 → 尺寸/包装数量 → 型号
```

---

## 7. 变体规则（variation）

| 规则 | 值 | 说明 |
|---|---|---|
| `variation.parent_no_attrs` | **true** | 父 ASIN 标题**不含**尺寸/颜色 |
| `variation.child_has_attrs` | **true** | 子 ASIN 标题**含**尺寸/颜色 |
| `variation.child_attrs` | `["color","size","flavor","scent","style"]` | 子 ASIN 变体属性白名单 |

| 类型 | 示例 |
|---|---|
| 父 ASIN | `Anker Soundcore Liberty 4 NC Earbuds` |
| 子 ASIN | `Anker Soundcore Liberty 4 NC Earbuds, Black` |

---

## 8. AI 改写窗口期（品牌卖家务必主动）

### 8.1 机制（2026-07-27 起）

1. 7-27 后超 75 字符的标题，亚马逊用 **AI 逐步生成建议版本**（基于后台产品信息）。
2. 品牌卖家有 **14 天审核窗口**：可查看、修改或批准 AI 建议。
   - **Agree**：接受 AI 建议。
   - **Fix myself**：自己修改（须回传表格）。
   - **不操作**：窗口期结束 AI 版本**自动生效**。
3. **错过 14 天**：亚马逊自动发布 AI 推荐版本，确保 Listing 不被抑制；卖家事后仍可手动改回合规标题。
4. **不影响账户健康得分**（官方明确）。

### 8.2 风险提示

AI 改写大概率会删减部分差异化关键词，**主动手动优化远比被动接受稳妥**。
skill 应在文档中建议用户：**7-27 前主动用 strict_75 模式重写所有超长标题**。

### 8.3 后台操作路径

卖家中心 → 管理所有库存（Manage Inventory）→ 找到商品 → 点击「编辑」→ 查看改进内容。
系统会提供符合新规的标题 + 商品亮点建议，将关键信息保留在标题、其余移至亮点。

---

## 9. 常见违规速查表

| # | 违规类型 | 示例 | 校验字段 |
|---|---|---|---|
| 1 | 超 75 字符 | 任意长标题 | `max_chars.strict_75` |
| 2 | 词重复 >2 次（含单复数/连字符归一） | `Bluetooth ... Bluetooth` | `word_repeat_max` |
| 3 | 禁用特殊字符 | `Best Price!!!` | `forbidden_chars` |
| 4 | 非语言 ASCII | `ÆØßŒŽ` | `forbidden_non_ascii` |
| 5 | 促销词 | `Free Shipping` | `forbidden_promo_words` |
| 6 | 主观词 | `Amazing` | `forbidden_subjective` |
| 7 | 全大写 | `WATER BOTTLE` | `no_all_caps` |
| 8 | 价格/公司信息 | `Only $9.99` | （`forbidden_promo_words` 扩展） |
| 9 | 变体属性放父 ASIN | 父：`T-Shirt, White, Medium` | `variation.parent_no_attrs` |
| 10 | 核心词靠后 | `[一堆形容词] Water Bottle` | `core_keyword_within_chars` |

---

**版本**：v1.0
