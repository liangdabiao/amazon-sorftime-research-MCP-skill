---
name: amazon-base-skills
description: 亚马逊关键词调研与文案生成的技能库入口。分两层：modules/ 是本项目主线（输入契约、关键词调研、竞品分析、用户洞察、卖点提炼、文案生成、主图需求），vendor/ 是上游方法论与 MCP 工具参考。当用户要做关键词调研、竞品拆解、痛点分析、卖点提炼、卖点库、Listing 文案时使用。用户说"/keyword-research"、"挖关键词"、"调研这个 ASIN"、"这个词值不值得做"、"建卖点库"、"写标题/五点"时触发。
---

# 亚马逊技能库（amazon-base）

## 结构

```
skills/
├── modules/          本项目主线，按思维导图分模块
│   ├── _common/      输出规范、政策边界
│   ├── 00-input/     竞品 asin 组、本品事实卡、数据回流
│   ├── 10-keyword/   关键词调研  ← 已完成
│   ├── 20-competitor/ 竞品分析
│   ├── 30-insight/   用户洞察
│   ├── 40-selling-point/ 卖点提炼 ← 已完成
│   ├── 50-copy/      文案生成
│   └── 90-main-image/ 主图设计需求
└── vendor/           上游方法论与工具参考（只读，别在这里改）
    ├── sellersprite-amazon-research/  43 个 MCP 工具手册
    ├── review-analysis/               6 维痛点框架
    ├── amazon-listing-builder/        八步 Listing 工程 + 合规清单
    └── amazon-analyse/                单 Listing 穿透框架
```

**改东西改 `modules/`，`vendor/` 只当参考资料看。**

## 主链路

```
00-input（竞品组 + 事实卡）
    ↓
10-keyword（四路采集 → 词库 + 层级 + 优先级）
    ↓
20-competitor（竞品怎么打）  ┐
30-insight（用户要什么）      ├→ 40-selling-point（卖点 + 权重）
                              ┘
    ↓
50-copy（标题/亮点/五点/ST）
    ↓
90-main-image（主图 brief）
```

每一步都落文件，下一模块读文件，不靠上下文传递。

## 路由表

| 用户意图 | 去这里 |
|---|---|
| 挖词、扩词、做词库、否词清单 | `modules/10-keyword/SKILL.md` |
| 竞品怎么打、竞品卖点拆解 | `modules/20-competitor/` |
| 评论痛点、用户画像、使用场景 | `modules/30-insight/` |
| 卖点库、卖点提炼、卖点排序、这个卖点成不成立 | `modules/40-selling-point/SKILL.md` |
| 写标题 / 亮点 / 五点 / ST | `modules/50-copy/` |
| 主图顺序、设计 brief | `modules/90-main-image/` |
| 查某个 MCP 工具怎么调 | `vendor/sellersprite-amazon-research/reference/` |
| 合规红线、政策边界 | `modules/_common/政策边界.md` |
| 输出怎么写才合规 | `modules/_common/输出规范.md` |
| 单 Listing 全维度穿透的框架 | `vendor/amazon-analyse/SKILL.md` |

## 硬性规矩

1. **工具前缀只有 `mcp__ss_mcp__`。** Sorftime / Sif / 西柚的接口本机不存在，`vendor/` 里若有残留写法，按 `MCP映射表.md` 换掉。
2. **每个数字都要标来源和口径。** 见 `modules/_common/输出规范.md`，不标视为不合格。
3. **多口径不混用。** 卖家精灵、ABA、后台商机探测器的搜索量不能相加，一份报告只用一个口径。
4. **没数据就标 DATA_MISSING。** 不要用别的方法凑，也不要用浏览器抓 Amazon 顶替。
5. **改 `modules/` 不改 `vendor/`。** vendor 是上游快照，改了就 diff 不出原版了。

## 已清理的内容

2026-11-13 删掉了对本项目无用的部分：

| 删除 | 原因 |
|---|---|
| `sif-amazon-research` | 需 Sif MCP，本机没有 |
| `xiyou-insight` | 需西柚 MCP，本机没有 |
| `category-selection` | 类目选品，本项目不做 |
| `product-research` | 选品调研，本项目不做 |
| `keyword-research` | 已升级为 `modules/10-keyword/` |
| `sellersprite/tactical`（16 张战术卡） | 选品用，本项目不做 |
| `sellersprite/comprehensive`（10 个工作流） | 选品用，被 modules 取代 |

GitHub 仓库里还留着这些文件的历史副本（API 删除要逐文件调用，先不动），本地工作区已经干净。

## 当前进度

| 模块 | 状态 |
|---|---|
| `00-input` | ✅ |
| `10-keyword` | ✅ v3，可运行 |
| `_common` | ✅ |
| `20-competitor` | ⬜ 骨架 |
| `30-insight` | ⬜ 骨架 |
| `40-selling-point` | ✅ v1，可运行（`scripts/build_selling_points.py` + `check_sp.py`，图片维度待图包） |
| `50-copy` | ⬜ 骨架 |
| `90-main-image` | ⬜ 骨架 |

下一步：`20-competitor` 补齐竞品拆解表，`30-insight` 把 `amz-review-analysis` 的产物正式纳入模块，之后 `50-copy` 接 `40-selling-point` 的交接单。
