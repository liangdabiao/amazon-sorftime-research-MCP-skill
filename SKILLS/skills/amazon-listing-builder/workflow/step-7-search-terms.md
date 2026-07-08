# 第七步：Search Terms（后台搜索词）

> **ST 不是垃圾桶**。它的作用是补充索引，不是把所有没放进标题的词都塞进来。

## 🚨 本步不调 MCP

本步基于**第一步完整词库 + 第四步最终标题 + 第五步五点**做差集运算（找出未在前台出现的词），不再调用 MCP 工具。

### 数据来源
- 完整词库：第一步 MCP 输出
- 前台已出现词：第四步标题 + 第五步五点
- ST 候选词：词库 - 前台词 = 后台补充词

---

## 一、ST 的真实价值

| 该做的 | 不该做的 |
|-------|---------|
| 放同义词、变体词、错拼词 | 重复标题已有的词 |
| 放次要场景词 | 放竞品品牌词 |
| 放补充索引词 | 堆砌不相关词 |
| 遵守 250 字节限制 | 超字段限制 |
| 用空格分词 | 用逗号分隔 |

---

## 二、ST 词源分类

把第一步的关键词分层词库重新分类：

| 词类 | 是否进 ST | 示例 |
|------|----------|------|
| 核心品类词（L1） | ❌ 已在前台 | artificial flowers, faux plants |
| 功能属性词（L2） | ❌ 已在前台 | UV resistant, fade resistant |
| 主场景词（L3） | ❌ 已在前台 | patio, garden, porch |
| 次场景词（L3 变体） | ✅ 进 ST | balcony, terrace, deck |
| 问题词（L4） | 部分进 ST | for outdoor planters, no watering |
| 规格词（L5） | ❌ 已在前台 | 12 bundles |
| **同义词** | ✅ 进 ST | faux greenery, fake plants |
| **变体词** | ✅ 进 ST | fake florals, silk flowers |
| **错拼词** | ✅ 进 ST | articifial flowers, fake flower |
| **次要场景** | ✅ 进 ST | cemetery, front door, backyard |

---

## 三、抗 UV 户外仿真植物 ST 示例

假设标题和五点已覆盖：artificial flowers, outdoor, UV resistant, patio, garden, porch, planters, 12 bundles, fade resistant, realistic。

**ST 候选词**：
```
faux greenery fake plants outdoor silk flowers front porch decor planter filler backyard terrace deck balcony cemetery window box summer decor wedding centerpiece no watering maintenance free decor realistic fake flower arrangement
```

**优化后（去重 + 控制字节）**：
```
faux greenery silk flowers fake plants front porch planter filler backyard terrace deck balcony cemetery window box summer wedding centerpiece low maintenance outdoor decor fake flower arrangement
```

---

## 四、字节限制与格式规范

| 站点 | 字节限制 | 分隔方式 |
|------|---------|---------|
| 美国站 | 250 字节 | 空格 |
| 欧洲站 | 250 字节 | 空格 |
| 日本站 | 100 字节（jp） | 空格 |

### 格式规则
1. 用 **空格** 分隔，**不要用逗号**
2. 全小写（节省字节）
3. 不要重复任何词
4. 单数/复数只放一次（系统会自动匹配）
5. 不要用引号、连字符、特殊符号

---

## 五、给 Codex 的提示词（本步专用）

> 输入：完整词库、当前标题、当前五点描述。
>
> 任务：
> 1. 找出标题和五点**已经出现**的关键词（这些不进 ST）
> 2. 从词库中筛选未在前台出现的词，作为 ST 候选
> 3. 按优先级排序：同义词 > 次场景 > 问题词变体 > 错拼词
> 4. 控制总字节在 250 以内（美国站）
> 5. 用空格分隔，全小写
> 6. 排除竞品品牌词、夸大词、不相关词
> 7. 输出 ST 文本 + 字节计数 + 已排除词清单（含原因）

---

## 六、合规红线

| 禁用 | 原因 |
|------|------|
| 竞品品牌名（其他卖家品牌） | 违反亚马逊品牌政策 |
| 促销词（free shipping, best seller, sale） | 平台禁止 |
| 主观夸大词（best, #1, top rated） | 合规风险 |
| 医疗/环保绝对词（cure, 100% eco） | 合规风险 |
| 重复前台已出现的词 | 浪费字节 |
| 任何不相关的热词 | 影响相关性 |

---

## 七、输出模板

```markdown
# Search Terms 草稿 — {产品名}

## ST 文本（已优化）
```
faux greenery silk flowers fake plants front porch planter filler backyard terrace deck balcony cemetery window box summer wedding centerpiece low maintenance outdoor decor fake flower arrangement
```

**总字节**：238 / 250

## 已排除词清单
| 词 | 原因 |
|----|------|
| artificial flowers | 标题已出现 |
| UV resistant | 五点已出现 |
| [其他品牌] | 竞品品牌词 |
| best | 夸大词 |

## 候选词优先级排序
1. 同义词：faux greenery, silk flowers
2. 次场景：terrace, deck, balcony, backyard, cemetery, window box
3. 问题词变体：low maintenance
4. 错拼词：（如适用）
```

---

## 八、检查清单

- [ ] 字节 ≤ 250（美国）/ ≤ 100（日本）
- [ ] 用空格分隔，无逗号
- [ ] 全小写
- [ ] 无重复
- [ ] 无竞品品牌词
- [ ] 无夸大词
- [ ] 无前台已出现的词
- [ ] 已排除词清单完整
