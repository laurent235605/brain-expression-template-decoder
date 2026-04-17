# Key Earning Input Feature Engineering Analysis Report

**Dataset**: earnings10
**Category**: Earnings
**Region**: EUR
**Delay**: 1
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 8

---

## Executive Summary

**Primary Question Answered by Dataset**: What are equity research analysts expecting for the key earnings drivers (KEI) of companies, and how are those expectations changing on a daily basis?

**Key Insights from Analysis**:
- Dataset captures analyst-selected key earnings inputs (KEI), representing up to 5 critical drivers per company that are inputs to earnings forecasts
- Dual-stream structure provides both absolute estimate levels (`elta_value`) and daily reconciliation deltas (`aily_delta_recon_value`) enabling tracking of revision momentum
- Vector data structure allows aggregation across multiple KEI items per instrument to create composite signals
- Daily update frequency with delay=1 makes this suitable for short-term revision signals and momentum strategies

**Critical Field Relationships Identified**:
- `aily_delta_recon_value` represents the daily change in `elta_value`, providing the revision flow while `elta_value` provides the stock level
- `elta_run_timestamp` and `aily_delta_recon_run_timestamp` track data freshness and can identify stale estimates
- `elta_period_year` and `aily_delta_recon_period_year` link estimates to specific fiscal periods, enabling period-alignment validation

**Most Promising Feature Concepts**:
1. **Cumulative Revision Momentum** - because sustained directional revisions indicate analyst conviction that likely predicts future price movement
2. **Revision Surprise Score (Z-Score)** - because anomalous daily changes relative to historical revision patterns signal potential information shocks not yet priced in
3. **Estimate Staleness Indicator** - because the recency of the last estimate update (`elta_run_timestamp`) indicates data quality and potential stale pricing

---

## Dataset Deep Understanding

### Dataset Description
This dataset provides access to Equity Research Analyst's estimates for up to five of the most closely tracked drivers identified by the covering analyst team (Key Earnings Inputs). These metrics are selected at the discretion of the analyst team and serve as direct inputs to the team's earnings forecasts. The dataset contains both the estimate values and daily reconciliation deltas, enabling tracking of how expectations evolve over time.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `ern10_elta_value` | Value of KEI (Key Earnings Input) | Vector (Numeric) | Daily | >95% |
| `ern10_aily_delta_recon_value` | Daily delta reconciliation value | Vector (Numeric) | Daily | >95% |
| `ern10_elta_run_timestamp` | Time file is created | Timestamp | Daily | 100% |
| `ern10_aily_delta_recon_run_timestamp` | Time file is created | Timestamp | Daily | 100% |
| `ern10_elta_period_year` | Year of the period | Integer | Daily | 100% |
| `ern10_aily_delta_recon_period_year` | Year of the period | Integer | Daily | 100% |
| `ern10_elta_period_end` | Date of period end | Date | Daily | 100% |
| `ern10_aily_delta_recon_period_end` | Date of period end | Date | Daily | 100% |

### Field Deconstruction Analysis

#### `ern10_elta_value`: KEI Estimate Value
- **What is being measured?**: The numerical estimate for a specific key earnings input (e.g., unit sales, average selling price, gross margin, revenue) as projected by the covering analyst team
- **How is it measured?**: Extracted directly from equity research analyst financial models; represents the analyst's best estimate for the metric
- **Time dimension**: Forward-looking point estimate applicable to a specific future fiscal period (quarter/year)
- **Business context**: Captures analyst expectations on the fundamental drivers that determine earnings, before they aggregate to the bottom line
- **Generation logic**: Manually maintained by coverage analysts based on company guidance, industry trends, and macro factors; updated when new information emerges
- **Reliability considerations**: Subject to analyst bias and coverage quality; different analysts may use different methodologies; vector structure implies multiple KEI items per company that may have varying reliability

#### `ern10_aily_delta_recon_value`: Daily Delta Reconciliation Value
- **What is being measured?**: The daily change or adjustment made to the KEI estimate value
- **How is it measured?**: Calculated as the difference between the current period's estimate and the previous period's estimate, or as explicit adjustments distributed by the data provider
- **Time dimension**: Daily flow representing the most recent 24-hour change in expectations
- **Business context**: Tracks analyst activity intensity and direction of forecast revisions; serves as an early indicator of changing sentiment
- **Generation logic**: Automated reconciliation between consecutive data distributions; captures overnight or intraday analyst model updates
- **Reliability considerations**: Zero values indicate no change (stable expectations); non-zero values indicate active revision; magnitude indicates conviction level

