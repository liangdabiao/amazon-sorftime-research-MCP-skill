# 站点差异与豁免（site_overrides）

> 本文件汇总各站点 / 类目对 2026-07-27「75 字符 + 125 字符商品亮点」新规的差异与豁免。
> 供 `lint_title.py` 在按 `market` 取规则时引用，避免一刀切。
> 字段名与数值遵循 `rules.json.site_overrides` 与 `category_exempt`。

---

## 0. 配置入口

站点差异在 `rules.json` 中有两处配置：

```json
{
  "site_overrides": {
    "JP": {"recommended_max": 50},
    "ME": {"skip_75_rule": true}
  },
  "category_exempt": {
    "media_exempt_75": true,
    "media_categories": ["Books", "Music", "DVD", "Video", "Software"]
  }
}
```

`lint_title.py` 读取顺序：
1. 先按 `category` 查 `categories.json` 判定是否媒体豁免（命中则走 200 字符路径）。
2. 再按 `market` 查 `site_overrides` 叠加站点差异。
3. 最后按 `mode`（`strict_75` / `transition_200`）取最终上限。

---

## 1. 媒体类目豁免（已确认，官方明确）

### 1.1 配置

| 字段 | 值 | 状态 |
|---|---|---|
| `category_exempt.media_exempt_75` | **true** | ✅ 官方明确 |
| `category_exempt.media_categories` | `["Books","Music","DVD","Video","Software"]` | ✅ 官方明确 |

### 1.2 规则说明

- 媒体类目（图书 / 音乐 / DVD / 视频 / 软件）**不受 75 字符新规限制**。
- 7-27 后仍沿用各自独立的字符上限（`categories.json` 中 `Media` 条目：`exempt_75_rule: true, title_max: 200`）。
- 依据：亚马逊官方公告明确豁免。

### 1.3 skill 处理逻辑

```python
# categories.json 中 Media 条目
{
  "Media": {"exempt_75_rule": true, "title_max": 200}
}
```

- `lint_title.py` 命中 `category in media_categories` → 跳过 75 字符硬限，改用 `title_max: 200`。
- 但重复词 / 禁字符 / 促销词规则**仍然适用**（这些是全类目规则，非 75 字符专属）。

---

## 2. 日本站（JP）差异 —— ⚠️ 待验证

### 2.1 配置

| 字段 | 值 | 状态 |
|---|---|---|
| `site_overrides.JP.recommended_max` | **50** | ⚠️ **待验证** |

### 2.2 背景

- 行业普遍说法：日本站历史要求标题在全角 **50 文字以内**（约 100 字符）。
- 此说法来自中文卖家媒体汇总，**未直接抓取日本站 Seller Central 原文确认**。
- 即便属实，**2026-07-27 后统一为 75 字符**，该差异将消失。

### 2.3 7-27 后的处理建议

| 时间 | JP 站 `recommended_max` | 说明 |
|---|---|---|
| 7-27 前（过渡期） | **50**（待验证） | 沿用历史全角 50 文字说法，配置保留 |
| 7-27 后 | **75**（与其他站点一致） | 新规统一执行，差异消失 |

### 2.4 skill 处理逻辑

- `lint_title.py` 命中 `market == "JP"`：
  - `mode == "strict_75"` → 上限仍取 75（新规覆盖历史差异），但 `recommended_max` 取 50 作为更严的推荐值（告警线提前）。
  - `mode == "transition_200"` → `recommended_max` 取 50。
- **建议复核**：7-27 后抓取日本站 Seller Central 官方公告，确认是否完全统一为 75。

---

## 3. 中东站（ME）差异 —— ⚠️ 待验证

### 3.1 配置

| 字段 | 值 | 状态 |
|---|---|---|
| `site_overrides.ME.skip_75_rule` | **true** | ⚠️ **待验证** |

### 3.2 背景

- 行业媒体汇总：中东站（Souq）**暂不执行 75 字符新规**。
- 来源非亚马逊官方中东站公告，**建议以 Seller Central 中东站官方公告为准**。

### 3.3 skill 处理逻辑

- `lint_title.py` 命中 `market == "ME"` 且 `site_overrides.ME.skip_75_rule == true`：
  - **跳过 75 字符硬限校验**，改用 `transition_200` 上限（200 字符）。
  - 重复词 / 禁字符 / 促销词规则**仍然适用**。
- **建议复核**：上线前查 Seller Central 中东站（sellercentral.amazon.me 或对应域名）官方公告，确认豁免是否长期有效。

---

## 4. 美国站 / 欧洲站（默认基准）

