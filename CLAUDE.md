# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Amazon competitive intelligence and category selection analysis workspace using Sorftime MCP (Model Context Protocol) data service. Three core skills:
- **amazon-analyse**: Single listing competitor analysis (`/amazon-analyse {ASIN} {SITE}`)
- **category-selection**: Category-level product selection analysis with five-dimensional scoring model (`/category-select "{Category}" {SITE}`)
- **skill-creator**: Meta-skill for creating new Claude skills

## Sorftime MCP Integration

### API Configuration
- **Config file**: `.mcp.json` - stores API key and endpoint
- **Endpoint**: `https://mcp.sorftime.com?key={API_KEY}`
- **Protocol**: `streamableHttp` using Server-Sent Events (SSE)
- **Get API key**: https://sorftime.com/zh-cn/mcp

### SSE Response Handling
All Sorftime responses return as SSE format: `event: message\ndata: {JSON}\n\n`

**Critical patterns**:
- Chinese text is Unicode-escaped (`\u4ea7\u54c1`) → use `codecs.decode(text, 'unicode-escape')` or `json.loads()` with proper encoding
- Large responses (>25KB) are saved to temp files → use `Read` tool with offset/limit or `Grep` for extraction
- Increment `id` field for each request in a session (1, 2, 3...)

### Direct curl invocation (when MCP unavailable):
```bash
curl -s -X POST "https://mcp.sorftime.com?key={API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"TOOL_NAME","arguments":{"amzSite":"US","nodeId":"NODE_ID"}}}'
```

## Skills Architecture

Skills located in `.claude/skills/skill-name/`:
- `SKILL.md` - YAML frontmatter + instructions (trigger mechanism)
- `scripts/` - Executable Python utilities
- `references/` - API docs, patterns loaded on-demand
- `assets/` - Templates for output files (HTML, Excel templates)

### category-selection Skill Updates (v6.0 - 2026-03-04)

**Recent Improvements**:
- ✅ **自动编码修复**: 集成 Mojibake (UTF-8/Latin-1 双重编码) 自动检测和修复
- ✅ **错误容错机制**: 趋势 API 失败时不影响整体流程
- ✅ **Markdown 报告**: 新增自动生成 Markdown 分析报告
- ✅ **执行状态跟踪**: 显示每步执行状态和最终总结
- ✅ **关键词解析增强**: 3 种解析策略支持更多数据格式
- ✅ **独立编码修复工具**: `fix_encoding.py` 可修复现有 JSON 文件

**故障排查**:
- 如遇乱码: 运行 `python .claude/skills/category-selection/scripts/fix_encoding.py <json_file>`
- 如遇解析失败: 查看 `.claude/skills/category-selection/SKILL.md` 中的故障排查章节

### amazon-analyse (`/amazon-analyse {ASIN} {SITE}`)
**Trigger**: User provides ASIN for competitor listing analysis

**Analysis stages**:
1. ASIN validation via `product_detail`
2. Data collection: product, reviews, traffic terms, competitor keywords, trends
3. SWOT analysis and strategic recommendations
4. Report saved to `reports/analysis_{ASIN}_{SITE}_{date}.md`

**Key tools**: `product_detail`, `product_reviews`, `product_traffic_terms`, `competitor_product_keywords`, `product_trend`

### category-selection (`/category-select "{Category}" {SITE} --limit N`)
**Trigger**: User requests category analysis (default Top 20 products)

**Five-dimensional scoring model** (100 points total):
| Dimension | Points | Metric |
|-----------|--------|--------|
| Market Size | 20 | Category monthly revenue |
| Growth Potential | 25 | Year-over-year growth rate |
| Competition | 20 | HHI index, CR3 concentration |
| Entry Barrier | 20 | Avg review count, Amazon share, new product % |
| Profit Margin | 15 | 1688 cost comparison |

**Rating thresholds**: 80-100 (优秀), 60-79 (良好), 40-59 (一般), 0-39 (较差)

**Analysis stages**:
1. Search category → get nodeId via `category_name_search`
2. Fetch Top100 products + stats via `category_report`
3. (Optional) Fetch individual product details via `product_detail`
4. Calculate scores and generate three report formats:
   - Markdown: `category-reports/{Category}_{Site}_{date}/report.md`
   - Excel: `category-reports/{Category}_{Site}_{date}/category_report_*.xlsx`
   - HTML Dashboard: `category-reports/{Category}_{Site}_{date}/dashboard.html`

