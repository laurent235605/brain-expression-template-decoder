**Dataset**: analyst4
**Region**: EUR
**Delay**: 1

# Analyst Estimate Data for Equity Feature Engineering Analysis Report

**Dataset**: analyst4
**Category**: Analyst
**Region**: EUR
**Analysis Date**: 2024
**Fields Analyzed**: 297

---

## Executive Summary

**Primary Question Answered by Dataset**: What do professional financial analysts collectively expect regarding corporate financial performance, and how do those expectations evolve in real-time?

**Key Insights from Analysis**:
- The dataset captures multi-dimensional consensus views through statistical moments (mean, median, standard deviation) and range extremes (high/low), enabling measurement of both central tendency and dispersion in market expectations
- Forecast type flags (revision vs. new estimates) provide metadata on the *nature* of information flow, distinguishing between evolving opinions and fresh coverage
- Intraday update frequency creates opportunity to detect momentum in estimate revisions before they fully diffuse into prices
- Coverage depth metrics (number of estimates) serve as proxy for information environment quality and liquidity

**Critical Field Relationships Identified**:
- Mean vs. Median divergence indicates skewness in analyst distributions (optimism/pessimism bias)
- High-Low range relative to standard deviation reveals the tail risk perception vs. typical disagreement
- Standard deviation normalized by absolute mean level creates comparable uncertainty metric across differently-scaled companies
- Coverage count correlates with estimate stability (more analysts typically reduce volatility in consensus)

**Most Promising Feature Concepts**:
1. **Analyst Disagreement Momentum** - because shifts in {std} often precede price volatility
2. **Consensus Skewness Indicator** - because ({mean} - {median}) captures directional bias in expectations
3. **Estimate Revision Intensity** - because ts_delta of {median} tracks changing fundamental momentum
4. **Coverage-Adjusted Uncertainty** - because {std} / log({number}) distinguishes true disagreement from low-coverage noise

---

## Dataset Deep Understanding

