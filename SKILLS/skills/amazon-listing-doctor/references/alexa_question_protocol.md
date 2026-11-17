# ALEXA AEO 买家问题生成规范

> Agent 读这份规范 + listing 全文,针对**该 listing 的具体产品**生成真实买家会向 AI 购物助手(Alexa for Shopping / Rufus)提的问题,然后判断 listing 能不能回答。
>
> ⚠️ **核心红线**:问题必须贴合该 listing 的具体产品,**不得套用其他子品类的固定问法**(手机 listing 不得问 earbuds 相关;猫用品 listing 不得问 dog 相关;食品 listing 不得问电池续航)。固定问题库会被品类局限,所以改为「规范驱动 + Agent 生成」。

---

## Agent 流程(一次完成三步)

1. **理解产品**:读 listing 全文,用一句话说清"这是什么产品 + 核心属性 + 典型买家是谁"
2. **生成问题**:按下方 8 个 aspect 框架,生成 **14-18 个真实买家问题**(贴合该具体产品)
3. **判断回答**:对每个问题判断 listing 能不能答(covered / partial / missing)

---

## 8 个 aspect 提问框架

对每个 aspect,基于【该具体产品】生成 1-3 个真实买家问题。括号里是该 aspect 的「提问方向」,不是固定问句——要替换成具体产品 + 该产品买家真正会纠结的点。

### 1. 场景适配 scenario_fit
这个产品在什么真实场景下用?那个场景下够不够用、会不会有问题?
> 例(耳机):Are these good for running? / Can I use this on a plane?
> 例(充电宝):Will this charge my phone on a long flight? / Can I take it through airport security?

### 2. 人群适配 audience_fit
适合什么人?特定人群(老人 / 小孩 / 新手 / 专业人士 / 敏感体质 / 大体重)能不能用?
> 例(宠物喂食器):Is this good for a multi-pet household? / Will this work for someone who travels a lot?
> 例(护肤品):Is this safe for sensitive skin? / Can teenagers use this?

### 3. 兼容性 compatibility
配合什么设备 / 系统 / 配件 / 环境用?兼容吗?
> 例(耳机):Does this work with iPhone / Android? / Does this connect to my laptop?
> 例(厨房工具):Can I use this on an induction cooktop? / Does this fit my sink?

### 4. 耐用可靠 durability
能用多久?抗造吗?有什么可靠性顾虑?
> 例:Are these waterproof / sweatproof? / Will this survive being dropped? / How long will this last?

### 5. 易用性 ease_of_use
上手难吗?要不要额外配件 / 安装?日常维护麻烦吗?
> 例:Is this easy to set up? / Does this need batteries (included)? / Is it easy to clean?

### 6. 规格尺寸 sizing
尺寸 / 容量 / 重量 / 力度 / 浓度……规格对不对?怎么选?
> 例(服饰):Is this true to size? / Does this run small or large?
> 例(背包):Will this fit a 15-inch laptop? / Is this carry-on size?

### 7. 对比选择 comparison
和同类产品 / 常见竞品 / 替代方案比,怎么样?
> 例:Is this better than [该品类公认标杆]? / How does this compare to other options at this price?

### 8. 价值顾虑 value_risk
值不值?有什么坑 / 安全顾虑 / 退换风险?
> 例:Is this worth the price? / Are there any common issues I should know? / Is this safe to use long-term?

---

## 口吻规范

- **真实买家口吻**:用买家真的会问 Alexa / 客服的自然问句,**不是市场调研话术**
- **口语化英文**(随 listing 语言调整):`Is this good for...?` / `Can I use this to...?` / `Will this...?` / `How does this compare to...?` / `Is this ... ?`
- **具体到产品**:问题里可带该产品的品类词 / 核心属性词(基于 listing 内容),但**不要引入 listing 里没有的子品类假设**
- **贴近真实决策**:问的是买家掏钱前真正会纠结的疑虑,不是泛泛的"这个产品怎么样"

---

## 数量与覆盖

- 总数 **14-18 问**,8 个 aspect 都要覆盖(每个 1-3 问)
- **优先该产品买家最关心的 aspect**:
  - 电子 / 数码 → 重兼容性、耐用、易用
  - 服饰 / 鞋靴 → 重尺寸合身、场景、打理
  - 食品 / 保健品 → 重成分、口味、安全、忌口
  - 家居 / 厨房 → 重规格、易清洁、兼容灶台/水槽
  - 宠物 / 母婴 → 重安全、人群适配、规格
- 不重要的 aspect 也至少 1 问,保覆盖面

---

## 红线(不得违反)

- ❌ **不得套用其他子品类的固定问题**(给手机问 earbuds 舒服吗、给猫用品问 dog 用不用、给毛巾问电池续航)
- ❌ **不得问 listing 完全不可能涉及的问题**(基于产品类型显然无关的)
- ❌ **不得用市场调研 / 问卷话术**("请评估该产品的性价比""请列举优缺点")
- ❌ **不得超过 20 问**(聚焦真实高频疑虑,别灌水)

---

## 判断口径(covered / partial / missing)

生成问题后,对每问判断 listing 能不能回答(每个问题落到且只落到一态):

- **covered**:listing 有明确、可查的信息能**直接回答**该问题
- **partial**:listing 提到了相关内容,但信息不全 / 不清晰,Agent 只能**部分回答**
- **missing**:listing 完全没涉及,Agent **答不上**

**严格口径**:
- "compatible with iPhone 15" 能答 "Does this work with iPhone?" ✅
- 但泛泛的参数表**不能**答 "Is this good for running?"(除非 listing 明确把产品和跑步关联)❌→ missing
- 不确定的判 partial 或 missing,**不凑 covered**(宁可严判,不虚高分数)

---

## 输出 schema

```json
{
  "extraction_method": "aeo_agent",
  "product": "一句话:这是什么产品 + 核心属性 + 典型买家(例:'蓝牙降噪耳机,主打通勤/运动场景,买家多为年轻数码用户')",
  "buyer_questions": [
    "Agent 针对该产品生成的 14-18 个真实买家问题"
  ],
  "buyer_alignment": {
    "covered": ["listing 能直接答的问题"],
    "partial": ["listing 答不全的问题"],
    "missing": ["listing 答不上的问题"]
  }
}
```

> `buyer_questions` 与 `buyer_alignment` 三态的并集应一致(每个生成的问题都落到一态)。算分用三态:`score = (covered×1.0 + partial×0.5) / 总问题数 × 100`。
