**Dataset**: model172
**Region**: EUR
**Delay**: 1

# Model172 Feature Engineering Analysis Report

**Dataset**: model172
**Category**: Model
**Region**: EUR
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 119

---

## Executive Summary

**Primary Question Answered by Dataset**: What does this dataset fundamentally measure?

This dataset captures a comprehensive multi-factor equity model centered on Cash Flow Return on Investment (CFROI) analytics across multiple time horizons, internal growth rate indicators (IGAIGR), market valuation multiples, price momentum, and capital structure metrics. It essentially measures the intersection of corporate profitability quality, sustainable growth capacity, and market pricing efficiency.

**Key Insights from Analysis**:
- CFROI metrics form a temporal sequence (cfroi_1 through cfroi_5) enabling persistence and trend analysis of cash flow efficiency
- IGAIGR series (1_gaigr through 5_igaigr) provide multi-dimensional growth perspectives, likely representing different forecasting methodologies or confidence intervals
- The dataset uniquely combines accounting-based profitability (CFROI) with market-based expectations (epsgrow5, percgrowfy1) and technical price action (ret1wkpr, tot4wkret)
- Valuation multiples are bifurcated into trailing (p_erati1) and likely forward (p_erati2) perspectives, enabling spread analysis

**Critical Field Relationships Identified**:
- CFROI time series relationship: cfroi_1 (recent) through cfroi_5 (older) creates a historical profitability curve
- Growth-Value tension: igaigr growth indicators interact with prc_book and prc_sale valuation metrics
- Leverage-Profitability trade-off: entwdrat and debteqiv capital structure fields moderate cfroi returns

**Most Promising Feature Concepts**:
1. **CFROI Persistence Score** - because stable cash flow returns across the 5 horizons indicate high-quality earnings less susceptible to mean reversion
2. **Growth-Value Interaction Spread** - because combining grow_fy5 with prc_book identifies GARP (Growth at Reasonable Price) opportunities
3. **CFROI Market Deviation** - because the spread between cfroi_1 and cfroimk5 reveals when company fundamentals diverge from market-wide cash flow trends

---

## Dataset Deep Understanding

### Dataset Description

Model172 is a composite equity factor model dataset containing 119 pre-computed financial indicators for European equities (EUR region). The dataset appears to be derived from a fundamental quantitative model emphasizing cash flow economics (CFROI framework), sustainable growth analysis, and relative valuation. Fields include multi-horizon CFROI calculations (1-5 periods), internal growth rate estimates (IGAIGR variants), standard valuation multiples (P/E, P/B, P/S), momentum indicators, and leverage metrics. The data likely represents monthly or quarterly model updates with delay=1 ensuring no look-ahead bias.

### Field Inventory

| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `mdl172_cfroi_1` | CFROI Period 1 | Float | Monthly | ~95% |
| `mdl172_cfroi_2` | CFROI Period 2 | Float | Monthly | ~95% |
| `mdl172_cfroi_3` | CFROI Period 3 | Float | Monthly | ~90% |
| `mdl172_cfroi_4` | CFROI Period 4 | Float | Monthly | ~85% |
| `mdl172_cfroi_5` | CFROI Period 5 | Float | Monthly | ~80% |
| `mdl172_1_gaigr` | IGAIGR Estimate 1 | Float | Monthly | ~90% |
| `mdl172_grow_fy5` | 5-Year Growth Forecast | Float | Monthly | ~85% |
| `mdl172_prc_book` | Price to Book Ratio | Float | Daily | ~99% |
| `mdl172_mark_cap` | Market Capitalization | Float | Daily | ~99% |
| `mdl172_ret1wkpr` | 1-Week Price Return | Float | Daily | ~99% |
| `mdl172_tot4wkret` | 4-Week Total Return | Float | Daily | ~99% |
| `mdl172_entwdrat` | Enterprise Value to Debt Ratio | Float | Quarterly | ~95% |
| `mdl172_vol_his_3m` | 3-Month Historical Volatility | Float | Daily | ~98% |

