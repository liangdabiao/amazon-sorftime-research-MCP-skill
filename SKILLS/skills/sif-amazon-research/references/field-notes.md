# Field notes from real Sif MCP usage

## Prefer MCP tools, but handle large outputs

Some Sif tool responses are large. If direct tool output is truncated or hard to parse, call the MCP HTTP endpoint with a small script and write a compact local JSON summary. Do not paste secrets into the final answer.

Recommended pattern:
1. Load the MCP URL and secret from `.mcp.json` if local config is available.
2. Call `tools/call` with the exact tool name and arguments.
3. Parse `result.content[0].text` as JSON.
4. Extract only business-relevant fields into a compact summary.
5. Read the compact summary before writing the final answer.

Use this when a full analysis needs many tools or when output exceeds the visible context.

## Robust parsing notes

Sif fields may vary by tool or response mode:
- Variant count may appear as `vaiantsNum` or `variantsNum`.
- Variant attributes may be a list of dicts (`[{value: "Buzz"}]`) or strings (`["Buzz"]`).
- Traffic trend channel arrays may be arrays of objects with `score`, `scoreRatio`, and `scoreChangeRatio`, not plain numeric arrays.
- Keyword distribution numeric values may be strings; convert before arithmetic.
- Some tools return Chinese keys such as `官网验证`; preserve verification links when useful.

When parsing, inspect keys first and write defensive extraction logic. If a field is absent, report the gap instead of fabricating a value.

## Tool parameter pitfalls

- `market_get_keyword_competition` may reject the same `keywords` array style accepted by `market_get_keyword_history`; if it errors, continue with keyword history concentration (`top3_click_share`, `top3_conversion_share`), ASIN keyword signals, and root trend, and label competition-tool output as missing.
- `ads_get_asin_campaign_contribution_overview` requires an explicit `start_date` and `end_date` in some schemas. For a current snapshot, use a recent 30-day window.
- `ads_get_asin_ad_window_feature_profile` schema descriptions may mention window dates, but the observed schema can require `granularity`; check current tool schema if available.
- `analyze_traffic_anomaly` is for explicit diagnosis/root-cause requests, not normal full research.

## Full-analysis minimum dataset

For a comprehensive ASIN report, collect at least:
1. `ops_get_asin_sales_list` and/or `ops_get_asin_sales_trend`.
2. `ops_get_asin_traffic_trend`.
3. `ops_get_listing_traffic_overview`.
4. `ops_get_listing_traffic_structure` or `ops_get_listing_keyword_distribution`.
5. `market_get_asin_keyword_signals`.
6. `market_get_keyword_history` for top 3-5 traffic keywords.
7. `market_get_keyword_root_trend` for the main exact/root terms.
8. Ads tools when ad share is material or the user asks for ads: `ads_get_asin_ad_traffic_trend`, `ads_get_asin_ad_structure`, `ads_get_asin_ad_feature_profile`, `ads_get_asin_campaign_contribution_overview`.

Do not call every drill-down tool by default. Drill down only if a decision depends on a campaign/ad group/keyword cause.

## Interpretation lessons

- High sales plus high review count plus high natural share indicates a moat; do not recommend direct white-label entry without IP/compliance and differentiation checks.
- A product can have many campaigns while still being natural-led. Compare ad share against total traffic before calling it ad-driven.
- For parent/variant listings, separate parent-level demand from variant-level winners. Identify which styles or variants absorb most sales and traffic.
- Root coverage ratio changes strategy: low exact/root coverage means long-tail opportunity; high coverage means exact-term competition is the main battleground.
- Top3 click share near or above 0.6 means traffic is concentrated; below 0.3 means demand is more open.
- If a Sif competition tool fails, keyword history and ASIN keyword signals still provide usable concentration and ranking evidence, but confidence should be reduced for competition conclusions.

## Final answer hygiene

- Never mention raw scripts, temporary file paths, or parsing errors unless the user asked about process details.
- Do mention data limitations that affect business confidence.
- Keep source links from Sif verification fields at the end when available.
- Use direct business language: `做 / 不做 / 小样测试`, `加码 / 优化 / 止损`, `防守词 / 进攻词 / 长尾词`.
