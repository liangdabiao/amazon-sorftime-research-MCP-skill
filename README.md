# Amazon Sorftime MCP Skills - 亚马逊竞品分析与品类选品工具

基于 Sorftime MCP 服务和 Claude Skills 的亚马逊分析工具集。

## 项目简介

本项目配置了 Sorftime 跨境电商数据服务的 MCP (Model Context Protocol) 服务器，并开发了四个核心技能：

| 技能 | 分析对象 | 命令 | 用途 |
|------|----------|------|------|
| `amazon-analyse` | 单个Listing | `/amazon-analyse {ASIN} {SITE}` | 竞品Listing全维度穿透分析 |
| `category-selection` | 整个品类 | `/category-select "{品类}" {SITE}` | 品类自动化选品分析 |
| `keyword-research` | 关键词词库 | `/keyword-research {ASIN} {SITE}` | 关键词深度调研与8维智能分类 |
| `review-analysis` | 用户评论 | `/review-analysis {ASIN} {SITE}` | 评论深度分析与痛点挖掘 |

### 核心功能

#### Listing级别分析 (amazon-analyse)
- **竞品Listing分析**: 自动获取产品详情、评论、关键词、趋势数据
- **关键词分析**: 流量来源、竞品布局、长尾词挖掘
- **评论情感分析**: 优势聚类、痛点识别、改进建议
- **跨平台分析**: TikTok带货视频、达人分析、1688采购成本

#### 品类级别分析 (category-selection)
- **市场大盘分析**: Top100产品数据 + 统计指标
- **五维评分模型**: 市场规模、增长潜力、竞争烈度、进入壁垒、利润空间
- **可视化报告**: Markdown + Excel + HTML 三种格式

#### 关键词深度调研 (keyword-research)
- **海量词库采集**: 通过 Sorftime API 采集 1500+ 关键词
- **8维智能分类**: 否定词、品牌词、材质词、场景词、属性词、功能词、核心词、其他
- **广告策略指导**: 否定词清单、精准匹配组、场景广告组、广泛匹配组
- **多格式输出**: Markdown 报告、CSV 词库、HTML 仪表板

#### 评论深度分析 (review-analysis)
- **6维痛点分析**: 电子模块故障、结构/组装问题、设计/功能缺陷、外观/材质问题、描述不符、服务/物流问题
- **服务维度细分**: 收到二手/瑕疵品、配件缺失、退换货困难、客服问题、物流问题
- **双轨解决方案**: 产品改进建议 + 客服话术/Listing优化
- **风险预警**: 二手/瑕疵品阈值警告（>5%危险）、服务问题自动预警
- **原始数据保存**: SSE 响应、解析数据、结构化分析 JSON

---

## 快速开始

### 环境要求

- Claude Code CLI
- 有效的 Sorftime API Key
- Bash shell 环境

### 获取 API Key

