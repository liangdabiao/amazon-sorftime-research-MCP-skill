# 合规 + 关键词 + 语义 + 转化 四项校验报告

> 校验对象：草稿 A（推荐上线版本）
> 校验依据：Amazon TOS、Cosmo 语义算法、Alexa/Rufus 对话式购物逻辑

---

## 一、合规检查（Amazon TOS）

| 检查项 | 状态 | 说明 |
|---|:---:|---|
| 标题 ≤ 200 字符 | ✅ | 180 字符 |
| 标题无促销词（Best/Cheap#1） | ✅ | 无违规促销词 |
| 标题无主观评价（"amazing"） | ✅ | 客观描述 |
| 五点无保证词（"warranty"在五点） | ⚠️ | 五点 5 提及"12-month warranty" — **建议改为 "backed by LEKATO's responsive US seller support"** 避免触发保证敏感词审查 |
| 五点无医疗/治疗词 | ✅ | 无 |
| ST 无品牌名侵权 | ✅ | joyo/xvive 是竞品品牌词，ST 中可用作索引但**不可投放 SP 广告匹配竞品品牌**（Amazon 政策因站点而异，US 站允许但建议监控 ACOS） |
| 图片合规 | ✅ | 无 |
| A+ 不诋毁竞品 | ⚠️ | "Why pay $200+ for a Shure or Xvive" 五点 5 表达直接，**建议改为 "Why pay premium prices when most gigging guitarists can't hear the difference?"** 避免点名 |

**合规风险等级**：🟢 低（修正后）

---

## 二、关键词覆盖检查

| 核心词 | 标题 | 五点 | A+ | ST | 覆盖? |
|---|:---:|:---:|:---:|:---:|:---:|
| wireless guitar system | ✅ | ✅ | ✅ | - | ✅ |
| wireless guitar transmitter receiver | ✅ | ✅ | ✅ | - | ✅ |
| guitar wireless | - | ✅ | ✅ | - | ✅ |
| wireless guitar | - | ✅ | ✅ | - | ✅ |
| **5.8 ghz wireless guitar system** | ✅ | ✅ | ✅ | - | ✅ |
| wireless guitar transmitter | ✅ | ✅ | ✅ | - | ✅ |
| lekato wireless guitar system | ✅ | - | - | - | ✅ |
| joyo wireless guitar system | - | - | - | ✅ | ✅ |
| wireless bass guitar system | ✅ | ✅ | ✅ | ✅ | ✅ |
| church worship guitar wireless | ✅ | ✅ | ✅ | ✅ | ✅ |
| bluetooth guitar transmitter (误搜) | - | - | - | ✅ | ✅ |
| sistema inalámbrico para guitarra | - | - | - | ✅ | ✅ |

**关键词覆盖率**：12/12 = **100%** ✅

---

## 三、语义覆盖检查（Cosmo + Alexa/Rufus）

### 用户任务清单（是否每个任务都有承接）

| 用户任务 | 承接位置 |
|---|---|
| "我想买一个不会断连的无线吉他系统" | 五点 1（5.8GHz 抗干扰） |
| "适合教会敬拜使用的无线吉他" | 标题 + 五点 1/4 + QA Q1 |
| "性价比高的无线吉他发射器" | 五点 5（价值对比） |
| "5.8GHz 的无线吉他系统" | 标题前 5 词 + 五点 1 |
| "可以同时多人使用的无线吉他" | 五点 5 + QA Q6 |
| "适合 Stratocaster 的无线" | 五点 3 + QA Q3 |
| "贝斯无线发射器" | 标题 + 五点 3 + QA Q4 |
| "5 小时续航的无线吉他" | 五点 4 + QA Q5 |
| "plug and play 的无线吉他" | 五点 5 + QA Q8 |
| "¿sistema inalámbrico para guitarra?" | ST + QA Q10 |

**语义覆盖率**：10/10 = **100%** ✅

### 自然语言问答测试（Alexa/Rufus 模拟）

