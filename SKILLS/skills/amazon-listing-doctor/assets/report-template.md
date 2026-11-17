# Amazon Listing 体检报告

> 本报告由 **amazon-listing-doctor** 生成，依据 Amazon 2026 新规、CDQ 评分模型与 COSMO 意图覆盖度。
> 占位符 `{{path.to.field}}` 由渲染时替换为实际值。**只诊断不改写**——改进建议指向问题，改写由你自己决定。

**类目**: `{{meta.category}}` · **站点**: `{{meta.market}}` · **语言**: `{{meta.language}}` · **模式**: `{{meta.mode}}`
**品牌**: `{{meta.brand}}` · **父体**: `{{meta.is_parent}}` · **子体**: `{{meta.is_variation}}`
**生成时间**: `{{meta.generated_at}}`

---

## 〇、数据覆盖度

> 体检前先看：本次输入覆盖了多少字段？缺哪些？补哪些字段可解锁剩余评分维度？

| 维度 | 已收 / 总数 |
|---|---|
| **前台**（visible to buyer） | `{{compliance_report.data_coverage.frontend.provided_count}}` / `{{compliance_report.data_coverage.frontend.total_count}}` |
| **后台**（backend-only） | `{{compliance_report.data_coverage.backend.provided_count}}` / `{{compliance_report.data_coverage.backend.total_count}}` |
| **覆盖度** | `{{meta.data_coverage_ratio}}`（{{meta.data_coverage_overall}}） |

**前台已收**: `{{compliance_report.data_coverage.frontend.provided}}`
**前台缺失**: 遍历 `{{compliance_report.data_coverage.frontend.missing}}`（每项含 field/label）
**后台已收**: `{{compliance_report.data_coverage.backend.provided}}`
**后台缺失**: 遍历 `{{compliance_report.data_coverage.backend.missing}}`

> ℹ️ **数据分层原则**：前台数据(title/bullets/description/images/brand/has_a_plus)可通过 SellerSprite MCP（asin_detail）或卖家粘贴获取；后台数据(item_highlights/backend_search_terms/attributes_filled/attributes_top10_expected/band_a_critical_6)只能从 Seller Central 后台导出。

**补齐这些字段可解锁更多维度**（`{{compliance_report.data_coverage.unlock_dimensions}}`，遍历每项含 field/label/source）:

---

## 总览

| 指标 | 值 |
|---|---|
| **总体结论** | `{{compliance_report.summary}}` |
| **CDQ 总分（主）** | `{{cdq_score.total}}` / 100（`{{cdq_score.grade}}`） |
| **CDQ 可用子分** | `{{cdq_score.available_total}}` / 100（仅基于非降级子项，参考用） |
| **收录健康度（A9）** | `{{indexability_report.score}}` / 100 |
| **意图覆盖度（COSMO）** | `{{cosmo_report.score}}` / 100 · 覆盖率 `{{cosmo_report.coverage_ratio}}` · 可用 `{{cosmo_report.input_available}}` |
| **Alexa 可发现性** | `{{alexa_discoverability.score}}` / 100 · 可用 `{{alexa_discoverability.input_available}}` |
| **合规检查** | PASS `{{compliance_report.passed_checks}}` · FAIL `{{compliance_report.failed_checks}}` · WARN `{{compliance_report.warnings}}` |

> ⚠️ `score=null` 表示评分因关键字段缺失而不可用（不强行给 0/100）；维度不可用的具体原因见 `input_unavailable_reason` 与 `action_items` 头部降级说明。

> CDQ 为主总分（官方权重背书）；A9/COSMO/Alexa 为并列诊断维度。COSMO 基于公开论文（WWW 2024）精神的社区概念覆盖诊断，**非官方 COSMO 分**。

---

## 一、合规体检

> 检查 Listing 各字段是否违反 Amazon 硬规则：标题 75 字符、亮点 ≤125 字符（逗号分隔短语）且 ≥3 短语、五点 5-6 条且单条 ≤500 字符、后台搜索词 ≤250 字节等。标题与亮点在前端拼成一行（竖线分隔），1.2 节给出合并呈现串。