访问 [Sorftime MCP](https://sorftime.com/zh-cn/mcp) 获取 API Key，然后更新 `.mcp.json`:

```json
{
  "mcpServers": {
    "sorftime": {
      "type": "streamableHttp",
      "url": "https://mcp.sorftime.com?key=YOUR_API_KEY",
      "name": "Sorftime MCP"
    }
  }
}
```

### 使用分析技能

#### 1. Listing竞品分析

```bash
# 分析美国站竞品
/amazon-analyse B07PWTJ4H1 US

# 分析欧洲站竞品
/amazon-analyse B08N5WRWNW DE
```

**报告保存**: `reports/analysis_{ASIN}_{站点}_{日期}.md`

#### 2. 品类选品分析

```bash
# 分析美国站沙发品类
/category-selection "Sofas & Couches" US

# 分析美国站无线耳机品类
/category-selection "Wireless Earbuds" US

# 指定Top20产品分析
/category-selection "Kids' Drawing Kits" US --limit 20
```

**报告保存**: `category-reports/{品类名称}_{站点}_{日期}/`
- `index.html` - 报告导航首页
- `dashboard.html` - 交互式可视化仪表板
- `report.md` - 完整Markdown分析报告
- `category_report_*.xlsx` - Excel数据表（含图表）
- `data.json` - 原始数据JSON

#### 3. 关键词深度调研

```bash
# 调研产品关键词词库
/keyword-research B0D9ZTW7PS US
```

**报告保存**: `keyword-reports/{ASIN}_{站点}_{日期}/`
- `report.md` - 完整Markdown分析报告
- `dashboard.html` - 交互式可视化仪表板
- `keywords.csv` - 完整词库（含分类、搜索量、CPC）
- `negative_words.txt` - 否定词清单（直接复制到广告后台）
- `keywords_*.csv` - 各分类专用词库文件
- `categorized_summary.json` - 分类统计数据

**8维智能分类**:
| 维度 | 说明 | 应用策略 |
|------|------|----------|
| NEGATIVE | 否定/敏感词 | 直接否定 |
| BRAND | 品牌词 | 竞品打法或否定 |
| MATERIAL | 材质词 | 精准匹配 |
| SCENARIO | 场景词 | 按场景拆分广告组 |
| ATTRIBUTE | 属性修饰词 | 长尾精准匹配 |
| FUNCTION | 功能词 | 广泛匹配扩流 |
| CORE | 核心产品词 | 大词投放占领坑位 |
| OTHER | 其他 | 补充埋词 |

#### 4. 评论深度分析

```bash
# 分析产品评论痛点
/review-analysis B0DZCBYCNY US
```

**报告保存**: `review-analysis-reports/{ASIN}_{站点}_{日期}/`
- `report.md` - 完整分析报告
- `data/` - 原始数据和分析结果
  - `raw_product_sse.txt` - 原始产品详情SSE响应
  - `raw_reviews_sse.txt` - 原始评论SSE响应
  - `negative_reviews_analysis.json` - 差评分析结构化数据

**6维痛点分析框架**:
| 维度 | 识别内容 | 严重程度评估 |
|------|----------|--------------|
| 电子模块故障 | 电池、充电、连接、功能失效 | 高/中/低 |
| 结构/组装问题 | 零件破损、密封失效、接口断裂 | 高/中/低 |
| 设计/功能缺陷 | 软件体验、操作复杂、功能缺失 | 高/中/低 |
| 外观/材质问题 | 有异味、材质过敏、色差、划痕 | 高/中/低 |
| 描述不符 | 功能预期偏差、尺寸颜色差异 | 高/中/低 |
| 服务/物流问题 | 二手/瑕疵品、配件缺失、退换货困难 | 高/中/低 |

**服务风险预警阈值**:
| 问题类型 | 警告阈值 | 危险阈值 |
|----------|----------|----------|
| 收到二手/瑕疵品 | >2% | >5% |
| 配件缺失 | >1% | >3% |
| 退换货困难投诉 | >5% | >10% |
| 客服负面评价 | >3% | >7% |

---

## 支持的站点

### 亚马逊 (14个站点)

| 站点 | 代码 | 站点 | 代码 |
|------|------|------|------|
| 美国 | US | 日本 | JP |
| 英国 | GB | 西班牙 | ES |
| 德国 | DE | 意大利 | IT |
| 法国 | FR | 加拿大 | CA |
| 印度 | IN | 墨西哥 | MX |
| 澳大利亚 | AU | 阿联酋 | AE |
| 巴西 | BR | 沙特 | SA |

### TikTok (6个站点)

US, GB, MY, PH, VN, ID

### 1688 供应链

中国批发平台采购成本分析

---

## Sorftime MCP 接口

### 亚马逊产品相关

| 接口 | 功能 |
|------|------|
| `product_detail` | 产品详情 |
| `product_trend` | 销量/价格/排名趋势 |
| `product_reviews` | 用户评论 (最多100条) |
| `product_traffic_terms` | 流量关键词 |
| `competitor_product_keywords` | 竞品关键词布局 |
| `product_search` | 产品搜索筛选 |

### 关键词相关

| 接口 | 功能 |
|------|------|
| `keyword_related_words` | 关键词长尾词扩展 |
| `keyword_detail` | 关键词详情数据 |
| `category_keywords` | 类目核心关键词 |

### 亚马逊类目相关

| 接口 | 功能 |
|------|------|
| `category_name_search` | 类目名称搜索获取 nodeId |
| `category_report` | 类目实时报告 (Top100产品 + 统计) |
| `category_tree` | 类目树结构 |
| `category_trend` | 类目历史趋势 |
| `category_keywords` | 类目核心关键词 |

### TikTok / 1688

- `tiktok_product_search` - TikTok产品搜索
- `tiktok_product_videos` - 带货视频分析
- `products_1688` - 1688采购成本分析

---

## 五维评分模型

品类选品评分体系（100分制）：

| 维度 | 分值 | 评分标准 |
|------|------|----------|
| 市场规模 | 20分 | 基于类目月销额 ($10M+/20分, $5M+/17分, $1M+/14分, $500K+/11分) |
| 增长潜力 | 25分 | 基于Amazon自营占比 (越低越好，新品机会) |
| 竞争烈度 | 20分 | 基于Top3品牌占比 (<30%/18分, <40%/15分, 其他/11分) |
| 进入壁垒 | 20分 | Amazon压力 + 高评分门槛 (各占10分) |
| 利润空间 | 15分 | 基于平均价格 ($100+/15分, $50+/13分, $20+/11分, $10+/8分) |

### 综合评级

| 总分 | 评级 | 建议 |
|------|------|------|
| 80-100 | 优秀 | 强烈推荐进入 |
| 70-79 | 良好 | 可以考虑进入 |
| 50-69 | 一般 | 谨慎进入 |
| 0-49 | 较差 | 不建议进入 |

---

## 项目结构

```
amazon-mcp/
├── .mcp.json                    # MCP 配置文件
├── .claude/
│   └── skills/
│       ├── amazon-analyse/      # 竞品Listing分析技能
│       │   ├── SKILL.md
│       │   └── references/
│       ├── category-selection/  # 品类选品分析技能
│       │   ├── SKILL.md
│       │   ├── scripts/         # 数据处理脚本
│       │   │   ├── data_utils.py
│       │   │   ├── parse_sorftime_sse.py
│       │   │   └── generate_reports.py
│       │   ├── assets/          # 模板文件
│       │   │   └── dashboard_template.html
│       │   └── references/
│       ├── keyword-research/    # 关键词调研分析技能
│       │   ├── SKILL.md
│       │   ├── scripts/         # 数据处理脚本
│       │   │   ├── workflow.py
│       │   │   └── regenerate_reports.py
│       │   └── references/
│       ├── review-analysis/     # 评论深度分析技能
│       │   ├── SKILL.md
│       │   └── references/
│       └── skill-creator/       # 技能创建工具
├── reports/                     # Listing分析报告
│   └── analysis_{ASIN}_{站点}_{日期}.md
├── category-reports/            # 品类选品报告
│   └── {品类}_{站点}_{日期}/
│       ├── index.html           # 导航页
│       ├── dashboard.html       # 可视化仪表板
│       ├── report.md            # Markdown报告
│       ├── category_report_*.xlsx
│       └── data.json
├── keyword-reports/             # 关键词调研报告
│   └── {ASIN}_{站点}_{日期}/
│       ├── report.md            # Markdown报告
│       ├── dashboard.html       # 可视化仪表板
│       ├── keywords.csv         # 完整词库
│       ├── negative_words.txt   # 否定词清单
│       └── keywords_*.csv       # 各分类词库
├── review-analysis-reports/     # 评论分析报告
│   └── {ASIN}_{站点}_{日期}/
│       ├── report.md            # Markdown报告
│       └── data/
│           ├── raw_product_sse.txt
│           ├── raw_reviews_sse.txt
│           └── negative_reviews_analysis.json
└── README.md
```

---

## 技能开发

### 创建新技能

```bash
# 初始化新技能模板
.claude/skills/skill-creator/scripts/init_skill.py <skill-name> --path .claude/skills

# 打包技能为 .skill 文件
.claude/skills/skill-creator/scripts/package_skill.py <skill-folder>
```

### 技能设计原则

1. **YAML frontmatter** - 包含完整的 `description` 说明使用场景
2. **Progressive disclosure** - SKILL.md 保持精简，细节放入 references/
3. **Scripts** - 用于需要确定性执行的代码
4. **References** - 存放 API 文档、指南等参考资料
5. **Assets** - 输出文件所需的模板、图片等

---

## 常见问题

### Q: ASIN 查询不到产品？

A: Sorftime 数据库覆盖有限，先使用 `product_detail` 验证 ASIN。如果返回"未查询到对应产品"，尝试：
1. 使用 `product_search` 搜索相关关键词
2. 确认是正确的亚马逊站点
3. 确认 ASIN 格式正确（10位字母数字）

### Q: 报告中出现乱码？

A: Sorftime 返回的中文是 Unicode 转义格式 (`\u4ea7\u54c1`)，技能会自动解码。如果仍有问题，检查 Python 环境是否支持 UTF-8 编码。

### Q: Excel 报告无法打开？

A: 确保安装了 `xlsxwriter` 库：`pip install xlsxwriter`

---

## 更新日志

### v2.5 (2026-03-15)
- **新增**: review-analysis 评论深度分析技能
- **新增**: 6维痛点分析框架（电子模块故障、结构/组装问题、设计/功能缺陷、外观/材质问题、描述不符、服务/物流问题）
- **新增**: 服务维度细分分析（收到二手/瑕疵品、配件缺失、退换货困难、客服问题、物流问题）
- **新增**: 服务风险预警阈值系统（二手/瑕疵品 >5% 危险）
- **新增**: 双轨解决方案（产品改进 + 客服话术/Listing优化）
- **新增**: 亚马逊合规差评回复邮件模板库

### v2.4 (2026-03-14)
- **新增**: keyword-research 关键词调研分析技能
- **新增**: 8维智能分类模型（否定词、品牌词、材质词、场景词、属性词、功能词、核心词、其他）
- **新增**: LLM 自动分类支持
- **新增**: 广告策略指导（否定词清单、精准匹配组、场景广告组、广泛匹配组）

### v2.3 (2026-03-03)
- **优化**: 统一报告输出格式（Markdown + Excel + HTML Dashboard）
- **新增**: index.html 导航页，集成所有报告格式
- **新增**: data.json 原始数据导出
- **修复**: 类目统计数据解析问题
- **修复**: Excel 报告生成兼容性问题

### v2.2 (2026-03-03)
- **新增**: category-selectionion 品类选品分析技能
- **新增**: 五维评分模型
- **新增**: Excel + HTML 双报告格式

### v2.1 (2026-03-02)
- 新增 Sorftime MCP API 完整文档
- 优化报告结构

### v2.0 (2026-03-02)
- 重新设计分析框架
- 新增四大维度分析模型

### v1.0 (初始版本)
- 基础竞品分析功能
- Sorftime MCP 集成

---

## 许可证

MIT License

---

## 联系方式

- Sorftime 官网: https://www.sorftime.com
- Claude Code 文档: https://claude.ai/code

---

*最后更新: 2026-03-15*
