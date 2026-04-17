# Fundamental Analyst Estimates (analyst69) Feature Engineering Analysis Report

**Dataset**: analyst69
**Category**: Analyst
**Region**: EUR
**Delay**: 1
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 216

---

## Executive Summary

**Primary Question Answered by Dataset**: What do professional analysts expect regarding companies' future financial performance across income statement, balance sheet, and cash flow metrics?

**Key Insights from Analysis**:
- The dataset captures consensus estimates ("best" estimates) for both current and next fiscal years, enabling temporal comparison of expectations
- Coverage spans core profitability metrics (EPS, EBITDA), valuation ratios (P/E), balance sheet health (NAV, Net Debt), and capital returns (DPS)
- Daily update frequency with delay=1 makes this suitable for alpha generation based on estimate revision momentum
- Expected report date fields enable event-driven features around earnings announcements

**Critical Field Relationships Identified**:
- Current year vs. next year estimates for the same metric (temporal growth structure)
- Cross-metric relationships (Sales → EBITDA → EPS conversion chain)
- Estimate levels vs. expected report dates (time-to-event dynamics)

**Most Promising Feature Concepts**:
1. **Estimate Revision Momentum** (ts_delta) - captures analyst sentiment shifts quickly due to daily updates
2. **EBITDA-EPS Conversion Efficiency** - reveals operating leverage expectations implicit in analyst models
3. **Inter-Temporal Estimate Coherence** - correlation between current/next year estimates indicates forecast consistency

---

## Dataset Deep Understanding

### Dataset Description
Fundamental Analyst Estimates (analyst69) provides consensus analyst forecasts for key financial metrics including earnings per share (EPS), EBITDA, sales, dividends per share (DPS), cash flow per share (CPS), book value per share (BPS), return on equity (ROE), return on assets (ROA), net asset value (NAV), and net debt. The dataset includes both current fiscal year and next fiscal year estimates, along with expected earnings report dates and times. Data is updated daily with a 1-day delay, providing timely capture of analyst revisions.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `anl69_eps_best_eeps_cur_yr` | Consensus EPS Current Year | Float | Daily | ~85% |
| `anl69_eps_best_eeps_nxt_yr` | Consensus EPS Next Year | Float | Daily | ~80% |
| `anl69_ebitda_best_eeps_cur_yr` | Consensus EBITDA Current Year | Float | Daily | ~75% |
| `anl69_sales_best_eeps_cur_yr` | Consensus Sales/Revenue Current Year | Float | Daily | ~90% |
| `anl69_roe_best_eeps_cur_yr` | Consensus ROE Current Year | Float | Daily | ~70% |
| `anl69_dps_best_eeps_cur_yr` | Consensus Dividend Per Share Current Year | Float | Daily | ~65% |
| `anl69_eps_expected_report_dt` | Expected Earnings Report Date | Date | Daily | ~95% |
| `anl69_rec_best_eeps_cur_yr` | Consensus Recommendation Current Year | Float | Daily | ~60% |
| `anl69_target_best_eeps_cur_yr` | Consensus Price Target Current Year | Float | Daily | ~70% |
| `anl69_best_crncy_iso` | Reporting Currency ISO Code | String | Static | 100% |

*(Additional 206 fields covering metrics like BPS, CPS, ROA, NAV, Net Debt, Free Cash Flow, Pretax Profit, Operating Profit, EPS GAAP, and corresponding next-year estimates)*

### Field Deconstruction Analysis

#### `anl69_eps_best_eeps_cur_yr`: Consensus EPS Current Year Estimate
- **What is being measured?**: The aggregated consensus earnings per share forecast for the current fiscal year from contributing sell-side analysts
- **How is it measured?**: Aggregation (mean or median) of individual analyst forecasts submitted to data providers; "best" indicates the highest quality consensus methodology
- **Time dimension**: Point-in-time daily snapshot that evolves as analysts revise forecasts throughout the fiscal year
- **Business context**: Primary metric for equity valuation (P/E ratios) and earnings surprise calculations; reflects market expectations of profitability
- **Generation logic**: Derived from bottom-up analyst models covering revenue, margins, taxes, and share count; updated intraday as analysts publish research
- **Reliability considerations**: Coverage varies by market cap (higher for large caps); stale estimates may persist for illiquid names; fiscal year alignment differs across companies

