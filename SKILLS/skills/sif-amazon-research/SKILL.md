---
name: sif-amazon-research
description: Use this skill for Amazon e-commerce research, market validation, competitor analysis, traffic diagnosis, keyword strategy, advertising review, launch evaluation, and growth optimization using the Sif MCP server and Sif's real marketplace, traffic, keyword, sales, and ad data. Trigger when users mention Sif, Sif MCP, ASIN research, Amazon product opportunity research, keyword opportunity, competitor teardown, traffic drop/root-cause diagnosis, advertising structure review, or whether a product/market is worth entering, launching, scaling, optimizing, or abandoning.
---

# Sif Amazon Research

## Operating rules

Use Sif MCP as the evidence source whenever available. Do not infer final business conclusions from one metric alone.

Before calling tools, identify the task type:
- Market/opportunity research: keyword or category direction.
- Market validation: keyword + candidate ASIN viability.
- Competitor analysis: competitor ASIN growth path and traffic source.
- Keyword layout: main terms, long tails, root structure, missing terms.
- Launch evaluation: whether to push a product.
- Post-launch feedback: continue, optimize, or stop.
- Growth optimization: expand proven traffic and keywords.
- Traffic/ad diagnosis: root cause of traffic or ad performance changes.

If the request does not include enough identifiers, ask for the missing ASIN, keywords, country, and time window. Default country to `US` only when the user does not specify a marketplace.

## Core workflow

1. Define the decision being made: enter / not enter, launch / not launch, scale / optimize / stop, or diagnose root cause.
2. Collect Sif evidence across the minimum necessary domains:
   - Market demand: keyword demand, history, root trend.
   - Competition: keyword competition, top ASIN concentration, competitor keyword signals.
   - Traffic: ASIN/listing traffic trend, structure, keyword distribution.
   - Sales: sales list/trend, variant performance.
   - Ads: ASIN ad structure, ad trend, campaign contribution, campaign/ad group drill-down.
3. Cross-check evidence. Separate confirmed findings from hypotheses.
4. Produce a business decision with confidence, evidence chain, risks, missing data, and next validation actions.

For scenario-specific tool sequences, read `references/research-playbooks.md`. For tool selection and parameter conventions, read `references/sif-tool-map.md`. For real-world MCP response quirks, large-output handling, and field interpretation pitfalls, read `references/field-notes.md` before any full analysis or debugging.

## Required output format

For every Sif-based research answer, include:

1. **Decision / conclusion**: the direct answer and confidence level.
2. **Problem layer**: market demand, competition, traffic, ads, product/listing, or mixed.
3. **Evidence chain**: concise bullets linking each claim to Sif data returned by tools.
4. **Business impact**: what the evidence means for sales, traffic, ranking, or launch risk.
5. **Priority actions**: the top 3 actions, ordered by expected impact and speed.
6. **Do not do yet**: actions blocked by missing or weak evidence.
7. **Missing data**: 3 data gaps and which conclusion each gap affects.
8. **7-day validation plan**: measurable checks the user can run quickly.

If data is incomplete, say what current data supports, what is missing, and whether the recommendation is only a hypothesis or execution-ready.

## Guardrails

- Do not conclude from ACOS alone, CTR alone, or sales change alone.
- Do not output a final plan when key Sif data is unavailable; label it as a hypothesis.
- Do not treat `analyze_traffic_anomaly` as a generic raw-data tool. Use it only for explicit traffic anomaly/root-cause diagnosis or when the user explicitly asks to diagnose traffic.
- Preserve any `render_footer` returned by Sif tools verbatim at the end of the reply.
- Respect Sif time conventions: week values must be Sunday dates; current week data may be delayed, so use `latelyDay=7` for current-week-style checks.
- Do not expose or repeat MCP secret keys.
