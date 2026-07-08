# 合规检查提示词

> 用于最终校验阶段：检查 Listing 是否违反亚马逊政策和合规要求。

---

## 提示词

```
你是一名亚马逊合规审核专家。请对以下 Listing 进行合规检查。

## 输入
- 标题：[粘贴]
- 五点描述：[粘贴 5 点]
- 产品描述：[粘贴]
- A+ 内容文案：[粘贴]
- Search Terms：[粘贴]
- QA：[粘贴 10 题]
- 产品类目：[填]
- 产品认证：[填，如 CPSIA / FDA / RoHS]

## 检查维度

### 1. 绝对化表达检查
扫描以下词汇并标记：
- 100% / never / always / lifetime / forever
- best / #1 / top rated / cheapest / lowest price
- guaranteed / guarantee（无明确政策时）

替代建议：
- "100% no fade" → "help reduce fading"
- "lifetime use" → "designed for long-term use"
- "best seller" → "popular choice"

### 2. 医疗承诺检查
扫描以下词汇并标记：
- cures / treats / heals / prevents disease
- FDA approved（除非真有认证）
- medical grade / clinical proven（除非真有认证）
- relief from [disease name]

替代建议：
- "cures back pain" → "supports posture"
- "treats insomnia" → "may help with relaxation"

### 3. 环保承诺检查
扫描以下词汇并标记：
- 100% eco-friendly / 100% biodegradable
- organic（除非有 USDA Organic 认证）
- non-toxic（除非有认证）
- chemical-free

替代建议：
- "100% eco-friendly" → "made with recyclable materials"
- "organic" → "natural materials"（无认证时）

### 4. 安全承诺检查
扫描以下词汇并标记：
- FDA approved / CPSIA certified（除非真有）
- child-safe / baby-safe（如无测试）
- fireproof / waterproof（如无测试）

### 5. 竞品品牌词检查
扫描已知竞品品牌名（用户提供）：
- 竞品 A：[填]
- 竞品 B：[填]
- 检查所有文案 + ST 是否含这些词

### 6. 重复堆词检查
- 标题中是否有同一关键词重复出现（如 "artificial flowers" 出现 2 次）
- 五点中同一卖点是否重复
- 标题 vs ST 是否重复（ST 不应重复标题已有词）

### 7. 字段长度检查
| 字段 | 限制 |
|------|------|
| 标题（美国） | ≤ 200 字符（建议 ≤ 180） |
| 五点单点 | ≤ 500 字符（建议 ≤ 300） |
| 描述 | ≤ 2000 字符（建议 ≤ 1200） |
| ST（美国） | ≤ 250 字节 |

### 8. 关键词相关性检查
- 每个埋入的关键词是否与产品真实相关
- 是否有为了流量埋不相关热词

### 9. 夸大承诺检查
- "premium quality" / "perfect for any occasion" / "great gift" / "easy to use"
- 没有具体证据的形容词

### 10. 虚假声明检查
- "limited edition"（除非真有限量）
- "best seller"（除非真有数据）
- "as seen on TV"（除非真有）
- "doctor recommended"（除非真有）

## 输出格式

# 合规审核报告

## 风险等级
- 高风险：X 处（必须修改）
- 中风险：X 处（建议修改）
- 低风险：X 处（可选修改）

## 详细问题清单

### 高风险问题
| # | 位置 | 原文 | 问题 | 修改建议 |
|---|------|------|------|---------|
| 1 | 五点 1 | "100% no fade" | 绝对化表达 | 改为 "help reduce fading" |

### 中风险问题
...

### 低风险问题
...

## 通过的检查项
- [x] 无竞品品牌词
- [x] 字段长度全部合规
- [x] 无医疗承诺
- ...

## 整改建议
1. 优先修改高风险问题（X 处）
2. 修改后再做一次复审
3. 中风险问题上线后逐步优化
```

---

## 红线词清单（必须替换）

| 红线词 | 替代 |
|--------|------|
| 100% | help / support / designed to |
| never / always | tends to / designed to |
| lifetime / forever | long-term use |
| best / #1 / top rated | popular / favored |
| cheap / lowest price | affordable / value |
| cures / treats | supports / may help |
| 100% eco-friendly | made with recyclable materials |
| FDA approved（无认证） | meets [actual standard] |
| organic（无认证） | natural materials |
| guaranteed | designed for / backed by [policy] |
| fireproof（无测试） | fire-resistant（如有测试） |

---

## 使用时机

1. **生成 Listing 后必须先跑一次合规检查**
2. **修改后再跑一次**确保问题都解决
3. **上线前最后一次审核**
4. **定期复审**（亚马逊政策更新时）
