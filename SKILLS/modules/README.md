# 模块化技能库

按思维导图拆的。**输入层 → 处理层 → 输出层**，每个模块自己带输入契约和输出规范。

```
00-input          输入层：竞品 asin 组、本品事实卡、数据回流
10-keyword        关键词调研                 ← 本轮做满
20-competitor     竞品分析（产出：竞品拆解、竞品痛点）
30-insight        用户洞察（产出：画像、场景、痛点）
40-selling-point  卖点提炼（产出：卖点库、卖点权重）
50-copy           文案生成（标题/亮点/五点/ST）
90-main-image     主图设计需求
_common           跨模块共用：输出规范、口径声明
```

脚本不放在各模块里，统一在 `skills/scripts/`（全库共用一份）：

```
scripts/config.yaml            10-keyword 的阈值、权重、词表——唯一真相源
scripts/merge.py               合并 → 打分 → 分层 → 优先级 → 四象限
scripts/check.py               关键词交付自检（7 项）
scripts/sp_config.yaml         40-selling-point 的阈值、卖点定义、等级规则
scripts/build_selling_points.py 卖点库 → 七张表 + xlsx
scripts/check_sp.py            卖点库交付自检（7 项）
scripts/fact_schema.yaml       00-input 事实卡字段定义与必填分级
scripts/check_facts.py         事实卡自检（C1-C8）
scripts/copy_config.yaml       50-copy 的字段边界、词表、判定阈值
scripts/build_copy.py          正文 → CP-02 / 粘贴稿 / CP-05 / CP-06 / 文案.xlsx / _summary.json
scripts/check_copy.py          文案交付自检（15 项，C0-C12）
```

一个模块一套 `配置 + build + check`，三个模块同一套结构：阈值全在配置里，`build` 出表，`check` 定生死，退出码非 0 不许交。

**为什么脚本要单独一层**：同一套打分逻辑会被多个模块调用，散在各模块里迟早出现"两份不一样的实现"。更关键的是——词表和阈值必须待在一个运营能改的文件里，而不是藏在代码中间。历史教训：早期四份脚本并存（`score.py` → `score_v2` → `score_v3` → `build_library.py`），阈值散落，最后谁也不知道该跑哪个，而且词库和五路产出根本没接上。


## 关键改动：竞品分析、痛点分析算产出物

导图上它们在「处理层」，但按实际用法，**它们本身就是交付物**——调研完给老板看的就是"竞品怎么打、痛点在哪"，不是中间步骤。

所以：
- 竞品分析独立成 `20-competitor` 模块，输出是**成品报告**，不是中间数据
- 痛点分析挂在 `30-insight` 的输出里，和用户画像、场景并列

区别只在措辞：处理层的动作叫"拆解"，输出层的产物叫"分析结论"。模块归属按**产物**算，不按动作算。

## 和思维导图的对应

| 导图节点 | 落在这里 | 产物性质 |
|---|---|---|
| 输入层 / 竞品 asin 组 | `00-input/README.md` | 契约 |
| 输入层 / 本品事实卡 | `00-input/README.md` | 契约 |
| 输入层 / 数据回流 | `00-input/README.md` | 契约 |
| 处理层 / 关键词调研（5 子项） | `10-keyword/` | 词库 + 优先级 |
| 处理层 / 竞品分析 → **归入输出** | `20-competitor/` | 竞品拆解报告 |
| 处理层 / 用户洞察（review + QA） | `30-insight/` | 画像 / 场景 / 痛点 |
| 处理层 / 卖点提炼 | `40-selling-point/` | 卖点库 + 权重评分 |
| 处理层 / listing 文案生成 | `50-copy/` | 标题 / 亮点 / 五点 / ST |
| 处理层 / 主图设计需求 | `90-main-image/` | brief / 提示词 |
| 输出层 / 全部 | 各模块「输出」节 | 统一按 `_common/输出规范.md` |
| 边界 / 最新政策规则 | `_common/政策边界.md` | 约束 |

## 五条贯穿全局的规矩

**1. 输出必须标数据源和口径。**
导图原话：AI 输出不应该杂乱。每条结论都要能追溯到"哪个接口、哪个月份、什么样本"。见 `_common/输出规范.md`。

**2. 多口径数据交叉校验，不能直接相加。**
卖家精灵、ABA、后台商机探测器对同一个词的搜索量口径不同，差值可能 3-5 倍。一份报告只用一个口径，另一个只验证方向。

**3. 模块之间靠文件交接。**
上一模块输出落成文件，下一模块读文件。任何一步都能单独重跑。

**4. 判断词表和阈值，一律进 `config.yaml`，不许写进代码。**
代码里出现的词或数字，必须是配置项，不是常量。这不是洁癖——实测出过一次事故：打分脚本自带一份手写词表，五路各自出了 CSV，词库却只吃掉 3-5 个词，因为脚本根本不读那些文件。另一个小号复发：覆盖率有 16 个值直接写在代码里。写死在代码里的数据，等于让产物和数据脱钩，而且看不出来。

**5. 交付前跑 `check.py`，不过就不交。**
七项：字段是否齐、五路是否每路非零、EST 占比、否定清单有没有过泛词、P0 名额、BRAND 有没有混进 P0/P1、层级与优先级取值是否合法。退出码非 0 就是有 FAIL。这一条比前四条更能拦住"看起来完整、实际空转"的交付。

## 当前状态

| 模块 | 状态 |
|---|---|
| `00-input` | ✅ 契约已定 |
| `10-keyword` | ✅ v3.7，可运行（`scripts/merge.py` + `check.py`，7 项自检全过） |
| `_common` | ✅ 输出规范已定 |
| `scripts/` | ✅ `config.yaml` + `merge.py` + `check.py` |
| `20-competitor` | ⬜ 骨架 |
| `30-insight` | ⬜ 骨架 |
| `40-selling-point` | ✅ v1，可运行（`scripts/build_selling_points.py` + `check_sp.py`，7 项自检全过；图片维度待图包） |
| `50-copy` | ✅ v2，可运行（`SKILL.md` + 8 份 references + `copy_config.yaml` + `build_copy.py` + `check_copy.py` 15 项自检）；sponge-holder 成稿已出，四字段全绿 |
| `90-main-image` | ⬜ 骨架 |
