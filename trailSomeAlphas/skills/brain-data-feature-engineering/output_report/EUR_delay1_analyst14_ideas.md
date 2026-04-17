**Dataset**: analyst14
**Region**: EUR
**Delay**: 1

# Estimations of Key Fundamentals Feature Engineering Analysis Report

**Dataset**: analyst14
**Category**: Analyst
**Region**: EUR
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 121

---

## Executive Summary

**Primary Question Answered by Dataset**: What do financial analysts collectively expect about future company performance, how confident are they in those expectations, and how do actual reported results compare to those expectations?

**Key Insights from Analysis**:
- The dataset captures a multi-dimensional view of analyst sentiment through point estimates (revenue, earnings), dispersion measures (stddev, high/low ranges), recommendation distributions, and price targets
- Critical time structure exists between fp0 (actual reported), fp1 (next quarter estimates), and fp2 (following quarter estimates) enabling growth trajectory and surprise analysis
- The combination of coverage count (`numofests`) and dispersion (`stddev`) creates a natural "confidence" metric for each estimate
- Recommendation data (buy/hold/sell) provides sentiment overlay independent of fundamental estimates

**Critical Field Relationships Identified**:
- `mean` vs `stddev`: Inverse relationship indicates consensus confidence (low stddev with high mean = strong conviction)
- `fp1` vs `fp2`: Sequential quarterly estimates reveal growth acceleration/deceleration patterns
- `actvalue_fp0` vs lagged `mean_fp1`: Basis for earnings surprise measurement when temporally aligned
- `high` vs `low`: Range indicates analyst disagreement/extreme views

**Most Promising Feature Concepts**:
1. **Estimate Coefficient of Variation** (`stddev/mean`) - because it normalizes uncertainty by the magnitude of expectations, identifying stocks with dangerous high-variance consensus
2. **Consensus Trajectory** (`fp2/fp1` growth ratios) - because it captures analyst views on acceleration/deceleration independent of absolute levels
3. **Recommendation Intensity** (`(buy-sell)/total`) - because it distills complex recommendation distributions into directional sentiment

---

## Dataset Deep Understanding

### Dataset Description
This dataset reports analyst consensus estimates for key fundamental metrics (revenue, EBITDA, EBIT, EPS, net profit) across multiple forecast horizons (current actual fp0, upcoming quarter fp1, and following quarter fp2). For each metric and horizon, it provides distributional statistics (mean, median, high, low, standard deviation) and coverage metrics (number of estimates). Additionally, it includes recommendation distributions (buy, hold, sell, outperform, underperform), price target statistics, and actual reported values for the most recent quarter. This creates a comprehensive view of both market expectations (forward-looking) and reality (backward-looking actuals).

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `anl14_mean_revenue_fp1` | Mean analyst revenue estimate - upcoming quarter | Float | Daily | 85% |
| `anl14_stddev_revenue_fp1` | Standard deviation of revenue estimates | Float | Daily | 85% |
| `anl14_numofests_revenue_fp1` | Number of analysts covering revenue | Integer | Daily | 85% |
| `anl14_actvalue_revenue_fp0` | Actual reported revenue - recent quarter | Float | Quarterly | 95% |
| `anl14_high_revenue_fp1` | Highest revenue estimate (bull case) | Float | Daily | 85% |
| `anl14_low_revenue_fp1` | Lowest revenue estimate (bear case) | Float | Daily | 85% |
| `anl14_buy` | Count of buy recommendations | Integer | Daily | 80% |
| `anl14_sell` | Count of sell recommendations | Integer | Daily | 80% |
| `anl14_meanrating` | Mean recommendation rating | Float | Daily | 80% |
| `rtk_ptg_mean` | Mean price target | Float | Daily | 75% |
| `anl14_cursharesoutstanding` | Current shares outstanding | Float | Daily | 99% |

*(Additional fields follow similar patterns for EBIT, EBITDA, EPS, Net Profit across fp1/fp2 horizons)*

### Field Deconstruction Analysis

#### `anl14_mean_revenue_fp1`: Mean Revenue Estimate (Upcoming Quarter)
- **What is being measured?**: The central tendency of analyst expectations for revenue in the next fiscal quarter
- **How is it measured?**: Arithmetic mean of all active analyst estimates for that metric and horizon
- **Time dimension**: Forward-looking (next reporting period)
- **Business context**: Represents the market's consensus expectation for near-term top-line performance; deviations from actuals drive earnings surprise reactions
- **Generation logic**: Aggregated from individual analyst models; updates as analysts revise estimates
- **Reliability considerations**: Reliability increases with `numofests`; single-analyst means are volatile

