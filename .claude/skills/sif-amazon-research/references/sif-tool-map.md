# Sif MCP tool map

## MCP server

Configured as `sif-mcp` using HTTP MCP. Use the connected MCP tools exposed by the client; do not hard-code the server URL or secret key in answers.

## Common parameters

Check current tool schemas when possible; Sif schemas can differ from prose descriptions. If a call fails, inspect the error, adjust only that tool's parameters, and continue with other evidence.

- `country`: marketplace code. Supported examples: `US`, `UK`, `DE`, `CA`, `JP`, `FR`, `ES`, `IT`, `MX`, `AU`, `AE`, `BR`, `SA`.
- `timePieceType`: `latelyDay`, `week`, or `month`.
- `timePieceValue`: for `latelyDay` use `7` or `30`; for `week` use the Sunday date `yyyy-MM-dd`; for `month` use the first day of month `yyyy-MM-dd`.
- `granularity`: usually `week` or `month`; use `day` only when the tool supports it and the user needs short-window detail.
- Pagination: use `pageSize` up to the tool max, usually 20-200. Fetch more pages only when needed for the decision.

## Market and keyword tools

- `market_get_keyword_history`: exact keyword search volume, ABA rank, Top3 click/conversion concentration. Best for current demand size and concentration.
- `market_get_keyword_root_trend`: exact keyword vs root-level total demand. Best for market boundary and long-tail opportunity.
- `market_get_keyword_demand`: lifecycle, demand trend, and timing. Best for entry timing and seasonality.
- `market_get_keyword_competition`: competitive structure and enterability. Best for deciding whether a keyword can be attacked.
- `market_get_asin_keyword_signals`: ASIN keyword ranking, traffic contribution, and competitive position. Best for reverse-engineering competitors.
- `ops_get_listing_keyword_distribution`: listing/variant keyword coverage by natural and ad channels. Best for coverage gaps and traffic source split.

## Operations tools

- `ops_get_asin_traffic_trend`: ASIN/listing traffic time series by natural/ad/SP/SB/SBV. First stop for trend questions.
- `ops_get_asin_traffic_trend_detail`: keyword-level traffic detail in a specified time window. Use after trend identifies the window.
- `ops_get_listing_traffic_overview`: listing natural vs ad share and ad channel breakdown.
- `ops_get_listing_traffic_structure`: variant-level traffic structure by natural/ad channels.
- `ops_get_asin_sales_trend`: monthly sales trend by ASIN/variant/dimension.
- `ops_get_asin_sales_list`: sales, price, attributes, and short trend for one or more ASINs.

## Advertising tools

- `ads_get_asin_ad_traffic_trend`: ASIN SP/SB/SBV exposure trend and dominant channel.
- `ads_get_asin_ad_structure`: campaigns and ad groups under the ASIN.
- `ads_get_asin_ad_feature_profile`: ASIN ad structure, rhythm, complexity, stability.
- `ads_get_asin_ad_historical_feature_profile`: historical change in ad style.
- `ads_get_asin_ad_window_feature_profile`: ad profile for a chosen date window.
- `ads_get_asin_campaign_contribution_overview`: campaign contribution ranking in a date window.
- `ads_get_asin_campaign_changes`: bid/budget/status changes; use for suspected operational causes.
- `ads_get_campaign_structure`: ad groups in a campaign.
- `ads_get_campaign_traffic_trend`: campaign lifecycle trend and anomaly weeks.
- `ads_get_campaign_contribution_breakdown`: contribution by ad group or keyword within campaign.
- `ads_get_ad_group_traffic_trend`: ad group trend.
- `ads_get_ad_group_keyword_breakdown`: keywords and display ASINs inside an ad group for a week.

## Scenario tool

- `analyze_traffic_anomaly`: end-to-end ASIN traffic drop root-cause diagnosis. Use for explicit anomaly diagnosis; not for raw data display.

## Interpretation thresholds

- Top3 click share > 0.6: traffic is highly concentrated; new entrants face high traffic acquisition difficulty.
- Top3 click share 0.3-0.6: moderate concentration; entry depends on differentiation and keyword route.
- Top3 click share < 0.3: distributed demand; more room for new entrants.
- Root coverage ratio > 0.8: demand is concentrated in the exact term.
- Root coverage ratio 0.4-0.8: mix exact and long-tail layout.
- Root coverage ratio < 0.4: demand is dispersed; exact term alone underestimates market size.

Treat thresholds as heuristics. Confirm with competition, sales, price, review moat, and product relevance before recommending execution.
