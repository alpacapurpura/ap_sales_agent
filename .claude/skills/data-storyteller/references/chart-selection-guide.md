# Chart Selection Guide

## Decision Tree

Ask: **"What do you want to show?"**

### Comparison between categories
→ **Bar chart vertical** (≤7 categories)
→ **Bar chart horizontal** (>7 categories or long names, also for rankings)
→ NEVER pie chart

### Trend over time
→ **Line chart** (1-3 series max)
→ **Area chart** (to show accumulated volume)
→ **Sparkline** (inside a scorecard, no axes — just trajectory)

### Part of a whole (composition)
→ **Stacked bar** (composition by category, allows comparison)
→ **Treemap** (many categories with hierarchy)
→ NEVER pie chart

### Single key number (KPI)
→ **Scorecard**: value + delta% + trend arrow + sparkline
→ Always include comparison period

### Relationship between two variables
→ **Scatter plot** (if >20 data points)
→ **Table with conditional highlighting** (if few data points)

### Distribution
→ **Histogram** (continuous data)
→ **Grouped bar chart** (discrete categories)

### Flow / process / conversion
→ **Funnel chart** (sequential conversion, e.g., visitors → leads → MQLs → SQLs)
→ **Sankey diagram** (multi-path flow, e.g., traffic sources → conversion paths)

### Time patterns (day/hour activity)
→ **Heatmap** (rows = days, columns = hours, color = intensity)

---

## Universal Rules

| Rule | Why |
|------|-----|
| Value + Delta + Trend always together | A number alone is meaningless. "2,340 clicks (+18%↑)" tells a story |
| Max 3 series in a line chart | More than 3 lines = visual noise |
| Y-axis starts at 0 (bar charts) | Truncating exaggerates differences, misleads |
| Y-axis can skip 0 (line charts) | For showing variation, truncation is valid |
| Tooltips mandatory | Every data point must have hover with exact value + context |
| Responsive: ≤768px → scorecards only | Complex charts don't work on mobile — show KPIs only |
| Max 6-8 colors per chart | More = indistinguishable |
| Labels: plain language + technical tooltip | "Costo por Lead: $12.50" not "CPL: $12.50" — tooltip shows formula |
| Sort bar charts by value, not alphabetically | The ranking IS the insight |
| Left-align text, right-align numbers in tables | Readability convention |

---

## Time Handling

### Date Range Picker (always visible, top-right)

**Required presets:**
- Last 7 days
- Last 30 days
- This month
- Last month
- Custom range (calendar)

**Comparison toggle:**
- "vs previous period" (default)
- "vs same period last year"
- Shows ghost line/bar overlay + delta badge

### Temporal Display Patterns

| Pattern | Use Case |
|---------|----------|
| Sparkline in scorecard | Mini trend (7/30 days) inside the KPI card |
| Ghost line overlay | Previous period as dashed/faded line behind current |
| Delta badge | "+12.5%" green or "-3.2%" red next to value |
| Period-over-period table | Columns: This Period / Last Period / Change / Change % |
| Trend arrow | ↑ green / ↓ red / → gray for flat |

---

## Progressive Disclosure Levels

| Level | What's Shown | Access |
|-------|-------------|--------|
| **Glance** | 4-5 scorecards with deltas | Default view (top of page) |
| **Explore** | Line/bar charts showing trends | Scroll down or tab |
| **Analyze** | Tables with sortable columns, breakdowns | Click to drill |
| **Raw** | Export CSV, API data | "Export" button |

Each level is ONE click deeper. Never show analyze-level detail at glance level.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Pie chart | Horizontal bar chart | Humans can't compare angles; lengths are intuitive |
| 3D charts | 2D always | 3D adds visual noise, distorts proportions |
| Dual Y-axis | Two separate charts stacked | Dual axes confuse which series maps to which axis |
| Gauge / speedometer | Scorecard with delta | Gauges waste space and hide trend |
| Decorative animations | Functional transitions (fade-in on load) | Animation should aid comprehension, not distract |
| Rainbow colors | Semantic palette (channel=color, positive=green, negative=red) | Arbitrary colors add cognitive load |
| Auto-rotating dashboards | Static with manual navigation | Auto-rotation frustrates users trying to read |
| Data tables as primary viz | Charts primary, tables for drill-down | Tables require analysis; charts tell stories instantly |