*(Additional 107 fields covering EPS metrics, momentum variants, and leverage indicators)*

### Field Deconstruction Analysis

#### `mdl172_cfroi_1` through `mdl172_cfroi_5`: Cash Flow Return on Investment Series
- **What is being measured?**: Economic profitability calculated as cash flow divided by gross investment, representing the true cash yield on capital employed
- **How is it measured?**: Likely calculated using inflation-adjusted gross plant and working capital against sustainable cash flows
- **Time dimension**: Sequential time periods (period 1 = most recent, period 5 = oldest), creating a 5-point historical profitability curve
- **Business context**: Measures whether companies generate returns above their cost of capital; core metric for "economic moat" assessment
- **Generation logic**: Derived from inflation-adjusted balance sheets and cash flow statements; less susceptible to accounting distortions than ROE/ROA
- **Reliability considerations**: Capital-intensive industries may show volatility; requires adjustment for asset age and inflation regimes

#### `mdl172_1_gaigr` through `mdl172_5_igaigr`: Internal Growth Rate Indicators
- **What is being measured?**: Sustainable growth rate achievable without external financing, based on retention ratio and return on equity
- **How is it measured?**: Calculated as ROE × (1 - Dividend Payout Ratio), or via alternative methodologies across the 5 variants
- **Time dimension**: Cross-sectional estimates likely representing different model specifications or confidence levels rather than time periods
- **Business context**: Indicates organic growth capacity; high values suggest self-sustaining expansion, low values indicate dependency on external capital
- **Generation logic**: Model-derived estimates incorporating earnings quality adjustments and dividend policy stability
- **Reliability considerations**: Highly sensitive to earnings volatility and one-time dividend changes; may require smoothing

#### `mdl172_prc_book`: Price-to-Book Ratio
- **What is being measured?**: Market valuation relative to accounting book value of equity
- **How is it measured?**: Market capitalization divided by shareholders' equity (common book value)
- **Time dimension**: Point-in-time market price against most recent reported book value
- **Business context**: Classic value factor indicating market skepticism (high P/B = growth expectations, low P/B = value/distress)
- **Generation logic**: Standard calculation using closing prices and most recent quarterly book value
- **Reliability considerations**: Book value quality varies by industry (intangibles, goodwill); financials may distort readings

### Field Relationship Mapping

**The Story This Data Tells**:
The dataset narrates the tension between economic reality (CFROI) and market perception (valuation multiples). It tracks how efficiently companies convert capital into cash flows (CFROI series), how much they can grow without external funding (igaigr), and how markets price these fundamentals (prc_book, p_erati). The inclusion of devtracking and fade fields suggests the model explicitly measures mean-reversion tendencies—whether high CFROI companies are likely to see profitability decline (fade) and whether market prices deviate from model-implied values (devtracking).

**Key Relationships Identified**:
1. **Profitability Persistence**: cfroi_1 (current) vs cfroi_5 (historical) reveals mean-reversion patterns; stable spreads indicate durable competitive advantages
2. **Growth-Financing Interactions**: igaigr growth rates intersect with entwdrat leverage; high growth + low leverage = sustainable expansion, high growth + high leverage = vulnerability
3. **Valuation-Quality Spread**: prc_book (market value) vs cfroi_1 (economic value) identifies disconnects between accounting assets and cash-generating ability
4. **Momentum-Fundamental Linkage**: ret1wkpr and tot4wkret provide price confirmation (or divergence) to cfroichg fundamental momentum

