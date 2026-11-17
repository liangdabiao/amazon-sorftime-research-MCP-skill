# SOURCE.md · 第三方来源与改动记录

本目录下的文件**整体来自第三方开源项目，本项目未修改任何一行代码或规则**。放在这里的目的只有一个：让 `50-copy` 的评分交付物可复现——同一份 `copy.json`，任何时候重跑都得到同一个分。

| 项 | 值 |
|---|---|
| 项目 | amazon-listing-doctor |
| 仓库 | https://github.com/buluslan/amazon-listing-doctor |
| 作者 | Buluu@新西楼（公众号：新西楼.AI） |
| 版本 | v0.4.12（`SKILL.md` frontmatter） |
| 拉取提交 | `5c35168c54ec040abca59b8f16c1e503514e0110`（2026-09-17） |
| 拉取日期 | 2026-11-17 |
| 许可 | MIT，见 `LICENSE`（Copyright © 2026 Buluu@新西楼） |
| 依赖 | 无。纯标准库 Python 3.10+，零 API Key |

## 本项目怎么用它

只调一个入口：

```bash
python skills/vendor/amazon-listing-doctor/scripts/compliance_report.py --file <listing.json>
```

`listing.json` 由 `skills/scripts/score_copy.py` 从 `copy.json` 自动生成，输出解析后写 `CP-07-评分明细.csv`。

**不调用的部分**：`scripts/sellersprite_fetch.py`（本项目数据来自领星 / 卖家精灵 MCP，不重复接）、`scripts/alexa_question_gen.py`（AEO 问题生成需要 Agent 参与，本轮未接入，Alexa 维度按 substring 兜底，输出会标 `used_fallback`）。

## 已知口径差异（用它之前必须知道）

| 差异 | 它的口径 | 本项目口径 | 本项目怎么处理 |
|---|---|---|---|
| 标题字符未用满 | `char_utilization` 判 WARN，建议补到 75 | 75 是上界不是配额，剩余词 W 不够高就不塞 | 评分照实记 WARN，不据此改稿，理由写进 `文案报告.md` |
| 属性维度权重 30% | 需要 `attributes_filled` + `attributes_top10_expected` | 本项目事实卡没有这一层 | 维度标「降级·无数据」，从总分里剔除后另算可用分 |
| 图片维度权重 15% | 需要 images 数组 | 90-main-image 还没跑 | 同上 |
| COSMO / Alexa | 通用本体 + 通用提问词库，不按类目收敛 | 本项目的 D 分是按竞品覆盖率算的 | 只当参考，不进主结论；COSMO 降级时标「本体为通用词，未按类目收敛」 |
| 五点条数 | 允许 5-6 条 | 官方 5 个字段位，本项目固定 5 条 | 无冲突 |

**一句话**：它给的是"内容质量体检"的外部视角，我们自己的 C0-C12 给的是"规则合规"的内部视角。两套并存，不互相取代，也不合并进同一个分数。
