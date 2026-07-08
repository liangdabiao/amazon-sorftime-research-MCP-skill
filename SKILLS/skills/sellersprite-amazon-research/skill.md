---
name: sellersprite-amazon-research
description: 卖家精灵 Amazon 全链路数据调研 Skill。通过 43 个 MCP 数据工具完成选品分析、关键词研究、竞品监控、市场分析、定价策略、评论分析、广告优化、流量分析、Listing 优化和蓝海机会挖掘。触发场景：(1) 用户询问 Amazon 选品/市场/竞品分析 (2) 用户输入 /product-research, /market-analysis, /competitor-analysis, /keyword-research, /listing-optimizer, /traffic-analysis, /opportunity-finder, /review-insights, /pricing-strategy, /ad-optimizer 等命令 (3) 用户提及新品爆发、隐形爆款、ABA 增长词、低品牌垄断、评论分析等选品策略。适用于跨境电商卖家、Amazon 运营和产品开发决策。
---

# 卖家精灵 Amazon 数据调研

## 重要：MCP 连接配置

`.mcp.json` 必须使用以下格式（⚠️ 密钥通过 header 传入，不是 URL 参数）：

```json
{
  "mcpServers": {
    "sellersprite": {
      "url": "https://mcp.sellersprite.com/mcp",
      "headers": {
        "secret-key": "你的密钥"
      }
    }
  }
}
```

| 配置项 | 正确值 | 错误值 |
|--------|--------|--------|
| URL | `https://mcp.sellersprite.com/mcp` | `.../sse` 或 `.../mcp?key=xxx` |
| 认证方式 | `headers.secret-key` | URL 查询参数 `?key=` |

---

## 工具调用方式

### 方式 A：通过 MCP 客户端（推荐）

MCP 客户端直接调用工具：

```
mcp__sellersprite__<tool_name>
```

例: `mcp__sellersprite__product_research`

### 方式 B：通过 curl（无 MCP 客户端时备用）

```bash
curl -s -X POST "https://mcp.sellersprite.com/mcp" \
  -H "Content-Type: application/json" \
  -H "secret-key: <YOUR_KEY>" \
  -d '{
    "jsonrpc": "2.0", "id": 1, "method": "tools/call",
    "params": {
      "name": "<tool_name>",
      "arguments": { <扁平参数或{"request":{...}}> }
    }
  }'
```

### 方式 C：通过 Python（批量调用场景）

```python
import json, urllib.request
payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call",
    "params":{"name":"market_research","arguments":{"request":{
        "marketplace":"US","nodeIdPath":"...","topNum":10}}}}).encode()
req = urllib.request.Request("https://mcp.sellersprite.com/mcp", data=payload,
    headers={"Content-Type":"application/json","secret-key":"<KEY>"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    result = json.loads(data['result']['content'][0]['text'])
```

### 方式 D：通过 mcp_call.py 工具脚本（项目内预置）

```bash
python3 mcp_call.py <tool_name> '{"param1":"value1"}'
```

---

## 关键：参数传递模式

### 模式 A："扁平参数"（少部分工具）

直接在顶层传字段。例如 `asin_detail`、`keyword_research_trends`、`review`：

```json
{"marketplace": "US", "asin": "B0XXXXX"}
```

### 模式 B："request 嵌套对象"（大部分工具）

绝大多数筛选/搜索类工具（market_research、product_research、keyword_miner 等）的**唯一必填参数是 `request`**，其值为一个嵌套对象：

```json
{
  "request": {
    "marketplace": "US",
    "nodeIdPath": "11091801:11974521:8882489011:11974711",
    "topNum": 10,
    "size": 50
  }
}
```

**MCP 客户端调用时**，`arguments` 写为 `{"request": {...}}`。

### 识别方法
查看工具的 `required` 字段：
- `required=["marketplace","asin"]` → 扁平参数
- `required=["request"]` → 嵌套对象

---

## 全局参数默认值

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `marketplace` | `US` | 目标站点：US/JP/UK/DE/FR/IT/ES/CA/IN |
| `matchType` | `2` | 1=词组匹配 2=模糊匹配 3=精准匹配 |
| `size` | `50` | 每页返回条数（最大 100） |

