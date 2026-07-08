---
name: amazon-listing-builder
description: 亚马逊爆款 Listing 打造助手（基于 Cosmo 语义算法 + Alexa/Rufus 对话式购物趋势）。通过"先分析、再生成、最后校验"的 AI 工程化流程，把 Listing 从"关键词堆砌"升级为"语义覆盖 + 需求证据 + 答案型内容"。提供八步工作流（关键词分层词库 → 用户问题库 → 卖点证据库 → 标题 → 五点 → 描述A+ → Search Terms → QA）、给 Codex 的可复用提示词、真实案例（抗 UV 户外仿真植物、down filled pillows QA）以及五大常见误区检查。触发场景：(1) 用户说"帮我写 Listing / 写标题 / 写五点 / 写描述 / 写 A+ / 写 QA / 写 Search Terms"(2) 用户输入 /listing-builder, /build-listing, /cosmo-listing, /alexa-qa, /listing-title, /listing-bullets, /listing-aplus, /listing-st, /listing-qa(3) 用户提及 Cosmo 算法、Alexa 算法、Rufus、对话式购物、语义搜索、答案型 Listing(4) 用户希望结合卖家精灵 MCP 数据做关键词分层与痛点映射。适用于亚马逊美国站等站点的运营、Listing 优化师、产品开发、跨境营销人员。
---

# 亚马逊爆款 Listing 打造助手（Cosmo / Alexa 新算法版）

---

## 🚨 铁律 0：数据来源优先级（必须先读）

> **MCP（卖家精灵）> 浏览器**
>
> 核心数据必须走 MCP；浏览器仅作为 MCP 没有覆盖的数据的补充来源。

### 必须使用 MCP 的场景（禁止浏览器抓 Amazon）

| 数据类型 | MCP 工具 |
|---------|---------|
| 关键词搜索量 / PPC / 趋势 | `mcp__sellersprite__keyword_miner` / `keyword_research_trends` |
| 竞品 ASIN 详情（标题/五点/价格/评分） | `mcp__sellersprite__asin_detail` |
| 竞品关键词反查 | `mcp__sellersprite__traffic_keyword` / `keyword_order` |
| **竞品评论（含差评）** | `mcp__sellersprite__review` ⚠️ **禁止抓 `amazon.com/product-reviews/`** |
| 竞品流量结构 | `mcp__sellersprite__traffic_listing` / `traffic_keyword_stat` |
| 价格 / BSR 历史 | `mcp__sellersprite__keepa_info` |
| 市场价格分布 | `mcp__sellersprite__market_price_distribution` |
| 类目节点 | `mcp__sellersprite__product_node` |

### 允许使用浏览器的场景（MCP 无对应数据）

| 数据类型 | 浏览器来源 |
|---------|----------|
| 站外买家反馈 | Reddit / TikTok / Pinterest |
| 亚马逊前台 QA 板块 | `amazon.com/ask-questions/...`（MCP 无 QA 工具） |
| 自己的广告报表 / 客服 / 退货 | 卖家后台导出 |
| 认证查询 | FDA / CPSIA / RoHS 官网 |
| 品牌官网 | 验证品牌定位 |

> 详细协议、调用顺序、参数模板见 `reference/mcp-mandatory-protocol.md`。
> MCP 调用失败的字段标 `DATA_MISSING`，**禁止用浏览器凑 Amazon 数据**。

---

## 一、为什么需要这个 Skill

旧 Listing 方法正在失效：找词 → 标题埋大词 → 五点写功能 → ST 填同义词 → 跑广告。这套逻辑只解决"被检索"，没解决"被系统理解、被买家相信、被转化"。

新语境（Cosmo 语义算法 + Alexa/Rufus 对话式购物）要求 Listing 同时回答三类问题：
- 系统问：你的产品属于什么品类、解决什么需求、适合什么场景？
- 买家问：会不会褪色？尺寸多大？能不能用在 XX 场景？包装会不会坏？
- AI 助手问：用户用自然语言问"适合全日照户外花盆的仿真花"，你的 Listing 是不是最强匹配？

本 Skill 的目标：**把关键词背后的"用户任务、使用场景、痛点问题、产品证据、购买疑虑"全部讲清楚**。

---

## 二、核心方法论：先分析、再生成、最后校验