#### `anl69_eps_expected_report_dt`: Expected Earnings Report Date
- **What is being measured?**: The anticipated calendar date for the company's next quarterly or annual earnings announcement
- **How is it measured?**: Derived from company investor relations calendars, exchange filings, or historical reporting patterns
- **Time dimension**: Forward-looking date that updates as companies confirm or revise announcement schedules
- **Business context**: Defines the horizon for estimate validity and the timing of potential earnings surprises; critical for event studies
- **Generation logic**: Usually based on company guidance ("we expect to report in late January") or historical patterns (e.g., 45 days after quarter-end)
- **Reliability considerations**: Dates may shift due to holidays, audit delays, or corporate changes; time zone differences for EUR region reporting

#### `anl69_sales_best_eeps_cur_yr`: Consensus Sales Current Year Estimate
- **What is being measured?**: Top-line revenue consensus forecast for the current fiscal year
- **How is it measured?**: Aggregation of analyst revenue models, often built from volume and price assumptions by segment
- **Time dimension**: Annual fiscal period aggregate (not quarterly), though analysts model quarterly path to reach annual total
- **Business context**: Growth indicator independent of margin changes; used to validate EPS quality (are earnings growing due to sales or just margins?)
- **Generation logic**: Sum of analyst revenue forecasts; may include constant currency adjustments for EUR region multinationals
- **Reliability considerations**: Less prone to accounting discretion than EPS; stronger coverage for industrial/consumer sectors than financials

### Field Relationship Mapping

**The Story This Data Tells**:
Analysts construct detailed financial models projecting companies' future performance. This dataset captures the consensus of those expectations across the income statement (Sales → EBITDA → EBIT → EPS), balance sheet (NAV, Net Debt), and returns (DPS, ROE). The dual-year structure (current vs. next) reveals growth trajectories, while expected report dates anchor these expectations in time. Changes in these estimates reflect new information flow, sentiment shifts, and model refinements.

**Key Relationships Identified**:
1. **Vertical Income Statement Chain**: Sales estimates flow through to EBITDA (operating leverage), then to EPS (financial leverage and taxes). Disruptions in this chain indicate changing margin expectations.
2. **Temporal Consistency**: Current year and next year estimates for the same metric should be logically consistent; large disparities suggest inflection points or model uncertainty.
3. **Capital Allocation Coherence**: DPS, Buyback (implied in EPS share count), and Net Debt estimates should reflect consistent capital allocation priorities.
4. **Event Clock**: Expected report dates create a countdown mechanism; estimate revisions intensify as report dates approach (guidance game).

**Missing Pieces That Would Complete the Picture**:
- Quarterly estimate breakdowns (only annual fiscal year estimates provided)
- Dispersion statistics (standard deviation of analyst estimates, number of contributors)
- Historical actuals for surprise calculation (would need to be joined with fundamental data)
- Individual analyst identifiers for reputation-weighted consensus
- Revision timestamps (direction of change, not just levels)

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: EPS Estimate Stability Score
- **Sample Fields Used**: eps_best_eeps_cur_yr
- **Definition**: Rolling standard deviation of current year EPS estimates over 20-day window measuring consensus volatility
- **Why This Feature**: Low volatility indicates stable analyst views and high conviction; high volatility suggests disagreement or uncertainty about earnings trajectory
- **Logical Meaning**: Measures the steadiness of professional opinion; stable estimates suggest information efficiency, unstable estimates suggest pending information arrival
- **is filling nan necessary**: Daily updates with delay=1 suggest good continuity, but sparse coverage for some EUR small-caps may require ts_backfill(20) to avoid look-ahead bias. If NaN appears, it likely means no analyst coverage (meaningful missingness), so group_mean() filling would be inappropriate.
- **Directionality**: Low values (stable) generally indicate lower uncertainty; high values indicate potential earnings risk or event volatility
- **Boundary Conditions**: Near-zero values suggest stale/consensus estimates; extremely high values may precede earnings announcements or guidance changes
- **Implementation Example**: `ts_std_dev({eps_best_eeps_cur_yr}, 20)`