---

## 字段映射与刻度陷阱（重要）

### 改名规律（网页 API → MCP 响应）
- `totalUnits` → **`units`**（月销量）
- `totalAmount` → **`revenue`**（月销售额）
- `reviews` → **`ratings`**（评分数）
- `bsrRank` → **`bsr`**（BSR 排名）
- `sellerType` → **`fulfillment`**（配送方式）
- `*Ratio` → `*Proportion`，`HeadListing*` → `Top*`

### 刻度陷阱
- **集中度字段**（`top*Crn`/`l*NewRatio`）为 **0~1 小数**，展示需 ×100
- **`returnRatio`/`*Proportion`** 已是 0~100 百分数，不再换算
- **`purchaseRate`/`cvsShareRate`/`monopolyClickRate`** 为 0~1，展示 ×100
- **`supplyDemandRatio`** 已是真实比值（如 78.88），不换算
- **多值参数**（brands/sellers/fulfillment）传逗号字符串，非数组

### 类名翻译陷阱 ⚠️
product_node 返回的 `nodeLabelLocale`（中文翻译）**不可靠**，常见错误：
| 英文名 | 错误翻译 |
|--------|---------|
| Microphones | 显微镜 ❌ |
| Microphone Accessories | 辅料 ❌ |
| Hand Percussion | 手部打击乐 ❌ |
| Stands | 摊位 ❌ |
| Sound | 声音 ❌ |

**始终以 `nodeLabelPath`（英文完整路径）为准。**

---

## MCP 响应解析要点

### 标准响应结构
```json
{
  "jsonrpc": "2.0", "id": 1,
  "result": {
    "content": [{"type": "text", "text": "{\"code\":\"OK\",\"data\":...}"}],
    "isError": false
  }
}
```

`result.content[0].text` 是卖家精灵 API 的 JSON 字符串，**需二次解析**。

### 数据组织结构差异
| 工具类型 | data 结构 | 示例 |
|---------|-----------|------|
| `market_research` | `{ items: [...] }` | 子市场数组在 `items` |
| `market_brand_concentration` | `[{...}]`（直接数组） | 品牌列表直接返回 |
| `market_price_distribution` | `{ items: [...] }`（嵌套） | 价格区间在 `items` |
| `product_node` | `[{...}]`（直接数组） | 节点列表直接返回 |

**安全取值**：
```python
def safe_items(data):
    if isinstance(data, dict): return data.get('items', [])
    if isinstance(data, list): return data
    return []
```

### ⚠️ 实际 API 响应字段陷阱（实测发现，与文档不一致）

部分工具的 JSON 响应字段名与文档描述不同，**必须按实际响应取值**：

| 工具 | 你以为的字段 | 实际字段 | 后果 |
|------|------------|---------|------|
| `keyword_research_trends` | `month`, `searches` | **`time`**, **`search`** | 全显示 N/A |
| `keyword_research_trends` | `growth`, `change` | **`chainGrowth`**(环比), **`yearlyGrowth`**(同比) | 无增长率 |
| `keyword_research_trends` | `purchaseCount` | **`purchase`** | 无购买数据 |
| `aba_research_trend` | `clickShareRate`, `conversionShareRate` | **没有这两个字段** | 全显示 0% |
| `aba_research_trend` | `month` | **`label`**, `date`, `searches`, `rank` | 无趋势 |
| `traffic_keyword_stat` | `searchTotal`, `naturalTotal` | **`keywords`**(总数), **`ranks`**(有排名), **`ads`**(有广告) | 全显示空 |
| `review` | `body`, `createTime` | **`content`**, **`date`** | 评论内容为空 |
| `keepa_info` | `currentPrice`, `bsrHistory` | **`buyBox`**([{timePoint,value}]), **`bsr`**([{timePoint,value}]) | 全显示空 |
| `traffic_source` | `request` 嵌套对象 | 实际需**扁平参数** + `"q": "asin"` | HTTP 200 但返回 `q is required` |
| `keyword_research` | 传入 `keyword` 参数 | 返回按搜索量排序的全局关键词，无视筛选 | 数据全为不相关词 |