#### `anl14_stddev_revenue_fp1`: Standard Deviation of Revenue Estimates
- **What is being measured?**: Dispersion or disagreement among analysts regarding future revenue
- **How is it measured?**: Statistical standard deviation across the distribution of estimates
- **Time dimension**: Forward-looking snapshot of uncertainty
- **Business context**: High values indicate controversy or unpredictable business conditions; low values indicate consensus
- **Generation logic**: Calculated from the same estimate population as the mean
- **Reliability considerations**: Requires minimum analyst coverage (n>2) to be meaningful; zero with single analyst

#### `anl14_actvalue_revenue_fp0`: Actual Reported Revenue (Recent Quarter)
- **What is being measured?**: The realized, audited revenue figure for the most recently completed fiscal quarter
- **How is it measured?**: Company-reported financial statement data
- **Time dimension**: Backward-looking, historical fact
- **Business context**: Ground truth against which previous estimates are measured; basis for surprise metrics
- **Generation logic**: Derived from official company filings (10-Q, earnings releases)
- **Reliability considerations**: Audited numbers are highly reliable but subject to restatements; timing aligned with fiscal calendar, not trading calendar

#### `anl14_buy`: Buy Recommendation Count
- **What is being measured?**: The number of analysts explicitly recommending purchase of the stock
- **How is it measured?**: Count of ratings categorized as "Buy" or equivalent
- **Time dimension**: Current snapshot (valid until analyst changes rating)
- **Business context**: Direct sentiment indicator reflecting analyst conviction in upside potential independent of specific financial estimates
- **Generation logic**: Categorical aggregation across analyst ratings
- **Reliability considerations**: Subject to banking relationship biases; counts without price target context can be misleading

#### `rtk_ptg_mean`: Mean Price Target
- **What is being measured?**: Analyst consensus on 12-month forward stock price expectation
- **How is it measured?**: Average of individual analyst price target estimates
- **Time dimension**: Forward-looking (typically 12-month horizon)
- **Business context**: Represents implied upside/downside from current price; synthesis of valuation models and fundamental estimates
- **Generation logic**: Aggregation of analyst DCF/multiples-based price targets
- **Reliability considerations**: Less frequent updates than earnings estimates; stale targets common during quiet periods

### Field Relationship Mapping

**The Story This Data Tells**:
Analysts form expectations about future fundamentals (revenue, earnings) across multiple time horizons. These expectations have both a central tendency (mean/median) and uncertainty (stddev, range). As actual results approach, the estimates converge toward reality, creating predictable patterns of revision. Simultaneously, analysts issue directional recommendations and price targets that synthesize these fundamental views into investment advice. The dataset captures the full lifecycle from expectation formation (fp1/fp2 estimates) to realization (fp0 actuals) to market reaction implications (recommendations, price targets).

**Key Relationships Identified**:
1. **Precision-Coverage Relationship**: Higher `numofests` typically correlates with lower `stddev` (law of large numbers in consensus building), creating a confidence metric
2. **Horizon Decay**: The variance between `fp1` and `fp2` estimates reveals growth trajectory expectations; stable businesses show parallel paths, cyclical/disruptive businesses show divergence
3. **Expectation-Actual Divergence**: The gap between `actvalue_fp0` and prior-period `mean_fp1` (when temporally aligned) measures earnings quality and surprise magnitude
4. **Sentiment-Fundamental Alignment**: `buy` counts should theoretically correlate with positive estimate revision momentum and high `mean` relative to historical trends

