# Amazon Listing Builder Skill

> **AI 驱动的亚马逊爆款 Listing 打造助手** — 基于 Cosmo 语义算法 + Alexa/Rufus 对话式购物趋势，通过"先分析、再生成、最后校验"的工程化流程，把 Listing 从"关键词堆砌"升级为"语义覆盖 + 需求证据 + 答案型内容"。

---

## 一、Overview（这个 Skill 是干什么的）

传统 Listing 方法（找词 → 标题埋大词 → 五点写功能 → ST 填同义词 → 跑广告）正在失效。

**新语境要求 Listing 同时回答三类问题**：

| 系统问 | 买家问 | AI 购物助手问 |
|-------|-------|--------------|
| 你的产品属于什么品类？解决什么需求？适合什么场景？ | 会不会褪色？尺寸多大？能不能用在 XX 场景？包装会不会坏？ | "适合全日照户外花盆的仿真花有哪些？" |

本 Skill 把这些要求落地为可执行的**八步工作流**，配套 7 个给 AI 的提示词模板、3 个真实案例和 4 份背景参考知识。

> **核心方法论**：先分析（词库 + 痛点库 + 证据库）→ 再生成（多版本对比）→ 最后校验（合规 + 语义 + 转化）。

---

## 二、Features（核心特性）

- **关键词分层词库** — 把关键词按 5 层（核心/功能/场景/问题/规格）组织，决定每个词放哪里
- **用户问题库** — 从评论、QA、客服、Reddit/TikTok 提取真实买家疑虑
- **卖点证据库** — 每个卖点必须有材料/工艺/数据证据，杜绝"漂亮废话"
- **3 版标题对比** — 关键词覆盖版 / 转化表达版 / 简洁合规版，列出优缺点再由人决策
- **五点决策链** — 每点对应一个用户决策环节（核心价值 → 痛点 → 场景 → 规格 → 信任）
- **A+ 7 屏模块结构** — 每屏对应一个语义关系，承接 Cosmo 算法
- **Search Terms 策略** — 只放补充索引词，不重复、不堆砌、不超字节
- **Alexa 风格 QA** — 答案型内容，承接对话式购物搜索
- **四项校验** — 合规 + 关键词覆盖 + 语义覆盖 + 转化逻辑
- **数据迭代** — 上线后用广告/转化/差评数据持续优化

---

## 三、Prerequisites（前置条件）

