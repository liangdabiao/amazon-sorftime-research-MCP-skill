<div align="center">

<!-- Banner: 把一张 banner 图放进 assets/banner.png 后,去掉下一行的注释即可显示 -->
<img width="2172" height="724" alt="003ccd81-adaa-4cc3-8244-ed9cb7930657" src="https://github.com/user-attachments/assets/88a64a44-cb0a-40a6-be34-a3dceddbd8ab" />


# 🩺 Amazon Listing Doctor

**给亚马逊 Listing 做一次全身体检，揪出流量加倍的机会点**

**想了解更多最新AI行业动态,AI+电商/广告的行业实践方法,人与AI如何协作共生的思考,请关注公众号:【新西楼.AI】**

![qrcode_for_gh_e3b954bd3859_258](https://github.com/user-attachments/assets/d8f068d9-c4f8-46c7-914c-fbcab5d52f2a)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.4.12-black.svg)]()
[![English](https://img.shields.io/badge/lang-English-blue.svg)](README_EN.md)

**CDQ 质量分 · A9 收录 · COSMO 意图覆盖 · Alexa 可发现性 · 合规体检 · 标题词组分诊**

**Created By Buluu@新西楼**

</div>

---

## 项目简介

amazon-listing-doctor 是由 buluslan（公众号：新西楼.AI）研发的亚马逊 Listing 质检 Skill，他会基于 CDQ算法 / A9 / COSMO / Alexa 四大底座知识，来给Listing进行全身体检和打分，输出一份诊断报告，帮你揪出"流量加倍、弯道超车"的机会点。

> [!TIP]
> **更多跨境电商 AI 实战内容，请关注公众号「新西楼.AI」**

作为 **Agent 原生** 工具，它适配各类 AI Coding Agent，**零依赖、零 API Key**，纯标准库 Python，clone 下来就能跑。**只诊断不改写** —— 告诉你"哪里有问题、该改什么"，改写由你自己决定。

**兼容性**:基于命令行调用,任何能执行 shell 的 Agent 都能用 —— 通过 Skill 加载 / AGENTS.md 注入 / 直接终端调用均可。

---

## ✨ 它做什么

一条命令,给你的 Listing 出一份多维度体检报告:

| 维度 | 底座 | 回答的问题 |
|---|---|---|
| **CDQ 质量分**(主总分) | 亚马逊内部 6 维 ASIN 质量评分 | 我的内容质量能打几分? |
| **A9 收录健康度** | A9 搜索收录逻辑 | 我的 Listing 能不能被搜到? |
| **COSMO 意图覆盖度** | 亚马逊常识知识图谱(WWW 2024) | 我的 Listing 对不对得上用户意图? |
| **Alexa 可发现性** | Alexa for Shopping / Rufus（AEO 买家问答） | AI 购物助手回答买家提问时会推荐我吗? |
| **合规体检** | 2026-07-27 新规 | 我有没有违规? |
| **标题词组分诊** | 词性 + 合规信号 | 标题里每个词该留 / 该挪 / 该删? |

## 🚫 它不做什么

- **不改写文案** —— 只给"该改什么"的改进建议清单,改写交给你自己
- **不内置浏览器抓取** —— 零依赖,数据靠你粘贴(推荐用第三方工具取数后粘贴)
- **不冒充官方 COSMO 分** —— COSMO 无公开权重,本 skill 的 COSMO 维度是基于公开论文精神的社区诊断,如实标注

## 🚀 快速开始

```bash
# 1. 把你的 listing 归一化成 JSON(见下方 schema),存为 listing.json
# 2. 跑全量体检
python scripts/compliance_report.py --file listing.json > report.json

# 3.(或单独跑某一维)
python scripts/cdq_score.py --file listing.json        # CDQ 质量分
python scripts/cosmo_check.py --file listing.json      # COSMO 意图覆盖
python scripts/indexability.py --file listing.json     # A9 收录
python scripts/title_triage.py --file listing.json     # 标题词组分诊
```

输出是结构化 JSON;按 `assets/report-template.md` 渲染成人类可读报告。

### listing JSON 最小结构 + 数据分层

输入字段分两组,缺字段触发**评分降级**(标 score=null + 字段缺失原因)而非报错:

```json
{
  "market": "US", "language": "en", "mode": "strict_75", "category": "Electronics",
  "brand": "Anker", "is_parent": false, "is_variation": true,
  "title": "...", "item_highlights": "...",
  "bullets": [{"header": "...", "body": "..."}],
  "description": "...", "backend_search_terms": "...",
  "attributes_filled": ["brand", "color"],
  "has_a_plus": true
}
```

| 分层 | 字段 | 来源 |
|------|------|------|
| **前台（详情页可见）** | title / item_highlights / bullets / description / images / brand / has_a_plus / market / language / attributes_filled / attributes_top10_expected | 第三方 API / SP-API 均可取；⚠️ item_highlights 与 title 在标题区竖线拼接同行显示，多数抓取入口拿到的是拼接串——skill 会提示拆分（SKILL.md §1.2） |
| **后台（详情页不可见）** | backend_search_terms / band_a_critical_6 / is_parent / is_variation | **必须从 Seller Central 后台导出** |

为什么这样切:前台数据=详情页对买家可见,第三方工具理论上都能拉;后台数据(backend_search_terms)=隐藏索引字段,外部 API 拿不到。item_highlights 特殊:前台可见(与标题拼接同行)但卖家精灵取不到,需 Seller Central 导出或从拼接串拆分。Skill 支持用户单独贴前台/后台/两者一起,缺字段不影响审计流程跑通。

### 评分降级示例

只给 title 一个字段,缺其他字段时报告输出:
```
Overall NON-COMPLIANT; 17 passed, 2 failed, 1 warn; CDQ 31.2/100 (Poor); data 29% (minimal)
- COSMO 评分降级: 缺 bullets / item_highlights
- Alexa 评分降级: 缺 bullets / item_highlights
- CDQ 子分 structured_attribute 降级: 缺 attributes_filled + attributes_top10_expected
- A9 子分 backend_hygiene 降级: 缺 backend_search_terms
- ...
data_coverage.unlock_dimensions: [补 item_highlights → 解锁 A9 高亮强度..., 补 attributes → 解锁 CDQ 30% 权重...]
```

字段不全也没关系——缺的字段对应检查自动跳过,不会报错。详见 `SKILL.md`。

### 多语言修复

- ✅ 德语 listing 不再因 mit / für / durch / aus 等介词被判关键词堆砌(虚词按 `language` 自动取)
- ✅ promo / subjective 黑名单补齐 de / fr / it / es
- ✅ 全大写品牌名 DJI / BMW / LG / HP / HTC / OPPO / TCL 等走白名单(不依赖用户传 brand 字段)

## 🧠 四大底座怎么落地

- **CDQ**:6 维加权(属性 30% / 标题 25% / 变体 20% / 图片 15% / 五点 5% / A+ 5%)→ 0-100 分 + 档位
- **A9**:核心词前置位置 + backend 卫生度 + 属性完整度 + 有效索引词
- **COSMO**:扫全文匹配 `references/cosmo_ontology.json` 的常识概念,四维覆盖(use_case / audience / goal / constraint)+ 缺失清单
- **Alexa**:模拟买家向 AI 购物助手提问,判断 listing 能否被回答(AEO 买家问答,Agent 按规范针对具体产品生成问题;substring 词匹配兜底)
- **标题词组分诊**:把标题拆成语义词组,按词性 + 合规信号给去向建议(标题必留 / 下移亮点 / 下移五点 / 删除违规),告诉你每个词该去哪——诊断不是改写

## 📁 结构

```
amazon-listing-doctor/
├── SKILL.md                  # 质检路由(工作流 + 原则)
├── scripts/                  # 13 个纯标准库 Python 脚本
│   ├── compliance_report.py  # 汇总器(核心入口,含 data_coverage 降级板块)
│   ├── cdq_score.py          # CDQ 6 维评分
│   ├── cosmo_check.py        # COSMO 意图覆盖(本项目独占)
│   ├── title_triage.py       # 标题词组分诊(去向建议)
│   ├── indexability.py       # A9 收录
│   ├── alexa_check.py        # Alexa 可发现性(AEO 买家问答)
│   ├── alexa_question_gen.py # ALEXA AEO 规范加载器
│   ├── image_check.py        # 图片缺陷
│   ├── lint_title/highlights/bullets/backend.py  # 合规校验
│   └── check_keyword_layering.py
├── references/               # 规则与词库(公开版)
│   ├── cosmo_ontology.json   # COSMO 概念本体(4 维 + 10 类目分词)
│   ├── alexa_question_protocol.md # ALEXA AEO 问题生成规范
│   ├── cdq_weights.json      # CDQ 权重
│   ├── rules.json            # 合规硬规则(含 de/fr/it/es 多语言黑名单)
│   └── ...
└── assets/                   # 输出模板
    ├── output-template.json
    └── report-template.md
```

## 🏠 交流社区

<div align="center">

🎯 **更多 AI 实战教程和专属福利尽在我们「MBG 跨境AI实战圈」,已有 50+ 跨境大卖、AI 专家热聊中**

—— 欢迎跨境电商从业者加入我们,一起探索 AI+商业的最佳实践和真实边界,跑通【跨境AI】的从 0 到 1,打败你的同事,干掉你的老板。

**社区介绍:[my.feishu.cn/wiki/WNi0wh3mIiOLhzkCLFPcwUr9nrg](https://my.feishu.cn/wiki/WNi0wh3mIiOLhzkCLFPcwUr9nrg)**

<img width="1125" height="618" alt="image" src="https://github.com/user-attachments/assets/20f47cd6-e33c-4f3e-9362-3846c11135fd" />

</div>

## 📜 License

MIT — 随便用,欢迎 PR 扩展词库/类目。

---

<div align="center">

**如果这个工具帮到了你,欢迎 ⭐ Star 支持。更多 AI × 跨境电商实操内容,关注公众号「新西楼」。**

</div>