**Missing Pieces That Would Complete the Picture**:
- Historical estimate revision trails (how did fp1 estimates change over the past 90 days) - partially reconstructible with time-series operators but native deltas would be cleaner
- Analyst identity/affiliation data to weight estimates by historical accuracy or detect herding behavior
- Timestamp of last estimate update to identify stale consensus
- Sector/industry classification for relative comparison benchmarks

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: Estimate Dispersion Stability (Coefficient of Variation)
- **Sample Fields Used**: stddev_revenue_fp1, mean_revenue_fp1
- **Definition**: The ratio of standard deviation to absolute mean value, measuring relative disagreement among analysts normalized by the magnitude of the estimate
- **Why This Feature**: Raw standard deviation is scale-dependent; normalizing by mean allows comparison across companies of different sizes. Low values indicate strong consensus (stable expectations), high values indicate controversy.
- **Logical Meaning**: Measures the signal-to-noise ratio of analyst consensus. A low CV (<0.1) suggests analysts agree precisely; high CV (>0.3) suggests fundamental unpredictability or conflicting information.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. For single-analyst coverage (stddev undefined), NaN is meaningful (no disagreement to measure) and should be preserved or handled via conditional logic rather than forward-fill.
- **Directionality**: Lower values (high stability/consensus) typically associated with lower volatility and more predictable earnings; higher values indicate uncertainty
- **Boundary Conditions**: Approaches infinity as mean approaches zero (loss-making companies); undefined for single-analyst coverage
- **Implementation Example**: `{stddev_revenue_fp1} / abs({mean_revenue_fp1} + 0.01)`

**Concept**: Consensus Durability
- **Sample Fields Used**: mean_revenue_fp1, mean_revenue_fp2
- **Definition**: The correlation or ratio stability between near-term (fp1) and medium-term (fp2) estimates over time, measuring whether the growth trajectory is consistent
- **Why This Feature**: Distinguishes between companies with stable, predictable growth profiles (consistent fp1/fp2 ratios) and those with cyclical or one-time growth impacts (volatile ratios)
- **Logical Meaning**: Captures the structural stability of the business model. Consistent fp2/fp1 ratios suggest recurring revenue/predictable operations; highly variable ratios suggest project-based or cyclical earnings.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: High stability (consistent ratio ~1.0 for flat growth or stable growth rate) indicates mature, predictable business; high variance indicates uncertainty or inflection points
- **Boundary Conditions**: Extreme values when fp1 approaches zero (loss quarters)
- **Implementation Example**: `ts_mean({mean_revenue_fp2} / ({mean_revenue_fp1} + 0.01), 20)`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Estimate Revision Momentum
- **Sample Fields Used**: mean_revenue_fp1
- **Definition**: The rate of change in consensus estimates over recent trading days, capturing analyst optimism/pessimism trends
- **Why This Feature**: Analysts revise estimates based on new information; aggregating these revisions captures emerging fundamental trends before they appear in actuals. Positive momentum often precedes price appreciation.
- **Logical Meaning**: Measures the direction and velocity of changing expectations. Accelerating upward revisions suggest improving business conditions; deceleration suggests peak growth.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Positive values indicate upgrading estimates (bullish momentum); negative values indicate downgrades (bearish momentum)
- **Boundary Conditions**: Extreme values during earnings announcement windows when analysts batch-update models
- **Implementation Example**: `ts_delta({mean_revenue_fp1}, 5)`

**Concept**: Growth Trajectory Shift
- **Sample Fields Used**: mean_revenue_fp1, mean_revenue_fp2
- **Definition**: The changing relationship between near-term and longer-term growth expectations, calculated as the delta of the fp2/fp1 ratio
- **Why This Feature**: Distinguishes between sustainable growth (stable or improving fp2/fp1) and decelerating growth (declining fp2/fp1). Captures inflection points in business cycles.
- **Logical Meaning**: Measures acceleration/deceleration. Ratio > 1 indicates growth expected to continue or accelerate; declining ratio indicates peak growth concerns.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Increasing ratio indicates acceleration (positive); decreasing indicates deceleration (negative)
- **Boundary Conditions**: Volatile when fp1 estimates cross zero or change signs
- **Implementation Example**: `ts_delta({mean_revenue_fp2} / ({mean_revenue_fp1} + 0.01), 10)`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Extreme Estimate Divergence
- **Sample Fields Used**: high_revenue_fp1, low_revenue_fp1, mean_revenue_fp1, stddev_revenue_fp1
- **Definition**: The normalized range between bull (high) and bear (low) case estimates, measuring analyst polarization
- **Why This Feature**: Wide ranges indicate binary outcomes or controversy (takeover targets, turnaround stories). Identifies stocks where consensus mean may be misleading due to bimodal distributions.
- **Logical Meaning**: Quantifies analyst disagreement. Values >3 standard deviations suggest extreme views; values <0.5 std devs suggest tight clustering.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Higher values indicate extreme uncertainty/controversy (often contrarian signals); lower values indicate consensus
- **Boundary Conditions**: Minimum bound of zero (perfect agreement); no upper bound theoretically
- **Implementation Example**: `({high_revenue_fp1} - {low_revenue_fp1}) / ({stddev_revenue_fp1} + 0.01)`