### Field Relationship Mapping

**The Story This Data Tells**:
This dataset narrates the evolution of analyst expectations for the critical building blocks of corporate earnings. While earnings estimates aggregate everything into a single number, KEI reveals *which* specific drivers analysts are adjusting and by how much. The daily reconciliation stream captures the velocity of these adjustments, allowing detection of accelerating or decelerating expectations before they fully impact earnings consensus.

**Key Relationships Identified**:
1. **Revision Flow vs. Stock Level**: `aily_delta_recon_value` is the first difference (flow) of `elta_value` (stock). The flow indicates momentum while the stock indicates absolute expectations.
2. **Temporal Alignment**: `elta_run_timestamp` vs. `aily_delta_recon_run_timestamp` reveals data freshness. Large gaps between these timestamps may indicate stale estimates or data distribution issues.
3. **Period Consistency**: `elta_period_year` should align with `aily_delta_recon_period_year` for valid comparisons; divergence indicates fiscal period rollover effects.
4. **Cross-Driver Correlation**: Since `elta_value` is a vector of up to 5 KEI items, the internal dispersion (std dev across items) indicates analyst confidence consistency across different business drivers.

**Missing Pieces That Would Complete the Picture**:
- Actual reported values for these KEI items to calculate surprise (estimate vs. actual)
- Historical accuracy of each analyst to weight estimates by reliability
- Number of analysts contributing to each KEI (coverage breadth)
- Standard deviation across analysts (dispersion) rather than just the selected team's estimates

---

## Feature Concepts by Question Type


### Q1: "What is stable?" (Invariance Features)

**Concept**: KEI Cross-Driver Stability
- **Sample Fields Used**: `{elta_value}`
- **Definition**: Standard deviation of KEI estimates across different drivers for the same instrument
- **Why This Feature**: Low dispersion indicates analysts have consistent expectations across all key business drivers; high dispersion suggests mixed signals or uncertainty about which drivers will dominate
- **is filling nan necessary**: NaN values in the vector likely indicate missing coverage for specific KEI items. Since vec_stddev ignores NaNs by default, no filling is necessary; filling with zeros would artificially reduce measured dispersion.
- **Directionality**: High values indicate fragmented expectations (bearish signal due to uncertainty); low values indicate coherent forecasts (bullish signal of certainty)
- **Boundary Conditions**: Near-zero values indicate all drivers aligned; extremely high values relative to historical norms indicate business model confusion or transition periods
- **Implementation Example**: `vec_stddev({elta_value})`

**Concept**: Revision Calmness Index
- **Sample Fields Used**: `{aily_delta_recon_value}`
- **Definition**: 20-day average of absolute daily revisions
- **Why This Feature**: Measures the baseline volatility of analyst expectations. Stable estimates suggest information efficiency; frequent revisions suggest ongoing discovery or uncertainty.
- **is filling nan necessary**: NaN in daily delta likely means no revision (zero change). Using ts_backfill to carry forward zeros is appropriate since no change is meaningful information (stability).
- **Directionality**: Low values indicate stable, confident forecasts; high values indicate active revision and uncertainty
- **Boundary Conditions**: Zero indicates completely static estimates (potentially stale); values above historical 90th percentile indicate unusual analyst activity (potential signal)
- **Implementation Example**: `ts_mean(abs(vec_avg({aily_delta_recon_value})), 20)`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Estimate Revision Momentum
- **Sample Fields Used**: `{elta_value}`
- **Definition**: 5-day rate of change in average KEI estimates
- **Why This Feature**: Captures the direction and velocity of analyst sentiment shifts. Sustained momentum often precedes price moves as analysts incorporate new information before the broader market.
- **is filling nan necessary**: If estimate is missing for a day, ts_backfill is preferred to avoid treating missing data as zero change, which would create artificial momentum spikes.
- **Directionality**: Positive values indicate upgrading expectations (bullish); negative values indicate downgrades (bearish)
- **Boundary Conditions**: Large positive/negative values indicate rapid re-rating; values near zero indicate consensus stability
- **Implementation Example**: `ts_delta(vec_avg({elta_value}), 5)`