### review 工具采样限制（重要）
- `review` 工具 **每次最多返回 20 条**（size=100 也会被限制）
- 所以评分分布是 **样本**，不代表总体
- 报告中必须注明："⚠️ 仅展示最近 20 条评论，不代表总体分布"
- 情感分析和差评主题也要加"基于样本"限定

### keepa 时间序列数据提取
keepa_info 返回的价格/BSR 均为 `[{timePoint: timestamp, value: number}]` 格式数组：
```python
price_data = keepa.get('buyBox', [])
if price_data:
    prices = [p['value'] for p in price_data if p.get('value', 0) > 10]
    current_price = prices[-1] if prices else 'N/A'
    avg_price = sum(prices)/len(prices) if prices else 'N/A'
```

### HTML 实体解码
API 返回的标题/描述中可能包含 `&amp;` `&quot;` `&lt;` 等 HTML 实体，必须解码：
```python
import html
clean_title = html.unescape(raw_title)
```

---

## 一、综合分析工作流

通过 `/命令` 调用，执行多步骤分析。详细步骤见 `comprehensive/` 下对应文件。

| 命令 | 名称 | 核心工具 | 详见 |
|------|------|----------|------|
| `/product-research` | 智能选品助手 | `product_research` + `product_node` | `comprehensive/product-research.md` |
| `/market-analysis` | 市场全景分析 | `market_research` + 分布工具集 | `comprehensive/market-analysis.md` |
| `/competitor-analysis` | 竞品深度拆解 | `asin_detail` + `traffic_keyword` | `comprehensive/competitor-analysis.md` |
| `/keyword-research` | 关键词选品研究 | `keyword_research` + `keyword_miner` | `comprehensive/keyword-research.md` |
| `/listing-optimizer` | Listing 优化诊断 | `traffic_listing` + `keyword_order` | `comprehensive/listing-optimizer.md` |
| `/traffic-analysis` | 流量结构分析 | `traffic_source` + `traffic_keyword_stat` | `comprehensive/traffic-analysis.md` |
| `/opportunity-finder` | 蓝海机会挖掘 | `aba_research_trend` + `google_trend` | `comprehensive/opportunity-finder.md` |
| `/review-insights` | 买家评论洞察 | `review` + NLP 分析 | `comprehensive/review-insights.md` |
| `/pricing-strategy` | 定价策略分析 | `market_price_distribution` | `comprehensive/pricing-strategy.md` |
| `/ad-optimizer` | 广告投放优化 | `keyword_order` + `traffic_keyword` | `comprehensive/ad-optimizer.md` |

---

## 二、战术选品策略卡

对话中引用名称触发。详细参数见 `tactical/` 下对应文件。

### 新品爆发型
| 策略 | 核心工具 | 逻辑 | 详见 |
|------|----------|------|------|
| 新品快速爆发 | `product_research` | 上架≤2月+销量≥300+Review≤100 | `tactical/new-product-burst.md` |
| 隐形爆款 | `product_research` | 上架≤3月+销量≥500+Review≤50 | `tactical/hidden-bestseller.md` |

### 关键词趋势型
| 策略 | 核心工具 | 逻辑 | 详见 |
|------|----------|------|------|
| ABA 高增长趋势词 | `keyword_research` | 近3月持续增长+点击不集中 | `tactical/aba-high-growth-trend.md` |
| 流量分散关键词 | `keyword_miner` | 搜索≥5000+集中度<50% | `tactical/low-monopoly-keyword.md` |
| 标题密度漏洞 | `keyword_miner` | 标题密度≤5的长尾词 | `tactical/title-density-gap.md` |

### 产品缺陷型
| 策略 | 核心工具 | 逻辑 | 详见 |
|------|----------|------|------|
| 热销低评分产品 | `product_research` | 月销≥1000+评分≤4.2 | `tactical/hot-low-rating.md` |
| 评论语义分析 | `review` | 差评NLP聚类→改良指南 | `tactical/review-sentiment.md` |

### 类目结构型
| 策略 | 核心工具 | 逻辑 | 详见 |
|------|----------|------|------|
| 低品牌垄断类目 | `market_research` | 品牌集中度<45% | `tactical/low-brand-monopoly.md` |
| 高新品占比市场 | `market_research` | 新品占比>5%+新品仍出单 | `tactical/high-new-product-ratio.md` |
| 高毛利轻小品 | `product_research` | FBA≤$4+毛利≥50% | `tactical/high-margin-lightweight.md` |