**Concept**: Earnings Surprise Magnitude
- **Sample Fields Used**: actvalue_revenue_fp0, mean_revenue_fp1
- **Definition**: The standardized difference between actual reported revenue and the lagged consensus estimate from the beginning of the quarter (using ts_delay to align temporally)
- **Why This Feature**: Captures the "expectations gap" - stocks systematically beating or missing estimates. High positive surprises often lead to drift; consistent misses indicate guidance gaming.
- **Logical Meaning**: Measures actual performance vs expectations. Large deviations indicate information asymmetry or analyst bias.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Positive values indicate beat (bullish); negative values indicate miss (bearish)
- **Boundary Conditions**: Extreme values during M&A or restructuring when estimates become stale
- **Implementation Example**: `{actvalue_revenue_fp0} - ts_delay({mean_revenue_fp1}, 90)`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Confidence-Weighted Estimate
- **Sample Fields Used**: mean_revenue_fp1, numofests_revenue_fp1, stddev_revenue_fp1
- **Definition**: The consensus estimate weighted by the precision of that estimate (coverage divided by dispersion), emphasizing high-coverage, low-disagreement forecasts
- **Why This Feature**: Not all estimates are equal; this distinguishes between a $100M mean from 20 analysts (reliable) vs $100M from 2 analysts with wide dispersion (unreliable). Creates quality-adjusted signal.
- **Logical Meaning**: High values indicate strong conviction (many analysts, tight range); near-zero values indicate low confidence. Penalizes thin or controversial coverage.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Higher absolute values indicate stronger signal reliability; sign depends on mean value direction
- **Boundary Conditions**: Zero when no coverage; dominated by stddev when dispersion is high
- **Implementation Example**: `{mean_revenue_fp1} * ({numofests_revenue_fp1} / ({stddev_revenue_fp1} + 1.0))`

**Concept**: Margin Quality Score
- **Sample Fields Used**: mean_ebit_fp1, mean_revenue_fp1
- **Definition**: The ratio of operating profit estimates to revenue estimates, measuring expected operational efficiency and business model quality
- **Why This Feature**: Revenue growth without margin expansion indicates competitive pressure; margin expansion with stable revenue indicates pricing power. Combines top-line and bottom-line expectations.
- **Logical Meaning**: Higher values indicate capital-light or high-margin businesses; improving trends indicate scaling efficiency; declining trends indicate margin compression.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Higher values indicate better operational efficiency; negative values indicate expected operating losses
- **Boundary Conditions**: Extreme values for pre-revenue biotech or asset-light software; undefined at zero revenue
- **Implementation Example**: `{mean_ebit_fp1} / ({mean_revenue_fp1} + 0.01)`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Recommendation Distribution Skew
- **Sample Fields Used**: buy, sell, hold, outperform, underperform
- **Definition**: The net sentiment calculated as (buy + outperform - sell - underperform) normalized by total recommendations, creating a bounded sentiment score
- **Why This Feature**: Raw buy counts are size-dependent; this normalization creates comparable sentiment metric across large and small cap stocks. Captures the skew of the recommendation distribution.
- **Logical Meaning**: Values near +1 indicate unanimous bullishness; near -1 indicate bearish consensus; near 0 indicate confusion or hold-heavy coverage.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Positive values indicate bullish skew (predictive of outperformance in some markets); negative values indicate bearish skew
- **Boundary Conditions**: Approaches +1 with unanimous buys; undefined with zero coverage (denominator protection needed)
- **Implementation Example**: `({buy} + {outperform} - {sell} - {underperform}) / ({buy} + {sell} + {hold} + {outperform} + {underperform} + 1.0)`

