# 痛点-证据映射提示词

> 用于第三步：把产品卖点拆解成"痛点 → 解决方案 → 证据 → 关键词 → 图片"完整链。

## 🚨 数据来源铁律

**用户痛点主来源必须走 MCP**：竞品差评用 `mcp__sellersprite__review`，**严禁**用浏览器抓 `amazon.com/product-reviews/`。

```python
# 必须调用（拿竞品差评作为痛点真相）
for asin in competitor_asins:
    mcp__sellersprite__review({"marketplace":"US","asin":asin})
    # ⚠️ 每次最多 20 条，需多 ASIN 取并集
```

✅ **浏览器补充**（仅 MCP 无对应数据）：
- 竞品 QA 板块：`amazon.com/ask-questions/...`（MCP 无 QA 工具）
- Reddit / TikTok 站外反馈
- 认证官网：FDA / CPSIA / RoHS（验证证书真实性）

❌ **严禁**：`webReader(amazon.com/product-reviews/B07X...)` 抓评论

---

## 提示词

```
你是一名亚马逊产品证据工程师。请基于以下输入，建立"痛点-证据映射表"。

## 输入
- 产品规格：[粘贴]
- 供应链信息（材料/工艺/认证）：[粘贴]
- 产品功能列表：[粘贴]
- 用户问题库（来自第二步）：[粘贴]
- 关键词分层词库（来自第一步）：[粘贴]
- 竞品差评主题：[粘贴]

## 任务

### 1. 列出产品所有可能的卖点
不少于 10 个，按主次排序。

### 2. 为每个卖点找到证据
证据类型：
- 材料证据（如 PE plastic / stainless steel）
- 工艺证据（如 reinforced stitching / double-stitched）
- 规格证据（如 12 bundles / 16 inches / 24 x 24）
- 场景证据（如 tested for outdoor use）
- 对比证据（如 vs standard faux flowers）
- 客户反馈证据（来自好评）
- 数据证据（如 200+ hours UV test）
- 认证证据（如 CPSIA / RoHS）

每个卖点至少 1 条证据，无证据的卖点必须标注"待补充证据"，不能进 Listing。

### 3. 建立映射表

每个卖点拉成一条完整链：

| 字段 | 说明 |
|------|------|
| feature | 卖点名称 |
| painpoint | 对应用户痛点 |
| evidence | 证据描述（材料/工艺/数据） |
| keywords | 对应关键词（来自词库） |
| image_brief | 图片需求简述 |
| aplus_module | A+ 模块位置 |
| bullet_point_n | 五点第几条 |
| qa_n | QA 第几题 |
| compliance_risk | high / medium / low |
| verification_status | 已验证 / 待验证 / 无证据 |

### 4. 合规风险检查
对每个卖点检查：
- 是否含绝对化表达（100% / never / always）
- 是否含医疗承诺（cures / treats / heals）
- 是否含环保绝对词（100% eco-friendly）
- 是否含安全承诺（FDA approved 如无认证）
- 是否含持久承诺（lifetime / forever）

如发现，标注合规风险等级并给出替代建议。

### 5. 输出图片需求清单
列出所有需要的图片素材，给美工：
| 图片编号 | 用途 | A+ 位置 | 需求简述 |
|---------|------|---------|---------|

## 输出格式

# 卖点证据库 — {产品名}

## 核心卖点（前 5 个，必进 Listing）

### 卖点 1: UV Resistant Design
- 痛点：户外暴晒容易褪色
- 证据：采用抗 UV 处理 PE 塑料花瓣
- 对应关键词：UV resistant / fade resistant / outdoor sunlight
- 图片需求：户外阳光下场景图
- A+ 位置：第 2 屏
- 五点位置：第 1 点
- QA 位置：Q1
- 合规风险：低
- 验证状态：已验证（供应链确认）

### 卖点 2-5: ...

## 次核心卖点（6-10）

## 待补充证据的卖点（不要进 Listing）
- 卖点 X：[描述]，但无 [证据类型] 支撑，建议补充 [测试/认证] 或从 Listing 删除

## 图片需求清单
| 编号 | 用途 | 需求简述 |
|------|------|---------|
| IMG-01 | A+ 第 1 屏主图 | 户外门廊场景 |
| IMG-02 | A+ 第 2 屏 | 抗 UV 材料示意 |
| ...  | ...  | ...     |

## 合规风险汇总
- 卖点 X：原表达 "100% no fade"，建议改为 "help reduce fading"
- 卖点 Y：原表达 "lifetime warranty"，建议改为 "designed for long-term use"
```

---

## 关键原则

1. **没证据的卖点必须剔除** — 不能让 AI 写漂亮废话
2. **合规风险必须标注** — AI 容易写过头
3. **图片需求必须列清单** — 给美工明确指引
4. **验证状态必须真实** — 供应链/测试/客户反馈来源要清晰