**Concept**: Inter-Temporal Estimate Coherence
- **Sample Fields Used**: eps_best_eeps_cur_yr, eps_best_eeps_nxt_yr
- **Definition**: 60-day rolling correlation between current year and next year EPS estimates
- **Why This Feature**: High correlation suggests analysts view earnings as persistent (good year followed by good year); breakdowns indicate cyclical inflection or one-time items
- **Logical Meaning**: Captures the structural relationship between near-term and long-term earnings expectations; coherence breakdowns often precede rating changes
- **is filling nan necessary**: Both fields should have similar coverage patterns given they're from the same dataset module; ts_backfill(5) on each before correlation to handle staggered updates.
- **Directionality**: High correlation (0.8+) indicates stable business model; low/negative correlation indicates transition year or cyclical peak/trough
- **Boundary Conditions**: Correlation approaching 1.0 may indicate mechanical forecasting (next year = current year * 1.1); negative correlation suggests turnaround situation
- **Implementation Example**: `ts_corr({eps_best_eeps_cur_yr}, {eps_best_eeps_nxt_yr}, 60)`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Short-Term Estimate Revision Momentum
- **Sample Fields Used**: eps_best_eeps_cur_yr
- **Definition**: 5-day difference in current year EPS estimates capturing recent analyst sentiment shifts
- **Why This Feature**: Daily updates allow capture of fresh information; 5-day window balances noise vs. signal for revision strategies
- **Logical Meaning**: Directional change in consensus expectations; positive values indicate upgrades, negative indicate downgrades
- **is filling nan necessary**: Daily data rarely has gaps, but if present, ts_backfill(5) ensures we capture last known estimate before differencing to avoid false zeros.
- **Directionality**: Positive values bullish (upgrades); negative values bearish (downgrades); magnitude indicates conviction of change
- **Boundary Conditions**: Extreme values may follow earnings announcements or guidance updates; zero values indicate stale consensus
- **Implementation Example**: `ts_delta({eps_best_eeps_cur_yr}, 5)`

**Concept**: EBITDA Estimate Trajectory
- **Sample Fields Used**: ebitda_best_eeps_cur_yr
- **Definition**: 20-day change in EBITDA estimates capturing operating profit expectation shifts
- **Why This Feature**: EBITDA is less affected by financial engineering than EPS; changes indicate core operational sentiment shifts
- **Logical Meaning**: Top-line profitability momentum independent of capital structure changes; often leads EPS revisions for companies with stable leverage
- **is filling nan necessary**: EBITDA coverage may be sparser than EPS for some EUR names; ts_backfill(20) recommended before applying ts_delta to ensure valid prior values.
- **Directionality**: Positive indicates operating momentum; negative indicates margin compression or revenue challenges
- **Boundary Conditions**: Large changes often coincide with management guidance or industry conferences; seasonal businesses show cyclical patterns
- **Implementation Example**: `ts_delta({ebitda_best_eeps_cur_yr}, 20)`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Estimate Volatility Spike Detection
- **Sample Fields Used**: eps_best_eeps_cur_yr
- **Definition**: Change in rolling 20-day volatility of estimates (second moment shift) over 5-day window
- **Why This Feature**: Sudden increases in estimate dispersion/volatility often precede earnings events or guidance confusion; detects uncertainty inflection
- **Logical Meaning**: Anomalous instability in professional forecasts; indicates breaking news, pending announcements, or model parameter uncertainty
- **is filling nan necessary**: Requires two levels of time series calculation; ensure robust handling by applying ts_backfill(25) to underlying data to cover both windows.
- **Directionality**: High positive values indicate sudden uncertainty spike (often bearish due to risk premium); negative values indicate consensus crystallizing
- **Boundary Conditions**: Spikes typically occur 1-2 weeks before earnings or after guidance surprises; sustained elevation suggests ongoing uncertainty
- **Implementation Example**: `ts_delta(ts_std_dev({eps_best_eeps_cur_yr}, 20), 5)`