**Concept**: Estimate Coverage Breadth
- **Sample Fields Used**: numofests_revenue_fp1, numofests_eps_fp1, numofests_ebitda_fp1
- **Definition**: The minimum coverage level across key metrics (revenue, earnings, EBITDA), identifying stocks with complete vs partial analyst coverage
- **Why This Feature**: Stocks with coverage gaps (many revenue estimates but few EPS estimates) may have complex revenue recognition or unclear cost structures. Complete coverage indicates thorough analyst attention.
- **Logical Meaning**: High values indicate institutional coverage depth; low values indicate neglected stocks or complexity that deters analysis.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Higher values indicate greater scrutiny and information efficiency; very low values indicate potential information asymmetry opportunities
- **Boundary Conditions**: Zero for uncovered stocks; capped by maximum analysts in universe
- **Implementation Example**: `min({numofests_revenue_fp1}, min({numofests_eps_fp1}, {numofests_ebitda_fp1}))`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Cumulative Positive Revision Pressure
- **Sample Fields Used**: mean_revenue_fp1
- **Definition**: The sum of all positive daily changes in estimates over a lookback period, ignoring negative revisions, measuring accumulated upward pressure
- **Why This Feature**: Isolates the asymmetry of information flow - persistent small upgrades may indicate gradual improvement recognition. Cumulative metrics capture persistence better than point-in-time changes.
- **Logical Meaning**: Large values indicate sustained positive news flow; near-zero values indicate stability or mixed revisions; distinguishes trend from noise.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Higher values indicate strong accumulation of positive sentiment; zero indicates no positive momentum
- **Boundary Conditions**: Bounded below by zero; upper bound determined by magnitude and frequency of revisions
- **Implementation Example**: `ts_sum(max(ts_delta({mean_revenue_fp1}, 1), 0), 20)`

**Concept**: Coverage Accumulation Rate
- **Sample Fields Used**: numofests_revenue_fp1
- **Definition**: The change in analyst coverage count over time, measuring emerging interest or declining attention from the sell-side
- **Why This Feature**: Increasing coverage often precedes index inclusion or catalyst events; decreasing coverage indicates waning institutional interest. Captures the "discovery" phase of stocks.
- **Logical Meaning**: Positive values indicate growing analyst attention (often young growth companies); negative values indicate declining coverage (often mature or troubled companies).
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Positive values indicate increasing institutional attention; negative values indicate neglect
- **Boundary Conditions**: Cannot go below zero; sharp drops when brokers drop coverage
- **Implementation Example**: `ts_delta({numofests_revenue_fp1}, 20)`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Mean-Median Divergence (Skewness Proxy)
- **Sample Fields Used**: mean_revenue_fp1, median_revenue_fp1, stddev_revenue_fp1
- **Definition**: The normalized difference between mean and median estimates, indicating the skewness of the analyst estimate distribution
- **Why This Feature**: When mean > median, the distribution is right-skewed (bullish outliers pulling average up); when mean < median, left-skewed (bearish outliers). Identifies asymmetric risk.
- **Logical Meaning**: Positive values indicate optimistic tail risk (some analysts very bullish); negative values indicate pessimistic tail risk. Zero indicates symmetric distribution.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Positive indicates bullish skew (mean pulled above median by high outliers); negative indicates bearish skew
- **Boundary Conditions**: Normalized by stddev to be scale-invariant; undefined with zero dispersion
- **Implementation Example**: `({mean_revenue_fp1} - {median_revenue_fp1}) / ({stddev_revenue_fp1} + 0.01)`

**Concept**: Price Target to Earnings Valuation Gap
- **Sample Fields Used**: ptg_mean, mean_eps_fp1, cursharesoutstanding
- **Definition**: The implied forward P/E ratio derived from price target divided by estimated earnings, measuring valuation optimism relative to earnings power
- **Why This Feature**: Combines valuation (price target) with fundamentals (earnings) to identify stocks where analysts expect multiple expansion vs earnings growth to drive returns.
- **Logical Meaning**: High values indicate valuation-driven expectations; low values indicate earnings-recovery plays. Changes indicate shifting analyst valuation models.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Higher values indicate rich valuation expectations; lower values indicate value expectations
- **Boundary Conditions**: Extreme when earnings near zero; requires shares outstanding for total earnings calculation
- **Implementation Example**: `{ptg_mean} / ({mean_eps_fp1} * {cursharesoutstanding} + 0.01)`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Standard Error of Consensus
- **Sample Fields Used**: stddev_revenue_fp1, numofests_revenue_fp1
- **Definition**: The standard deviation divided by the square root of sample size, representing the statistical precision of the consensus estimate
- **Why This Feature**: Distills the essence of estimate quality - not just how much disagreement, but how statistically reliable the mean is. Fundamental to the dataset's value proposition.
- **Logical Meaning**: Lower values indicate high-precision estimates (tight consensus with many analysts); higher values indicate low confidence. The theoretical minimum error of the consensus.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Lower values indicate higher quality estimates; very high values indicate the consensus mean is statistically unreliable
- **Boundary Conditions**: Undefined for n<2; decreases with sqrt(n) law
- **Implementation Example**: `{stddev_revenue_fp1} / sqrt({numofests_revenue_fp1} + 0.01)`