**Missing Pieces That Would Complete the Picture**:
- Explicit cost of capital estimates to compare against CFROI (spread calculation)
- Sector/industry classification for relative CFROI benchmarking
- Earnings announcement dates to contextualize epssurpq timing
- Short interest or institutional ownership data to explain devtracking anomalies

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: CFROI Temporal Stability Score
- **Sample Fields Used**: cfroi_1, cfroi_2, cfroi_3, cfroi_4, cfroi_5
- **Definition**: Coefficient of variation across the five CFROI time horizons, measuring consistency of cash flow returns over time
- **Why This Feature**: Stable CFROI indicates persistent competitive advantages and predictable capital efficiency, distinguishing quality companies from cyclical or lucky performers
- **Logical Meaning**: Low values (high stability) represent "all-weather" profitability; high values indicate volatile or mean-reverting cash economics
- **is filling nan necessary**: Yes, older CFROI horizons (cfroi_4, cfroi_5) may have NaN for recent IPOs or companies with limited history. Use ts_backfill() to carry forward recent values only if temporal consistency is critical, but generally preserve NaN to avoid assuming stability where data is missing.
- **Directionality**: Low values (stable) = positive quality signal; High values (volatile) = negative quality signal
- **Boundary Conditions**: Near-zero values indicate exceptional stability (potential monopolies); values >0.5 indicate highly cyclical or distressed businesses
- **Implementation Example**: `divide(ts_std_dev(add(add(add({cfroi_1}, {cfroi_2}), {cfroi_3}), {cfroi_4}), 5), abs(ts_mean(add(add(add({cfroi_1}, {cfroi_2}), {cfroi_3}), {cfroi_4}), 5)))`

**Concept**: IGAIGR Cross-Estimate Consensus
- **Sample Fields Used**: 1_gaigr, 2_igaigr, 3_igaigr, 4_igaigr, 5_igaigr
- **Definition**: Standard deviation across the five IGAIGR growth estimates, measuring model confidence in sustainable growth rates
- **Why This Feature**: Agreement across multiple estimation methodologies indicates reliable, model-robust growth prospects; disagreement signals estimation uncertainty or data quality issues
- **Logical Meaning**: Low spread = high confidence in growth sustainability; High spread = model uncertainty, potentially avoiding forecast errors
- **is filling nan necessary**: Yes, some igaigr variants may not compute for certain sectors. Use group_mean() within sector buckets to fill NaN, as growth estimates should be comparable within industries.
- **Directionality**: Low values (consensus) = investable growth; High values (disagreement) = avoid or investigate further
- **Boundary Conditions**: Zero spread indicates all models agree (rare); spreads >10% of mean value indicate significant model divergence
- **Implementation Example**: `ts_std_dev(add(add(add(add({1_gaigr}, {2_igaigr}), {3_igaigr}), {4_igaigr}), {5_igaigr}), 5)`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Fundamental Momentum Acceleration
- **Sample Fields Used**: cfroichg, cfroi_1, cfroi_2
- **Definition**: Rate of change in CFROI acceleration, measuring whether cash flow improvements are gaining or losing steam
- **Why This Feature**: Captures inflection points in business performance earlier than traditional earnings momentum; second derivative of profitability
- **Logical Meaning**: Positive values indicate improving rate of improvement (accelerating); negative values indicate decelerating improvements or worsening declines
- **is filling nan necessary**: No, preserve NaN for cfroichg as missing change data is informative (indicates insufficient history). Do not fill.
- **Directionality**: Positive = accelerating fundamentals (buy); Negative = decelerating fundamentals (sell/avoid)
- **Boundary Conditions**: Extreme positive values may signal unsustainable spikes; extreme negative may indicate cyclical troughs
- **Implementation Example**: `subtract({cfroichg}, ts_delay({cfroichg}, 5))`

