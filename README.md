# Amazon 技能库（模块化）

一套跑在 Claude / Claude Code 上的亚马逊运营技能库。**分两层**：

- **上游技能层** `SKILLS/skills/` —— 9 个现成 skill（竞品分析、品类选品、评论分析、Listing 打造、卖家精灵全链路等），原作者 [liangdabiao](https://github.com/liangdabiao/Amazon-Skills-Liang)，本仓库原样保留。
- **本项目改造层** `SKILLS/modules/` + `SKILLS/scripts/` —— 按真实运营流程重写的模块化流程层，共享一套配置与脚本。

上游那 9 个 skill 是"单点能用"，改造层解决的是"一条链路能跑通"：输入契约 → 关键词 → 竞品 → 洞察 → 卖点 → 文案 → 主图，每一步落成文件，下一步读文件。

## 目录

```
SKILLS/
├── skills/                 上游 9 个 skill（原样保留，只读参考）
│   ├── amazon-analyse/             竞品 Listing 穿透分析
│   ├── category-selection/         品类选品
│   ├── keyword-research/           关键词调研（上游版）
│   ├── review-analysis/            评论痛点分析
│   ├── product-research/           选品深度调研
│   ├── sellersprite-amazon-research/  卖家精灵 43 工具全链路
│   ├── sif-amazon-research/        Sif 市场验证
│   ├── xiyou-insight/              西柚流量与广告
│   └── amazon-listing-builder/     Listing 八步工作流
│
├── amz-review-analysis/    类目级评论分析流水线（第三方 skill，见「致谢」许可说明）
│
├── vendor/                 第三方 skill 原样留存（只读参考，各自 LICENSE 生效）→ 仓库侧映射到 SKILLS/skills/
│   ├── amazon-listing-doctor/  Listing 体检评分：CDQ / A9 / COSMO / Alexa / 合规（MIT）
│   ├── amazon-listing-builder/ Listing 八步工作流
│   └── ...                 每个目录带 SOURCE.md 或 README，写明来源与版本
│
├── modules/                本项目改造层：按运营流程拆的模块
│   ├── 00-input/           输入契约：竞品 ASIN 组、本品事实卡、后台数据回流
│   ├── 10-keyword/         ✅ 关键词调研 v3.7（唯一做满的模块）
│   ├── 20-competitor/      竞品分析（骨架）
│   ├── 30-insight/         用户洞察（骨架）
│   ├── 40-selling-point/   卖点提炼 ✅ v1
│   ├── 50-copy/            文案生成 ✅ v2（含第三方体检评分）
│   ├── 90-main-image/      主图设计需求（骨架）
│   └── _common/            输出规范、口径声明、政策边界
│
└── scripts/                全库共用的脚本层（唯一真相源）
    ├── config.yaml         权重、阈值、名额、判断词表、路径——全部外置
    ├── merge.py            合并 → 打分 → 分层 → 优先级 → 四象限
    ├── check.py            交付前 7 项自检，不过就不许交
    ├── sp_config.yaml      卖点定义、角色矩阵、分级名额、图片开关
    ├── build_selling_points.py  五点 × 评论 × 词库 → 卖点库
    ├── check_sp.py         卖点库 7 项自检，退出码非 0 不许交
    ├── copy_config.yaml    文案字段边界、词表、判定阈值、体检工具配置
    ├── check_copy.py       文案 15 项自检（C0-C12），写 08 / CP-03 / CP-04
    ├── score_copy.py       文案体检评分，调 vendor/amazon-listing-doctor，写 CP-07
    └── build_copy.py       正文 → CP-02 / 粘贴稿 / CP-05 / CP-06 / 文案.xlsx / _summary.json
```

## 快速开始

```bash
pip install pyyaml

# 在一个已按 10-keyword 的输入契约准备好数据的项目目录里：
python SKILLS/scripts/merge.py  <项目目录>
python SKILLS/scripts/check.py  <项目目录>     # 退出码 0 才算交付

# 50-copy 出稿：check → score → build，三步顺序不能换
python SKILLS/scripts/check_copy.py --category sponge-holder   # 写 08 自检 / 覆盖清单 / 问题清单
python SKILLS/scripts/score_copy.py --category sponge-holder   # 调 vendor 体检，写 CP-07 评分
python SKILLS/scripts/build_copy.py --category sponge-holder --sku <SKU>   # 出 xlsx / 粘贴稿 / 汇总
```

第三方体检工具零依赖、无需 API Key，随仓库一起走（`SKILLS/vendor/amazon-listing-doctor/`），不联网、不额外安装。若该目录被删掉，`score_copy.py` 会在 `04_评分` 表写「未执行」并继续，不影响其余产物。

`merge.py` 只读文件、不认代码里的常量；`check.py` 检查的是"这轮有没有偷工"（字段是否齐、五路是否都有贡献、EST 占比、否定清单有没有过泛词、P0 名额、品牌词有没有混进标题层、取值是否合法）。**换类目只改 `config.yaml`，不改代码。**

## 10-keyword 做了什么

五路采集，每一路各出一份文件，最后由 `merge.py` 消费：

| 路 | 方法 | 产出 | 强项 |
|---|---|---|---|
| A | 竞品 ASIN 反查流量词 | `0A-竞品流量词.csv` | 有真实曝光信号 |
| B | 竞品标题词频 | `02-标题高频词.csv` + `02b-竞品标题原文.csv` | 反映竞品的词取舍 |
| C | 竞品五点词频 | `03-Listing高频词.csv` + `03b-三类词抽取.csv` | 抓得到买家语言、痛点、限制 |
| D | 前台自动补全 | `04-自动补全词表.csv` | 即时搜索行为、长尾 |
| E | 后台报表（用户上传） | `05-后台数据对标.csv` | 唯一带真实转化率 |

几个不显然但很关键的设计：

- **分层和相关性彻底解耦**。层级只看搜索量宽度（四档，默认以本类目最大词为 100% 切片）；优先级只看 W 排名，名额制（P0 默认 3 个，可配）。早期把 R 塞进层级判定，相关性算法一调整，"大词"整档就消失了。
- **R3 用精确覆盖率**。拿候选词逐条比对 30 条竞品标题原文（拆实词、去标点、复数折单数），而不是读预计算的 n-gram 表。后者只存 3 词以内，实测 235 个词里 210 个（89%）根本取不到值，一直在用中性分 0.5 凑数。
- **方法 C 只做证据，不做发现**。五点里大量词组不是搜索词（285 条里只有 23 条是），全放进来会把词库灌满没有搜索量的词。它默认只给已发现的词补一条"竞品确实这么写"的证据，真正的产出是三类词（痛点 / 证据 / 限制）给五点用。
- **否定清单有白名单**。`kitchen sink`、`suction cup` 这类比本品宽得多的词，R1=0 但不该否定——否掉等于关掉半个类目入口，只标观察。

## 40-selling-point 做了什么

三源交叉：竞品五点是「供给」，评论痛点是「需求」，关键词是「搜索」。主键复用 `30-insight` 的 19 个一级类目，三源才能对齐；各建一套分类就只剩三张互不相干的表。

- **两个分数分工**：`G = P × (1 − 覆盖率)` 定级，`M = S×0.45 + P×0.35 + D×0.20` 只做五点排序。拿 M 定级会误杀"痛点重但没人搜"的卖点——一个类目里大半卖点没有专属搜索词。
- **角色六分类**：入场券 / 主攻空白 / 常见卖点 / 已验证卖点 / 品类标配 / 待验证。核心判断是"低覆盖不等于机会"：评论侧没痛点，没人写就只是废话；评论侧有痛点但没人写，才是真空隙。
- **冲突单独成表**：品类级反噬（全员写全员骂）、声称与体验背离（承诺了没做到）、痛点未解决（差评集中但少数人写——这是机会）。
- **图片维度是明确缺口**：沙箱无外网、Amazon 页面反爬、`asin_detail` 只给一张主图 URL 且不可读。只能走用户截图图包，缺省标 `DATA_MISSING`，同时输出"应承载图位"清单等图包回填。

## 模块状态

| 模块 | 状态 |
|---|---|
| `00-input` | ✅ 输入契约已定 |
| `10-keyword` | ✅ v3.7，可运行，7 项自检全过 |
| `_common` | ✅ 输出规范与口径声明 |
| `20-competitor` | ⬜ 骨架 |
| `30-insight` | ⬜ 骨架（评论分析可复用 `amz-review-analysis`） |
| `40-selling-point` | ✅ v1，可运行（`scripts/build_selling_points.py` + `check_sp.py`，7 项自检全过；图片维度待图包） |
| `50-copy` | ✅ v2，可运行（`check_copy.py` 15 项 + `score_copy.py` 第三方体检 + `build_copy.py` 出 xlsx；sponge-holder 已出成稿，两套检查全过） |
| `90-main-image` | ⬜ 骨架 |

## 四条贯穿全库的规矩

1. **输出必须标数据源和口径**：每条结论都能追溯到哪个接口、哪个月份、什么样本。
2. **多口径数据交叉校验，不能相加**：卖家精灵、ABA、商机探测器对同一个词的口径差 3-5 倍，一份报告只用一个口径，另一个只验证方向。
3. **模块之间靠文件交接**：上一步落成文件，下一步读文件，任何一步都能单独重跑。
4. **判断词表和阈值一律进 `config.yaml`**：代码里出现硬编码的词或数字就算缺陷。这条是被事故逼出来的——早期四份打分脚本并存，词表写成常量，结果五路各自出了 CSV，词库却只吃掉三五个词。

## 致谢：参考过的项目与 skill

这个仓库不是从零写的，改造层大量参考了下面这些项目。原样保留的（`SKILLS/skills/`）版权归原作者，改造层的判断规则是重新写的。

| 项目 / skill | 作者 | 在本项目里的角色 |
|---|---|---|
| [Amazon-Skills-Liang](https://github.com/liangdabiao/Amazon-Skills-Liang) | liangdabiao | 上游 9 个 skill 的原作者，`SKILLS/skills/` 下内容来自这里 |
| [amz-review-analysis-skill](https://github.com/CoderAndyLee/amz-review-analysis-skill) | Andy（CoderAndyLee / Andy聊跨境） | 类目级评论分析流水线：合并卖家精灵 review、逐层长出分类列、输出 HTML 看板。**自定义许可（源码可见、自用免费），不是 MIT/Apache，转载或商用前请看它的 LICENSE** |
| **amazon-keyword-strategy v0.4.0** | — | 关键词模块 v3.7 借鉴了四条：绝对锚分层、竞争度四维打分与四象限打法、词根六分类、品牌双分类 |
| [zach-feature-demand-validator](https://github.com/zach22-1999/amazon-skills) | Zach | 卖点库的"三维交叉验证真伪"思路来源：低覆盖不等于机会，要看评论侧有没有需求 |
| **卖家精灵 MCP**（SellerSprite） | SellerSprite | 全部市场侧数据来源：`keyword_miner` 搜索量与竞争指标、`asin_detail` 详情与五点（`features` 字段）、`traffic_keyword` 流量词、`product_research` 扩池 |
| **amazon-listing-builder** | liangdabiao | `50-copy` 的词位规则（5 层词库）、字段边界、红线词表来源。**注意：`reference/ranking-rules.md` 不在上游仓库，是本项目 11-13 写进去的草稿，已作废** |
| **xiyou-insight / sif-amazon-research** | liangdabiao | 流量诊断与市场验证，作为后续模块的参考 |
| [amazon-listing-doctor](https://github.com/buluslan/amazon-listing-doctor) | Buluu@新西楼（公众号：新西楼.AI） | `50-copy` 的**第三方体检评分**（`04_评分` 表 / `CP-07`）：CDQ 六维质量分、A9 收录、COSMO 意图覆盖、Alexa 可发现性、2026 新规合规、标题词组分诊。**MIT 许可，原样存放于 `SKILLS/vendor/amazon-listing-doctor/`，未改一行代码**；来源、版本、提交号与口径差异见该目录 `SOURCE.md` |

被借鉴的部分都改过：不是照抄，是拿真实类目跑完之后，把"和数据对不上"的规则换掉。比如上游的竞争分用等权平均，实测会被三项低值拉平、掩盖"商品数四万九"这种硬壁垒，于是补了单项极端值覆盖；上游的层级用固定绝对锚，小类目会被压成全是长尾，于是改成头部比例锚。

## 数据与口径限制

- 卖家精灵 MCP 只提供市场侧数据，**没有**店铺后台（广告报告、业务报告、退货报告）。这部分必须由用户在卖家后台导出上传，单独标 `sources=E`，不能和前几路相加。
- `searches` 是**月度值**，跨月会大幅变（实测两个月之间个别词差 5 倍）。搜索量底表必须只存一期，并把期次写进 `source` 列。
- `asin_detail` 能拿到标题和五点（`features`），**拿不到描述**（`description` 为 null）。所以方法 C 只做五点，不做描述。
- 搜索量是估算值，绝对值不可信；单口径只用于排序，不要跨类目比。

## 更新日志

- **v5**（2026-11-17）：`50-copy` 补第三方体检评分。新增 `skills/scripts/score_copy.py` 与 `vendor/amazon-listing-doctor/`（MIT，v0.4.12）；`文案.xlsx` 第 4 张表改为 `04_评分`（原 04 问题清单顺移到 05，自检 06）。体检抓到 3 个真问题：后台 ST 与五点重复词 `rv`（删除后 A9 87→94、合规失败项 1→0）、标题核心词 `kitchen sink organizer` 未进前 50 字符（改不动，两个十万级词互换无增量）、COSMO/Alexa 因本体未收敛降级（不作结论）。
- **v4**（2026-11-16）：新增 `40-selling-point` 卖点库模块（`sp_config.yaml` + `build_selling_points.py` + `check_sp.py`），G/M 双分数分工，7 项自检；图片维度留作缺口，等图包回填。
- **v3.7**（2026-11-13）：关键词模块四项结构改造——四档分层（三模式可切）、竞争度与四象限、词根六分类、品牌双分类；R3 改精确覆盖率；搜索量底表统一期次。
- **v3.6**：脚本收敛为 `scripts/{config.yaml, merge.py, check.py}`；优先级改名额制；搜索转化率退出排序；分层与相关性解耦。
- **v3.5**：R3 覆盖率归一化；新增五路合并追踪表；EST 词限 P2；否定清单加白名单。
- **v3.4**：扩池三步（排变体 + 品牌去重 + 形态过滤）。
- **v3.0–3.3**：拆成模块，四路方法独立成文件，补后台数据上传契约。
