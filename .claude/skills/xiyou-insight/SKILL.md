---
name: xiyou-insight
description: 基于西柚洞察MCP的亚马逊竞品分析与广告策略工具。提供7大核心工作场景：实时监控广告投放效果、快速找到高性价比流量缺口、快速拆解对标竞对打法、提升新品推广效率、精准拆解竞品流量以及广告策略、透视竞品广告策略和预算、高效搭建关键词库。适用于亚马逊卖家进行竞品分析、广告优化和关键词研究。
argument-hint: "[场景名称] [ASIN/关键词] [站点]"
user-invocable: true
---

# 西柚洞察 (Xiyou Insight)

## 定位

基于 **西柚洞察MCP** 的亚马逊竞品分析与广告策略工具。LLM Agent 直接调用 MCP 工具获取数据，脚本仅负责数据后处理、报告生成和可视化渲染。

**核心特点**：
- **MCP驱动**：所有数据获取通过 xydc-mcp 直接调用
- **场景化工作流**：7大核心场景，覆盖广告监控、流量分析、竞品拆解、新品推广、关键词库搭建
- **轻量脚本**：仅用于数据聚合、报告生成和 Dashboard 渲染

---

## MCP 工具速查表

### ASIN 基础信息

| 工具名称 | 功能 | 参数 |
|----------|------|------|
| `get_asin_info` | 获取ASIN基础信息（标题、价格、评分、评论数、主图） | `asins`, `country` |
| `get_asin_variations` | 查询父子变体关系 | `asin`, `country` |
| `get_asin_info_trends` | 商品信息日趋势（价格、评分、评论数变化） | `asin`, `country`, `start_date`, `end_date` |

### ASIN 关键词分析

| 工具名称 | 功能 | 参数 |
|----------|------|------|
| `get_asin_keywords` | ASIN反查关键词（近7天） | `asin`, `country`, `page`, `page_size`, `sort_field`, `sort_order` |
| `get_asin_keywords_monthly` | ASIN反查关键词（月度历史） | `asin`, `country`, `start_month`, `end_month`, `page`, `page_size` |
| `get_asin_keyword_rank_trends` | 关键词日排名趋势 | `asin`, `keyword`, `country`, `start_date`, `end_date` |
| `get_asin_keyword_rank_hourly` | 关键词小时级排名（仅US/UK/DE） | `asin`, `keyword`, `country`, `date` |
| `get_asin_keyword_traffic_trends` | 关键词日流量趋势 | `asin`, `keyword`, `country`, `start_date`, `end_date` |

### ASIN 流量与销量

| 工具名称 | 功能 | 参数 |
|----------|------|------|
| `get_asin_traffic` | 近7天流量得分（自然/广告流量占比） | `asins`, `country` |
| `get_asin_traffic_trends` | 日流量趋势（自然/广告/位置维度） | `asin`, `country`, `start_date`, `end_date` |
| `get_asin_order_trends` | 月订单量趋势 | `asin`, `country`, `start_month`, `end_month` |
| `get_asin_bsr_trends` | BSR类目排名日趋势 | `asin`, `country`, `start_date`, `end_date` |

### ASIN 广告分析

| 工具名称 | 功能 | 参数 |
|----------|------|------|
| `get_asin_ad_change_trends` | 广告投放变化日趋势（新增/移除广告活动） | `asin`, `country`, `start_date`, `end_date` |

### 关键词分析

| 工具名称 | 功能 | 参数 |
|----------|------|------|
| `get_keyword_info` | 关键词基础指标（搜索量、竞争难度、建议竞价） | `keywords`, `country` |
| `get_keyword_aba_trends` | ABA搜索量周趋势（最长52周） | `keywords`, `country`, `start_week`, `end_week` |
| `get_keyword_asin_analysis` | 关键词反查ASIN（近7天竞争格局） | `keyword`, `country`, `page`, `page_size`, `sort_field`, `sort_order` |
| `get_keyword_analysis_monthly` | 关键词竞争格局月度历史 | `keyword`, `country`, `start_month`, `end_month`, `page`, `page_size` |

---

## 7大核心工作场景

### 场景1：实时监控广告投放效果

**目标**：通过小时级排名变化和广告放映机，实时监控广告投放效果

**工作流程**：

```
Step 1: 获取ASIN基础信息
  → get_asin_info(asin)
  
Step 2: 查询小时级排名（仅US/UK/DE）
  → get_asin_keyword_rank_hourly(asin, keyword, date)
  分析广告排名位置和持续时间
  
Step 3: 查询日排名趋势
  → get_asin_keyword_rank_trends(asin, keyword, start_date, end_date)
  判断广告投放带动自然排名上升情况
  
Step 4: 查询广告投放变化
  → get_asin_ad_change_trends(asin, start_date, end_date)
  分析广告活动新增/移除情况
  
Step 5: 生成分析报告
  → 评估广告投放效率，判断是否带来自然排名提升
```

**输出**：广告投放效果分析报告

---