### 1.1 标题（Title）

- **当前值**: `{{title.value}}`
- **字符数**: `{{title.char_count}}` / 75
- **合规**: `{{title.compliant}}`

| 检查项 | 状态 | 详情 |
|---|---|---|
| 字符上限 | `{{title.checks.char_limit.status}}` | `{{title.checks.char_limit.actual}}` / `{{title.checks.char_limit.limit}}` |
| 字符利用率 | `{{title.checks.char_utilization.status}}` | `{{title.checks.char_utilization.actual}}` / `{{title.checks.char_utilization.limit}}` |
| 重复词 | `{{title.checks.repeated_word.status}}` | `{{title.checks.repeated_word.details}}` |
| 禁用字符 | `{{title.checks.forbidden_char.status}}` | — |
| 促销词 | `{{title.checks.promo_word.status}}` | — |
| 主观词 | `{{title.checks.subjective_word.status}}` | — |
| 大小写 | `{{title.checks.casing.status}}` | — |
| 核心词前置 | `{{title.checks.core_keyword_pos.status}}` | 前 `{{title.checks.core_keyword_pos.within_chars}}` 字符内（限 `{{title.checks.core_keyword_pos.limit}}`） |

> ⚠️ 前端标题与商品亮点的呈现形态目前不稳定（拼接一行 / 分行显示两种形态并存，且随亚马逊灰度切换）——本节标题判定基于归一化输入，动手修改前建议你自行打开 listing 页面二次确认实际显示形态。

**修复建议**:
{{title.fix_suggestions}}

### 1.2 商品亮点（Highlights）

> ℹ️ 2026 新规：标题与亮点在**前端拼成一行**显示在标题位（竖线 `|` 分隔，亚马逊承认的展示 bug）。后台虽是两个独立字段，但买家看到的是一行连续文本——故下方单独给出"合并呈现串"。

- **当前值**: `{{highlights.value}}`
- **字符数**: `{{highlights.char_count}}` / 125
- **短语数**: `{{highlights.clause_count}}`（官方要求逗号分隔）
- **合规**: `{{highlights.compliant}}`

**合并呈现串**（前端实际形态，系统自动用 `|` 拼接，卖家无需手填分隔符）：

> `{{highlights.display_string.preview}}`

合并字符数: `{{highlights.display_string.combined_chars}}`（标题 `{{highlights.display_string.title_chars}}` + 亮点 `{{highlights.display_string.highlights_chars}}`）

| 检查项 | 状态 | 详情 |
|---|---|---|
| 字符上限 | `{{highlights.checks.char_limit.status}}` | `{{highlights.checks.char_limit.actual}}` / 125 |
| 短语数 ≥3 | `{{highlights.checks.min_clauses.status}}` | `{{highlights.checks.min_clauses.actual}}` / `{{highlights.checks.min_clauses.limit}}` |
| 逗号分隔格式 | `{{highlights.checks.separator_format.status}}` | `{{highlights.checks.separator_format.found}}` |
| 短语非句子 | `{{highlights.checks.phrase_not_sentence.status}}` | `{{highlights.checks.phrase_not_sentence.details}}` |
| 不含自填分隔符 | `{{highlights.checks.no_embedded_pipe.status}}` | `{{highlights.checks.no_embedded_pipe.found}}` |
| 字符利用率 | `{{highlights.checks.char_utilization.status}}` | `{{highlights.checks.char_utilization.actual}}` / 125 |
| 与标题不重复 | `{{highlights.checks.distinct_from_title.status}}` | — |
| 跨字段重复词(TBD) | `{{highlights.checks.cross_field_repeat.status}}` | `{{highlights.checks.cross_field_repeat.details}}` |

> ⚠️ 跨字段重复词为 TBD 项（官方无跨字段明文规则，拼接同行后买家会看到堆砌），仅 WARN 不计合规。

**修复建议**:
{{highlights.fix_suggestions}}

### 1.3 五点描述（Bullets）

- **条数**: `{{bullets.count}}`（要求 5-6）
- **合规**: `{{bullets.compliant}}`