### Dataset Description
This dataset provides intraday updates of consensus financial estimates, actuals, and company guidance for over 16,000 global companies, sourced from more than 800 contributing brokers. It includes multiple daily delta files per region, allowing users to track real-time changes in analyst expectations for key financial metrics such as EPS, sales, dividends, cash flow, and industry-specific items. The dataset offers daily historical consensus timelines, enabling analysis of estimate revisions, surprises, and trends.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `anl4_adz_eps_mean` | Earnings per share - mean of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_eps_median` | Earnings per share - median of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_eps_std` | Earnings per share - std of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_eps_high` | Earnings per share - The highest estimation | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_eps_low` | Earnings per share - The lowest estimation | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_eps_number` | Earnings per share - number of estimations | Integer | Intraday | EUR TOPCS1600 |
| `anl4_eps_flag` | EPS - forecast type (revision/new/...) | Categorical | Intraday | EUR TOPCS1600 |
| `anl4_adz_ebitda_mean` | EBITDA - mean of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_ebitda_median` | EBITDA - median of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_ebitda_std` | EBITDA - std of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_netprofit_median` | Net profit - median of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_netprofit_mean` | Net profit - mean of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_netprofit_std` | Net profit - std of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_qfv4_median_eps` | Earnings per share - median of estimations (quarterly) | Float | Intraday | EUR TOPCS1600 |
| `anl4_qfv4_eps_number` | Earnings per share - number of estimations (quarterly) | Integer | Intraday | EUR TOPCS1600 |
| `anl4_sadaf_median_epsreported` | GAAP Earnings per share - median of estimations | Float | Intraday | EUR TOPCS1600 |
| `quarterly_estimate_median` | Sales - median of estimations | Float | Intraday | EUR TOPCS1600 |
| `quarterly_estimate_count` | Sales - number of estimations | Integer | Intraday | EUR TOPCS1600 |
| `quarterly_standard_deviation` | Sales - std of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_bvps_median` | Book value per share - Median value among forecasts | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_cfo_median` | Cash Flow From Operations - median of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_cfo_mean` | Cash Flow From Operations - mean of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_cfo_std` | Cash Flow From Operations - std of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_fcf_median` | Free cash flow - aggregation on estimations, 50th-percentile | Float | Intraday | EUR TOPCS1600 |
| `anl4_adz_fcf_mean` | Free cash flow - mean of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_af_div_median` | Dividend per share - median of estimations | Float | Intraday | EUR TOPCS1600 |
| `anl4_af_div_mean` | Dividend per share - average of estimations | Float | Intraday | EUR TOPCS1600 |

*(Additional 270+ fields covering various financial metrics and statistical aggregations)*

### Field Deconstruction Analysis

#### `anl4_adz_eps_median`: Consensus EPS Expectation
- **What is being measured?**: The central tendency (50th percentile) of analyst earnings per share forecasts for a specific fiscal period
- **How is it measured?**: Aggregation of individual broker estimates, updated intraday as new estimates are submitted or revised
- **Time dimension**: Point-in-time snapshot of forward-looking expectations (typically for next fiscal year or quarter), with daily historical trail
- **Business context**: Represents the market's collective earnings expectation; deviations between this and actual reported earnings drive post-earnings drift
- **Generation logic**: Calculated from 800+ contributing brokers, with real-time aggregation when brokers submit revisions
- **Reliability considerations**: More reliable when `anl4_adz_eps_number` is high (>10); median is robust to outlier individual estimates

#### `anl4_adz_eps_std`: Analyst Disagreement
- **What is being measured?**: Dispersion or cross-sectional variance in analyst EPS estimates
- **How is it measured?**: Standard deviation of the distribution of individual analyst estimates
- **Time dimension**: Instantaneous measure of uncertainty, changes reflect evolving information or conflicting interpretations
- **Business context**: High values indicate uncertainty about future earnings; often precedes volatility expansion and information events
- **Generation logic**: Computed from same underlying estimates as median; increases when analysts diverge in views
- **Reliability considerations**: Meaningless when {number} < 3; scales with earnings level so normalization by {mean} or {median} often required

#### `anl4_adz_eps_number`: Coverage Depth
- **What is being measured?**: Count of active analysts providing estimates for the metric
- **How is it measured?**: Simple count of unique contributing brokers with active forecasts
- **Time dimension**: Relatively stable but changes with initiation/dropout of coverage
- **Business context**: Proxy for information environment quality; high coverage reduces idiosyncratic noise in consensus
- **Generation logic**: Automated count of valid estimates in aggregation system
- **Reliability considerations**: Sudden drops may indicate data issues or delisting events rather than true coverage changes

#### `anl4_eps_flag`: Estimate Revision Type
- **What is being measured?**: Metadata indicating whether latest consensus change stems from new estimate or revision of existing estimate
- **How is it measured?**: Categorical classification by data vendor (revision/new/confirmed)
- **Time dimension**: Event-based, captures the *type* of information flow
- **Business context**: Revisions indicate changing analyst views (more informative); new estimates may simply expand coverage
- **Generation logic**: Vendor-side classification based on broker submission metadata
- **Reliability considerations**: Classification accuracy depends on vendor algorithms; may not capture subtle distinction between true revision and replacement

#### `anl4_adz_eps_high` / `anl4_adz_eps_low`: Expectation Bounds
- **What is being measured?**: Extreme values (max and min) of analyst estimate distribution
- **How is it measured?**: Minimum and maximum values among all contributing estimates
- **Time dimension**: Instantaneous range; changes reflect extreme optimist or pessimist revisions
- **Business context**: Range indicates the "disagreement tails" and potential surprise magnitude; wide range suggests binary outcome uncertainty
- **Generation logic**: Simple min/max functions on estimate array
- **Reliability considerations**: Outliers can be stale estimates (analysts who haven't updated); {high} - {low} is volatile and may need winsorization

### Field Relationship Mapping

**The Story This Data Tells**:
Analysts form expectations about future corporate performance, but they disagree. The dataset captures not just the average opinion (mean) but the distribution shape (median vs mean), the uncertainty (std), the extremes (high/low), and the sample size (number). As new information arrives (earnings announcements, macro data, industry news), analysts revise estimates (flags), shifting the consensus (median change) and potentially increasing or decreasing agreement (std change). The relative positioning of mean vs median reveals whether the analyst community is skewed optimistic or pessimistic.

**Key Relationships Identified**:
1. **Central Tension**: {mean} - {median} indicates distribution skewness; positive values suggest optimistic tail (some high outliers pulling mean up)
2. **Uncertainty Scaling**: {std} scales with earnings level; {std}/abs({median}) creates relative uncertainty comparable across companies
3. **Range vs Deviation**: ({high} - {low}) vs {std} - wide range with low std suggests bimodal disagreement; narrow range with high std suggests clustering around mean with outliers
4. **Coverage-Uncertainty**: Inverse relationship between {number} and {std} typically observed (more analysts reduce uncertainty)
5. **Revision-Consensus**: Changes in {median} correlate with {flag} = 'revision' events, providing momentum signal

**Missing Pieces That Would Complete the Picture**:
- Individual analyst identity and reputation (to weight estimates by accuracy)
- Time stamps of individual estimate submissions (to weight recent vs stale estimates)
- Analyst-specific bias indicators (some analysts consistently over/under-estimate)
- Corresponding actual reported values for surprise calculation (partially present but not comprehensive)
- Sector/regional analyst composition effects

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: Estimate Dispersion Stability
- **Sample Fields Used**: {std}, {median}
- **Definition**: Rolling coefficient of variation of analyst standard deviation, measuring whether disagreement among analysts is stable or trending
- **Why This Feature**: Stable disagreement suggests consistent uncertainty; collapsing disagreement often precedes information events; expanding disagreement signals emerging controversy
- **Logical Meaning**: Measures the volatility of uncertainty itself - meta-uncertainty about earnings prospects
- **is filling nan necessary**: Yes, use ts_backfill() for missing std values as absence of estimates is temporary data gap, not meaningful signal
- **Directionality**: Low values indicate stable analyst agreement (consensus confidence); high values indicate shifting opinions and potential information volatility
- **Boundary Conditions**: Near zero indicates all analysts converging to same view; spikes indicate earnings event approaching or major news
- **Implementation Example**: ts_std_dev({std}, 20) / ts_mean(abs({median}), 20)

**Concept**: Coverage Persistence
- **Sample Fields Used**: {number}, {estimate_count}
- **Definition**: Stability of analyst coverage count over time, identifying companies with consistent following vs those experiencing coverage changes
- **Why This Feature**: Dropping coverage often precedes delisting or reduced liquidity; stable coverage enables reliable consensus metrics; increasing coverage suggests growing investor interest
- **Logical Meaning**: Proxy for institutional attention and information environment stability
- **is filling nan necessary**: No, NaN in {number} indicates no coverage which is meaningful (unfollowed stocks)
- **Directionality**: High stability (low ts_std_dev of {number}) indicates mature coverage; declining trend indicates deteriorating information environment
- **Boundary Conditions**: Sudden drops to zero indicate data issues or suspension; gradual decline indicates waning interest
- **Implementation Example**: ts_delta(ts_backfill({number}, 10), 5)

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Consensus Revision Momentum
- **Sample Fields Used**: {median}, {median_epsreported}
- **Definition**: Rate of change in median analyst estimates over short windows, capturing earnings momentum from forecast updates
- **Why This Feature**: Analyst revisions are leading indicators of price momentum; positive revision trends predict future outperformance; speed of revision matters as much as direction
- **Logical Meaning**: Captures the velocity of changing expectations - how quickly the analyst community is updating views
- **is filling nan necessary**: Yes, use ts_backfill() to handle non-trading days or data gaps, as estimates carry forward
- **Directionality**: Positive values indicate upgrading expectations (bullish); negative values indicate downgrades (bearish); magnitude indicates conviction
- **Boundary Conditions**: Extreme values indicate earnings surprises or guidance changes; zero indicates stale estimates or consensus equilibrium
- **Implementation Example**: ts_delta({median}, 5) / abs(ts_delay({median}, 5))

**Concept**: Disagreement Expansion/Contraction
- **Sample Fields Used**: {std}, {standard_deviation}
- **Definition**: Change in analyst standard deviation, measuring whether uncertainty is increasing (diverging opinions) or decreasing (convergence)
- **Why This Feature**: Expanding disagreement often precedes volatility spikes and earnings events; contracting disagreement suggests information resolution and potential return to normal volatility
- **Logical Meaning**: Second derivative of information flow - acceleration or deceleration of uncertainty
- **is filling nan necessary**: Yes, backfill required as std changes only when new estimates arrive
- **Directionality**: Positive ts_delta indicates emerging controversy or uncertainty; negative indicates analysts converging on consensus
- **Boundary Conditions**: Rapid expansion suggests upcoming binary event; rapid contraction suggests earnings resolution or guidance clarity
- **Implementation Example**: ts_delta({std}, 10) / ts_delay({std}, 10)

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Estimate Outlier Detection (Z-Score)
- **Sample Fields Used**: {median}, {mean}, {std}
- **Definition**: Current median estimate position relative to its own recent historical distribution, identifying extreme consensus levels
- **Why This Feature**: Extreme consensus readings (very high or very low z-scores) often indicate over-optimism or over-pessimism, leading to future mean reversion or momentum depending on information environment
- **Logical Meaning**: Measures how unusual current expectations are relative to recent history - identifies consensus extremes
- **is filling nan necessary**: Yes, use ts_backfill() for continuous time series
- **Directionality**: High positive z-scores indicate unusually high expectations (potential disappointment risk); high negative indicate pessimism (potential beat risk)
- **Boundary Conditions**: |z-score| > 2 indicates extreme positioning; >3 indicates potential data errors or major structural changes
- **Implementation Example**: ({median} - ts_mean({median}, 60)) / ts_std_dev({median}, 60)

**Concept**: Skewness Anomaly
- **Sample Fields Used**: {mean}, {median}, {std}
- **Definition**: Normalized difference between mean and median estimates, quantifying optimism/pessimism bias in analyst distribution
- **Why This Feature**: Skewed distributions indicate asymmetric risk perceptions; positive skew suggests tail-risk optimism; persistent skew indicates systematic analyst bias for that company
- **Logical Meaning**: Detects when the "average" analyst differs from the "typical" analyst, indicating outlier influence
- **is filling nan necessary**: Yes, backfill needed when either mean or median missing
- **Directionality**: Positive values indicate right-skew (optimistic outliers); negative indicate left-skew (pessimistic outliers); near zero indicates symmetric disagreement
- **Boundary Conditions**: Values > 0.5 indicate significant skew; sign persistence indicates directional bias
- **Implementation Example**: ({mean} - {median}) / {std}

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Relative Uncertainty Index
- **Sample Fields Used**: {std}, {median}, {mean}
- **Definition**: Coefficient of variation of analyst estimates, normalizing disagreement by consensus level to enable cross-sectional comparison
- **Why This Feature**: Raw std is higher for high-earnings companies; this metric allows comparison of uncertainty across differently-scaled firms; identifies high-uncertainty-low-expectation situations
- **Logical Meaning**: Risk-adjusted disagreement - uncertainty per unit of expected earnings
- **is filling nan necessary**: Yes, handle zeros in median/mean by adding small epsilon or using conditional
- **Directionality**: High values indicate high uncertainty relative to expected earnings (risky forecasts); low values indicate high confidence relative to expected level
- **Boundary Conditions**: Approaches infinity as consensus approaches zero (turnaround situations); very low values indicate certainty about large numbers
- **Implementation Example**: {std} / abs({median})

**Concept**: Coverage-Weighted Consensus
- **Sample Fields Used**: {median}, {number}, {estimate_count}
- **Definition**: Consensus estimate adjusted by the logarithm of coverage depth, down-weighting estimates from thinly covered securities
- **Why This Feature**: Median from 3 analysts is noisier than median from 30; this adjusts consensus quality by information environment richness; prevents false signals from low-coverage outliers
- **Logical Meaning**: Information-quality-adjusted expectations - more weight to well-covered stocks
- **is filling nan necessary**: Yes, backfill number to ensure continuous adjustment
- **Directionality**: Higher values indicate strong consensus with deep coverage (high conviction); lower values indicate weak consensus or thin coverage
- **Boundary Conditions**: Approaches zero as coverage drops; logarithmic scaling prevents extreme penalization
- **Implementation Example**: {median} * log(1 + {number})

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Estimate Range Utilization
- **Sample Fields Used**: {high}, {low}, {std}, {median}
- **Definition**: Ratio of inter-quartile-implied range to actual high-low range, measuring whether estimates cluster or disperse across the spectrum
- **Why This Feature**: Reveals distribution structure - clustering indicates consensus with outliers; uniform distribution indicates genuine uncertainty; helps identify stale outlier estimates
- **Logical Meaning**: Efficiency of the estimate range - how much of the range represents true disagreement vs outlier noise
- **is filling nan necessary**: Yes, backfill for missing high/low values
- **Directionality**: High values (near 1) suggest uniform distribution (high uncertainty); low values suggest clustering with outliers (bimodal with extremes)
- **Boundary Conditions**: Near zero suggests all analysts agree except one outlier; 0.5 suggests normal distribution
- **Implementation Example**: (2 * {std}) / ({high} - {low} + 0.001)

**Concept**: Forecast Type Composition
- **Sample Fields Used**: {flag} (if encoded numerically), {number}
- **Definition**: Proportion of recent estimate changes classified as revisions vs new estimates, indicating information update rate
- **Why This Feature**: High revision rate indicates active information processing by analysts; low revision with high new estimate count indicates coverage expansion rather than opinion change
- **Logical Meaning**: Information velocity metric - distinguishes between expanding coverage and changing minds
- **is filling nan necessary**: N/A - categorical handling required
- **Directionality**: High revision concentration indicates dynamic expectations; high new estimate concentration indicates static expectations with expanding coverage
- **Boundary Conditions**: 100% revision indicates all analysts updating views; 100% new indicates initiation of coverage
- **Implementation Example**: ts_sum({flag} == 'revision', 5) / {number}

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Cumulative Revision Pressure
- **Sample Fields Used**: {median}, {mean}
- **Definition**: Accumulated sum of daily median estimate changes over a window, capturing persistent directional momentum in analyst views
- **Why This Feature**: Single-day changes may be noise; cumulative changes indicate sustained momentum; sign persistence indicates trending earnings expectations
- **Logical Meaning**: Integral of consensus velocity - total distance traveled by expectations over time
- **is filling nan necessary**: Yes, backfill to treat missing days as zero change
- **Directionality**: Large positive values indicate sustained upward revisions (positive momentum); large negative indicate sustained downgrades; near zero indicates oscillation or stability
- **Boundary Conditions**: Extreme cumulative values indicate extended trending periods; zero indicates mean-reverting estimates
- **Implementation Example**: ts_sum(ts_delta({median}, 1), 20)

**Concept**: Persistent Disagreement Score
- **Sample Fields Used**: {std}, {standard_deviation}
- **Definition**: Average level of analyst disagreement over extended periods, identifying chronically controversial stocks vs temporarily uncertain ones
- **Why This Feature**: Persistent high disagreement indicates structural uncertainty (complex businesses, opaque reporting); temporary spikes indicate event-driven uncertainty; persistent low disagreement indicates stable, predictable businesses
- **Logical Meaning**: Baseline uncertainty level for a stock - its inherent predictability
- **is filling nan necessary**: Yes, backfill to ensure continuous calculation
- **Directionality**: High persistent values indicate "controversial" stocks suitable for volatility strategies; low values indicate "predictable" stocks suitable for quality strategies
- **Boundary Conditions**: Values > 2x cross-sectional median indicate extreme persistent disagreement; values < 0.5x indicate consensus champions
- **Implementation Example**: ts_mean({std}, 60)

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Cross-Sector Consensus Z-Score
- **Sample Fields Used**: {median}, {mean}
- **Definition**: Standardized position of company's consensus estimate relative to sector peers, capturing relative optimism/pessimism
- **Why This Feature**: Absolute estimate levels are meaningless; relative positioning indicates which stocks have relatively upgraded vs downgraded expectations within their peer group
- **Logical Meaning**: Peer-relative expectation momentum - outperforming or underperforming the sector in analyst favor
- **is filling nan necessary**: Yes, backfill before cross-sectional operation
- **Directionality**: High positive values indicate analysts favor this stock vs sector (relative optimism); negative values indicate relative pessimism; zero indicates neutral sector positioning
- **Boundary Conditions**: Extreme outliers indicate sector rotation candidates; near-zero indicates sector-beta pure plays
- **Implementation Example**: ({median} - group_mean({median}, sector)) / group_std({median}, sector)

**Concept**: Dispersion Rank Stability
- **Sample Fields Used**: {std}, {number}
- **Definition**: Rank of stock's analyst disagreement relative to universe, and stability of that rank over time
- **Why This Feature**: Identifies stocks moving from low-disagreement to high-disagreement regimes (controversy emergence) or vice versa (information resolution); relative disagreement more predictive than absolute
- **Logical Meaning**: Controversy lifecycle position - entering or exiting the "hard to predict" category
- **is filling nan necessary**: Yes, backfill for rank calculation stability
- **Directionality**: Rising rank indicates becoming more controversial than peers; falling rank indicates convergence to consensus; high stable rank indicates permanently controversial
- **Boundary Conditions**: Top decile indicates highest uncertainty stocks; bottom decile indicates consensus blue chips; rapid rank changes indicate regime shifts
- **Implementation Example**: rank({std}) / count({std})

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Pure Information Surprise
- **Sample Fields Used**: {median}, {mean}, {number}
- **Definition**: Change in median normalized by coverage depth, capturing information content per analyst rather than raw consensus shift
- **Why This Feature**: Raw consensus changes confounded by coverage (more analysts = more potential for change); this isolates the information intensity of revisions
- **Logical Meaning**: Information density - how much surprise is contained in the consensus shift relative to the analyst following size
- **is filling nan necessary**: Yes, backfill for continuous calculation
- **Directionality**: High values indicate rare but significant information events; low values indicate noise or frequent minor updates; sign indicates direction of surprise
- **Boundary Conditions**: Extreme values indicate material disclosures; zero indicates no information flow despite coverage
- **Implementation Example**: ts_delta({median}, 1) / sqrt({number})

**Concept**: Expectation Reality Gap
- **Sample Fields Used**: {median}, {value} (actuals)
- **Definition**: Divergence between forward-looking median estimate and most recent actual reported value, measuring the implied growth/decay embedded in expectations
- **Why This Feature**: Captures the " priced in" expectation vs current reality; large gaps indicate high growth expectations (risky if unmet) or pessimistic expectations (opportunity if beaten)
- **Logical Meaning**: The market's implied trajectory - how much improvement or decline is expected
- **is filling nan necessary**: Yes, backfill actuals as they are reported quarterly while estimates update daily
- **Directionality**: Large positive values indicate high growth expectations (expectation risk); large negative values indicate pessimistic turnarounds (surprise potential); near zero indicates steady-state expectations
- **Boundary Conditions**: Values > 50% indicate aggressive growth pricing; negative values indicate expected decline; cross-sectional comparison essential
- **Implementation Example**: ({median} - {value}) / abs({value} + 0.01)

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Variable across market cap; large caps have 20+ analysts, small caps may have 3-5; features using {number} should filter for minimum coverage (>3)
- **Timeliness**: Intraday updates create look-ahead bias if not properly delayed; ensure delay=1 usage for all features
- **Accuracy**: Actual values ({value} fields) update quarterly while estimates update daily; alignment of fiscal periods critical for surprise calculation
- **Potential Biases**: Analysts exhibit herding behavior; mean estimates often optimistic due to investment banking relationships; median more robust but less sensitive to genuine new information

### Computational Complexity
- **Lightweight features**: ts_delta of {median}, {mean}-{median}, {high}-{low}
- **Medium complexity**: ts_std_dev of {std}, rank calculations, ts_sum of changes
- **Heavy computation**: Cross-sectional group_mean/group_std operations, regression_neut for sector adjustment, ts_regression for trend extraction

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Consensus Revision Momentum** (ts_delta of {median}) - because it captures the core analyst revision effect with minimal complexity
2. **Relative Uncertainty** ({std}/abs({median})) - because it provides cross-sectionally comparable risk measure
3. **Skewness Indicator** (({mean}-{median})/{std}) - because it detects bias with simple arithmetic

**Tier 2 (Secondary Priority)**:
1. **Cumulative Revision Pressure** (ts_sum of changes) - because it filters noise but requires parameter tuning
2. **Estimate Outlier Z-Score** - because it requires careful handling of lookback windows to avoid lookahead bias
3. **Coverage-Weighted Consensus** - because coverage data quality varies by vendor timestamp

**Tier 3 (Requires Further Validation)**:
1. **Forecast Type Composition** - because flag data categorical encoding may vary
2. **Cross-Sector Z-Score** - because sector definitions and group operations computationally expensive
3. **Pure Information Surprise** - because square root of coverage assumption may not hold empirically

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How does the intraday update frequency interact with daily trading close - should we use last estimate of day or VWAP of intraday revisions?
2. Do analyst revisions cluster around specific times (pre-market, post-close) creating temporal autocorrelation?
3. How do forecast type flags (revision vs new) correlate with actual subsequent accuracy - are revisions more informative?
4. What is the optimal lookback window for measuring "stable" disagreement - does it vary by sector volatility?

### Recommended Additional Data:
- Individual analyst identifiers to track specific broker accuracy and bias
- Timestamp of estimate submissions to weight by recency (not just daily snapshots)
- Actual reported earnings aligned to exact fiscal periods for surprise calculation
- Analyst price targets alongside earnings estimates for valuation context
- Sector and industry classifications for relative value features

### Assumptions to Challenge:
- That median is always superior to mean (mean may be better when few analysts cover, as median ignores magnitude of outlier views)
- That high analyst disagreement is always bad (may indicate opportunity for information arbitrage in efficient markets)
- That all analysts are equal (investment banks vs independent research may have different information content)
- That intraday updates are immediately reflected in prices (latency arbitrage opportunity may exist)

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence (consensus distributions vs point estimates)
2. Question-driven feature generation (8 fundamental questions applied to estimate distributions)
3. Logical validation of each feature concept against financial theory (analyst revision momentum, disagreement models)
4. Transparent documentation of reasoning with explicit operator usage

**Design Principles**:
- Focus on distributional aspects (mean, median, std, range) rather than just central tendency
- Every feature answers a specific question about analyst behavior or information flow
- Clear documentation of "why" for each suggestion linking to market microstructure
- Emphasis on relative measures (coefficients, z-scores) given cross-sectional nature of equity screening

---

*Report generated: 2024*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate coverage filters, gather additional actuals data for surprise features*