**Concept**: Report Date Uncertainty Indicator
- **Sample Fields Used**: eps_expected_report_dt
- **Definition**: Days since last change in expected report date using days_from_last_change operator
- **Why This Feature**: Stability in reporting dates indicates corporate planning consistency; frequent changes may signal audit issues, M&A activity, or operational instability
- **Logical Meaning**: Corporate event planning stability; unstable dates often correlate with negative events or complex reporting situations
- **is filling nan necessary**: Date fields should not have NaNs unless coverage is missing; if NaN present, it indicates no known report date (significant signal), do not fill.
- **Directionality**: Low values (recent change) indicate schedule uncertainty; high values (stable for long period) indicate predictable reporting
- **Boundary Conditions**: Value resetting to 0 indicates date revision; values > 90 suggest long-stable schedule (quarterly reporters)
- **Implementation Example**: `days_from_last_change({eps_expected_report_dt})`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: EBITDA-to-EPS Conversion Efficiency
- **Sample Fields Used**: eps_best_eeps_cur_yr, ebitda_best_eeps_cur_yr
- **Definition**: Ratio of EPS to EBITDA estimates capturing implicit operating and financial leverage in analyst models
- **Why This Feature**: Reveals how analysts expect operating profits to convert to earnings; changes indicate tax rate, interest, or depreciation forecast shifts
- **Logical Meaning**: Net profitability extraction rate from operations; structural declines may indicate rising interest costs or tax rate changes
- **is filling nan necessary**: Ensure both metrics have valid data; divide operation will propagate NaN if either input is NaN. Use ts_backfill(5) on both if coverage differs slightly.
- **Directionality**: Higher values indicate efficient profit conversion (high margins, low leverage); declining values suggest margin pressure or financial cost increases
- **Boundary Conditions**: Extreme values near 0 or negative indicate losses; values > 0.5 unusual for capital-intensive industries (check for one-time items)
- **Implementation Example**: `divide({eps_best_eeps_cur_yr}, {ebitda_best_eeps_cur_yr})`

**Concept**: Sales-EPS Correlation Quality
- **Sample Fields Used**: sales_best_eeps_cur_yr, eps_best_eeps_cur_yr
- **Definition**: 40-day rolling correlation between sales and EPS estimate changes measuring top-line dependency
- **Why This Feature**: High correlation indicates earnings driven by volume/price (quality earnings); low correlation indicates cost-driven or financial engineering earnings
- **Logical Meaning**: Earnings quality indicator based on revenue correlation; divergence often signals margin compression/expansion or non-operating items
- **is filling nan necessary**: Sales and EPS updates may be asynchronous; ts_backfill(10) on both series before correlation to align observation dates.
- **Directionality**: High correlation (>0.7) indicates revenue-quality earnings; low correlation suggests cost-cutting or buyback-driven EPS growth
- **Boundary Conditions**: Correlation breakdowns often occur during inflationary periods (revenue up, margins down) or restructuring
- **Implementation Example**: `ts_corr({sales_best_eeps_cur_yr}, {eps_best_eeps_cur_yr}, 40)`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Implied Fiscal Year Growth Structure
- **Sample Fields Used**: eps_best_eeps_cur_yr, eps_best_eeps_nxt_yr
- **Definition**: Forward growth rate implied by next year vs. current year estimate spread
- **Why This Feature**: Captures the structural growth trajectory embedded in analyst models; positive spread indicates growth expectations
- **Logical Meaning**: Expected year-over-year earnings growth rate; reflects business cycle position and company-specific growth initiatives
- **is filling nan necessary**: Next year estimates may have sparser coverage than current year; ts_backfill(20) on both to ensure paired observations exist.
- **Directionality**: Positive values indicate growth expected; negative values indicate earnings decline expected; magnitude indicates growth rate
- **Boundary Conditions**: Extreme values (>50% or <-50%) may indicate base year anomalies or transformational events
- **Implementation Example**: `divide(subtract({eps_best_eeps_nxt_yr}, {eps_best_eeps_cur_yr}), {eps_best_eeps_cur_yr})`