| 阶段 | 动作 | 输出 |
|------|------|------|
| **准备阶段** | 建词库 + 问题库 + 卖点证据库 | 三份结构化数据 |
| **生成阶段** | 多版本标题/五点/描述/ST/QA | 至少 3 版可对比草稿 |
| **校验阶段** | 合规 + 关键词覆盖 + 语义覆盖 + 转化逻辑 | 4 项检查报告 |

> ⚠️ 不要让 AI 直接写。先有词库、痛点库、问题库、证据库，再写才有根。

---

## 三、八步工作流总览

| 步骤 | 名称 | 关键产出 | 详见 |
|------|------|----------|------|
| 1 | 关键词分层词库 | 5 层词表（核心/功能/场景/问题/规格） | `workflow/step-1-keyword-library.md` |
| 2 | 用户问题库 | 真实买家疑虑清单（来自评论/QA/Reddit/TikTok） | `workflow/step-2-question-library.md` |
| 3 | 卖点证据库 | 每个卖点对应材料/数据/图片证据 | `workflow/step-3-evidence-library.md` |
| 4 | 标题结构设计 | 品牌+核心词+差异属性+主场景+规格 | `workflow/step-4-title-design.md` |
| 5 | 五点描述 | 5 点对应 5 个决策环节（不堆词） | `workflow/step-5-bullet-points.md` |
| 6 | 描述 + A+ 内容 | 痛点 → 场景 → 方案 → 细节 → 对比 → 注意 | `workflow/step-6-description-aplus.md` |
| 7 | Search Terms | 只放补充索引词，不重复、不堆砌 | `workflow/step-7-search-terms.md` |
| 8 | QA 设计 | 答案型内容，对应自然语言搜索 | `workflow/step-8-qa-design.md` |

---

## 四、给 Codex / Claude 的主提示词（直接复用）

详见 `prompts/master-prompt.md`。精简版：

> 你是一名亚马逊美国站资深 Listing 策略顾问，熟悉 Cosmo 语义搜索、Alexa/Rufus 对话式购物、关键词索引、转化文案和合规表达。
>
> 接下来我会提供：产品信息、竞品 Listing、关键词数据、广告搜索词、评论痛点、QA 问题、供应链卖点和合规限制。
>
> **请你先不要直接写 Listing**，而是先完成以下分析：
> 1. 关键词分层词库（核心 / 功能 / 场景 / 属性 / 问题 / 同义词 / 后台补充）
> 2. 每个词标注：搜索意图、建议位置、是否必须前台、是否进 ST
> 3. 评论痛点 + 用户问题 → 输出"痛点-解决方案-证据-关键词-图片模块"映射表
> 4. 基于 Cosmo + 对话式购物逻辑，列出必须覆盖的用户任务和自然语言问题
> 5. 生成 3 版标题（关键词覆盖版 / 转化表达版 / 简洁合规版）+ 优缺点对比
> 6. 五点描述：每点对应一个用户疑虑 + 一个核心卖点，禁用空泛词
> 7. 产品描述 + A+ 模块结构（使用场景 → 产品结构 → 痛点解决 → 信任证明）
> 8. Search Terms 建议（只放前台未覆盖但有索引价值的词）
> 9. 10 个 QA：问题来自真实疑虑，答案稳健不夸大
> 10. 最后做：合规检查 + 关键词覆盖检查 + 语义覆盖检查 + 转化逻辑检查

---

## 五、子命令

| 命令 | 用途 |
|------|------|
| `/listing-builder` | 完整八步流程，端到端生成全套 Listing |
| `/listing-title` | 仅生成多版本标题（含优缺点对比） |
| `/listing-bullets` | 仅生成五点描述（按决策链） |
| `/listing-aplus` | 仅生成描述 + A+ 模块结构 |
| `/listing-st` | 仅生成 Search Terms（补充索引策略） |
| `/alexa-qa` | 仅生成对话式 QA（针对 Alexa/Rufus） |
| `/listing-audit` | 对现有 Listing 做合规 + 语义 + 转化四项校验 |

---

## 六、与卖家精灵 MCP 集成（必须使用，本项目已配置）

本项目 `.mcp.json` 已配置 sellersprite MCP，**核心数据必须走 MCP**，详见顶部"铁律 0"和 `reference/mcp-mandatory-protocol.md`。

### 八步工作流的 MCP 调用清单

