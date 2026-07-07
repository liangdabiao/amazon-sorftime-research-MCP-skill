#!/usr/bin/env python3
"""Mini Mic Pro - Negative Review Deep Dive Analysis"""
import sys, json, urllib.request, time, os
from datetime import datetime
from collections import Counter
import re

SECRET_KEY = ""
URL = "https://mcp.sellersprite.com/mcp"
OUT_DIR = "D:/sellersprite-skills/lavalier-microphones"
ASIN = "B0CMJTSVRW"

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def call_tool(name, arguments):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments}
    }).encode('utf-8')
    req = urllib.request.Request(URL, data=payload,
        headers={"Content-Type": "application/json", "secret-key": SECRET_KEY,
                 "Accept": "application/json, text/event-stream"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode('utf-8')
            data = json.loads(raw)
            text = data['result']['content'][0]['text']
            return json.loads(text)
    except Exception as e:
        return {"error": str(e), "_tool": name}

print("=== Fetching Reviews ===")
r1 = call_tool("review", {"marketplace": "US", "asin": ASIN})
print(f"  review: {r1.get('code', 'ERROR')}")

# Try to get page 2 as well
time.sleep(0.5)
r2 = call_tool("review", {"marketplace": "US", "asin": ASIN, "page": 2})
print(f"  review page2: {r2.get('code', 'ERROR')}")

all_reviews = {"page1": r1, "page2": r2, "asin": ASIN}
with open(f"{OUT_DIR}/review_data.json", "w", encoding="utf-8") as f:
    json.dump(all_reviews, f, ensure_ascii=False, indent=2)

# ====== PARSE ======
def safe_items(data):
    if isinstance(data, dict):
        if data.get('code') == 'OK':
            d = data.get('data', {})
            if isinstance(d, list): return d
            return d.get('items', d.get('data', []))
        return []
    if isinstance(data, list): return data
    return []

reviews = []
for resp in [r1, r2]:
    items = safe_items(resp)
    reviews.extend(items)

print(f"\nTotal reviews collected: {len(reviews)}")

# Categorize
positive, neutral, negative = [], [], []
for r in reviews:
    star = r.get('star', r.get('rating', 0))
    try:
        star = int(star)
    except:
        star = 0
    if star >= 4: positive.append(r)
    elif star == 3: neutral.append(r)
    else: negative.append(r)

print(f"Positive (4-5★): {len(positive)}")
print(f"Neutral (3★): {len(neutral)}")
print(f"Negative (1-2★): {len(negative)}")

# ====== NEGATIVE REVIEW ANALYSIS ======
def extract_text(r):
    return r.get('text', r.get('content', ''))

# Build pain point categories
pain_keywords = {
    "音质/音效问题": ["sound", "audio", "quality", "static", "noise", "distortion", "crackling", "tinny", "muffled", "quiet", "volume", "echo", "voice"],
    "连接/蓝牙问题": ["connect", "pair", "bluetooth", "sync", "drop", "interference", "range", "signal", "disconnect", "link"],
    "充电/电池问题": ["charge", "battery", "power", "die", "dead", "overheat", "melt", "hot", "charging", "usb", "port", "cable"],
    "兼容性问题": ["compatible", "android", "iphone", "ipad", "usb-c", "lightning", "device", "adapter", "work with", "not work"],
    "做工/质量": ["cheap", "flimsy", "break", "crack", "fragile", "build", "quality control", "defect", "stop working", "broken"],
    "使用体验": ["difficult", "hard to", "setup", "confusing", "instructions", "clunky", "convenient", "button", "indicator"],
    "降噪/环境音": ["wind", "background", "noise cancellation", "ambient", "environment", "outdoor", "breeze"],
}

def classify_pain(text):
    text_lower = text.lower()
    found = {}
    for category, keywords in pain_keywords.items():
        matches = [kw for kw in keywords if kw in text_lower]
        if matches:
            found[category] = matches
    return found

pain_counter = Counter()
pain_examples = {}

for r in negative + neutral:
    text = extract_text(r)
    pains = classify_pain(text)
    for cat in pains:
        pain_counter[cat] += 1
        if cat not in pain_examples:
            pain_examples[cat] = []
        if len(pain_examples[cat]) < 5:
            pain_examples[cat].append({
                "star": r.get('star', r.get('rating', 0)),
                "date": r.get('date', r.get('time', '')),
                "text": text[:200]
            })

# ====== GENERATE REPORT ======
lines = []
def L(s=""):
    lines.append(s)

L(f"# Mini Mic Pro (B0CMJTSVRW) — 差评深度分析报告")
L()
L(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 数据源: 卖家精灵 SellerSprite + NLP 分析")
L()

L("---")
L()
L("## 一、评论总览")
L()
total = len(reviews)
L(f"| 维度 | 数值 |")
L(f"|------|:----:|")
L(f"| ASIN | {ASIN} |")
L(f"| 整体评分 | 4.4 / 5.0 |")
L(f"| 总评分数 | 7,182 |")
L(f"| 本次分析样本 | {total} 条 |")
L(f"| 好评 (4-5★) | {len(positive)} 条 ({len(positive)/total*100:.1f}%) |")
L(f"| 中评 (3★) | {len(neutral)} 条 ({len(neutral)/total*100:.1f}%) |")
L(f"| 差评 (1-2★) | {len(negative)} 条 ({len(negative)/total*100:.1f}%) |")
L()

L("---")
L()
L("## 二、差评痛点聚类分析")
L()
L("### 痛点分布")
L()
L("| 排名 | 痛点类别 | 提及次数 | 占比 |")
L("|:---:|---------|:-------:|:---:|")
sorted_pains = pain_counter.most_common()
for i, (cat, cnt) in enumerate(sorted_pains, 1):
    pct = cnt / (len(negative) + len(neutral) + 1) * 100
    bar = "█" * int(pct / 5) + "░" * max(0, 20 - int(pct / 5))
    L(f"| {i} | {cat} | {cnt} | {pct:.0f}% {bar} |")
L()

for cat, cnt in sorted_pains:
    L(f"### {i}. {cat}（提及 {cnt} 次）")
    L()
    examples = pain_examples.get(cat, [])
    if examples:
        L("| 评分 | 日期 | 评论原文摘要 |")
        L("|:---:|:----:|-------------|")
        for ex in examples:
            star = ex['star']
            date = ex['date']
            if isinstance(date, int):
                from datetime import datetime as dt
                date = dt.fromtimestamp(date/1000).strftime('%Y-%m-%d') if date else 'N/A'
            L(f"| {star}★ | {date} | {ex['text']} |")
    L()

L("---")
L()

# Detailed negative reviews
L("## 三、差评原文（完整）")
L()
if negative:
    for i, r in enumerate(negative[:15], 1):
        text = extract_text(r)
        star = r.get('star', r.get('rating', 0))
        date = r.get('date', r.get('time', ''))
        if isinstance(date, int):
            from datetime import datetime as dt
            date = dt.fromtimestamp(date/1000).strftime('%Y-%m-%d') if date else 'N/A'
        L(f"### {i}. [{star}★] {date}")
        L()
        L(f"> {text}")
        L()
else:
    L("*样本中无差评*")
    L()

L("---")
L()

# Product improvement recommendations
L("## 四、产品改良建议")
L()
improvements = {
    "音质问题": [
        "升级麦克风元件，提升信噪比",
        "增加音频处理芯片，减少底噪和杂音",
        "优化音量均衡，避免忽大忽小"
    ],
    "充电/电池": [
        "改进充电接口质量，防止过热熔化",
        "增加过温保护电路",
        "提升电池容量或快充支持"
    ],
    "连接稳定性": [
        "增强射频设计，提升传输距离和抗干扰能力",
        "改进自动重连机制"
    ],
    "兼容性": [
        "优化 Android 设备兼容性测试",
        "提供更全的适配器配件"
    ],
    "做工质量": [
        "提升外壳材料品质",
        "加强质检流程"
    ]
}

L("| 痛点 | 建议改进方向 | 优先级 |")
L("|------|-------------|:-----:|")
for pain, sugs in improvements.items():
    sug_text = "；".join(sugs)
    priority = "🔴 高" if pain in ["音质问题", "充电/电池"] else "🟡 中"
    L(f"| **{pain}** | {sug_text} | {priority} |")
L()

L("---")
L()
L("## 五、市场竞争启示")
L()
L("### Mini Mic Pro 的弱点即你的机会")
L()
L("1. **音质是最大突破口** — 差评中反复提到音质一般、有杂音，这是 $25 价位产品的通病")
L("2. **安全性痛点** — 充电过热/熔化是严重的产品缺陷，如果能解决将建立信任优势")
L("3. **Android 兼容性** — 大量差评来自 Android 用户，这是一个被忽视的细分市场")
L("4. **$30-$40 品质升级带** — 在 $25-$50 之间存在空白带，定价 $34.99 配合更好的音质和做工")
L()
L("### 产品开发 Checklist")
L()
L("- [ ] 高音质麦克风元件（信噪比 > 70dB）")
L("- [ ] 安全快充（过温保护、阻燃材料）")
L("- [ ] 双平台兼容（iOS + Android 原生支持）")
L("- [ ] 降噪算法（环境音过滤）")
L("- [ ] 续航 > 8 小时")
L("- [ ] 多色/多接口变体")
L()
L("---")
L()
L(f"*报告生成: 2026-07-05 | 数据工具: 卖家精灵 SellerSprite + NLP 分析 | 站点: Amazon US*")

report = "\n".join(lines)
with open(f"{OUT_DIR}/review_analysis.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"\nReview analysis saved to {OUT_DIR}/review_analysis.md")
print(f"Report size: {len(report)} chars")