**Concept**: Multi-Metric Revision Alignment
- **Sample Fields Used**: eps_best_eeps_cur_yr, sales_best_eeps_cur_yr
- **Definition**: Product of signs of 20-day estimate changes for EPS and Sales (co-directionality indicator)
- **Why This Feature**: Alignment between revenue and earnings revisions indicates consistent business momentum; divergence signals margin pressure
- **Logical Meaning**: Directional agreement between top-line and bottom-line forecasts; +1 indicates both upgrading, -1 indicates disagreement, 0 indicates one flat
- **is filling nan necessary**: Calculate deltas first, then signs; handle NaNs in delta by returning NaN for the product (conservative approach).
- **Directionality**: +1 (both upgrading) bullish signal; -1 (revenue up but earnings down) bearish margin signal; 0 indicates mixed or stale data
- **Boundary Conditions**: Persistent -1 readings indicate inflationary/cost headwinds; persistent +1 indicates operating leverage
- **Implementation Example**: `multiply(sign(ts_delta({eps_best_eeps_cur_yr}, 20)), sign(ts_delta({sales_best_eeps_cur_yr}, 20)))`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Cumulative Revision Pressure (Quarterly)
- **Sample Fields Used**: eps_best_eeps_cur_yr
- **Definition**: 63-day (quarter) sum of daily estimate changes measuring total revision momentum over fiscal quarter
- **Why This Feature**: Captures persistent directional pressure vs. noise; large absolute values indicate sustained analyst sentiment shift
- **Logical Meaning**: Total adjustment to earnings expectations over a fiscal quarter; proxy for information arrival intensity
- **is filling nan necessary**: Daily changes should be calculated on backfilled series to avoid summing false zeros; use ts_backfill(5) on level data before differencing.
- **Directionality**: Large positive indicates sustained upgrades; large negative indicates sustained downgrades; near zero indicates mean-reverting noise
- **Boundary Conditions**: Cumulative values plateau when estimates stabilize; inflection points often lead price momentum
- **Implementation Example**: `ts_sum(ts_delta({eps_best_eeps_cur_yr}, 1), 63)`

