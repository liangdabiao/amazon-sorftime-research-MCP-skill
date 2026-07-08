# SellerSprite Amazon Research Skill

> **AI-powered Amazon product research skill** — 43 MCP tools for product discovery, keyword research, competitor analysis, market intelligence, and listing optimization on Amazon.

## Overview

This skill integrates **SellerSprite (卖家精灵)** — a leading Amazon analytics platform — with AI assistants (Claude Code) via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It enables natural-language-driven, end-to-end Amazon product research workflows: from category scanning and keyword mining to competitive analysis, pricing strategy, and listing optimization.

## Features

- **Smart Product Discovery** — Find winning products with flexible filtering (sales volume, rating, listing age, price, seller type, etc.)
- **Market Panorama** — Full market analysis across 13 dimensions: size, concentration, price distribution, ratings, listing age, seller countries, fulfillment types, and more
- **Keyword Research** — Mine keywords, analyze trends (ABA/Google Trends), find title-density gaps and low-monopoly opportunities
- **Competitor Analysis** — Deep-dive into any ASIN: traffic sources, keyword rankings, advertising strategy, review sentiment
- **Listing Optimization** — Diagnose listing quality, A+ content, video presence, and keyword coverage
- **Traffic Analysis** — Decompose traffic sources (organic vs paid), identify referral traffic and ad placements
- **Blue Ocean Discovery** — Find underserved niches: low brand monopoly, high new-product ratio, high-margin lightweight products
- **Review Intelligence** — Sample-based review analysis and pain-point clustering for product improvement
- **Pricing Strategy** — Price distribution analysis, Keepa historical trends, seasonal pricing patterns

## Prerequisites

- [Claude Code](https://claude.ai/code) CLI
- A **SellerSprite** account with API access (secret key)

## Installation

### 1. Clone the skill repository

```bash
git clone <your-repo-url> sellersprite-skills
cd sellersprite-skills
```

### 2. Configure your SellerSprite API key

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "sellersprite": {
      "url": "https://mcp.sellersprite.com/mcp",
      "headers": {
        "secret-key": "YOUR_SECRET_KEY"
      }
    }
  }
}
```

> **Important**: The secret key is passed via `headers.secret-key`, NOT as a URL parameter or `Authorization` header.

### 3. Install the skill in Claude Code

The skill is auto-discovered from `.claude/skills/sellersprite-amazon-research/`. If your Claude Code project settings point here, it will be available automatically.

## Quick Start

### Analyze a product by ASIN

```
/research https://www.amazon.com/dp/B08R8FSFRB
```

The assistant will call 10+ tools (product detail, sales trend, Keepa history, keyword research, traffic analysis, reviews, competitors, etc.) and produce a comprehensive report.

### Scan a category

```
/market-analysis [nodeIdPath]
```

### Find keyword opportunities

```
/keyword-research wireless guitar system
```

## Command Reference

Comprehensive workflows accessible via slash commands:

| Command | Description | Core Tools Used |
|---------|-------------|----------------|
| `/product-research` | Smart product discovery with advanced filters | `product_research` + `product_node` |
| `/market-analysis` | Full market panorama across 13 dimensions | `market_research` + 12 distribution tools |
| `/competitor-analysis` | Deep ASIN competitive decomposition | `asin_detail` + `traffic_keyword` |
| `/keyword-research` | Keyword-based product research | `keyword_research` + `keyword_miner` |
| `/listing-optimizer` | Listing quality diagnosis & optimization | `traffic_listing` + `keyword_order` |
| `/traffic-analysis` | Traffic source decomposition | `traffic_source` + `traffic_keyword_stat` |
| `/opportunity-finder` | Blue ocean opportunity discovery | `aba_research_trend` + `google_trend` |
| `/review-insights` | Review sentiment analysis | `review` + NLP |
| `/pricing-strategy` | Pricing strategy & price distribution | `market_price_distribution` |
| `/ad-optimizer` | Advertising optimization | `keyword_order` + `traffic_keyword` |

## Tactical Strategy Cards

18 pre-defined strategy cards for specific product hunting scenarios:

### New Product / Growth
| Strategy | Logic |
|----------|-------|
| **New Product Burst** | Listed ≤2 months, sales ≥300/month, reviews ≤100 |
| **Hidden Bestseller** | Listed ≤3 months, sales ≥500/month, reviews ≤50 |
| **ABA High-Growth Trend** | 3-month sustained growth, low click concentration |
| **Low-Monopoly Keyword** | Search ≥5,000/month, monopoly <50% |

### Product Improvement
| Strategy | Logic |
|----------|-------|
| **Hot Low-Rating Product** | Sales ≥1,000/month, rating ≤4.2 |
| **Review Sentiment Analysis** | NLP clustering of negative reviews → improvement guide |

### Category Structure
| Strategy | Logic |
|----------|-------|
| **Low Brand Monopoly** | Brand concentration <45% |
| **High New-Product Ratio** | New products >5% of category sales |
| **High-Margin Lightweight** | FBA fee ≤$4, margin ≥50% |

### Opportunity Capture
| Strategy | Logic |
|----------|-------|
| **Local Premium Disruption** | US sellers, high price, high sales |
| **FBM Intercept** | FBM fulfillment, sales ≥300/month |
| **Poor Listing Winner** | LQS ≤60, sales ≥400/month |
| **High-Ticket Long-Tail** | Avg price ≥$80, moderate search volume |
| **Seasonal Pre-positioning** | Historical YoY growth >100% |

### Traffic & Variant
| Strategy | Logic |
|----------|-------|
| **Natural Traffic Audit** | Organic traffic share >60% |
| **Variant Gap Analysis** | Find uncovered variant gaps |

## Directory Structure

```
.claude/skills/sellersprite-amazon-research/
├── SKILL.md                          # Main skill instructions (entry point)
├── README.md                         # This file
├── comprehensive/                    # Workflow guides (10 commands)
│   ├── product-research.md
│   ├── market-analysis.md
│   ├── competitor-analysis.md
│   ├── keyword-research.md
│   ├── listing-optimizer.md
│   ├── traffic-analysis.md
│   ├── opportunity-finder.md
│   ├── review-insights.md
│   ├── pricing-strategy.md
│   └── ad-optimizer.md
├── tactical/                         # Strategy cards (18 strategies)
│   ├── new-product-burst.md
│   ├── hidden-bestseller.md
│   ├── hot-low-rating.md
│   └── ...
├── reference/                        # MCP tool parameter references
│   ├── tools_index.md                # Full 43-tool catalog
│   ├── product_research.md
│   ├── market_research.md
│   ├── asin_detail.md
│   └── ...
└── scripts/                          # Utility scripts
    └── mcp_call.py                   # MCP API caller (Python)