| 检查项 | 状态 | 详情 |
|---|---|---|
| 条数范围 | `{{bullets.checks.count_limit.status}}` | `{{bullets.checks.count_limit.actual}}`（`{{bullets.checks.count_limit.min}}`-`{{bullets.checks.count_limit.max}}`） |

**修复建议**:
{{bullets.fix_suggestions}}

### 1.4 后台搜索词（Backend Search Terms）

- **字节数**: `{{backend.byte_count}}` / 250
- **合规**: `{{backend.compliant}}`

| 检查项 | 状态 | 详情 |
|---|---|---|
| 字节上限 | `{{backend.checks.byte_limit.status}}` | `{{backend.checks.byte_limit.actual}}` / `{{backend.checks.byte_limit.limit}}` |
| 空格分隔 | `{{backend.checks.separator.status}}` | — |
| 无停用词 | `{{backend.checks.no_stopwords.status}}` | 命中: `{{backend.checks.no_stopwords.found}}` |
| 无特殊字符 | `{{backend.checks.no_special_chars.status}}` | — |
| 不重复前文 | `{{backend.checks.distinct_from_title_bullets.status}}` | 重复: `{{backend.checks.distinct_from_title_bullets.duplicates}}` |

**修复建议**:
{{backend.fix_suggestions}}

### 1.5 属性与变体

- **Top10 属性完整度**: `{{attributes.filled_ratio}}`（已填 `{{attributes.filled}}` / 期望 `{{attributes.top10_expected}}`）
- **Band A 关键 6 项**: 已填 `{{attributes.band_a_filled}}` / 全量 `{{attributes.band_a_critical_6}}`
- **属性合规**: `{{attributes.compliant}}`

> ⚠️ 若属性期望清单来自工具内置兜底（`cdq_score.components.structured_attribute.basis == "builtin_fallback"`），上述完整度为**参考值**——内置清单为公开版大类近似，可能不符子品类；结论以 Seller Central 属性面板或前台类目筛选器实测为准。

| 变体检查 | 状态 |
|---|---|
| 父标题不含尺寸/颜色 | `{{variation.checks.parent_no_attrs.status}}` |
| 子体携带变体属性 | `{{variation.checks.child_has_attrs.status}}` |

---

## 二、CDQ 评分（Content Data Quality）

> 反映 Listing 内容质量对转化的支撑度，满分 100。权重：结构化属性 30% / 标题 25% / 变体 20% / 图片 15% / 五点 5% / A+ 5%。

**总分**: **`{{cdq_score.total}}` / 100** · 档位: **`{{cdq_score.grade}}`**

| 维度 | 子分 | 权重 | 说明 |
|---|---|---|---|
| 结构化属性 | `{{cdq_score.components.structured_attribute.score}}` | `{{cdq_score.components.structured_attribute.weight}}` | `{{cdq_score.components.structured_attribute.reason}}` |
| 标题 | `{{cdq_score.components.title.score}}` | `{{cdq_score.components.title.weight}}` | `{{cdq_score.components.title.reason}}` |
| 变体 | `{{cdq_score.components.variation.score}}` | `{{cdq_score.components.variation.weight}}` | `{{cdq_score.components.variation.reason}}` |
| 图片 | `{{cdq_score.components.image.score}}` | `{{cdq_score.components.image.weight}}` | `{{cdq_score.components.image.reason}}` |
| 五点 | `{{cdq_score.components.bullet_point.score}}` | `{{cdq_score.components.bullet_point.weight}}` | `{{cdq_score.components.bullet_point.reason}}` |
| A+ | `{{cdq_score.components.a_plus.score}}` | `{{cdq_score.components.a_plus.weight}}` | `{{cdq_score.components.a_plus.reason}}` |

> ⚠️ 子分 `null` 表示该子项因关键字段缺失被降级；缺字段时不要看总分误导，可用子分 `cdq_score.available_total` 才是真实可比的分数。降级维度列表见 `{{cdq_score.score_unavailable}}`。