**Concept**: Accumulated Revision Drift
- **Sample Fields Used**: `{aily_delta_recon_value}`
- **Definition**: 10-day cumulative sum of daily reconciliation values
- **Why This Feature**: Captures the total magnitude of revision over a period, distinguishing between large one-day moves and sustained gradual adjustments
- **is filling nan necessary**: NaN daily deltas should be treated as zero (no change) for accumulation purposes to avoid bias. Use replace or assume ts_sum handles NaN as identity.
- **Directionality**: Positive accumulation indicates sustained upward pressure on estimates; negative indicates persistent downgrades
- **Boundary Conditions**: Extreme positive/negative values indicate analyst conviction; near-zero after volatile period indicates reversal or noise
- **Implementation Example**: `ts_sum(vec_avg({aily_delta_recon_value}), 10)`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Revision Surprise Z-Score
- **Sample Fields Used**: `{aily_delta_recon_value}`
- **Definition**: Standardized unexpected revision measuring how many standard deviations today's revision differs from the 20-day historical mean
- **Why This Feature**: Identifies information shocks. Large z-scores indicate analyst updates that break from recent trends, potentially signaling material new information not yet reflected in prices.
- **is filling nan necessary**: Historical NaNs should be backfilled to maintain stable std_dev calculation, but current day NaN should result in NaN output (no signal).
- **Directionality**: High positive values indicate surprise upgrades; high negative values indicate surprise downgrades; both extremes predictive of volatility
- **Boundary Conditions**: |z| > 2 indicates statistically significant surprise; |z| > 3 extreme outlier requiring attention
- **Implementation Example**: `(vec_avg({aily_delta_recon_value}) - ts_mean(vec_avg({aily_delta_recon_value}), 20)) / ts_std_dev(vec_avg({aily_delta_recon_value}), 20)`

**Concept**: Mean Revision Deviation
- **Sample Fields Used**: `{aily_delta_recon_value}`
- **Definition**: Deviation of current revision from the 20-day moving average (unstandardized)
- **Why This Feature**: Raw deviation captures magnitude of surprise without normalization, useful when absolute change matters more than relative to historical volatility
- **is filling nan necessary**: Use ts_backfill on the historical window to ensure robust mean calculation; current NaN propagates as NaN.
- **Directionality**: Large positive values indicate unusual upward revision; large negative indicates unusual downgrade
- **Boundary Conditions**: Values exceeding historical percentiles indicate regime change in expectations
- **Implementation Example**: `ts_av_diff(vec_avg({aily_delta_recon_value}), 20)`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Level-Adjusted Revision Intensity
- **Sample Fields Used**: `{elta_value}`, `{aily_delta_recon_value}`
- **Definition**: Daily revision magnitude scaled by the absolute level of the estimate (proportional change)
- **Why This Feature**: A $1 change on a $10 estimate (10%) is more significant than a $1 change on a $100 estimate (1%). This feature normalizes revision importance by estimate scale.
- **is filling nan necessary**: Denominator cannot be zero; add small epsilon (0.01) or use max(abs(vec_avg({elta_value})), 0.01). NaN handling in numerator as standard.
- **Directionality**: High values indicate material proportional revisions; low values indicate trivial updates
- **Boundary Conditions**: Values > 0.1 indicate 10%+ revisions (major updates); values < 0.001 indicate immaterial noise
- **Implementation Example**: `vec_avg({aily_delta_recon_value}) / (abs(vec_avg({elta_value})) + 0.01)`

**Concept**: Revision Direction-Estimate Level Interaction
- **Sample Fields Used**: `{elta_value}`, `{aily_delta_recon_value}`
- **Definition**: Product of estimate level and sign of revision
- **Why This Feature**: Captures whether high expectations are being revised up (momentum acceleration) or low expectations revised down (value trap formation). Positive values when high estimates upgrade; negative when low estimates downgrade.
- **is filling nan necessary**: Sign operator handles NaN by returning NaN; ensure vec_avg outputs are valid before multiplication.
- **Directionality**: Positive values indicate optimism begetting optimism; negative values indicate pessimism begetting pessimism; crossing zero indicates inflection
- **Boundary Conditions**: Extreme positive suggests bubble dynamics; extreme negative suggests capitulation
- **Implementation Example**: `vec_avg({elta_value}) * sign(vec_avg({aily_delta_recon_value}))`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Fiscal Period Alignment Consistency
- **Sample Fields Used**: `{elta_period_year}`, `{aily_delta_recon_period_year}`
- **Definition**: Binary indicator checking if current estimate and delta recon refer to the same fiscal year
- **Why This Feature**: Structural breaks occur at fiscal year-ends when analysts roll estimates forward. Misalignment indicates transition periods where estimates may be less reliable or subject to seasonal effects.
- **is filling nan necessary**: Period years are metadata; NaN unlikely. If present, treat as misaligned (0).
- **Directionality**: 1 indicates aligned periods (stable structure); 0 indicates transition (potential structural break)
- **Boundary Conditions**: Values flipping from 1 to 0 indicate fiscal year rollover; sustained 0 indicates data quality issues
- **Implementation Example**: `if_else({elta_period_year} == {aily_delta_recon_period_year}, 1.0, 0.0)`