- [Claude Code](https://claude.ai/code) CLI
- **卖家精灵 MCP 密钥（必须）** — 本 Skill 核心数据全部依赖 MCP，禁止用浏览器抓 Amazon 凑数据
- 项目根目录的 `.mcp.json` 已正确配置（本项目已配好）

---

## 🚨 铁律：数据来源优先级

> **MCP（卖家精灵）> 浏览器**
>
> 核心数据必须走 MCP；浏览器仅作为 MCP 没有覆盖的数据的必要补充。

### 必须使用 MCP 的数据（禁止浏览器抓 Amazon）

| 数据 | MCP 工具 |
|------|---------|
| 关键词搜索量 / PPC / 趋势 | `mcp__sellersprite__keyword_miner` / `keyword_research_trends` |
| 竞品 ASIN 详情（标题/五点/价格） | `mcp__sellersprite__asin_detail` |
| 竞品关键词反查 | `mcp__sellersprite__traffic_keyword` / `keyword_order` |
| **竞品评论（含差评）** | `mcp__sellersprite__review` ⚠️ **严禁**抓 `amazon.com/product-reviews/` |
| 价格 / BSR 历史 | `mcp__sellersprite__keepa_info` |
| 市场价格分布 | `mcp__sellersprite__market_price_distribution` |
| 流量结构 | `mcp__sellersprite__traffic_listing` / `traffic_keyword_stat` |

### 允许使用浏览器的场景（MCP 无对应数据）

| 数据 | 浏览器来源 |
|------|----------|
| 站外买家反馈 | Reddit / TikTok / Pinterest |
| 亚马逊前台 QA 板块 | `amazon.com/ask-questions/...` |
| 自己的广告报表 | 卖家后台（Reports → Advertising） |
| 自己的客服记录 | 卖家后台 |
| 认证查询 | FDA / CPSIA / RoHS 官网 |
| 品牌官网 | 验证品牌定位 |

详见 `reference/mcp-mandatory-protocol.md`。

---

## 四、Quick Start（快速开始）

### 场景 A：完整打造一个新 Listing

直接对话告诉 Claude：

> "我要为抗 UV 户外仿真植物打造 Listing，价格 $24.99-$29.99，主打 patio/porch/花盆场景，请用 amazon-listing-builder skill 跑完整八步流程。"

或使用子命令：

```
/listing-builder
```

Claude 会按八步工作流顺序执行：词库 → 问题库 → 证据库 → 标题 → 五点 → 描述A+ → ST → QA → 校验，最终输出完整 Listing 包到 `{产品名}/` 目录。

### 场景 B：只优化某一模块

```
/listing-title   → 只生成 3 版标题对比
/listing-bullets → 只生成五点描述
/listing-aplus   → 只生成描述 + A+ 模块结构
/listing-st      → 只生成 Search Terms
/alexa-qa        → 只生成 Alexa 风格 QA
```

### 场景 C：审核已有 Listing

```
/listing-audit
```

对现有 Listing 跑四项校验（合规 + 关键词覆盖 + 语义覆盖 + 转化逻辑），输出问题清单和整改优先级。

### 场景 D：基于关键词列表写 QA（参考需求文档示例）

> "我是亚马逊美国站卖家，产品 down filled pillows，特性 24x24/bulk/fluffy，核心卖点 24x24，关键词：down filled pillows / feather down pillow / down feather pillow / goose down pillows。请模拟 Alexa 算法下的 QA 问答。"

Claude 会调用 `examples/down-pillows-qa-example.md` 的模板风格生成。

---

## 五、Command Reference（子命令清单）

| 命令 | 用途 | 主要产出文件 |
|------|------|------------|
| `/listing-builder` | 完整八步流程端到端生成 | `listing_package.md` + 全部中间产出 |
| `/listing-title` | 多版本标题对比 | `drafts_comparison.md` |
| `/listing-bullets` | 五点描述（按决策链） | `drafts_comparison.md` |
| `/listing-aplus` | 描述 + A+ 模块结构 | `drafts_comparison.md` |
| `/listing-st` | Search Terms 补充索引策略 | `listing_package.md` |
| `/alexa-qa` | 对话式 QA（Alexa/Rufus 风格） | `listing_package.md` |
| `/listing-audit` | 对现有 Listing 做四项校验 | `audit_report.md` |

---

## 六、八步工作流总览

| 步骤 | 名称 | 关键产出 | 详见 |
|------|------|----------|------|
| 1 | 关键词分层词库 | 5 层词表（核心/功能/场景/问题/规格） | `workflow/step-1-keyword-library.md` |
| 2 | 用户问题库 | 真实买家疑虑清单 | `workflow/step-2-question-library.md` |
| 3 | 卖点证据库 | 每个卖点对应材料/数据/图片证据 | `workflow/step-3-evidence-library.md` |
| 4 | 标题结构设计 | 品牌+核心词+差异属性+主场景+规格 | `workflow/step-4-title-design.md` |
| 5 | 五点描述 | 5 点对应 5 个决策环节 | `workflow/step-5-bullet-points.md` |
| 6 | 描述 + A+ 内容 | 痛点 → 场景 → 方案 → 细节 → 对比 → 注意 | `workflow/step-6-description-aplus.md` |
| 7 | Search Terms | 只放补充索引词，不堆砌 | `workflow/step-7-search-terms.md` |
| 8 | QA 设计 | 答案型内容，对应自然语言搜索 | `workflow/step-8-qa-design.md` |

---

## 七、Directory Structure（目录结构）

```
.claude/skills/amazon-listing-builder/
├── skill.md                          # 主入口（必读）
├── README.md                         # 本文件
├── workflow/                         # 八步工作流分册
│   ├── step-1-keyword-library.md
│   ├── step-2-question-library.md
│   ├── step-3-evidence-library.md
│   ├── step-4-title-design.md
│   ├── step-5-bullet-points.md
│   ├── step-6-description-aplus.md
│   ├── step-7-search-terms.md
│   └── step-8-qa-design.md
├── prompts/                          # 给 AI 的提示词模板
│   ├── master-prompt.md              # 主提示词（可直接复制使用）
│   ├── layered-keyword-prompt.md     # 关键词分层
│   ├── painpoint-mapping-prompt.md   # 痛点-证据映射
│   ├── multiversion-prompt.md        # 多版本生成
│   ├── compliance-check-prompt.md    # 合规检查
│   ├── semantic-coverage-prompt.md   # 语义覆盖检查
│   └── data-iteration-prompt.md      # 上线后数据迭代
├── examples/                         # 真实案例
│   ├── uv-outdoor-plants-fullcase.md      # 抗 UV 户外仿真植物端到端
│   ├── down-pillows-qa-example.md         # down filled pillows QA 示例
│   └── layered-keyword-template.md        # 关键词分层填写模板
└── reference/                        # 背景知识
    ├── cosmo-alexa-algorithm.md           # COSMO + Alexa 算法理解
    ├── common-mistakes.md                 # 五大常见误区
    ├── sellersprite-mcp-integration.md    # 卖家精灵 MCP 集成
    └── output-format-spec.md              # 输出格式规范
```

---

## 八、给 Codex / Claude 的提示词清单

每个提示词文件可直接复制粘贴使用：

| 提示词文件 | 用途 |
|----------|------|
| `prompts/master-prompt.md` | 完整端到端生成全套 Listing |
| `prompts/layered-keyword-prompt.md` | 只跑第一步：把关键词分层 |
| `prompts/painpoint-mapping-prompt.md` | 只跑第三步：建立痛点-证据映射 |
| `prompts/multiversion-prompt.md` | 生成 3 版标题 / 2 版五点对比 |
| `prompts/compliance-check-prompt.md` | 跑合规检查（绝对化、医疗、环保、安全等） |
| `prompts/semantic-coverage-prompt.md` | 跑语义覆盖检查（含 Alexa 模拟） |
| `prompts/data-iteration-prompt.md` | 上线后用真实数据迭代优化 |

---

## 九、Real Examples（真实案例参考）

### 案例 1：抗 UV 户外仿真植物（端到端 9 步完整演示）
**文件**：`examples/uv-outdoor-plants-fullcase.md`

包含完整的词库拆解、痛点证据映射、3 版标题对比、五点描述、7 段式描述、A+ 7 屏结构、ST 优化、10 题 QA、上线后数据迭代示例。

### 案例 2：down filled pillows QA（Alexa 风格示例）
**文件**：`examples/down-pillows-qa-example.md`

基于需求文档中"down filled pillows"产品（24x24/bulk/fluffy），生成 10 题 Alexa 风格 QA，覆盖 4 个维度（场景/功能/人群/使用），自然埋入 4 个核心关键词。

### 案例 3：关键词分层填写模板
**文件**：`examples/layered-keyword-template.md`

空白模板，可直接复制用于任何产品的关键词分层。

---

## 十、与 SellerSprite MCP 集成

本 Skill 与同项目的 `sellersprite-amazon-research` skill 形成互补：

| Skill | 用途 |
|-------|------|
| **sellersprite-amazon-research** | 选品 / 市场分析 / 竞品调研 / 评论洞察（提供数据） |
| **amazon-listing-builder**（本 skill） | Listing 文案生成 / 优化 / 校验（消费数据） |

### 数据流

```
sellersprite-amazon-research（提供数据）
    ↓
keyword_miner / traffic_keyword / asin_detail / review 等
    ↓
amazon-listing-builder（消费数据）
    ↓
词库 → 问题库 → 证据库 → 标题/五点/A+/ST/QA → 校验
```

### 常用 MCP 工具映射

| 本 Skill 步骤 | 调用的卖家精灵工具 |
|------------|-----------------|
| 第 1 步：关键词分层 | `keyword_miner` / `keyword_research_trends` / `traffic_keyword` / `keyword_order` |
| 第 2 步：用户问题库 | `review`（差评主题）/ `asin_detail`（竞品结构） |
| 第 3 步：卖点证据库 | 主要靠人工（供应链/测试/认证） |
| 第 4-8 步 | 基于前三步数据，不再直接调 MCP |
| 上线后迭代 | `traffic_listing` / `keyword_order` / `market_price_distribution` |

> 详细调用方式、字段映射和已知陷阱见 `reference/sellersprite-mcp-integration.md`。

---

## 十一、Output Files（输出文件结构）

每次完整跑完八步工作流，会在当前目录生成：

```
{产品名}/
├── listing_package.md           # 完整 Listing 包（汇总交付）
├── keyword_library.md           # 关键词分层词库（第一步）
├── question_library.md          # 用户问题库（第二步）
├── evidence_library.md          # 卖点证据库（第三步）
├── drafts_comparison.md         # 多版本草稿对比（第四五六步）
├── audit_report.md              # 合规 + 语义 + 转化校验报告
├── input_data.json              # 原始输入数据
└── listing_package.html         # HTML 可视化版本（可选，推荐生成）
```

> 详细规范见 `reference/output-format-spec.md`。

---

## 十二、Common Mistakes（五大常见误区）

1. **把 Cosmo / Alexa 讲成玄学** — 没有隐藏规则，最终都是"更相关、更清楚、更可信、更能转化"
2. **认为关键词不重要** — 关键词仍是地基，区别在于要分层
3. **只优化标题** — Listing 是整体，标题/主图/五点/描述/ST/QA/评论/A+ 必须协同
4. **直接让 AI 写一版就上线** — 没有词库和证据库，AI 只会写漂亮废话
5. **用一个 Listing 承接所有人群** — 主图主场景，其他场景放五点/A+/QA 承接

详见 `reference/common-mistakes.md`。

---

## 十三、Compliance Red Lines（合规红线词清单）

| 红线词 | 安全替代 |
|--------|---------|
| 100% / never / always | help / support / designed to |
| lifetime / forever | long-term use |
| best / #1 / top rated | popular / favored |
| cheap / lowest price | affordable / value |
| cures / treats / heals | supports / may help |
| 100% eco-friendly | made with recyclable materials |
| FDA approved（无认证） | meets [actual standard] |
| organic（无认证） | natural materials |
| guaranteed | designed for / backed by [policy] |
| fireproof（无测试） | fire-resistant（如有测试） |

完整检查项见 `prompts/compliance-check-prompt.md`。

---

## 十四、Known Limitations（已知限制）

- **卖家精灵 review 采样限制** — 每次最多返回 20 条评论，是样本数据，评分分布不代表总体
- **`keyword_research` 忽略 keyword 参数** — 该工具会返回全球热词，使用 `keyword_miner` 替代
- **`traffic_source` 数据不可靠** — 可能返回无关产品的流量，建议用 `traffic_keyword` + `traffic_keyword_stat` 组合替代
- **`keyword_research_trends` 字段名差异** — 实际字段是 `time` / `search` / `chainGrowth` / `yearlyGrowth`，不是文档描述的 `month` / `searches` / `growth`
- **COSMO / Alexa 算法非官方评分规则** — 不要把它神化，本 Skill 把它理解为"语义搜索 + 对话式购物趋势"即可
- **AI 生成内容必须人工审核** — AI 容易写过头（夸大承诺、绝对化表达），合规风险需人工把关

---

## 十五、Recommended Workflow（推荐组合链路）

### 链路 A：从零打造爆款 Listing

```
1. 调用 sellersprite-amazon-research 做选品
   ↓ 输出：目标 ASIN + 竞品列表 + 市场数据
2. 调用 amazon-listing-builder /listing-builder
   ↓ 输入：竞品 ASIN + 产品规格 + 卖点
   ↓ 输出：完整 Listing 包
3. 上线后 2-4 周调用 /listing-audit + data-iteration-prompt
   ↓ 输出：迭代优化建议
4. 每月迭代一次
```

### 链路 B：优化现有 Listing

```
1. /listing-audit（先做诊断）
   ↓ 输出：合规 + 语义 + 转化四项报告
2. 根据报告选择子命令
   - 标题问题 → /listing-title
   - 五点问题 → /listing-bullets
   - QA 不足 → /alexa-qa
3. 上线新版后跟踪 2-4 周
```

### 链路 C：只补 QA（最小成本上线）

```
1. /alexa-qa
   ↓ 输入：产品规格 + 必须埋入的关键词
   ↓ 输出：10 题 Alexa 风格 QA
```

---

## 十六、FAQ（常见问题）

### Q1：必须用卖家精灵 MCP 才能用这个 Skill 吗？
**A**：不必须。Skill 可以基于用户提供的产品信息和关键词列表工作。但有 MCP 数据更精准，能避免编造。

### Q2：生成的 Listing 可以直接上线吗？
**A**：**不能**。必须人工审核：
- 合规风险（绝对化、医疗、环保承诺）
- 证据真实性（材料/工艺/认证是否真的有）
- 关键词相关性（是否真的匹配产品）
- 字段长度（标题/五点/描述字符数）

### Q3：3 版标题应该选哪个？
**A**：看场景：
- 广告冷启动 / 强竞价品类 → 关键词覆盖版
- 移动端流量为主 / 自然排名沉淀 → 转化表达版
- 高合规风险品类 / 新账号 → 简洁合规版

### Q4：Skill 支持哪些站点？
**A**：方法论支持所有站点。字符限制差异：
- 美国站：标题 200 字符、ST 250 字节
- 欧洲站：同美国
- 日本站：标题 100 字节、ST 100 字节

### Q5：上线后多久迭代一次？
**A**：
- 上线第 1 周：每天看 CTR
- 上线 2-4 周：每周一次词效分析
- 上线 1-3 个月：每月一次全面优化
- 上线 3 个月后：季度精修

### Q6：能不能跳过八步直接写 Listing？
**A**：技术上可以，但**不推荐**。没有词库和证据库，AI 写出来的就是漂亮废话（premium / perfect / easy to use / great gift）。八步的"先分析"阶段就是为了避免这个问题。

---

## 十七、Core Philosophy（核心理念）

> **Listing 不是文案工作，而是流量效率工程。**

- 标题不是堆词，是让系统和买家快速定位
- 五点不是卖点罗列，是购买决策链
- 描述和 A+ 不是重复信息，是场景和信任构建
- ST 不是垃圾桶，是补充索引池
- QA 不是可有可无，是对话式搜索和转化疑虑的补丁

**一句话总结**：

> 把关键词背后的"用户任务、使用场景、痛点问题、产品证据、购买疑虑"全部讲清楚，让系统能理解，让买家能相信，让数据能持续正反馈。

---

## License

MIT

特别致谢灵感来源： https://mp.weixin.qq.com/s/6AUEMvyjPb1C_cqpEERklQ?click_id=1881462166