**Concept**: Long-Term Estimate Drift
- **Sample Fields Used**: eps_best_eeps_cur_yr
- **Definition**: 63-day difference in current year estimates capturing persistent drift vs. short-term noise
- **Why This Feature**: Quarterly horizon aligns with fiscal reporting; distinguishes trend from temporary volatility
- **Logical Meaning**: Persistent bias in analyst revisions; drift indicates information diffusion or slow-moving sentiment changes
- **is filling nan necessary**: 63-day lookback requires ts_backfill(63) to ensure valid prior values for illiquid names in EUR universe.
- **Directionality**: Positive indicates ongoing upgrades (momentum); negative indicates ongoing downgrades (value trap risk)
- **Boundary Conditions**: Values exceeding 10% of stock price indicate significant forecast changes; check for earnings events or guidance shifts
- **Implementation Example**: `subtract({eps_best_eeps_cur_yr}, ts_delay({eps_best_eeps_cur_yr}, 63))`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Cross-Sectional Revision Percentile
- **Sample Fields Used**: eps_best_eeps_cur_yr
- **Definition**: Gaussian quantile transform of 5-day EPS revision across EUR universe
- **Why This Feature**: Relative ranking identifies extreme movers vs. peers; mean-reverting strategies benefit from cross-sectional z-scores
- **Logical Meaning**: Relative analyst sentiment intensity; extreme percentiles indicate outliers worthy of attention
- **is filling nan necessary**: Quantile operator handles NaNs by excluding from ranking; no filling necessary to preserve valid cross-sectional comparison.
- **Directionality**: High percentiles (top decile) indicate strongest upgrades; low percentiles indicate strongest downgrades; zero crossings significant
- **Boundary Conditions**: Uniform distribution expected; clustering near extremes indicates broad sector revisions
- **Implementation Example**: `quantile(ts_delta({eps_best_eeps_cur_yr}, 5), driver=gaussian)`

**Concept**: ROE-EPS Expectation Spread
- **Sample Fields Used**: roe_best_eeps_cur_yr, eps_best_eeps_cur_yr
- **Definition**: Difference between consensus ROE and EPS estimates (different scales, captures relative profitability expectations)
- **Why This Feature**: ROE is percentage-based, EPS is currency-based; spread anomalies indicate capital structure changes or share count volatility
- **Logical Meaning**: Discrepancy between return on equity and absolute earnings expectations; divergence may signal buyback impact or equity issuance
- **is filling nan necessary**: ROE and EPS have different coverage patterns; ts_backfill(20) on both to maximize paired observations.
- **Directionality**: Large positive spread indicates high profitability expectations relative to earnings level (may indicate small equity base)
- **Boundary Conditions**: Extreme values indicate potential data errors or extraordinary items affecting one metric but not the other
- **Implementation Example**: `subtract({roe_best_eeps_cur_yr}, {eps_best_eeps_cur_yr})`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Core Earnings Expectation (Normalized)
- **Sample Fields Used**: eps_best_eeps_cur_yr
- **Definition**: Gaussian quantile of raw EPS estimate level cross-sectionally
- **Why This Feature**: The essential information is the relative positioning of earnings expectations; normalization enables cross-sector comparison
- **Logical Meaning**: Pure expectation level independent of share price; captures the central thesis of analyst coverage
- **is filling nan necessary**: NaN indicates no coverage; quantile operator handles this naturally by exclusion; filling would distort distribution.
- **Directionality**: High values indicate high earnings expectations (growth or mature); low values indicate low/negative earnings expectations
- **Boundary Conditions**: Fat tails indicate bimodal market (growth vs. value); center clustering indicates consensus on normalized earnings
- **Implementation Example**: `quantile({eps_best_eeps_cur_yr}, driver=gaussian)`

**Concept**: Expectation Revision Velocity
- **Sample Fields Used**: eps_best_eeps_cur_yr
- **Definition**: Percentage change in estimates over 5 days (velocity of change)
- **Why This Feature**: Captures the rate of change rather than absolute level; essential for momentum strategies in analyst data
- **Logical Meaning**: Speed of information incorporation; high velocity indicates breaking news or sentiment shifts; low velocity indicates stable views
- **is filling nan necessary**: Division by prior value requires ts_backfill(10) to ensure denominator is valid; zero handling requires care (return NaN for zero denominator).
- **Directionality**: Positive values indicate accelerating upgrades; negative values indicate accelerating downgrades; magnitude indicates speed
- **Boundary Conditions**: Values >0.10 (10% revision in week) indicate significant events; values near zero indicate drift
- **Implementation Example**: `divide(ts_delta({eps_best_eeps_cur_yr}, 5), ts_delay({eps_best_eeps_cur_yr}, 5))`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Varies significantly by metric; EPS (~85%), Sales (~90%), but NAV/Net Debt may be sparser (~60-70%) for non-financials in EUR
- **Timeliness**: Daily updates with delay=1 means data is T-1; suitable for daily alpha but not high-frequency
- **Accuracy**: "Best" estimates use quality-weighted consensus methodology; more reliable than simple means for EUR region with varying analyst quality
- **Potential Biases**: Survivorship bias in estimates (analysts stop covering poorly performing stocks); currency translation issues for multinationals reporting in different currencies than `best_crncy_iso`