**Concept**: Estimate Staleness Structure
- **Sample Fields Used**: `{elta_run_timestamp}`
- **Definition**: Days since the last estimate file was generated
- **Why This Feature**: Identifies how fresh the estimate data is. Stale estimates (high days) may no longer reflect current analyst views, creating potential alpha from stale information arbitrage.
- **is filling nan necessary**: Timestamp NaN indicates missing data; should remain NaN as staleness is undefined.
- **Directionality**: Low values indicate fresh data (reliable); high values indicate stale estimates (potential mispricing opportunity)
- **Boundary Conditions**: Zero indicates today's data; values > 5 indicate potentially stale estimates in fast-moving markets
- **Implementation Example**: `days_from_last_change({elta_run_timestamp})`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Cumulative Revision Path
- **Sample Fields Used**: `{aily_delta_recon_value}`
- **Definition**: 20-day cumulative sum of daily reconciliation values
- **Why This Feature**: Measures the total adjustment to estimates over a month. Positive accumulation indicates sustained upgrading; negative indicates sustained downgrading. Captures trends that single-day metrics miss.
- **is filling nan necessary**: NaN daily values should be treated as zero (no change) to prevent accumulation bias. Use replace to convert NaN to 0 before ts_sum, or ensure operator treats NaN as 0.
- **Directionality**: Positive values indicate net upgrading pressure; negative values indicate net downgrading; magnitude indicates total adjustment magnitude
- **Boundary Conditions**: Extreme values indicate analyst conviction in new thesis; reversion to zero indicates whip-saw or noise
- **Implementation Example**: `ts_sum(vec_avg({aily_delta_recon_value}), 20)`

**Concept**: Accumulated Revision Volatility
- **Sample Fields Used**: `{aily_delta_recon_value}`
- **Definition**: Sum of squared daily revisions over 20 days
- **Why This Feature**: Captures total revision "energy" regardless of direction. High values indicate periods of intense analyst debate and uncertainty; low values indicate consensus stability.
- **is filling nan necessary**: NaN should be treated as 0 (no volatility contribution) to avoid understating volatility when data is missing.
- **Directionality**: High values indicate high uncertainty/information flux; low values indicate stable information environment
- **Boundary Conditions**: Values in top decile historically indicate unusual uncertainty (often precedes volatility expansion)
- **Implementation Example**: `ts_sum(signed_power(vec_avg({aily_delta_recon_value}), 2), 20)`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Cross-Sectional Revision Rank
- **Sample Fields Used**: `{aily_delta_recon_value}`
- **Definition**: Cross-sectional rank of today's revision magnitude across the universe
- **Why This Feature**: Identifies which instruments are experiencing the most significant analyst updates relative to peers. Extreme ranks indicate idiosyncratic information flow.
- **is filling nan necessary**: NaN values should remain NaN (no rank assigned) rather than being filled, as missing revision data is not comparable to zero revision.
- **Directionality**: High rank (top decile) indicates most positive revision in universe; low rank (bottom decile) indicates most negative revision
- **Boundary Conditions**: Values near 0.5 indicate median revision; near 0 or 1 indicate extreme tails
- **Implementation Example**: `rank(vec_avg({aily_delta_recon_value}))`

**Concept**: Historical Revision Percentile
- **Sample Fields Used**: `{aily_delta_recon_value}`
- **Definition**: Percentile position of current revision within the 60-day historical distribution for each instrument
- **Why This Feature**: Contextualizes today's revision against the instrument's own historical revision pattern. A revision that is normal for one stock may be extreme for another.
- **is filling nan necessary**: Historical NaNs should be ignored in percentile calculation; current NaN returns NaN.
- **Directionality**: High values (near 1.0) indicate historically large positive revision; low values (near 0.0) indicate historically large negative revision
- **Boundary Conditions**: Values > 0.9 or < 0.1 indicate extreme historical revisions; values near 0.5 indicate typical daily noise
- **Implementation Example**: `ts_percentage(vec_avg({aily_delta_recon_value}), 60)`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Pure Revision Signal
- **Sample Fields Used**: `{aily_delta_recon_value}`
- **Definition**: The raw average daily revision across all KEI items
- **Why This Feature**: Strips away all complexity to capture the essential change in analyst expectations. This is the first derivative of sentiment - the most direct measure of analyst belief changes.
- **is filling nan necessary**: NaN indicates no data, distinct from zero revision. Preserve NaN to avoid false signals.
- **Directionality**: Positive indicates upgrading expectations (bullish); negative indicates downgrading (bearish); zero indicates status quo
- **Boundary Conditions**: Extreme values indicate conviction; near-zero indicates indecision or lack of new information
- **Implementation Example**: `vec_avg({aily_delta_recon_value})`

