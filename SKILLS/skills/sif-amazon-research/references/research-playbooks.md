# Sif research playbooks

## 1. Quick traffic report

Use when the user asks for ASIN traffic status or traffic composition.

Tools:
1. `ops_get_asin_traffic_trend` for total/natural/ad trend.
2. `ops_get_listing_traffic_overview` for natural vs ad share.
3. `ops_get_listing_keyword_distribution` for keyword coverage by channel or variant.

Output: trend direction, traffic dependency, weak channel, top follow-up checks.

## 2. Keyword reverse audit

Use when the user wants to know which keywords bring traffic to an ASIN or competitor.

Tools:
1. `market_get_asin_keyword_signals` for ranking, traffic contribution, and competitive position.
2. `ops_get_listing_keyword_distribution` for channel-level keyword counts or scores.
3. `market_get_keyword_history` for demand and concentration of the top 5-10 candidate terms.
4. `market_get_keyword_competition` for enterability of priority terms.

Output: main traffic terms, ad/natural split, defend terms, attack terms, missing terms.

## 3. Ad operations report

Use when the user asks whether advertising is healthy or which campaigns/ad groups matter.

Tools:
1. `ads_get_asin_ad_traffic_trend` for SP/SB/SBV trend.
2. `ads_get_asin_ad_feature_profile` or `ads_get_asin_ad_window_feature_profile` for concentration, rhythm, stability.
3. `ads_get_asin_campaign_contribution_overview` to rank campaigns.
4. Drill down only when needed: `ads_get_campaign_traffic_trend`, `ads_get_campaign_contribution_breakdown`, `ads_get_ad_group_keyword_breakdown`.
5. `ads_get_asin_campaign_changes` when performance change may be caused by budget/bid/status edits.

Output: dominant channel, concentration risk, waste/scale candidates, exact campaign/ad group next actions.

## 4. Traffic anomaly diagnosis

Use when the user asks why traffic/ranking/sales dropped or says traffic is abnormal.

Preferred tool:
- `analyze_traffic_anomaly` with `asin`, `country`, and optional `time_type/time_value`.

If manual corroboration is needed:
1. `ops_get_asin_traffic_trend` for when the anomaly started.
2. `ops_get_listing_traffic_overview` for natural vs ad split.
3. `market_get_asin_keyword_signals` for keyword rank/traffic shifts.
4. Ad tools only if ad share changed.

Output must include a cause tree or Mermaid diagram if tool output supports it, plus excluded hypotheses.

## 5. Competitor deep analysis

Use when the user provides competitor ASINs and asks how they grew or how to beat them.

Tools:
1. `ops_get_asin_sales_list` and/or `ops_get_asin_sales_trend` for sales, price, variant winners, seasonality.
2. `ops_get_asin_traffic_trend` and `ops_get_listing_traffic_overview` for growth stages and ad/natural dependency.
3. `market_get_asin_keyword_signals` for traffic source and ranking position.
4. `market_get_keyword_history` and `market_get_keyword_competition` for the top traffic terms.
5. Ad tools if the competitor relies heavily on paid traffic.

Output: growth path, core keywords, traffic engine, variant/price pattern, copyable tactics, hard-to-copy moat.

## 6. Keyword opportunity batch

Use when the user provides multiple keywords and wants prioritization.

Tools:
1. `market_get_keyword_history` for search volume, ABA rank, top3 concentration.
2. `market_get_keyword_root_trend` for exact-vs-root demand boundary.
3. `market_get_keyword_demand` for lifecycle and timing.
4. `market_get_keyword_competition` for enterability.

Score each keyword on demand, trend, concentration, competition, relevance, and expansion space. Label as `攻主词`, `铺长尾`, `观察`, or `放弃`.

## 7. Market validation

Use when deciding whether a product/market is worth doing.

Tools:
1. Keyword tools for demand size, trend, seasonality, concentration, and competition.
2. `ops_get_asin_sales_list` for competitor sales, price band, and variants.
3. Competitor ASIN keyword signals for traffic sources.
4. Traffic/ad tools when candidate ASINs show abnormal paid dependency.

Decision logic: demand stable/growing + non-monopoly + reachable price/profit band + clear keyword entry + tolerable review/brand moat = worth testing.

Output: `做 / 不做 / 小样测试`, rationale, entry route, risk gates, minimum data needed before spend.

## 8. Full analysis

Use when the user asks for comprehensive research on an ASIN, product, or market. Also read `field-notes.md` first because full analysis commonly creates large Sif responses.

Minimum sequence:
1. Sales: `ops_get_asin_sales_list` for current sales, price, rating, review, variants; add `ops_get_asin_sales_trend` for seasonality.
2. Traffic: `ops_get_asin_traffic_trend`, `ops_get_listing_traffic_overview`, and either `ops_get_listing_traffic_structure` or `ops_get_listing_keyword_distribution`.
3. Reverse keywords: `market_get_asin_keyword_signals`; take the top 3-5 traffic keywords.
4. Market: `market_get_keyword_history` for those keywords; `market_get_keyword_root_trend` for main exact/root terms; use `market_get_keyword_demand` when timing/seasonality is material.
5. Ads: if ad share is material or the user asks for ads, call `ads_get_asin_ad_traffic_trend`, `ads_get_asin_ad_structure`, `ads_get_asin_ad_feature_profile`, and `ads_get_asin_campaign_contribution_overview` with an explicit recent 30-day date window.
6. Synthesis: decide whether the subject is a direct-entry opportunity, a moat/avoid case, an optimization case, or a long-tail opportunity.

If a tool errors or returns an unexpected schema, continue with available evidence, explicitly mark the missing layer, and avoid overstating confidence.