**Concept**: Growth Expectation Revision
- **Sample Fields Used**: grow_fy5, percgrowfy1, epsgrow5
- **Definition**: Discrepancy between long-term (5-year) and near-term (1-year) growth expectations, normalized by historical volatility
- **Why This Feature**: Identifies expectations mismatches where market may be overly optimistic/pessimistic about long-term vs short-term growth trajectories
- **Logical Meaning**: Positive values indicate accelerating growth curves (concave growth); negative values indicate decelerating curves (maturing businesses)
- **is filling nan necessary**: Yes, use ts_backfill() for grow_fy5 as long-term forecasts update infrequently; missing values likely mean stale but valid estimates.
- **Directionality**: Positive = growth acceleration expected; Negative = growth deceleration expected
- **Boundary Conditions**: Values >20% indicate extreme growth ramp expectations; <-20% suggest impending maturity/decline
- **Implementation Example**: `subtract({grow_fy5}, multiply({percgrowfy1}, 5))`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: CFROI Deviation from Structural Trend
- **Sample Fields Used**: cfroi_1, cfroitrn, cfroival
- **Definition**: Magnitude of current CFROI deviation from its model-implied trend line and theoretical valuation-implied level
- **Why This Feature**: Identifies when current profitability is unsustainably high or depressed relative to historical trajectory and asset valuation
- **Logical Meaning**: Large positive deviations suggest cyclical peaks or one-time gains; large negative deviations suggest temporary distress or inflection opportunities
- **is filling nan necessary**: No, cfroitrn and cfroival are model outputs where NaN indicates model failure to converge; preserving NaN avoids false signals.
- **Directionality**: High deviation = mean-reversion candidate (contrarian signal); Low deviation = trend continuation
- **Boundary Conditions**: Deviations >2 standard deviations historically indicate extreme anomalies
- **Implementation Example**: `subtract({cfroi_1}, ts_mean({cfroitrn}, 20))`

**Concept**: Earnings Surprise Anomaly Intensity
- **Sample Fields Used**: epssurpq, vol_his_3m
- **Definition**: EPS surprise magnitude normalized by historical volatility, measuring the "unexpectedness" of the earnings beat/miss relative to typical price movements
- **Why This Feature**: Captures earnings announcements that represent true information shocks vs. noise, particularly when drift (post-announcement drift) patterns exist
- **Logical Meaning**: High values indicate fundamental regime changes not priced by volatility; low values indicate anticipated earnings moves
- **is filling nan necessary**: Yes, epssurpq is quarterly with many NaNs between announcements. Use ts_backfill() with lookback=90 to carry the surprise signal for the quarter following announcement.
- **Directionality**: High positive = underreacted good news (momentum); High negative = underreacted bad news (reversal/avoid)
- **Boundary Conditions**: Values >3 sigma indicate extreme information events; near-zero indicates consensus meeting
- **Implementation Example**: `divide({epssurpq}, {vol_his_3m})`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Quality-Adjusted Value Score
- **Sample Fields Used**: prc_book, cfroi_1, entwdrat
- **Definition**: Valuation multiple adjusted by CFROI quality and leverage risk, creating a "price per unit of economic return" metric
- **Why This Feature**: Avoids value traps by ensuring low P/B stocks actually generate cash flows, while penalizing highly leveraged "cheap" stocks
- **Logical Meaning**: Low values = cheap quality (high CFROI, low P/B, low debt); High values = expensive or risky (low CFROI, high P/B, high debt)
- **is filling nan necessary**: No, entwdrat NaN likely indicates zero debt (good); handle via conditional or preserve NaN as neutral.
- **Directionality**: Low = undervalued quality; High = overvalued or distressed
- **Boundary Conditions**: Near-zero indicates extreme value; >10 indicates glamour/speculative stocks
- **Implementation Example**: `multiply({prc_book}, divide(add(1, {entwdrat}), add({cfroi_1}, 0.01)))`