```

## MCP Tool Catalog

43 tools across 7 categories:

| Category | Tools | Description |
|----------|-------|-------------|
| **ASIN Analysis** (7) | `asin_detail`, `keepa_info`, `bsr_prediction`, etc. | Product-level detail, history, prediction |
| **Products & Competition** (3) | `product_research`, `competitor_lookup`, `product_node` | Search, filter, category navigation |
| **Keywords** (4) | `keyword_miner`, `keyword_research`, `keyword_research_trends`, `keyword_order` | Mining, trends, ranking |
| **Traffic** (6) | `traffic_keyword`, `traffic_source`, `traffic_listing`, etc. | Traffic decomposition, keyword rankings |
| **Market Research** (15) | `market_research`, 14 distribution tools | Full market intelligence suite |
| **ABA/Trends** (4) | `aba_research_weekly/monthly/trend`, `google_trend` | Amazon Brand Analytics + Google Trends |
| **Reviews** (1) | `review` | Review data (capped at 20 samples) |
| **Trademarks** (4) | `trademark_list`, `trademark_detail`, etc. | Trademark search & details |

## Configuration

### Default Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `marketplace` | `US` | Target marketplace (US/JP/UK/DE/FR/IT/ES/CA/IN) |
| `matchType` | `2` | 1=phrase, 2=模糊(broad), 3=exact |
| `size` | `50` | Results per page (max 100) |

### Parameter Passing Modes

Two patterns are used across the 43 tools:

- **Flat params**: `{"marketplace": "US", "asin": "B0XXXXX"}` — used by `asin_detail`, `review`, `keyword_research_trends`, etc.
- **`request` nested**: `{"request": {"marketplace": "US", "nodeIdPath": "...", ...}}` — used by most search/filter tools

## Report Format

All research automatically generates two files:

```
{category-name}/
├── market_report.md       # Structured Markdown report (user-facing)
└── research_data.json     # Raw API response data (for re-analysis)
```

Reports include: screening methodology, KPI summary, multi-dimensional analysis (tables + insights), tiered conclusion.

## Known Limitations

- **Review sampling**: max 20 reviews per call regardless of `size` parameter
- **Traffic source**: `traffic_source` tool may return unrelated product traffic data; cross-verify with `traffic_keyword` + `traffic_keyword_stat`
- **Keyword research**: `keyword_research` ignores the `keyword` filter parameter — use `keyword_miner` for targeted keyword exploration
- **SSE transport**: WebSocket/SSE connections to the SellerSprite MCP server may fail due to CDN session affinity; use HTTP POST only

## License

MIT