### Computational Complexity
- **Lightweight features**: ts_delta, divide, subtract operations on single fields (Q2, Q4, Q5, Q7, Q8 examples)
- **Medium complexity**: ts_corr, ts_std_dev, ts_sum requiring 20-60 day lookbacks (Q1, Q2, Q4, Q6 examples)
- **Heavy computation**: Nested operators (ts_delta of ts_std_dev in Q3) or long lookbacks (63-day in Q6); recommend pre-calculation for production

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Short-Term Estimate Revision Momentum** (Q2) - classic price-momentum leading indicator with strong academic support
2. **EBITDA-to-EPS Conversion Efficiency** (Q4) - captures operating leverage, often overlooked in simple EPS strategies
3. **Implied Fiscal Year Growth Structure** (Q5) - forward-looking growth rate not dependent on historical data

**Tier 2 (Secondary Priority)**:
1. **Cumulative Revision Pressure** (Q6) - captures sustained sentiment better than single-period changes
2. **Cross-Sectional Revision Percentile** (Q7) - essential for relative-value strategies in EUR sector-neutral contexts
3. **EPS Estimate Stability Score** (Q1) - risk management feature identifying uncertain earnings situations

**Tier 3 (Requires Further Validation)**:
1. **Report Date Uncertainty Indicator** (Q3) - requires validation that date changes predict negative events in EUR markets
2. **ROE-EPS Expectation Spread** (Q7) - mixing percentage and currency units requires careful normalization testing
3. **Inter-Temporal Estimate Coherence** (Q1) - 60-day correlation may be too slow for daily strategies

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How does the "best" consensus methodology differ from simple mean/median, and does it weight certain analysts more heavily in EUR region?
2. Do expected report dates (`expected_report_dt`) shift systematically before negative surprises (guidance warnings)?
3. What is the correlation between estimate revision magnitude and subsequent price drift in EUR mid-caps (TOPCS1600)?

### Recommended Additional Data:
- **Analyst15 or similar**: To obtain estimate dispersion (standard deviation) and number of contributors for uncertainty weighting
- **Price data**: To calculate P/E on expected earnings and validate surprise calculations
- **Fundamental actuals**: To calculate earnings surprise vs. these estimates for backtesting
- **Short interest data**: To test if estimate downgrades correlate with short selling in EUR markets

### Assumptions to Challenge:
- **Analysts are informed**: Assumes sell-side estimates contain information not in price; may not hold for crowded names or in EUR where retail flows dominate
- **Daily changes matter**: Assumes T-1 updates are timely; may need to verify if revisions cluster at specific times (morning vs. close)
- **Cross-metric coherence**: Assumes Sales/EBITDA/EPS move together; in inflationary periods, these may diverge significantly (stagflation scenario)

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence (consensus expectations vs. individual forecasts)
2. Question-driven feature generation (8 fundamental questions applied to analyst estimate context)
3. Logical validation of each feature concept against EUR market microstructure
4. Transparent documentation of reasoning including NaN handling and boundary conditions

**Design Principles**:
- Focus on logical meaning over conventional patterns (e.g., EBITDA conversion efficiency vs. simple P/E)
- Every feature must answer a specific question about stability, change, anomaly, or structure
- Clear documentation of "why" for each suggestion based on analyst behavior and information diffusion
- Emphasis on cross-metric interactions (income statement chain) unique to analyst data

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate report date uncertainty hypothesis, gather dispersion data for Tier 3 features*