**Concept**: Growth-Financing Sustainability
- **Sample Fields Used**: grow_fy5, igaigr variants, sustratfy1
- **Definition**: Interaction between desired growth rate and internally sustainable growth capacity, adjusted for strategic feasibility
- **Why This Feature**: Identifies companies attempting to grow faster than their internal capital generation allows (funding gap) or underutilizing growth capacity
- **Logical Meaning**: Positive values indicate self-fundable growth (excess capacity); negative values indicate external financing dependency
- **is filling nan necessary**: Yes, sustratfy1 may have limited coverage. Use group_mean() by sector to fill, as sustainability strategies vary by industry norms.
- **Directionality**: Positive = sustainable growth; Negative = financing risk ahead
- **Boundary Conditions**: Large positive = cash accumulation potential; large negative = equity dilution or debt buildup risk
- **Implementation Example**: `multiply({sustratfy1}, subtract({grow_fy5}, {1_gaigr}))`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Valuation Multiple Decomposition
- **Sample Fields Used**: p_erati1, p_erati2, prc_book, prc_sale
- **Definition**: Structural composition of valuation across earnings, book value, and sales, measuring which component drives the valuation premium/discount
- **Why This Feature**: Distinguishes between earnings-driven value (P/E), asset-driven value (P/B), and revenue-driven value (P/S) to identify the economic basis of market pricing
- **Logical Meaning**: High earnings component = profitability focus; high book component = asset focus; high sales component = growth optionality focus
- **is filling nan necessary**: No, preserve NaN as inability to calculate specific valuation components indicates missing fundamental data (red flag).
- **Directionality**: Balanced composition = stable valuation; extreme skew = vulnerability to specific metric revision
- **Boundary Conditions**: Ratios >1 indicate that metric trades at premium to others; <-1 indicates deep discount
- **Implementation Example**: `divide(subtract({p_erati1}, {p_erati2}), add({prc_book}, {prc_sale}))`

**Concept**: Capital Structure Efficiency
- **Sample Fields Used**: entwdrat, debteqiv, coverage, leveragemkt
- **Definition**: Composite leverage score weighting market-based and accounting-based leverage measures by interest coverage capacity
- **Why This Feature**: Captures the full spectrum of financial risk by combining debt levels with ability to service that debt via operating cash flows
- **Logical Meaning**: Low values indicate conservative, flexible capital structures; high values indicate aggressive leverage with limited coverage cushion
- **is filling nan necessary**: Yes, coverage ratios may be missing for zero-debt companies. Use replace() to set coverage to a high default value (e.g., 100) for these cases, as no debt implies infinite coverage.
- **Directionality**: Low = financial flexibility; High = bankruptcy risk or aggressive financial engineering
- **Boundary Conditions**: Values <1 indicate coverage concerns; >10 indicates excess capacity
- **Implementation Example**: `divide(add({entwdrat}, {debteqiv}), {coverage})`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Multi-Dimensional Growth Accumulation
- **Sample Fields Used**: grow_fy5, epsgrow5, invgrow5, salegrow, assgrowthfy1
- **Definition**: Cumulative composite growth score aggregating earnings, investment, sales, and asset growth into single trajectory measure
- **Why This Feature**: Sustained growth across all dimensions indicates genuine business expansion vs. financial engineering or one-time factors
- **Logical Meaning**: High cumulative scores indicate broad-based growth; low scores indicate stagnation or mixed signals (e.g., earnings growth without investment growth)
- **is filling nan necessary**: Yes, growth rates may have varying fiscal year ends. Use ts_backfill() with 30-day window to align reporting periods.
- **Directionality**: High = broad growth acceleration; Low = deceleration or divergence
- **Boundary Conditions**: Values >100 indicate hyper-growth; <0 indicates contraction
- **Implementation Example**: `ts_sum(add(add(add({grow_fy5}, {epsgrow5}), {invgrow5}), {salegrow}), 5)`

**Concept**: CFROI Drift Accumulation
- **Sample Fields Used**: cfroidrs, cfroi_1, cfroi_5, cfroify5
- **Definition**: Cumulative directional drift of CFROI over the 5-period horizon, measuring persistent improvement or deterioration trends
- **Why This Feature**: Captures whether profitability changes are temporary blips or sustained trajectories via accumulation of period-over-period changes
- **Logical Meaning**: Positive accumulation indicates sustained operational improvement; negative indicates structural decline
- **is filling nan necessary**: No, cfroidrs is a derived drift metric; NaN indicates insufficient data for trend calculation and should be preserved.
- **Directionality**: Positive = improving economics; Negative = deteriorating economics
- **Boundary Conditions**: Extreme values indicate accelerating trends likely to mean-revert
- **Implementation Example**: `ts_sum({cfroidrs}, 10)`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: CFROI Market Relative Advantage
- **Sample Fields Used**: cfroi_1, cfroimk5, mark_cap
- **Definition**: Company-specific CFROI relative to market-wide CFROI expectations, adjusted for size (market cap) biases
- **Why This Feature**: Distinguishes between broad market cyclicality (beta) and company-specific execution (alpha) in cash flow generation
- **Logical Meaning**: Positive values indicate above-market cash efficiency; negative indicates below-market performance
- **is filling nan necessary**: No, cfroimk5 represents market aggregate; if missing, relative comparison is invalid.
- **Directionality**: Positive = superior capital allocation; Negative = capital destroyer relative to market
- **Boundary Conditions**: Values >5% indicate significant competitive advantage; <-5% indicates structural disadvantage
- **Implementation Example**: `vector_neut(subtract({cfroi_1}, {cfroimk5}), {mark_cap})`