> 档位参考：Optimized 90-100 · Great 80-89 · Good 70-79 · Fair 50-69 · Poor 0-49

**改进建议**:
{{cdq_score.improve_suggestions}}

---

## 三、收录健康度（A9 Indexability）

> 评估 Listing 被 Amazon A9 搜索引擎有效收录的能力。核心词前置越靠前、backend 卫生度越高、属性越完整，收录越充分。

**收录健康度**: **`{{indexability_report.score}}` / 100**

| 指标 | 值 |
|---|---|
| 核心词前置位置 | `{{indexability_report.core_keyword_position}}` 字符内 |
| Backend 卫生分 | `{{indexability_report.backend_hygiene}}` |
| 属性完整度 | `{{indexability_report.attribute_completeness}}` |
| 有效索引词数 | `{{indexability_report.effective_index_terms}}` |

**收录风险**:
{{indexability_report.risks}}

---

## 四、Alexa 可发现性（AEO 买家问答）

> 评估 AI 购物助手（Alexa for Shopping / Rufus）回答买家提问时，能不能从你的 Listing 里找到答案并推荐你。模拟真实买家提问，判断 Listing 能回答多少个问题——能回答的越多、越完整，AI 助手越会把你推给买家（Answer Engine Optimization）。
> ALEXA 与 COSMO 本质差异化——COSMO（概念覆盖）看你内容写全没，ALEXA（买家问答）看你能不能接住买家的问。

**可发现性**: **`{{alexa_discoverability.score}}` / 100** · 方式：`{{alexa_discoverability._extraction_method}}`（来源：`{{alexa_discoverability.lexicon_source}}`）

**产品理解**：`{{alexa_discoverability.product}}`

**Agent 针对该产品生成的买家问题**（共 `{{alexa_discoverability.total_questions}}` 个，模拟真实买家向 AI 购物助手提问）：
{{alexa_discoverability.buyer_questions}}

| 回答三态 | 数量 | 问题示例 |
|---|---|---|
| ✅ 完全可答（covered） | `{{alexa_discoverability.covered_count}}` | `{{alexa_discoverability.buyer_alignment.covered}}` |
| 🟡 部分可答（partial） | `{{alexa_discoverability.partial_count}}` | `{{alexa_discoverability.buyer_alignment.partial}}` |
| ❌ 未回答（missing） | `{{alexa_discoverability.missing_count}}` | `{{alexa_discoverability.buyer_alignment.missing}}` |

> 共模拟 `{{alexa_discoverability.total_questions}}` 个买家问题。score = (covered×1.0 + partial×0.5) / 总问题数 × 100。

**卖家最该补的回答（Top Missing）**:
{{alexa_discoverability.top_missing_questions}}

**补充建议**:
{{alexa_discoverability.suggestions}}

> ℹ️ 当未提供 `_alexa_aeo_result`（Agent 未做 AEO 判断）时，本维度自动降级为 substring 词匹配，输出 `scene_coverage` / `audience_coverage` / `limit_coverage` / `missing_*` 字段而非 `buyer_alignment`，用于零依赖兜底。

---

## 五、COSMO 意图覆盖度

> 评估 Listing 是否覆盖了"用户意图/常识关联"——除了产品属性词，是否说清了用户怎么用、为谁设计、为什么买、什么场景下用。基于亚马逊 COSMO 公开论文（WWW 2024 电商常识知识图谱）精神，**非官方 COSMO 分**。重点看缺失清单。

**意图覆盖度**: **`{{cosmo_report.score}}` / 100** · 精确覆盖率: **`{{cosmo_report.coverage_ratio}}`**