**Report output structure**:
```
category-reports/
└── {Category}_{Site}_{YYYYMMDD}/
    ├── index.html        # Navigation page
    ├── dashboard.html    # Interactive dashboard with charts
    ├── report.md         # Full markdown analysis
    ├── category_report_*.xlsx  # Excel with multiple sheets
    └── data.json         # Raw data for further processing
```

## Data Processing Utilities

Located in `.claude/skills/category-selection/scripts/`:

**`data_utils.py`** - Core data processor class with:
- `calculate_hhi()` - Herfindahl-Hirschman Index for market concentration
- `calculate_cr()` - Concentration Ratio (CR3, CR5)
- `group_by_price_range()` - Price distribution analysis
- `group_by_rating_range()` - Rating distribution analysis
- `filter_new_products()` - New product identification (days_online threshold)
- `analyze_brand_distribution()` - Brand market share calculation
- `analyze_seller_distribution()` - Seller source analysis (CN/US/Brand)
- `calculate_five_dimension_score()` - Scoring algorithm
- `prepare_html_data()` - Format data for HTML template rendering

**`parse_sorftime_sse.py`** - SSE response parser
- Extracts JSON data from SSE format
- Decodes Unicode-escaped Chinese text
- Handles large responses saved to temp files

## Report Generation Patterns

### Excel Report Generation
Use `xlsxwriter` library (not `openpyxl` - simpler for large files):
```python
wb = xlsxwriter.Workbook(output_file)
header_fmt = wb.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white'})
ws = wb.add_worksheet("Sheet Name")
ws.write(row, col, value, format)
chart = wb.add_chart({'type': 'column'})
ws.insert_chart('A1', chart)
wb.close()
```

### HTML Dashboard Template
Located in `.claude/skills/category-selection/assets/dashboard_template.html`
Uses Chart.js for visualizations. Template variables are replaced using:
- Direct substitution for scalars
- `json.dumps()` for arrays/objects passed to JavaScript

## Common Issues and Solutions

### Unicode-decoded Chinese text in responses
Sorftime returns `\u4ea7\u54c1` format. Solution:
```python
import codecs
decoded_text = codecs.decode(encoded_text, 'unicode-escape')
# Or for mojibake (UTF-8 decoded as Latin-1):
fixed_text = bad_text.encode('latin-1').decode('utf-8')
```

### Large responses saved to temp files
When tool returns "Output too large... saved to: {path}":
```python
# Use Grep to extract specific patterns
grep('"月销量":"(\\d+)"' /path/to/tempfile)

# Or use Read with offset/limit for file sections
Read(file_path, offset=1, limit=500)
```

### ASIN not found in Sorftime
Always validate ASIN first with `product_detail`. If "未查询到对应产品":
- Retry with `product_search` using ASIN or keywords
- Check if correct Amazon site
- Ask user to verify ASIN

## Supported Sites

**Amazon**: US, GB, DE, FR, IN, CA, JP, ES, IT, MX, AE, AU, BR, SA
**TikTok**: US, GB, MY, PH, VN, ID
**1688**: China wholesale platform

## Python Dependencies

Scripts in this project require:
- `xlsxwriter` - Excel report generation
- Standard library: `json`, `codecs`, `re`, `datetime`, `sys`

Install with: `pip install xlsxwriter`

## Creating New Skills

The `skill-creator` skill provides tooling for creating new skills:

```bash
# Initialize a new skill
.claude/skills/skill-creator/scripts/init_skill.py <skill-name> --path .claude/skills

# Package a skill into .skill file
.claude/skills/skill-creator/scripts/package_skill.py <skill-folder>
```

Skill structure:
```
skill-name/
├── SKILL.md         # YAML frontmatter + instructions
├── scripts/         # Executable Python utilities
├── references/      # API docs, patterns loaded on-demand
└── assets/          # Templates for output files
```

## Report Naming Conventions

| Report Type | Pattern | Example |
|-------------|---------|---------|
| Product analysis | `analysis_{ASIN}_{SITE}_{YYYYMMDD}.md` | `analysis_B07PWTJ4H1_US_20260302.md` |
| Category reports | `{Category}_{Site}_{YYYYMMDD}/` | `Sofas_US_20260303/` |