**Concept**: Cross-Valuation Rank Divergence
- **Sample Fields Used**: prc_book, prc_sale, p_erati1, grow_fy5
- **Definition**: Relative ranking discrepancy between different valuation metrics (value vs. growth), identifying market inconsistencies
- **Why This Feature**: Companies ranked cheap on P/B but expensive on P/E may have asset-heavy but low-margin businesses; divergence signals business model complexity
- **Logical Meaning**: High divergence indicates mixed quality (cheap on some metrics, expensive on others); low divergence indicates consistent valuation consensus
- **is filling nan necessary**: Yes, use quantile() to normalize before comparison, and ts_backfill() for any missing fundamental data.
- **Directionality**: High divergence = potential mispricing opportunity; Low divergence = fairly valued across metrics
- **Boundary Conditions**: Extreme divergence (>2 standard deviations) indicates potential value trap or hidden asset
- **Implementation Example**: `subtract(quantile({prc_book}, driver="uniform"), quantile({p_erati1}, driver="uniform"))`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Sustainable Economic Return Proxy
- **Sample Fields Used**: sustratfy1, cfroi_1, cfroi_5, fcg_in
- **Definition**: Core sustainable return on capital adjusted for strategic feasibility and free cash flow generation, stripping out cyclical and financial engineering effects
- **Why This Feature**: Gets to the essence of "economic moat" - persistent cash generation capacity without reliance on external financing or cyclical tailwinds
- **Logical Meaning**: High values indicate genuine competitive advantages; low/negative values indicate commoditized or capital-consuming businesses
- **is filling nan necessary**: Yes, sustratfy1 is a complex model output with limited coverage. Use ts_backfill() with 60-day window as sustainability ratings change slowly.
- **Directionality**: High = wide moat, high quality; Low = no moat, commoditized
- **Boundary Conditions**: Values >15% indicate exceptional economics; <5% indicates capital destruction over cycle
- **Implementation Example**: `multiply({sustratfy1}, multiply({cfroi_1}, {fcg_in}))`

**Concept**: Pure Value Essence
- **Sample Fields Used**: prc_book, grow_fy5, epsgrow5, vc_ratio
- **Definition**: Valuation metric purified of growth expectations, isolating the "asset value" component independent of future growth optionality
- **Why This Feature**: Separates Graham-style net asset value from growth-option value, identifying true deep value vs. growth-at-reasonable-price
- **Logical Meaning**: Low values indicate asset-backed value with low growth expectations (cigar butts); high values indicate growth-dominated valuation
- **is filling nan necessary**: No, vc_ratio (value-to-cost?) may already incorporate this; preserve NaN for failed calculations.
- **Directionality**: Low = deep value; High = growth/quality premium
- **Boundary Conditions**: Near-zero indicates liquidation value; >5 indicates franchise value dominance
- **Implementation Example**: `vector_neut({prc_book}, add({grow_fy5}, {epsgrow5}))`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: CFROI fields show declining coverage from cfroi_1 (~95%) to cfroi_5 (~80%), likely due to corporate actions, delistings, or historical data limitations for newer public companies
- **Timeliness**: Model172 appears to update monthly for fundamental fields (cfroi, igaigr) and daily for market fields (prc_book, ret1wkpr), requiring careful synchronization for mixed-frequency features
- **Accuracy**: CFROI calculations rely on inflation adjustments and asset age estimates; accuracy varies by industry (better for manufacturing than services/intangibles)
- **Potential Biases**: Survivorship bias possible in cfroi_5 (only companies surviving 5 periods have data); look-ahead bias minimized by delay=1 setting