| 维度 | 覆盖 / 总数 | 已覆盖 | 缺失（建议补充） |
|---|---|---|---|
| 用途/场景（use_case） | `{{cosmo_report.per_dimension.use_case.covered}}` / `{{cosmo_report.per_dimension.use_case.total}}` | `{{cosmo_report.covered_concepts.use_case}}` | `{{cosmo_report.missing_concepts.use_case}}` |
| 人群（audience） | `{{cosmo_report.per_dimension.audience.covered}}` / `{{cosmo_report.per_dimension.audience.total}}` | `{{cosmo_report.covered_concepts.audience}}` | `{{cosmo_report.missing_concepts.audience}}` |
| 目标/结果（goal） | `{{cosmo_report.per_dimension.goal.covered}}` / `{{cosmo_report.per_dimension.goal.total}}` | `{{cosmo_report.covered_concepts.goal}}` | `{{cosmo_report.missing_concepts.goal}}` |
| 约束/限制（constraint） | `{{cosmo_report.per_dimension.constraint.covered}}` / `{{cosmo_report.per_dimension.constraint.total}}` | `{{cosmo_report.covered_concepts.constraint}}` | `{{cosmo_report.missing_concepts.constraint}}` |

> ⚠️ `goal` 维度故意偏难：listing 常堆属性词而不写"用户目标"，goal 覆盖率低说明 listing 缺少从用户购买动机角度的表达——这是 COSMO 的核心诊断价值。

**补充建议**:
{{cosmo_report.suggestions}}

---

## 六、标题词组分诊（Title Triage）

> 把标题拆成语义词组，按词性 + 合规信号给每个词组一个去向建议：**标题必留 / 标题优先 / 下移亮点 / 下移五点 / 删除（违规）**。confidence=low 的词组多为品类词或混合词组，需人工复核类型。只给去向建议，不生成改写文案。

**标题**: `{{triage_report.title}}`（`{{triage_report.char_count}}` / `{{triage_report.char_limit}}` 字符，超限: `{{triage_report.over_char_limit}}`）

**去向汇总**: 必留 `{{triage_report.summary.keep_title}}` · 优先 `{{triage_report.summary.prefer_title}}` · 下移亮点 `{{triage_report.summary.demote_highlights}}` · 下移五点 `{{triage_report.summary.demote_bullets}}` · 删除 `{{triage_report.summary.remove}}`

**词组分诊表**（遍历 `triage_report.phrases`，每个词组渲染一行）:

| 词组 | 类型 | 去向 | 置信 | 依据 |
|---|---|---|---|---|
| `phrase.phrase` | `phrase.type` | `phrase.action` | `phrase.confidence` | `phrase.reason` |

> ⚠️ 词组切分为启发式（按标点与介词/连词边界）；多词词组命中单一类型时置信降为 low，提示可能混入品类词，建议拆分后仅移动命中部分。本表是改进建议不是改写结果——只给去向，不改写。

---

## 附录 A：关键词分层覆盖（Keyword Layering）

> 关键词在标题/亮点/五点/backend 各层的命中与去重情况。

- **加权索引分**: `{{keyword_coverage.weighted_index_score}}`
- **跨层重复**: `{{keyword_coverage.duplicates_across_layers}}`

| 层级 | 命中 / 总数 |
|---|---|
| 标题（title） | `{{keyword_coverage.coverage_per_layer.title.hit}}` / `{{keyword_coverage.coverage_per_layer.title.total}}` |
| 亮点（highlights） | `{{keyword_coverage.coverage_per_layer.highlights.hit}}` / `{{keyword_coverage.coverage_per_layer.highlights.total}}` |
| 五点（bullets） | `{{keyword_coverage.coverage_per_layer.bullets.hit}}` / `{{keyword_coverage.coverage_per_layer.bullets.total}}` |
| 后台（backend） | `{{keyword_coverage.coverage_per_layer.backend.hit}}` / `{{keyword_coverage.coverage_per_layer.backend.total}}` |

---

## 附录 B：待办清单（Action Items）

> 按优先级排列的修复动作。`critical_issues` 为 FAIL 级硬伤，需优先处理。
> 本报告只告诉你"该改什么"，改写由你自己决定。

**严重问题（Critical）**:
{{compliance_report.critical_issues}}

**待办（Actions）**:
{{compliance_report.action_items}}

---

*本报告由 **amazon-listing-doctor**(by buluslan · 公众号「新西楼.AI」)自动生成,最终决策请结合类目实际情况与运营经验。更多 Listing / 选品 / 运营实操内容,关注公众号「**新西楼.AI**」。*