| 步骤 | 必须调用的 MCP 工具 | 浏览器补充 |
|------|------------------|----------|
| 1 关键词分层 | `keyword_miner` + `keyword_research_trends` + `traffic_keyword` + `keyword_order` | 无 |
| 2 用户问题库 | `review`（差评主题）+ `asin_detail`（竞品结构） | Reddit / TikTok / 竞品 QA 板块 |
| 3 卖点证据库 | `review`（好评证据） | 品牌官网 + 认证官网 |
| 4 标题 | 不调（基于 1-3 步数据） | 无 |
| 5 五点 | 不调 | 无 |
| 6 描述+A+ | 不调 | 品牌官网（参考定位） |
| 7 Search Terms | 不调（基于第 1 步 + 第 4 步做差集） | 无 |
| 8 QA | 不调 | 竞品 QA 板块（补充问题） |

### 浏览器使用红线

| 场景 | ❌ 错误做法 | ✅ 正确做法 |
|------|-----------|-----------|
| 抓竞品评论 | `webReader(amazon.com/product-reviews/...)` | `mcp__sellersprite__review` |
| 抓竞品标题 | `webReader(amazon.com/dp/...)` | `mcp__sellersprite__asin_detail` |
| 拿关键词 | `webReader(Amazon 搜索建议)` | `mcp__sellersprite__keyword_miner` |
| 看 Reddit | ✅ `webReader(reddit.com/r/...)` | MCP 无此数据 |
| 看竞品 QA | ✅ `webReader(amazon.com/ask-questions/...)` | MCP 无 QA 工具 |
| 验证 FDA | ✅ `webReader(fda.gov)` | MCP 无认证查询 |

> 完整调用顺序、参数模板见 `reference/mcp-mandatory-protocol.md`。MCP 数据缺失时，必须列出需要人工补充的数据字段，**禁止用浏览器凑 Amazon 数据**。

---

## 七、五大常见误区（必须主动检查）

1. **把 Cosmo / Alexa 讲成玄学** — 没有隐藏规则，最终都是"更相关、更清楚、更可信、更能转化"
2. **认为关键词不重要** — 关键词仍是地基，区别在于要分层
3. **只优化标题** — Listing 是整体，标题/主图/五点/描述/ST/QA/评论/A+ 必须协同
4. **直接让 AI 写一版就上线** — 没有词库和证据库，AI 只会写漂亮废话
5. **用一个 Listing 承接所有人群** — 主图主场景，其他场景放五点/A+/QA 承接

详见 `reference/common-mistakes.md`。

---

## 八、真实案例参考

| 案例 | 详见 |
|------|------|
| 抗 UV 户外仿真植物（端到端 7 步） | `examples/uv-outdoor-plants-fullcase.md` |
| down filled pillows QA（Alexa 风格示例） | `examples/down-pillows-qa-example.md` |
| 关键词分层词库填写模板 | `examples/layered-keyword-template.md` |

---

## 九、输出格式规范

| 文件 | 命名规则 | 必存 |
|------|----------|:----:|
| 完整 Listing 包 | `{产品名}/listing_package.md` | ✅ |
| 关键词分层词库 | `{产品名}/keyword_library.md` | ✅ |
| 痛点-证据映射表 | `{产品名}/painpoint_evidence_map.md` | ✅ |
| 多版本草稿对比 | `{产品名}/drafts_comparison.md` | ✅ |
| 合规与语义校验报告 | `{产品名}/audit_report.md` | ✅ |
| 原始输入数据 | `{产品名}/input_data.json` | ✅ |

**所有报告必须保存为文件**，禁止只打印到控制台。详见 `reference/output-format-spec.md`。

---

## 十、执行流程

收到"帮我做 Listing"类请求时：

1. **澄清输入** — 产品信息（标题/类目/规格）、是否提供竞品 ASIN、是否启用卖家精灵 MCP、目标站点
2. **跑八步工作流** — 按步骤执行，每步保存产出
3. **生成草稿** — 至少 3 版标题 + 1 套五点 + 描述/A+/ST/QA
4. **跑校验** — 合规 + 关键词覆盖 + 语义覆盖 + 转化逻辑
5. **打包交付** — `listing_package.md` 汇总，附 HTML 可视化版本（可选）

---

## 十一、关键原则（每次都要回顾）

- **标题不是堆词**，是让系统和买家快速定位
- **五点不是卖点罗列**，是购买决策链
- **描述和 A+ 不是重复信息**，是场景和信任构建
- **ST 不是垃圾桶**，是补充索引池
- **QA 不是可有可无**，是对话式搜索和转化疑虑的补丁
- **先分析、再生成、最后校验** — 永远不要让 AI 直接写