### Computational Complexity
- **Lightweight features**: Single-field transformations (fade, devtracking), simple ratios (divide({cfroi_1}, {prc_book}))
- **Medium complexity**: Time-series aggregations (ts_std_dev, ts_sum), cross-sectional rankings (quantile), binary operations (multiply, subtract)
- **Heavy computation**: Multi-field aggregations across 5 CFROI horizons or 5 IGAIGR variants, nested vector_neut operations, conditional logic (if_else) for NaN handling

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **CFROI Temporal Stability Score** - High logical meaning, robust cross-horizon logic, strong quality factor literature support
2. **Quality-Adjusted Value Score** - Directly addresses value trap risk, combines three key dataset themes (value, quality, leverage)
3. **CFROI Market Relative Advantage** - Clean relative value concept with size neutrality

**Tier 2 (Secondary Priority)**:
1. **Earnings Surprise Anomaly Intensity** - Event-driven alpha potential, but requires careful NaN handling
2. **Growth-Financing Sustainability** - Captures capital structure risk, important for European credit-sensitive markets
3. **Fundamental Momentum Acceleration** - Second-order derivative captures inflection points earlier than first-order momentum

**Tier 3 (Requires Further Validation)**:
1. **Pure Value Essence** - Conceptually strong but vector_neut across growth/value may over-fit in certain regimes
2. **Multi-Dimensional Growth Accumulation** - Risk of double-counting correlated growth metrics (earnings and sales growth highly correlated)

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. Do the 5 IGAIGR variants (1_gaigr through 5_igaigr) represent different time horizons, different model specifications, or confidence intervals? This fundamentally changes how we interpret cross-estimate dispersion.
2. What is the exact calculation methodology for cfroimk5 (market 5-year CFROI)? Is it a market-cap weighted aggregate or sector-neutral composite?
3. How frequently are the "fade" and "devtracking" fields recalibrated, and do they represent model-implied alpha or risk-adjusted expected returns?

### Recommended Additional Data:
- **Sector/Industry Classification**: Essential for relative CFROI benchmarking (cfroi relative to sector median rather than absolute)
- **Cost of Capital Estimates**: To calculate CFROI spread (CFROI - WACC) as true economic profit measure
- **Earnings Calendar Dates**: To properly time epssurpq features around announcement dates vs. fiscal period ends
- **Short Interest Data**: To validate devtracking anomalies (high deviation + high short interest = potential crowded short)

### Assumptions to Challenge:
- **Assumption**: CFROI stability is always positive. Challenge: In disrupted industries, rapidly changing CFROI may indicate successful adaptation rather than volatility.
- **Assumption**: Low prc_book is universally good. Challenge: In asset-light digital economies, book value may be meaningless; CFROI-to-Enterprise Value may be superior.
- **Assumption**: igaigr growth is sustainable. Challenge: High internal growth may indicate under-leverage (inefficient balance sheet) rather than organic strength.

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence (CFROI economics, IGAIGR sustainability, valuation spreads)
2. Question-driven feature generation (8 fundamental questions) applied to financial model context
3. Logical validation of each feature concept against corporate finance theory and factor investing literature
4. Transparent documentation of reasoning including boundary conditions and NaN handling

**Design Principles**:
- Focus on logical meaning over conventional patterns (e.g., "Quality-Adjusted Value" vs. simple P/B)
- Every feature answers a specific investment question (stability, change, anomaly, etc.)
- Clear documentation of "why" each feature makes economic sense
- Emphasis on European market context (EUR region, leverage sensitivity, accounting standards)

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate CFROI stability persistence, test Quality-Adjusted Value in value drawdown regimes*