| 站点 | 7-27 后上限 | recommended_max | 状态 |
|---|---|---|---|
| **US**（美国） | 75 | 60 | ✅ 官方确认 |
| **GB**（英国） | 75 | 60 | ✅ 各子站一致 |
| **DE**（德国） | 75 | 60 | ✅ 需对应**德语**本地化 |
| **FR**（法国） | 75 | 60 | ✅ 需对应**法语**本地化 |
| **IT**（意大利） | 75 | 60 | ✅ 需对应**意大利语**本地化 |
| **ES**（西班牙） | 75 | 60 | ✅ 需对应**西班牙语**本地化 |

> 欧洲站各子站字符上限一致，但 `language` 字段决定促销词黑名单与主观词黑名单的取值（`forbidden_promo_words` 按 `language` 取：en/zh 有内容，de/fr/ja 当前为空数组，待补充）。

---

## 5. 其他站点状态（未显式配置，走 _default）

以下站点在 `rules.json.site_overrides` 中**无显式配置**，按 `_default` 处理（即 75 字符新规全量适用）：

| 站点代码 | 站点 | 处理 |
|---|---|---|
| CA | 加拿大 | 走 `_default`（75） |
| IN | 印度 | 走 `_default`（75） |
| AU | 澳大利亚 | 走 `_default`（75） |
| BR | 巴西 | 走 `_default`（75） |
| MX | 墨西哥 | 走 `_default`（75） |
| JP | 日本 | **见 §2**（recommended_max=50，待验证） |
| AE | 阿联酋 | **可能归属中东站 ME 豁免范围，待确认** |
| SA | 沙特 | **可能归属中东站 ME 豁免范围，待确认** |

> ⚠️ AE（阿联酋）/ SA（沙特）是否享受 `ME` 同等待遇，未显式列出。当前 `site_overrides` 仅配置 `ME` 一个 key。
> **建议复核**：确认中东站豁免是否覆盖 AE + SA，还是仅限 ME。复核前，AE/SA 走 `_default`（75 字符）。

---

## 6. 例外类目完整清单 —— ⚠️ 待补全

### 6.1 已知例外

| 类目 | 字符上限 | 来源 | 状态 |
|---|---|---|---|
| 媒体（Books/Music/DVD/Video/Software） | 200（不受 75 限制） | 官方明确 | ✅ |
| 服装（Apparel） | 7-27 后统一 75；过渡期原 80-100 | 官方例外表 | ✅ 已纳入 75 新规 |

### 6.2 待补全

- 亚马逊官方「**商品名称长度标准例外情况**」完整列表未逐一抓取。
- skill 实现时**应将例外表做成可配置字典**（`categories.json`），而非硬编码。
- 当前 `categories.json` 中除 `Media` 外，其他类目均配置 `title_max_strict: 75`，即默认无例外。
- **建议复核**：上线前抓取 sellercentral 官方例外表完整内容，若有其他特殊类目（如某些工业品 / 定制品），补入 `categories.json`。

---

## 7. 后台 search terms 字节数 —— ⚠️ 待确认

| 说法 | 来源 | 状态 |
|---|---|---|
| ≤ **250 字节** | 多数行业源（Jungle Scout / Helium 10 / Keywords.am） | ✅ 采纳（`backend_search_terms.max_bytes: 250`） |
| ≤ **262 字节** | Captain Bi 引用 | ⚠️ 少数源 |

> 采用 **250 字节**（多数源共识）。建议以 Seller Central 后台填写框实际提示为准。

---

## 8. 待验证项汇总（上线前必须复核）

| # | 待验证项 | 当前配置值 | 建议复核方式 | 影响 |
|---|---|---|---|---|
| 1 | 日本站「全角 50 文字」是否为官方现行要求 | `JP.recommended_max: 50` | 抓取 sellercentral.amazon.co.jp 官方帮助页 | 影响 JP 站推荐线；7-27 后差异消失 |
| 2 | 中东站是否完全不执行 75 字符新规 | `ME.skip_75_rule: true` | 查 Seller Central 中东站公告 | 影响 ME 站是否走 75 校验 |
| 3 | AE / SA 是否享受 ME 同等待遇 | 未配置（走 `_default`） | 确认中东站范围定义 | 影响 AE/SA 站上限 |
| 4 | 后台 search terms 字节数 | `max_bytes: 250` | 以 Seller Central 后台提示为准 | 影响 backend 校验阈值 |
| 5 | 例外类目完整清单 | 仅 Media 显式豁免 | 抓取官方「商品名称长度标准例外情况」全表 | 影响其他类目是否有特殊上限 |
| 6 | 商品亮点 A9 权重 | `field_weights.highlights: 4 (TBD)` | 7-27 后抓取首批收录案例验证 | 影响 indexability 评分权重 |

> 以上 6 项在 `rules.json` / `indexability_rules.json` 中已标注 `TBD` 或配置了保守值，skill 可先按保守值上线，复核后再调。

---

**版本**：v1.0