### 场景2：快速找到高性价比流量缺口

**目标**：通过多ASIN对比和关键词分析，找到竞争对手有排名但自身没有的流量缺口

**工作流程**：

```
Step 1: 获取多个ASIN基础信息
  → get_asin_info(asins)
  
Step 2: 获取各ASIN关键词列表
  → get_asin_keywords(asin1)
  → get_asin_keywords(asin2)
  → ...
  
Step 3: 对比关键词覆盖差异
  → 找出竞品有排名但自身没有的关键词
  
Step 4: 分析关键词竞争程度
  → get_keyword_info(keywords)
  判断搜索量、竞争难度、建议竞价
  
Step 5: 分析关键词下ASIN竞争格局
  → get_keyword_asin_analysis(keyword)
  判断自然位滚动率、广告位竞争难度
  
Step 6: 筛选高性价比流量缺口
  → 综合评估：搜索量中等、竞争难度低、竞品有排名但自身无排名
```

**输出**：流量缺口分析报告，包含推荐补充的关键词列表

---

### 场景3：快速拆解对标竞对打法

**目标**：全面分析竞品的关键词覆盖差异、流量结构和广告策略

**工作流程**：

```
Step 1: 获取竞品基础信息
  → get_asin_info(competitor_asins)
  
Step 2: 确认主推变体
  → get_asin_variations(asin)
  确定父体下流量最大的变体
  
Step 3: 分析流量结构
  → get_asin_keywords(asin)
  → get_asin_traffic(asin)
  分析头部词、腰部词、长尾词贡献的展示量
  
Step 4: 分析广告策略
  → get_asin_ad_change_trends(asin, start_date, end_date)
  → get_asin_traffic_trends(asin, start_date, end_date)
  了解广告流量构成和广告展示位置关键词
  
Step 5: 趋势分析
  → get_asin_keyword_rank_trends(asin, keyword, start_date, end_date)
  洞察竞品广告投放策略和节奏
  
Step 6: 综合对比分析
  → 关键词覆盖差异、流量份额、广告策略对比
```

**输出**：竞品打法拆解报告

---

### 场景4：提升新品推广效率

**目标**：分析新品流量分配阶段（稀疏期→震荡期→稳定期），把握异动关键词机会

**工作流程**：

```
Step 1: 获取ASIN基础信息
  → get_asin_info(asin)
  
Step 2: 分析流量趋势
  → get_asin_traffic_trends(asin, start_date, end_date)
  判断流量分配阶段：稀疏期/震荡期/稳定期
  
Step 3: 分析关键词排名变化
  → get_asin_keywords(asin)
  → get_asin_keyword_rank_trends(asin, keyword, start_date, end_date)
  
Step 4: 识别异动关键词
  - 新增：昨日无排名今日出现排名
  - 流失：昨日有排名今日消失
  - 流量升档：自然流量上升（稀疏→震荡→稳定）
  - 流量降档：自然流量下降
  
Step 5: 把握流量窗口机会
  → 针对新增和流量升档关键词加大投放
  → 针对流失和流量降档关键词分析原因并调整
```

**输出**：新品推广分析报告，包含流量阶段判断和异动关键词建议

---

### 场景5：精准拆解竞品流量以及广告策略

**目标**：深度分析竞品的关键词布局、流量来源和广告投放策略

**工作流程**：

```
Step 1: 获取竞品基础信息
  → get_asin_info(competitor_asins)
  
Step 2: 确认主推变体
  → get_asin_variations(asin)
  
Step 3: 分析关键词布局
  → get_asin_keywords(asin)
  → get_asin_keywords_monthly(asin, start_month, end_month)
  了解关键词覆盖广度和月度变化
  
Step 4: 分析流量结构
  → get_asin_traffic(asin)
  → get_asin_traffic_trends(asin, start_date, end_date)
  自然/广告流量占比、位置维度拆解
  
Step 5: 分析广告策略
  → get_asin_ad_change_trends(asin, start_date, end_date)
  → get_asin_keyword_traffic_trends(asin, keyword, start_date, end_date)
  
Step 6: 关键词竞争分析
  → get_keyword_info(keywords)
  → get_keyword_asin_analysis(keyword)
  分析竞品核心关键词的竞争格局
  
Step 7: 生成综合分析报告
  → 关键词覆盖差异、流量结构、广告策略洞察
```

**输出**：竞品流量与广告策略深度分析报告

---

### 场景6：透视竞品广告策略和预算

**目标**：分析竞品的广告类型分布、活动结构、预算分布和核心广告关键词

**工作流程**：