**Concept**: Core Expectation Level
- **Sample Fields Used**: `{elta_value}`
- **Definition**: The raw average estimate level across all KEI drivers
- **Why This Feature**: Represents the absolute level of analyst optimism/pessimism about key drivers. High levels suggest high expectations (potential disappointment risk); low levels suggest conservative estimates (potential beat opportunity).
- **is filling nan necessary**: NaN indicates missing coverage; preserve to avoid false zero-level signals.
- **Directionality**: High values indicate optimistic analyst expectations; low values indicate conservative expectations; trend matters more than absolute
- **Boundary Conditions**: Extreme high values relative to historical range indicate peak optimism; extreme low indicate trough pessimism
- **Implementation Example**: `vec_avg({elta_value})`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Vector data with up to 5 KEI items per instrument; vec_avg aggregates across available items but coverage varies by company complexity
- **Timeliness**: Delay=1 means T-1 data available; daily reconciliation provides high-frequency signal but may contain noise from non-informational updates
- **Accuracy**: Analyst-selected KEI items are subjective and may change over time (items added/removed), creating structural breaks in time series
- **Potential Biases**: Large-cap stocks tend to have more comprehensive KEI coverage; small-caps may have fewer items creating different vec_avg behaviors

### Computational Complexity
- **Lightweight features**: `vec_avg({elta_value})`, `vec_avg({aily_delta_recon_value})`, rank operations
- **Medium complexity**: `ts_delta`, `ts_mean`, `ts_std_dev` on vector-aggregated data (20-day windows)
- **Heavy computation**: `ts_percentage` with 60-day lookback, multi-operator combinations requiring careful NaN handling

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Pure Revision Signal** (`vec_avg({aily_delta_recon_value})`) - Direct, interpretable, high signal-to-noise for short-term alpha
2. **Revision Surprise Z-Score** - Standardized anomaly detection robust across different volatility regimes
3. **Estimate Revision Momentum** (`ts_delta`) - Classic momentum signal applicable to analyst expectations

**Tier 2 (Secondary Priority)**:
1. **Level-Adjusted Revision Intensity** - Proportional adjustment important for cross-sectional comparison
2. **Cumulative Revision Path** - Captures sustained trends missed by daily signals
3. **Cross-Sectional Revision Rank** - Relative positioning within universe reduces market-wide factor noise

**Tier 3 (Requires Further Validation)**:
1. **Fiscal Period Alignment Consistency** - Binary structure filter; requires validation that misalignment actually predicts noisier signals
2. **Estimate Staleness Structure** - Requires calibration of what constitutes "stale" (3 days? 5 days?)

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How does the number of active KEI items (vector length) affect signal quality? Do instruments with 5 items behave differently than those with 1 item?
2. Do revisions in specific KEI items (e.g., revenue vs. margin) have different predictive power, and can we weight vec_avg accordingly?
3. How does this dataset interact with actual earnings surprises? Do KEI revisions predict earnings beats/misses?

### Recommended Additional Data:
- **Actual reported KEI values** (for calculating true analyst accuracy and post-earnings drift)
- **Analyst identifier metadata** (to weight by analyst historical accuracy)
- **Cross-analyst dispersion** (standard deviation across multiple analysts for same KEI)

### Assumptions to Challenge:
- Assumption that all KEI items are equally important (they are analyst-selected but may have different economic significance)
- Assumption that daily delta represents new information rather than data corrections or methodological changes
- Assumption that analyst-selected KEI covers the true economic drivers (analysts may focus on easily forecastable metrics rather than value-relevant ones)

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction distinguishing between stock levels (elta_value) and flow deltas (aily_delta_recon_value)
2. Recognition of vector data structure requiring vec_avg aggregation before time-series operations
3. Question-driven feature generation applying 8 fundamental analytical perspectives
4. Emphasis on revision dynamics as the primary signal source in analyst estimate data

**Design Principles**:
- Distinguish between estimate levels (valuation context) and revisions (momentum signal)
- Account for vector aggregation requirements in all implementation examples
- Prioritize features that capture anomalous analyst behavior (surprise detection)
- Maintain transparency about NaN handling and data quality limitations

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate staleness assumptions, test interaction with price momentum factors*