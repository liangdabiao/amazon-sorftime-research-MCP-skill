# 卖家精灵 MCP 集成方法

> 本项目已配置 sellersprite MCP（`.mcp.json`）。本文件说明如何调用各工具获取真实数据。

---

## 一、连接配置（已完成）

`.mcp.json`：
```json
{
  "mcpServers": {
    "sellersprite": {
      "url": "https://mcp.sellersprite.com/mcp",
      "headers": {
        "secret-key": "<YOUR_KEY>"
      }
    }
  }
}
```

**关键**：
- URL 必须是 `https://mcp.sellersprite.com/mcp`（不是 `/sse`）
- 密钥通过 `headers.secret-key` 传入（不是 URL 参数）

---

## 二、调用方式

### 方式 A：MCP 客户端（推荐）
直接调用 `mcp__sellersprite__<tool_name>`。

### 方式 B：curl（备用）
```bash
curl -s -X POST "https://mcp.sellersprite.com/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "secret-key: <YOUR_KEY>" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call",
       "params":{"name":"<tool>","arguments":{...}}}'
```

### 方式 C：Python（批量场景）
```python
import json, urllib.request
payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call",
    "params":{"name":"keyword_miner","arguments":{"request":{
        "marketplace":"US","keyword":"artificial flowers"}}}}}).encode()
req = urllib.request.Request("https://mcp.sellersprite.com/mcp",
    data=payload,
    headers={"Content-Type":"application/json",
             "Accept":"application/json, text/event-stream",
             "secret-key":"<KEY>"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    result = json.loads(data['result']['content'][0]['text'])
```

---

## 三、本 Skill 常用工具映射

### 第一步：关键词分层词库

| 数据需求 | 工具 | 参数模式 |
|---------|------|---------|
| 关键词挖掘 | `keyword_miner` | `request` 嵌套 |
| 趋势验证 | `keyword_research_trends` | 扁平参数 |
| 竞品关键词反查 | `traffic_keyword` | `request` 嵌套 |
| 竞品出单词 | `keyword_order` | `request` 嵌套 |

### 第二步：用户问题库

| 数据需求 | 工具 | 参数 |
|---------|------|------|
| 竞品评论（差评主题） | `review` | `{"marketplace":"US","asin":"B0XXX"}`（扁平） |
| 竞品 Listing（QA 不支持 MCP，前台手动抓） | `asin_detail` | 扁平 |

> ⚠️ `review` 每次最多返回 20 条，是样本数据。

### 第三步：卖点证据库

主要靠人工：供应链信息、产品规格、测试数据、认证材料。
**卖家精灵不提供产品内部数据**。

### 第四步：标题、第五步：五点、第六步：A+
基于前三步数据生成，**不需要直接调用 MCP**。

### 第七步：Search Terms

基于第一步词库，对比前台已出现词，**不需要直接调用 MCP**。

### 第八步：QA
基于第二步问题库，**不需要直接调用 MCP**。

### 上线后迭代

| 数据需求 | 工具 |
|---------|------|
| 当前 Listing 流量诊断 | `traffic_listing` |
| 关键词出单表现 | `keyword_order` |
| 价格分布 | `market_price_distribution` |

---

## 四、关键陷阱（已踩过的坑）

### 陷阱 1：keyword_research 忽略 keyword 参数
- 现象：传 `keyword` 参数后，返回全球热词，不相关
- 解决：**用 `keyword_miner` 替代**

### 陷阱 2：keyword_research_trends 字段名
- 文档说：`month` / `searches` / `growth`
- 实际：`time` / `search` / `chainGrowth`（环比）/ `yearlyGrowth`（同比）

### 陷阱 3：review 限制
- `size` 参数无效，**最多返回 20 条**
- 评分分布是样本，不代表总体
- 字段名：`content`（非 body）、`date`（非 createTime）

### 陷阱 4：ABA 工具字段
- aba_research_trend 只有 `searches` / `rank`，没有 `clickShareRate` / `conversionShareRate`

### 陷阱 5：traffic_source 参数
- 文档说用 `request` 嵌套
- 实际需要**扁平参数** + `"q": "asin"`

### 陷阱 6：刻度转换
- 集中度字段（top*Crn / l*NewRatio）是 0~1 小数，展示 ×100
- purchaseRate / cvsShareRate / monopolyClickRate 是 0~1，展示 ×100
- returnRatio / *Proportion 已是 0~100 百分数，不再换算

### 陷阱 7：nodeLabelLocale 不可靠
- `Microphones` → 错误翻译成"显微镜"
- 始终用 `nodeLabelPath`（英文完整路径）

### 陷阱 8：keepa_info 字段
- 不存在 `currentPrice` / `bsrHistory`
- 用 `buyBox: [{timePoint, value}]` 和 `bsr: [{timePoint, value}]`

---

## 五、调用示例

### 示例 1：扩展关键词（第一步）
```python
import json, urllib.request

def call_mcp(tool, args):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call",
        "params":{"name":tool,"arguments":args}}).encode()
    req = urllib.request.Request("https://mcp.sellersprite.com/mcp",
        data=payload,
        headers={"Content-Type":"application/json",
                 "Accept":"application/json, text/event-stream",
                 "secret-key":"<YOUR_KEY>"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(json.loads(resp.read())['result']['content'][0]['text'])

# 关键词扩展
result = call_mcp("keyword_miner", {"request":{
    "marketplace":"US",
    "keyword":"artificial flowers outdoor"
}})
print(result)
```

### 示例 2：抓竞品评论（第二步）
```python
# 获取竞品 ASIN 评论
result = call_mcp("review", {
    "marketplace":"US",
    "asin":"B0XXXXXXX"
})
# 注意：最多返回 20 条，是样本
```

### 示例 3：竞品关键词反查（第一步补充）
```python
result = call_mcp("traffic_keyword", {"request":{
    "marketplace":"US",
    "asin":"B0XXXXXXX"
}})
```

---

## 六、MCP 数据缺失时的处理

如果某些数据 MCP 拿不到（如自己的广告搜索词报告、客服记录），**必须由人工补充**，不能让 AI 编造。

### 数据缺失标注规范

```markdown
## 数据需求清单

| 数据 | 来源 | 状态 |
|------|------|------|
| 关键词搜索量 | keyword_miner | ✅ 已获取 |
| 竞品评论 | review | ✅ 已获取（样本 20 条） |
| 自己的广告搜索词报告 | 亚马逊后台 | ⚠️ DATA_MISSING（人工补充） |
| 客服记录 | 客服系统 | ⚠️ DATA_MISSING（人工补充） |
| 供应链材料 | 工厂 | ⚠️ DATA_MISSING（人工补充） |
```

---

## 七、推荐调用顺序

```
1. keyword_miner → 关键词池
2. keyword_research_trends → 趋势验证
3. traffic_keyword (竞品 ASIN) → 竞品出单词
4. asin_detail (竞品 ASIN) → 竞品 Listing 结构
5. review (竞品 ASIN) → 差评主题
6. market_price_distribution → 定价参照
```

6 次调用即可拿到第一步和第二步的核心数据。

---

## 八、引用

更多细节参见 `sellersprite-amazon-research` skill 的：
- `skill.md` — 42 个工具完整清单
- `reference/tools_index.md` — 工具索引
- `comprehensive/listing-optimizer.md` — Listing 诊断流程