```
Step 1: 获取竞品基础信息
  → get_asin_info(asin)
  
Step 2: 确认主推变体
  → get_asin_variations(asin)
  
Step 3: 分析广告活动变化
  → get_asin_ad_change_trends(asin, start_date, end_date)
  识别新增/移除的广告活动，分析投放节奏
  
Step 4: 分析流量趋势
  → get_asin_traffic_trends(asin, start_date, end_date)
  判断SP/SB/SBV广告流量占比
  
Step 5: 分析关键词流量贡献
  → get_asin_keywords(asin)
  → get_asin_keyword_traffic_trends(asin, keyword, start_date, end_date)
  找出核心广告关键词及其流量占比
  
Step 6: 推断预算分布
  → 根据广告展示时长和关键词流量变化推断预算调整
  → 分析广告投放的周期性规律
  
Step 7: 生成广告策略分析报告
  → 广告类型分布、活动结构、核心关键词、预算推断
```

**输出**：竞品广告策略和预算分析报告

---

### 场景7：高效搭建关键词库

**目标**：通过反查竞品流量词和以词找词，搭建完整的关键词库

**工作流程**：

```
Step 1: 广泛收集关键词
  → 方式1：反查竞品流量词
    get_asin_keywords(competitor_asin) × 多个竞品
  → 方式2：关键词基础信息
    get_keyword_info(core_keywords)
  
Step 2: 关键词拓展
  → get_keyword_aba_trends(keywords, start_week, end_week)
  分析搜索量趋势和季节性
  
Step 3: 关键词竞争分析
  → get_keyword_asin_analysis(keyword)
  判断每个关键词下的竞争格局
  
Step 4: 按相关性筛选
  → 强/高/中相关 → 加入关键词库
  → 低/极低相关 → 加入否定词库
  
Step 5: 关键词分类
  → 数据维度：搜索量（大/中/小）、竞争难度（超难/难/中等/简单）、转化率（高/中/低）
  → 属性维度：人群受众、使用场景、产品维度、价值维度
  
Step 6: 输出关键词库
  → 结构化关键词列表，包含分类标签和优先级
```

**输出**：完整关键词库，包含关键词分类和优先级标注

---

## Script Directory

| 脚本 | 用途 | 何时调用 |
|------|------|---------|
| `report_generator.py` | **报告生成器**：将MCP数据聚合为Markdown报告 | 每个场景完成后 |
| `dashboard_generator.py` | **Dashboard渲染**：生成可视化看板HTML | 报告生成后 |
| `data_aggregator.py` | **数据聚合器**：合并多个ASIN/关键词数据 | 多ASIN对比场景 |

**脚本职责**：
- **不做API调用**：所有数据获取由LLM通过MCP直接调用
- **仅做数据处理**：聚合、清洗、格式化
- **报告渲染**：生成Markdown和HTML报告

---

## 执行流程

### 通用执行模式

```
1. 用户输入场景和参数（ASIN/关键词/站点）
2. LLM根据场景选择对应MCP工具组合
3. 调用MCP工具获取数据
4. 使用脚本进行数据后处理和报告生成
5. 输出Markdown报告和Dashboard看板
```

### 数据输出目录

```
xiyou-insight-reports/
└── {scenario}_{asin_or_keyword}_{site}_{YYYYMMDD}/
    ├── report.md              # Markdown完整报告
    ├── data.json              # 结构化数据
    ├── dashboard.html         # 可视化看板
    └── raw/                   # 原始MCP响应数据
        ├── asin_info.json
        ├── keywords.json
        ├── traffic.json
        └── ad_trends.json
```

---

## 数据字段命名规范

| 字段名 | 说明 | 示例 |
|--------|------|------|
| `natural_traffic` | 自然流量得分 | 85.5 |
| `ad_traffic` | 广告流量得分 | 42.3 |
| `total_traffic` | 总流量得分 | 127.8 |
| `keyword_count` | 关键词数量 | 156 |
| `natural_rank` | 自然排名位置 | 5 |
| `ad_rank` | 广告排名位置 | 2 |
| `weekly_search_volume` | 周搜索量 | 125000 |
| `competitive_difficulty` | 竞争难度(0-100) | 72 |
| `cost_per_click` | 建议竞价 | 2.35 |

---

## 支持的站点

US, CA, MX, BR, UK, DE, FR, ES, IT, JP, AE, AU, SA

**注意**：小时级排名(`get_asin_keyword_rank_hourly`)仅支持 US/UK/DE 站点

---

## 注意事项

1. **API限流**：每批请求建议控制并发数量，避免触发限流
2. **数据时效**：近7天数据实时性较好，历史数据可能有延迟
3. **消耗提示**：查询日期范围越长，API消耗越高
4. **intent_summary**：所有MCP调用必须包含脱敏的业务意图描述，禁止包含用户原始prompt、账号、手机号、邮箱或完整ASIN

---

## 与其他Skills的关系

```
category-selection (品类筛选)
        ↓
product-research (深度选品调研)
        ↓
xiyou-insight (竞品分析与广告策略) ← 本Skill
        ↓
review-analysis (评论深度分析)
```

**区别**：
- `category-selection`：品类级别的快速筛选
- `product-research`：指定品类的深度调研
- `xiyou-insight`：竞品流量分析和广告策略拆解
- `review-analysis`：评论的深度痛点分析

---

*版本: v1.0 (7场景工作流) | 最后更新: 2026-07-04*