### 流量防伪型
| 策略 | 核心工具 | 逻辑 | 详见 |
|------|----------|------|------|
| 自然流量反查 | `traffic_source` | 自然流量占比>60% | `tactical/natural-traffic-audit.md` |
| 变体拆解模型 | `asin_detail` | 找未被覆盖的变体缺口 | `tactical/variant-gap-analysis.md` |

### 机会捕捉型
| 策略 | 核心工具 | 逻辑 | 详见 |
|------|----------|------|------|
| 本土溢价降维 | `product_research` | 美国卖家+高价+高销 | `tactical/local-premium-disruption.md` |
| FBM 拦截 | `product_research` | FBM发货+月销≥300 | `tactical/fbm-intercept.md` |
| 低质量 Listing 高销量 | `product_research` | LQS≤60+月销≥400 | `tactical/poor-listing-winner.md` |
| 高客单长尾 | `keyword_miner` | 均价≥$80+搜索量适中 | `tactical/high-ticket-long-tail.md` |
| 季节前置爆破 | `keyword_miner` | 历史同期环比增长>100% | `tactical/seasonal-prepositioning.md` |

---

## 三、MCP 工具参考

详细参数、响应字段映射和陷阱见 `reference/` 下文件：

| 参考文件 | 对应工具 | 已验证 |
|----------|----------|--------|
| `reference/product_research.md` | `product_research` | ✅ |
| `reference/market_research.md` | `market_research` + 11 分布工具 | ✅ |
| `reference/traffic_keyword.md` | `traffic_keyword` + `traffic_extend` | ✅ |
| `reference/competitor_lookup.md` | `competitor_lookup` | ✅ |
| `reference/keyword_miner.md` | `keyword_miner` + `keyword_research` | ✅ |
| `reference/asin_detail.md` | `asin_detail` + `keepa_info` 等 ASIN 工具 | |
| `reference/tools_index.md` | 全部 42 个工具清单 + 参数模式 | ✅ 已更新 |

---

## 四、输出格式（必读：必须保存为文件）

### HTML 可视化报告生成（固定步骤，不可跳过）

完成 `market_report.md` 后，**必须自动生成**对应的 `market_report.html`：

1. **数据源** — 以刚完成的 `market_report.md` 为数据源，不额外调 API
2. **全面展示** — 覆盖报告的每个核心维度（概览、销量、流量、关键词、竞争、市场、评论、价格、SWOT、行动建议）
3. **图表呈现** — 关键数据用 Canvas 图表展示（价格/BSR 趋势、对比柱状图、趋势线等）
4. **设计风格** — 深色专业主题、配色统一、响应式适配、交互流畅
5. **输出** — 保存到与 MD 相同的目录 `{类别名}/market_report.html`

> 如果用户明确说"不需要 HTML"可以跳过，否则必须生成。

### 铁律：报告禁止仅打印到控制台

所有分析报告**必须保存为文件**，不得只 `print`/`echo` 到控制台。用户看不到控制台输出。

### 文件保存规范

| 文件 | 必存 | 命名规则 | 说明 |
|------|:----:|---------|------|
| 分析报告 | ✅ 必须 | `{类别名}/market_report.md` | 结构化 Markdown，用户可直接阅读 |
| HTML 可视化报告 | ✅ **必须**（新增） | `{类别名}/market_report.html` | **生成 MD 报告后自动配套生成**，单文件纯 HTML+CSS+JS，基于 MD 数据，无需额外 API 调用 |
| 原始数据 | ✅ 必须 | `{类别名}/research_data.json` | API 原始返回，供后续二次分析 |

**目录命名**：以调研的类别名为目录名，如 `wirelessinstruments/`、`bluetooth-speaker/`。

### ⚡ 铁律：MD 报告完成后必须生成 HTML 报告

每次完成 `market_report.md` 后，**必须立即** 基于 MD 内容生成对应的 `market_report.html`。这是不可跳过的步骤，原因：