**Concept**: Fundamental Information Ratio
- **Sample Fields Used**: mean_revenue_fp1, stddev_revenue_fp1
- **Definition**: The ratio of expected value (mean estimate) to uncertainty (standard deviation), analogous to Sharpe ratio for fundamentals
- **Why This Feature**: Captures the risk-adjusted opportunity in the fundamental outlook. Essential distillation of risk vs reward in the analyst forecasts.
- **Logical Meaning**: High values indicate attractive risk-reward (high expected growth relative to uncertainty); low/negative values indicate poor risk-reward or negative growth expectations with high uncertainty.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Higher values indicate better risk-adjusted growth expectations; negative values indicate expected decline
- **Boundary Conditions**: Zero-crossing behavior when estimates change sign; extreme values near zero stddev
- **Implementation Example**: `{mean_revenue_fp1} / ({stddev_revenue_fp1} + 0.01)`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Coverage varies significantly by market cap and sector; large-cap stocks have complete fp1/fp2 coverage across all metrics while small-caps may have sparse coverage (2-3 analysts). NaN handling is critical for universality.
- **Timeliness**: Estimates update asynchronously as analysts publish; high-frequency changes may reflect individual analyst inputs rather than consensus shifts. Consider smoothing (ts_decay) to reduce noise.
- **Accuracy**: Actual values (fp0) are audited but subject to restatements; price targets are discretionary and less frequently updated than estimates.
- **Potential Biases**: Analysts exhibit herding behavior; stddev may underestimate true uncertainty. Recommendation data biased by investment banking relationships (reluctance to issue sells).

### Computational Complexity
- **Lightweight features**: Ratio-based features (CV, margins, recommendation skew) - single operations
- **Medium complexity**: Time-series smoothed features (ts_mean, ts_delta over 20 days) - rolling window operations
- **Heavy computation**: Cross-sectional neutralization (group_mean by industry) if industry mappings added; triple correlations between fp0, fp1, fp2 across multiple metrics

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Estimate Dispersion Stability** (`stddev/mean`) - Robust cross-sectional signal with clear economic interpretation (uncertainty premium)
2. **Estimate Revision Momentum** (`ts_delta(mean, 5)`) - Classic earnings momentum factor with strong literature support
3. **Recommendation Distribution Skew** - Simple categorical aggregation providing orthogonal sentiment signal

**Tier 2 (Secondary Priority)**:
1. **Mean-Median Divergence** - Captures distribution asymmetry missed by mean-only features
2. **Confidence-Weighted Estimate** - Quality adjustment for estimate reliability
3. **Growth Trajectory Shift** - fp2/fp1 dynamics for acceleration detection

**Tier 3 (Requires Further Validation)**:
1. **Earnings Surprise Magnitude** - Requires careful temporal alignment (delay settings) to avoid look-ahead bias; validate with specific fiscal calendar offsets
2. **Price Target to Earnings Gap** - Requires validation of shares outstanding data frequency and adjustment events

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How does the optimal lookback period for estimate revisions vary by sector (growth vs value)?
2. Do analyst estimates exhibit systematic optimism bias that varies across market cycles, and can we adjust for this?
3. What is the information decay rate of price targets relative to earnings estimates?

### Recommended Additional Data:
- Industry classification for relative ranking within sectors
- Historical analyst accuracy scores to weight estimates by forecaster quality
- Earnings announcement dates to align surprise calculations properly
- Short interest data to combine with recommendation skew for contrarian signals

### Assumptions to Challenge:
- That more analyst coverage always increases estimate reliability (may increase herding/reduce information diversity)
- That mean estimates are more accurate than median (median may be robust to outlier analyst errors)
- That fp2 estimates contain independent information from fp1 (may simply be algorithmic extrapolations)

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence (actuals vs estimates, dispersion vs central tendency, multiple horizons)
2. Question-driven feature generation (8 fundamental questions) applied to analyst estimate context
3. Logical validation of each feature concept against financial theory and data limitations
4. Transparent documentation of reasoning including boundary conditions and bias acknowledgment

**Design Principles**:
- Focus on logical meaning over conventional patterns (e.g., emphasizing distribution skew over simple mean)
- Every feature must answer a specific question about the data structure
- Clear documentation of "why" for each suggestion with directional intuition
- Emphasis on the unique aspects of analyst data (dispersion, horizon structure, recommendation overlay)

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate assumptions, gather additional data as needed*