| 用户问 | 系统返回 LEKATO 的可能性 |
|---|---|
| "Alexa, what's a good wireless guitar system for church?" | 高（church + wireless guitar system 多次共现） |
| "Alexa, will this wireless guitar work with my Fender Strat?" | 高（Strat 兼容性 + recessed jack） |
| "Alexa, does the LEKATO wireless guitar have latency?" | 高（<6ms 在五点 2） |
| "Alexa, can I use a wireless guitar for bass?" | 高（贝斯长尾 + QA Q4） |

---

## 四、转化逻辑检查

### 决策链完整性

| 决策环节 | 是否承接 | 位置 |
|---|:---:|---|
| 1. 注意（标题埋主词） | ✅ | 标题 |
| 2. 兴趣（差异化卖点） | ✅ | 标题前置 5.8GHz |
| 3. 信任（差评防御） | ✅ | 五点逐一对应差评痛点 |
| 4. 欲望（场景代入） | ✅ | 五点 1/4/5 + QA |
| 5. 行动（CTA） | ⚠️ | 五点 5 末尾建议加 "Add to Cart" CTA（A+ 可加） |

### 痛点防御完整性（差评 TOP 7 → 是否都有承接）

| 痛点 | 五点 | A+ | QA | 防御? |
|---|:---:|:---:|:---:|:---:|
| 1 干扰 | ✅ | ✅ | ✅ | ✅ |
| 2 电池 | ✅ | ✅ | ✅ | ✅ |
| 3 音质 | ✅ | ✅ | ✅ | ✅ |
| 4 贝斯 | ✅ | ✅ | ✅ | ✅ |
| 5 耐用 | ✅ | ✅ | ✅ | ✅ |
| 6 高输出拾音器 | - | - | ✅ | ✅ |
| 7 品控 | - | ✅ | ✅ | ✅ |

**转化逻辑完整度**：7/7 = **100%** ✅

---

## 五、风险提示与改进建议

### 🟡 中等风险

1. **竞品品牌词投 SP 广告**（joyo / xvive）
   - US 站允许，但建议单独 campaign，监控 ACOS
   - 落地页应针对每个竞品做对比 A+ 模块

2. **bluetooth 误搜词进 ST**
   - 用户搜 bluetooth guitar transmitter 实际想买的是无线系统
   - 但 5.8GHz ≠ Bluetooth，需避免在标题/五点宣称 Bluetooth
   - ST 索引不违规，但**绝对不能在 A+ 或图片 alt 文字**写 Bluetooth

3. **贝斯差评多但标题仍主打 Bass**
   - 决策：保留 Bass（扩大语义匹配），五点 3 强化贝斯适配性话术，QA Q4 直接应对

### 🟢 低风险

4. **变体 brown 色**
   - 标题末尾保留 "Brown"（已 Amazon's Choice 子体），Black 变体 ASIN B07TYRQ222 单独优化

5. **QA Q10 西语**
   - 美国 Spanish-speaking 用户约 13%，QA 翻译留存对转化的边际收益明显

---

## 六、上线 checklist

- [ ] 标题替换为草稿 A
- [ ] 五点替换为草稿 A 的 5 点
- [ ] ST 替换为草稿 A 的 ST
- [ ] QA 上传 10 条（草稿 A）
- [ ] A+ 模块更新（5.8GHz 对比图 + 电池对比图 + 兼容乐器图 + 用户证言）
- [ ] 主图测试（建议加 "5.8GHz" 角标）
- [ ] SP 广告：竞品词单独 campaign
- [ ] 上线后 7 天监控：核心词自然排名、CTR、CVR、差评增量
- [ ] 14 天复盘：标题/五点是否需要 A/B test

---

## 七、最终评分

| 维度 | 评分 | 说明 |
|---|---|---|
| 合规 | 9/10 | 修正"warranty"和竞品点名后达标 |
| 关键词覆盖 | 10/10 | 12/12 核心 + 长尾全覆盖 |
| 语义覆盖 | 10/10 | 10/10 用户任务全覆盖 |
| 转化逻辑 | 9/10 | 7/7 痛点防御，CTA 可加强 |
| **综合** | **9.5/10** | 可上线 |