1. **用户体验** — HTML 报告包含可视化图表（Canvas 折线图/柱状图/趋势图），比纯文本直观得多
2. **数据验证** — 图表能暴露 Markdown 表格中不易察觉的数据异常
3. **分享便利** — 非技术背景的团队成员可直接在浏览器打开查看

> 注意：HTML 报告是 MD 报告的 **可视化增强版本**，不是替代。两者共存，各有用途。

### 报告内容结构

所有报告必须包含：
1. **筛选口径** — 工具参数、数据月份、ASIN/关键词、Review 采样说明
2. **KPI 摘要** — 关键指标高亮
3. **多维分析** — 表格 + 评分卡 + 洞察
4. **分级结论** — 推荐/谨慎/不推荐

### 报告质量检查清单（生成后必须自查）

报告保存前，逐项检查以下内容，确保没有质量问题：

| # | 检查项 | 说明 |
|---|--------|------|
| 1 | **标题/描述 HTML 实体** | 检查 `&amp;` `&quot;` 等是否用 `html.unescape()` 解码 |
| 2 | **销量汇总有重叠** | 多卖家/多变体叠加的合计要加⚠️注解 |
| 3 | **流量来源工具容错** | `traffic_source` 可能不返回数据，必须有 fallback |
| 4 | **ABA 字段正确** | 用 `searches`/`rank`，不要用不存在的 `clickShareRate` |
| 5 | **趋势字段正确** | 用 `time`/`search`/`chainGrowth`/`yearlyGrowth` |
| 6 | **Review 样本说明** | 必须注明"仅 20 条样本"，评分分布不能代表总体 |
| 7 | **关键词相关性过滤** | 高价值/蓝海词列表必须排除不相关泛词 |
| 8 | **品牌词不要列为机会** | 纯品牌词（"dji"等）不应出现在蓝海表中 |
| 9 | **Keepa 数据展示** | 调用 keepa_info 后必须在报告中展示 |
| 10 | **ASIN vs 市场数据区分** | 每个表格注明数据是 ASIN 自身的还是搜索市场的 |

### 数值格式化

销量/销售额千分位（`12,345`）、占比/评分 1 位小数（`23.4%`）、价格 `$X.XX`。注意 0~1 刻度换算。

---

## 五、推荐组合链路

```
品类扫描 -> 低品牌垄断 / 高新品占比（找蓝海类目）
    ↓
关键词挖掘 -> ABA增长词 / 流量分散词 / 标题密度漏洞（找增长词）
    ↓
竞品锁定 -> 新品爆发 / 隐形爆款 / 热销低评分（找目标竞品）
    ↓
竞品验真 -> 自然流量反查（流量防伪）
    ↓
痛点提炼 -> 评论语义分析（产品改进）
    ↓
产品开发 -> 变体拆解 + 高毛利轻小（利润验证）
```

---

## 六、实操技巧（实测经验）

### 类目节点查找技巧
- 用英文关键词搜索（`"wireless microphone"` 比 `"无线麦克风"` 结果更准）
- 找到后记录 `nodeIdPath` 供后续调用
- 父节点数据可能包含自身汇总行，取数据时注意过滤

### 批处理策略
- 市场全景分析至少调用 13 个工具（market_research + 12 分布工具）
- 工具间无数据依赖，可以全并行
- 关注响应中的 `code: "OK"` 字段判断调用成功

### 常见故障排查
| 现象 | 原因 | 解决方法 |
|------|------|---------|
| 返回 `secret_invalid` | key 配置错误 | 检查 header 名是 `secret-key`，非 `Authorization` |
| 数据全是 0 | 节点是根节点 | 必须使用叶子节点 nodeIdPath |
| HTTP 400 | 请求格式错误 | 检查 `request` 嵌套是否正确 |
| **`q is required`** | `traffic_source` 用了 `request` 嵌套 | 改用**扁平参数** + `"q": "asin"` |
| **返回不相关数据** | `keyword_research` 传了 keyword 但忽略筛选 | 该工具会忽略 keyword 参数，改用 `keyword_miner` 替代 |
| 翻译名称怪 | `nodeLabelLocale` 不可靠 | 使用英文 `nodeLabelPath` |
| 报告显示 N/A 或全 0 | 字段名与文档不符 | 查本文「实际 API 响应字段陷阱」表，用实际字段名 |
| ABA/趋势数据空白 | 用了 `clickShareRate`/`conversionShareRate` | 实际只有 `searches`/`rank` 字段 |
| 评论只有 20 条 | review 工具采样限制 | size 参数无效，最多返回 20 条 |
| 趋势月份显示 N/A | 用了 `month` 或 `label` | keyword_research_trends 用 `time` |
| 报告中有 `&amp;` | HTML 实体未解码 | 必须用 `html.unescape()` |
| Keepa 数据空白 | 用了 `currentPrice` 等不存在字段 | 用 `buyBox` / `bsr` 数组，内部是 `{timePoint, value}` |

