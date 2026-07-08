# 关键词分层提示词

> 用于第一步：把零散关键词数据整理成 5 层结构化词库。

## 🚨 数据来源铁律

**必须先调 MCP**，禁止用浏览器抓 Amazon 搜词建议。

```python
# 必须按顺序调用以下 MCP 工具
mcp__sellersprite__keyword_miner({"request":{"marketplace":"US","keyword":"<种子词>"}})
mcp__sellersprite__keyword_research_trends({"marketplace":"US","keyword":"<种子词>"})  # 扁平参数
for asin in competitor_asins:
    mcp__sellersprite__traffic_keyword({"request":{"marketplace":"US","asin":asin}})
    mcp__sellersprite__keyword_order({"request":{"marketplace":"US","asin":asin}})
```

❌ **严禁**：`webReader(amazon.com/s?k=...)` 抓 Amazon 搜索页凑词
✅ **允许**：用户自己提供的广告搜索词报告（后台导出）

---

## 提示词

```
你是一名亚马逊关键词分层专家。请把以下零散关键词数据整理成 5 层结构化词库。

## 输入数据
- 种子词：[用户填入，如 "artificial flowers outdoor"]
- 产品核心卖点：[用户填入]
- 卖家精灵 keyword_miner 返回数据：[粘贴 JSON]
- 卖家精灵 keyword_research_trends 返回数据：[粘贴 JSON]
- 竞品 ASIN 出单词（来自 traffic_keyword）：[粘贴]
- 广告搜索词报告：[粘贴]
- 评论高频词：[粘贴]

## 任务

### 1. 合并去重
所有来源的关键词合并，按文本去重。

### 2. 按 5 层分类
- L1 核心品类词：品牌+产品核心名词（artificial flowers / faux plants）
- L2 功能属性词：含 resistant / proof / free / material 等功能修饰
- L3 场景词：含 patio / garden / porch 等场景名词
- L4 问题词：含 won't / how to / can I / for ... 等问题句式
- L5 规格词：含数量、尺寸、颜色、形状等规格
- L6 后台补充：同义词、变体词、错拼词（前台不出现）

### 3. 字段标注（每个词必须填全）
| 字段 | 说明 |
|------|------|
| keyword | 关键词原文 |
| layer | L1-L6 |
| intent | 搜索意图（如"功能+场景"） |
| search_volume | 月搜索量（来自 keyword_miner） |
| chain_growth | 环比增长（来自 keyword_research_trends） |
| yearly_growth | 同比增长 |
| ppc_bid | 广告建议价 |
| click_concentration | 点击集中度（0-1） |
| conversion_concentration | 转化集中度（0-1） |
| suggested_position | 标题/五点/描述/ST/QA |
| must_frontend | true/false（核心词、功能词、主场景词默认 true） |
| priority | P0/P1/P2 |

### 4. 缺失数据标注
如果某些字段缺失（如某词 PPC 拿不到），标注 "DATA_MISSING"，不要编造。

### 5. 排除规则
- 排除竞品品牌词（其他卖家品牌）
- 排除不相关的泛词（如 "decor" 单独出现）
- 排除夸大词（best / #1）

### 6. 输出格式

按层级分组输出 Markdown 表格，并在最后输出 JSON 结构化数据供后续步骤使用。

## 输出模板

# 关键词分层词库 — {产品名}

## L1 核心品类词（必须前台）
| 关键词 | 月搜 | 趋势 | PPC | 集中度 | 优先级 | 建议位置 |
|--------|------|------|-----|--------|--------|---------|
| ...    | ...  | ...  | ... | ...    | ...    | 标题    |

## L2-L6：...

## 总结
- L1 词数：X
- L2 词数：X
- L3 词数：X
- L4 词数：X
- L5 词数：X
- L6 词数：X
- P0 优先级：X 个
- DATA_MISSING：X 个（列表）
- 已排除：X 个（列表）
```

---

## 使用示例

### 输入（种子词：artificial flowers outdoor）
```
种子词：artificial flowers outdoor
keyword_miner 返回：[JSON]
竞品出单词：uv resistant artificial outdoor plants, front porch planter flowers, ...
```

### 输出（节选）
```
## L1 核心品类词
| artificial flowers | 95,000 | +12% | $0.85 | 0.42 | P0 | 标题 |
| faux plants | 22,000 | +8% | $0.65 | 0.35 | P1 | 五点 |

## L2 功能属性词
| UV resistant | 18,000 | +25% | $1.20 | 0.55 | P0 | 标题 |
| fade resistant | 9,500 | +18% | $0.95 | 0.48 | P0 | 五点 1 |

...
```

---

## 检查清单

- [ ] 5 层结构完整
- [ ] 每词字段齐全（缺失字段标 DATA_MISSING）
- [ ] 无编造数据
- [ ] 排除了竞品品牌词
- [ ] P0 关键词清晰
- [ ] 同时输出 Markdown 表格和 JSON