---

## 七、实测经验与参数陷阱

> 以下为 2026-07-05 JOYO JW-03 深度调研中实测发现的工具行为差异，已修复到文档中。记录在此供未来快速参考。

### 7.1 连接与认证

| 经验 | 说明 |
|------|------|
| **Accept header 必须** | 调用 MCP endpoint 时必须传 `Accept: application/json, text/event-stream`，仅传 `application/json` 会 HTTP 400 |
| **密钥传 header** | `secret-key` 放 headers，非 URL 参数，非 `Authorization` |
| **SSE 方案不可用** | SDK SSE 连接 /sse → 阿里云 Tengine CDN session affinity 导致 302/504 Gateway Timeout，放弃。始终用 HTTP POST 到 `/mcp` |

### 7.2 工具参数模式实测纠正

| 工具 | 文档声称 | 实测正确方式 | 后果 |
|------|---------|-------------|------|
| `traffic_source` | `request` 嵌套对象 | **扁平参数** + `"q": "asin"`：`{"marketplace":"US","asin":"B0XXX","q":"asin"}` | HTTP 200 但返回 `q is required` |
| `traffic_keyword_stat` | `request` 嵌套对象 | **扁平参数**：`{"marketplace":"US","asin":"B0XXX"}` | 空数据 |
| `keyword_research` | 传 `keyword` 筛选 | **该工具完全忽略 keyword 参数**，返回全局热词按搜索量排序 | 数据全为不相关词 |

### 7.3 流量工具注意事项

- `traffic_source` 即使调用成功，`asinInfo` 也可能返回**无关产品的流量**（实测返回了空气净化器、SD 卡等），数据不可信赖
- 流量来源分析建议使用 `traffic_keyword` + `traffic_keyword_stat` 组合来代替
- `traffic_listing_stat` 和 `traffic_listing` 正常工作，可用 `request` 嵌套对象

### 7.4 评论工具缺陷

- `review` 工具 **size 参数无效**，最多永远返回 20 条
- 所以评分分布永远是样本，报告中必须注明"仅最近 20 条样本"
- 字段名：`content`（非 `body`）、`date`（非 `createTime`）

### 7.5 Keepa 数据处理

- `keepa_info` 返回的是时间序列数组：`buyBox: [{timePoint, value}]`、`bsr: [{timePoint, value}]`
- 不存在 `currentPrice` 或 `bsrHistory` 字段
- 提取当前价：取 `buyBox` 数组最后一个 `value`；BSR 同理

### 7.6 类目节点注意事项

- `product_node` 返回的 `nodeLabelLocale`（中文翻译）**经常错误**（Microphones → 显微镜）
- 始终以 `nodeLabelPath`（英文完整路径）为准
- 必须使用**叶子节点** `nodeIdPath`，父节点返回全 0 数据

### 7.7 混合类目识别

某些子类目下混合了不同类型的商品（如 "Electric Guitar Electronics" 下既有 $5-15 的电子元件，也有 $40+ 的无线吉他系统）。分析时需注意：

1. **价格分布会两极分化** — 不代表目标产品的合理定价区间
2. **品牌集中度可能失真** — 高价品牌销售额占比虚高
3. **解决方法**：手动标注类目内真实竞品，单独圈定可比价格区间

### 7.8 数据质量标注规范

报告中凡是遇到以下情况，必须加 ⚠️ 标注：

| 场景 | ⚠️ 原因 |
|------|---------|
| 多 ASIN 销量汇总 | 多变体/多卖家合计可能重叠 |
| 价格 vs 销量交叉表合计不一致 | 统计口径不同或重复计数 |
| 品牌集中度工具间差异 | `market_research` 和 `market_brand_concentration` 可能口径不同 |
| Google Trends 异常峰值 | 可能是短期事件（新品发布/KOL），不代表长期趋势 |
| 评论评分分布 | review 仅 20 条样本，不能代表总体 |
| 关联流量数据 | `traffic_listing_stat` 关联流量为快照值，非月度累计 |

---

## 八、报告质量检查清单

> 报告保存前，逐项检查以下内容，确保没有质量问题。此清单为生产报告的最后一道门禁。

### 8.1 数据完整性检查

| # | 检查项 | 说明 |
|---|--------|------|
| 1 | **报告和原始数据均已保存** | `market_report.md` + `research_data.json` 都必须在 `{类别目录}/` 下 |
| 2 | **至少调用 3+ 工具** | 单一工具的报告结论不可靠，must cross-reference |
| 3 | **流量来源数据有 fallback** | `traffic_source` 可能失败，必须有替代方案（traffic_keyword + traffic_keyword_stat） |
| 4 | **Keepa 数据已展示** | 调用 `keepa_info` 后必须在报告中展示价格/BSR 历史 |
| 5 | **谷歌趋势已调用** | 大型调研必须包含 Google Trends 数据进行外部验证 |

### 8.2 字段正确性检查

| # | 检查项 | 说明 |
|---|--------|------|
| 6 | **趋势字段使用正确** | 用 `time`/`search` 非 `month`/`searches`；`chainGrowth`(环比) 非 `growth` |
| 7 | **ABA 字段使用正确** | 用 `searches`/`rank`，**不要**用 `clickShareRate`/`conversionShareRate`（不存在） |
| 8 | **刻度转换正确** | 集中度 0~1 → ×100；`purchaseRate` 0~1 → ×100；`returnRatio` 已是百分数不再换算 |
| 9 | **HTML 实体已解码** | `&amp;` `&quot;` 等必须用 `html.unescape()` 解码 |
| 10 | **Review 样本已注明** | 必须标注"仅最近 20 条样本"，评分分布不具总体代表性 |

### 8.3 逻辑正确性检查

| # | 检查项 | 说明 |
|---|--------|------|
| 11 | **关键词列表排除了品牌词** | 纯品牌词（"dji"、"lekato"等）不应列为蓝海机会 |
| 12 | **关键词列表排除了不相关泛词** | 高价值/蓝海词列表必须人工过滤无关词 |
| 13 | **ASIN vs 市场数据区分** | 每个表格注明数据是 ASIN 自身的还是搜索市场的 |
| 14 | **混合类目已识别并标注** | 如 $5-15 元件 + $40+ 系统的混合类目，需加 ⚠️ 说明 |
| 15 | **销量汇总重叠已标注** | 多卖家/多变体叠加的合计要加 ⚠️ |

### 8.4 格式规范检查

| # | 检查项 | 说明 |
|---|--------|------|
| 16 | **数值格式化** | 销量/销售额千分位（`12,345`），占比/评分 1 位小数（`23.4%`），价格 `$X.XX` |
| 17 | **表格可读性** | Markdown 表格对齐（`:---` 左对齐 `:---:` 居中 `---:` 右对齐） |
| 18 | **标题层级合理** | 使用 `##` / `###` / `####` 层级结构，不超过 4 级 |
| 19 | **筛查口径已记录** | 报告中必须标注：调用工具列表、数据月份、ASIN/关键词、采样说明 |
| 20 | **数据质量警告** | 数据异常处必须使用 ⚠️ 标注（参考 7.8 节） |

### 8.5 发布前最终确认

- [ ] 以上 20 项检查已逐项通过
- [ ] `research_data.json` 已保存且包含所有 API 原始返回
- [ ] 报告包含筛选口径、KPI 摘要、多维分析、分级结论四要素
- [ ] 无仅打印到控制台的调试输出
- [ ] **`market_report.html` 已生成** — 在 `market_report.md` 同级目录，包含图表可视化
