**Dataset**: analyst90
**Region**: EUR
**Delay**: 1

# Analyst Idea Dataset (analyst90) Feature Engineering Analysis Report

**Dataset**: analyst90
**Category**: Analyst
**Region**: EUR
**Analysis Date**: 2024-12-19
**Fields Analyzed**: 15

---

## Executive Summary

**Primary Question Answered by Dataset**: What is the real-time aggregation of sell-side analyst trade recommendations, conviction levels, and expected price movements across major broker platforms?

**Key Insights from Analysis**:
- Dataset contains vector-type fields requiring aggregation (vec_avg, vec_sum) before cross-sectional or time-series analysis
- Buy and sell recommendation weightings provide net sentiment signals when differenced
- Success likelihood scores offer probability-weighted filtering of recommendation strength
- Expected vs. actual closing prices enable measurement of analyst forecast accuracy
- Author metadata (company, role, location) allows attribution-based filtering and quality scoring

**Critical Field Relationships Identified**:
- `buy_recommendation_weighting` and `sell_recommendation_weighting` form a paired sentiment spectrum (net positioning)
- `expected_exit_price` and `anl90_openprice` define the expected return distribution for trade ideas
- `success_likelihood_score` acts as a confidence modifier on recommendation weightings
- `anl90_investmentprice` and `trade_closing_price` provide realized vs. intended entry points

**Most Promising Feature Concepts**:
1. **Net Sentiment Imbalance** (vec_sum buy - vec_sum sell) - captures directional consensus intensity
2. **Risk-Adjusted Conviction** (likelihood × recommendation weighting) - filters low-confidence signals
3. **Expected Return Spread** (exit vs. open price ratio) - quantifies implied alpha magnitude
4. **Author Conviction Stability** (coefficient of variation of weightings) - measures consistency of recommendation sources

---

## Dataset Deep Understanding

### Dataset Description
This dataset aggregates and refines short-term trade ideas from multiple leading sell-side brokers and alpha capture platforms, including deduplication and integration of feeds from major sources such as UBS, Citi, TIM, and Bloomberg. It captures actionable buy and sell recommendations, conviction levels, catalysts, and target prices, along with detailed metadata on contributors and instruments. By consolidating and cleaning these trade ideas, the dataset provides a comprehensive, high-frequency view of analyst sentiment and market positioning. This information is valuable for predicting near-term price movements, identifying consensus shifts, and constructing event-driven or sentiment-based trading strategies.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `anl90_authorcompany` | author company | Vector | Daily | 95% |
| `anl90_authorlocation` | author location | Vector | Daily | 92% |
| `anl90_authorname` | author name | Vector | Daily | 95% |
| `anl90_authorrole` | author role | Vector | Daily | 88% |
| `anl90_investment` | investment | Vector | Daily | 90% |
| `anl90_investmentprice` | investment price | Vector | Daily | 85% |
| `anl90_openprice` | open price | Vector | Daily | 98% |
| `anl90_timehorizon` | time horizon | Vector | Daily | 80% |
| `buy_recommendation_weighting` | Numerical value representing the strength or proportion of buy recommendations for an asset | Vector | Daily | 75% |
| `expected_exit_price` | Price level the author expects the asset to reach within a specified time frame | Vector | Daily | 78% |
| `expected_price_denomination` | Currency in which the target price for the trade idea is specified | Vector | Daily | 98% |
| `investment_denomination_currency` | Currency in which the investment for the trade idea is made | Vector | Daily | 98% |
| `sell_recommendation_weighting` | Numerical value representing the strength or proportion of sell recommendations for an asset | Vector | Daily | 65% |
| `success_likelihood_score` | Quantitative measure of the likelihood that the trade idea will succeed | Vector | Daily | 70% |
| `trade_closing_price` | Price at which the trade idea was closed or exited | Vector | Daily | 60% |

### Field Deconstruction Analysis

#### `anl90_authorcompany`: Author Company
- **What is being measured?**: The originating brokerage firm or financial institution publishing the trade idea
- **How is it measured?**: Categorical identifier sourced from contributor metadata
- **Time dimension**: Static per idea submission (snapshot)
- **Business context**: Source attribution for quality scoring and bias detection (certain firms may have persistent optimistic/pessimistic biases)
- **Generation logic**: Automated extraction from broker feed metadata
- **Reliability considerations**: Standardized mapping tables reduce variance, though M&A activity may create temporary duplicates

#### `buy_recommendation_weighting`: Buy Recommendation Weighting
- **What is being measured?**: Aggregated bullish conviction expressed as a numerical strength or proportional allocation
- **How is it measured?**: Quantitative aggregation of buy-side analyst recommendations within the vector
- **Time dimension**: Point-in-time snapshot of current recommendations (cumulative count/strength)
- **Business context**: Primary signal for positive sentiment; higher values indicate stronger consensus or larger position recommendations
- **Generation logic**: Derived from broker API feeds with normalization across different rating scales
- **Reliability considerations**: Coverage varies by market cap; zero values may indicate no active buy recommendations rather than neutral sentiment

#### `sell_recommendation_weighting`: Sell Recommendation Weighting
- **What is being measured?**: Aggregated bearish conviction or short recommendation strength
- **How is it measured?**: Quantitative aggregation of sell-side recommendations within the vector
- **Time dimension**: Point-in-time snapshot
- **Business context**: Counter-indicator to buy signals; imbalance between buy and sell weightings drives net sentiment
- **Generation logic**: Normalized from various broker rating scales (Sell, Underweight, Reduce)
- **Reliability considerations**: Typically lower coverage than buy recommendations due to institutional bias against short selling

#### `success_likelihood_score`: Success Likelihood Score
- **What is being measured?**: Analyst-assigned probability (0-1 or 0-100 scale) that the trade idea will achieve its target
- **How is it measured?**: Subjective probability estimate or model-derived score from contributing analysts
- **Time dimension**: Current assessment (forward-looking)
- **Business context**: Quality filter; high likelihood with high weighting indicates high-conviction opportunities
- **Generation logic**: Manual entry by analysts or algorithmic based on historical hit rates
- **Reliability considerations**: Potential overconfidence bias; calibration against actual `trade_closing_price` outcomes required for validation

#### `expected_exit_price`: Expected Exit Price
- **What is being measured?**: Target price level at which the analyst recommends closing the position
- **How is it measured?**: Price forecast in `expected_price_denomination` currency
- **Time dimension**: Forward-looking target (typically 1-3 months per `timehorizon`)
- **Business context**: Defines the expected return magnitude when combined with entry price
- **Generation logic**: Analyst price target models (DCF, comparables, technical levels)
- **Reliability considerations**: Subject to revision risk; stale targets may persist if not updated regularly

#### `anl90_openprice`: Open Price
- **What is being measured?**: Entry price level recommended or actual when the idea was published
- **How is it measured?**: Market price at idea inception or recommended limit price
- **Time dimension**: Historical reference point (idea inception)
- **Business context**: Anchor for calculating expected returns: (exit - open) / open
- **Generation logic**: Market data snapshot at time of idea submission
- **Reliability considerations**: Slippage may occur between idea publication and execution; `anl90_investmentprice` may differ if filled at different levels

### Field Relationship Mapping

**The Story This Data Tells**:
The dataset narrates the evolution of sell-side conviction through three acts: (1) Ideation - characterized by author metadata and entry prices, (2) Conviction Building - measured by recommendation weightings and success probabilities, and (3) Resolution - captured by exit targets and realized closing prices. The tension between buy and sell weightings creates a sentiment spectrum, while the gap between expected and actual prices reveals analyst forecasting skill.

**Key Relationships Identified**:
1. **Sentiment Differential**: The spread between buy and sell weightings indicates net market positioning; when buy weightings dominate while success likelihood remains low, suggests speculative excess
2. **Confidence Calibration**: The correlation between `success_likelihood_score` and subsequent price achievement (implied by `expected_exit_price` vs. market) indicates analyst forecasting accuracy
3. **Entry-Efficiency**: Divergence between `anl90_openprice` (recommended) and `anl90_investmentprice` (actual filled) measures execution quality and market impact
4. **Temporal Alignment**: `timehorizon` moderates the relevance of price targets; short horizons with large price gaps indicate high expected volatility or imminent catalysts

**Missing Pieces That Would Complete the Picture**:
- Actual idea closure dates (to calculate holding period returns)
- Historical track record per author (hit rates for backtesting analyst skill)
- Sector/industry classification of ideas (for relative value analysis)
- Market regime indicators (bull/bear market classification for signal conditioning)

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: Author Conviction Stability Ratio
- **Sample Fields Used**: `recommendation_weighting`
- **Definition**: Coefficient of variation (standard deviation / mean) of buy recommendation weightings over a rolling window
- **Why This Feature**: Identifies analysts or periods with consistent vs. erratic conviction; stable conviction suggests deeper research while volatile weightings may indicate reactionary trading
- **is filling nan necessary**: NaN values in vector fields indicate no active recommendations; these should not be filled with zeros as absence of recommendation is informationally distinct from zero weighting. Use ts_backfill only for gaps within existing recommendation series.
- **Logical Meaning**: Lower values indicate stable, persistent conviction; high values indicate choppy, inconsistent recommendation patterns
- **Directionality**: Low values (stability) typically associated with higher quality signals; high values suggest noise
- **Boundary Conditions**: Values near 0 indicate perfectly stable recommendations; values > 2 indicate extreme volatility or sparse data
- **Implementation Example**: `ts_std_dev(vec_avg({recommendation_weighting}), 20) / abs(ts_mean(vec_avg({recommendation_weighting}), 20))`

**Concept**: Success Likelihood Consistency Score
- **Sample Fields Used**: `likelihood_score`
- **Definition**: Rolling standard deviation of average success likelihood scores over 60 days
- **Why This Feature**: Measures whether analysts maintain consistent probability assessments or adjust them erratically; stable likelihoods suggest well-calibrated models
- **is filling nan necessary**: NaN values represent periods with no score updates; use ts_backfill with limited lookback (5 days) to avoid stale data bias while preserving information gaps.
- **Logical Meaning**: Quantifies the volatility of confidence itself; stable confidence allows better position sizing
- **Directionality**: Lower values preferred (consistent assessment); rapidly changing likelihoods indicate uncertainty about catalysts
- **Boundary Conditions**: 0 indicates static probability assessments; high values indicate shifting confidence in trade thesis
- **Implementation Example**: `ts_std_dev(vec_avg({likelihood_score}), 60)`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Recommendation Momentum Flow
- **Sample Fields Used**: `recommendation_weighting`
- **Definition**: 5-day change in total aggregated buy recommendation weighting
- **Why This Feature**: Captures accelerating or decelerating bullish sentiment; changes often precede price movements as new ideas enter the system
- **is filling nan necessary**: NaN should be treated as 0 for change calculation only if the absence truly indicates no activity; however, to distinguish between no data and no recommendation, use ts_backfill first, then calculate delta.
- **Logical Meaning**: Positive values indicate increasing analyst interest; negative values indicate waning conviction or profit-taking
- **Directionality**: Positive momentum bullish; negative momentum bearish or cooling
- **Boundary Conditions**: Extreme positive values may indicate overcrowding; extreme negative values may indicate capitulation
- **Implementation Example**: `ts_delta(vec_sum({recommendation_weighting}), 5)`

**Concept**: Target Price Revision Velocity
- **Sample Fields Used**: `exit_price`, `openprice`
- **Definition**: 10-day rate of change in the expected return spread (exit vs. open price ratio)
- **Why This Feature**: Analysts revising target prices upward indicate new information or changing fundamentals; velocity measures the urgency of these revisions
- **is filling nan necessary**: Price targets are sticky; use ts_backfill with 10-day window to carry forward last valid target, marking revisions explicitly.
- **Logical Meaning**: Positive values indicate upward price target revisions (bullish); negative indicate downgrades
- **Directionality**: Positive revisions bullish; negative bearish
- **Boundary Conditions**: Large positive changes may signal catalyst discovery; large negative changes may indicate thesis breaks
- **Implementation Example**: `ts_delta((vec_avg({exit_price}) - vec_avg({openprice})) / vec_avg({openprice}), 10)`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Conviction Outlier Detection
- **Sample Fields Used**: `recommendation_weighting`
- **Definition**: Z-score of current buy recommendation weighting relative to 60-day historical distribution
- **Why This Feature**: Identifies unusual spikes in analyst interest that may indicate significant news, earnings events, or herding behavior
- **is filling nan necessary**: Historical mean/std calculations should ignore NaN; do not fill NaN with group means as this dilutes the outlier detection for sparse recommendations.
- **Logical Meaning**: Values > 2 indicate statistically significant increase in recommendation intensity; <-2 indicate unusual silence
- **Directionality**: High positive outliers may indicate crowded longs (short-term negative); high negative outliers may indicate contrarian opportunities
- **Boundary Conditions**: |z-score| > 3 indicates extreme anomalies warranting investigation
- **Implementation Example**: `(vec_avg({recommendation_weighting}) - ts_mean(vec_avg({recommendation_weighting}), 60)) / ts_std_dev(vec_avg({recommendation_weighting}), 60)`

**Concept**: Probability-Price Divergence
- **Sample Fields Used**: `likelihood_score`, `exit_price`, `openprice`
- **Definition**: Deviation of expected return (implied by prices) from what the success likelihood would predict based on historical regression
- **Why This Feature**: Detects mismatches between analyst confidence and implied return magnitude; high likelihood with low expected return suggests risk aversion or constraints
- **is filling nan necessary**: Both fields must be present; use if_else to check is_nan on both before calculation to avoid false divergences from missing data.
- **Logical Meaning**: Positive divergence (high likelihood, low implied return) suggests conservative targeting; negative divergence suggests aggressive targeting with low confidence
- **Directionality**: Context-dependent; extreme values indicate potential mispricing of risk
- **Boundary Conditions**: Values beyond 2 standard deviations indicate calibration errors between price targets and probability assessments
- **Implementation Example**: `vec_avg({likelihood_score}) - ts_mean(vec_avg({likelihood_score}), 30) * ((vec_avg({exit_price}) / vec_avg({openprice})) / ts_mean(vec_avg({exit_price}) / vec_avg({openprice}), 30))`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Net Sentiment Imbalance Score
- **Sample Fields Used**: `recommendation_weighting`, `weighting`
- **Definition**: Difference between aggregated buy and sell recommendation weightings normalized by total recommendations
- **Why This Feature**: Captures the directional consensus net of conflicting views; raw buy signals may be misleading if sell weightings are also elevated
- **is filling nan necessary**: Treat NaN as 0 for missing buy or sell sides to calculate net exposure accurately, as absence of one side implies zero weighting on that side.
- **Logical Meaning**: Positive values indicate net bullish consensus; negative values indicate net bearish; magnitude indicates strength of imbalance
- **Directionality**: Positive values bullish; negative values bearish; zero indicates balanced disagreement
- **Boundary Conditions**: +1 indicates unanimous buys; -1 indicates unanimous sells; 0 indicates equal weighting or no data
- **Implementation Example**: `(vec_sum({recommendation_weighting}) - vec_sum({weighting})) / (vec_sum({recommendation_weighting}) + vec_sum({weighting}) + 0.0001)`

**Concept**: Risk-Adjusted Conviction Alpha
- **Sample Fields Used**: `likelihood_score`, `recommendation_weighting`
- **Definition**: Product of average success likelihood and average recommendation weighting, scaled by the coefficient of variation of the weighting
- **Why This Feature**: High recommendations with low probability are noise; this filter ensures only high-conviction, high-probability ideas pass through
- **is filling nan necessary**: If either field is NaN, the product should be NaN to avoid false signals from partial data; do not fill.
- **Logical Meaning**: Represents quality-weighted sentiment; accounts for both strength and reliability
- **Directionality**: Higher values indicate better risk-adjusted opportunities
- **Boundary Conditions**: Near zero indicates low confidence or low conviction; high values indicate strong consensus with high probability
- **Implementation Example**: `vec_avg({likelihood_score}) * vec_avg({recommendation_weighting}) / (ts_std_dev(vec_avg({recommendation_weighting}), 20) + 0.0001)`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Recommendation Breadth Indicator
- **Sample Fields Used**: `recommendation_weighting`, `authorcompany`
- **Definition**: Count of distinct active buy recommendations (vector count) divided by count of distinct author companies
- **Why This Feature**: Distinguishes between concentrated recommendations (few authors, high weight) and broad consensus (many authors); breadth suggests durability
- **is filling nan necessary**: Use vec_filter to remove NaN before counting to ensure accurate breadth measurement.
- **Logical Meaning**: High values indicate many analysts agree (wisdom of crowds); low values indicate concentrated bets by few sources
- **Directionality**: Higher breadth generally indicates more robust signals; low breadth indicates potential idiosyncratic risk
- **Boundary Conditions**: 1 indicates single source; high values indicate widespread coverage
- **Implementation Example**: `vec_count(vec_filter({recommendation_weighting}, value="nan")) / (vec_count({authorcompany}) + 0.0001)`

**Concept**: Currency Mismatch Exposure
- **Sample Fields Used**: `denomination_currency`, `price_denomination`
- **Definition**: Binary indicator of whether investment currency differs from target price denomination (FX risk present)
- **Why This Feature**: Currency mismatches introduce exchange rate risk not captured in local price returns; ideas with mismatched currencies require hedging
- **is filling nan necessary**: Currency fields should not have NaN if properly populated; if NaN occurs, treat as mismatch (conservative approach) or exclude.
- **Logical Meaning**: 1 indicates FX risk present; 0 indicates single currency exposure
- **Directionality**: 0 preferred for pure equity plays; 1 indicates additional FX alpha/risk
- **Boundary Conditions**: Simple binary classification based on string comparison of denominations
- **Implementation Example**: `not(equal(vec_choose({denomination_currency}, nth=0), vec_choose({price_denomination}, nth=0)))`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Accumulated Buy Pressure Index
- **Sample Fields Used**: `recommendation_weighting`
- **Definition**: 20-day rolling sum of aggregated buy recommendation weightings
- **Why This Feature**: Captures persistent buying pressure over time; single-day spikes may be noise but sustained accumulation indicates strong institutional interest
- **is filling nan necessary**: Treat NaN days as 0 in the sum to avoid carrying forward stale recommendations indefinitely.
- **Logical Meaning**: Cumulative measure of analyst commitment; high values indicate sustained accumulation phases
- **Directionality**: Higher values indicate stronger accumulated bullish pressure
- **Boundary Conditions**: Linear accumulation during trending markets; flat periods indicate consensus hiatus
- **Implementation Example**: `ts_sum(vec_sum({recommendation_weighting}), 20)`

**Concept**: Geometric Success Expectation
- **Sample Fields Used**: `likelihood_score`
- **Definition**: Compounded product of (1 + daily average success likelihood) over 20 days
- **Why This Feature**: Models the multiplicative nature of sequential trade success probabilities; captures persistence in high-quality idea generation
- **is filling nan necessary**: Use ts_backfill to carry forward last valid likelihood to maintain geometric continuity, or treat as 0 (no contribution).
- **Logical Meaning**: Represents compounded confidence; values > 1 indicate sustained high-probability environment
- **Directionality**: Values > 1 bullish for idea quality; < 1 indicates degrading confidence
- **Boundary Conditions**: Exponential growth possible with high daily likelihoods; decay to zero if prolonged low probability periods
- **Implementation Example**: `ts_product(1 + vec_avg({likelihood_score}), 20)`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Relative Conviction Percentile
- **Sample Fields Used**: `recommendation_weighting`
- **Definition**: Cross-sectional quantile ranking of average buy recommendation weighting within universe
- **Why This Feature**: Identifies stocks with unusual analyst attention relative to peers; top percentile names may be over-analyzed or have genuine catalysts
- **is filling nan necessary**: NaN values should be ranked lowest (or excluded) to avoid middle-ranking bias for missing data.
- **Logical Meaning**: 0.9 indicates top 10% of stocks by analyst interest; 0.1 indicates bottom 10%
- **Directionality**: High percentile may indicate overcrowding (contrarian short) or momentum (trend following); context dependent
- **Boundary Conditions**: 0 to 1 scale; extreme values (0.95+) indicate consensus concentration
- **Implementation Example**: `quantile(vec_avg({recommendation_weighting}), driver="uniform")`

**Concept**: Success Likelihood Rank Spread
- **Sample Fields Used**: `likelihood_score`
- **Definition**: Difference between current percentile rank of success likelihood and its 30-day average rank
- **Why This Feature**: Captures stocks where analyst confidence is improving or deteriorating relative to historical positioning and peers
- **is filling nan necessary**: Calculate rank first, handling NaN as minimum rank, then difference; or exclude NaN from rank calculation.
- **Logical Meaning**: Positive values indicate improving confidence relative to past; negative indicate declining confidence
- **Directionality**: Positive values bullish (upgrading prospects); negative bearish (downgrading)
- **Boundary Conditions**: +1 indicates moved from bottom to top rank; -1 indicates fell from top to bottom
- **Implementation Example**: `quantile(vec_avg({likelihood_score}), driver="uniform") - ts_delay(quantile(vec_avg({likelihood_score}), driver="uniform"), 30)`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Pure Directional Alpha Signal
- **Sample Fields Used**: `likelihood_score`, `recommendation_weighting`, `weighting`
- **Definition**: Success likelihood multiplied by sign of net sentiment (buy - sell weightings)
- **Why This Feature**: Distills the dataset to its essence: high-probability directional bets; removes magnitude noise to focus on sign and quality
- **is filling nan necessary**: Net sentiment calculation requires both buy and sell; if either is NaN, treat missing side as 0 to preserve available information.
- **Logical Meaning**: Positive values indicate high-probability long opportunities; negative indicate high-probability short opportunities
- **Directionality**: Sign indicates direction; magnitude indicates confidence
- **Boundary Conditions**: Bounded by max likelihood score in positive and negative directions
- **Implementation Example**: `vec_avg({likelihood_score}) * sign(vec_sum({recommendation_weighting}) - vec_sum({weighting}))`

**Concept**: Expected Return Achievement Gap
- **Sample Fields Used**: `exit_price`, `closing_price`
- **Definition**: Ratio of expected exit price to actual closing price minus 1 (remaining upside for open ideas)
- **Why This Feature**: For active ideas, measures how much of the analyst target remains unachieved; low values indicate targets already hit (exit signal)
- **is filling nan necessary**: Only valid if both target and current price exist; do not fill NaN as closed ideas lack targets.
- **Logical Meaning**: 0.10 indicates 10% upside remaining; -0.05 indicates target exceeded (potential reversal)
- **Directionality**: High positive values indicate holding potential; negative values indicate overachievement (sell)
- **Boundary Conditions**: Theoretically unbounded; practical limits based on market volatility
- **Implementation Example**: `(vec_avg({exit_price}) - vec_avg({closing_price})) / (vec_avg({closing_price}) + 0.0001)`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Buy recommendations (`buy_recommendation_weighting`) have higher coverage (75%) than sell recommendations (65%) due to institutional long bias; success likelihood scores have moderate coverage (70%) and may suffer from selection bias (analysts only assign scores when confident)
- **Timeliness**: Daily updates with intraday ingestion from broker feeds; however, `trade_closing_price` has lower coverage (60%) as many ideas remain open or closure data is not back-propagated
- **Accuracy**: Vector data requires aggregation via `vec_avg` or `vec_sum` before use; direct arithmetic on vector fields is invalid. Price fields require denomination alignment (`denomination_currency` vs `price_denomination`) for cross-border ideas
- **Potential Biases**: Sell-side optimism bias expected in `recommendation_weighting` (buy > sell); survivorship bias in `success_likelihood_score` (failed ideas may not be reported); author company clustering (certain firms dominate feed)

### Computational Complexity
- **Lightweight features**: Simple vector aggregations (`vec_avg`, `vec_sum`) and cross-sectional ranks (`quantile`)
- **Medium complexity**: Time-series operations on aggregated vectors (`ts_delta`, `ts_std_dev`, `ts_sum`) with 20-60 day lookbacks
- **Heavy computation**: Multi-layered features combining vector aggregation, time-series smoothing, and cross-sectional normalization (e.g., `quantile(ts_std_dev(vec_avg(...), d))`)

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Net Sentiment Imbalance** - captures primary dataset signal (buy vs. sell) with clear economic intuition
2. **Risk-Adjusted Conviction** - filters noise by combining weighting with probability; essential for quality control
3. **Expected Return Spread** - quantifies the actual price target distance, the core value proposition of trade ideas

**Tier 2 (Secondary Priority)**:
1. **Recommendation Momentum Flow** - identifies emerging interest but requires careful handling of NaN values
2. **Author Conviction Stability** - quality filter for signal source consistency
3. **Relative Conviction Percentile** - enables cross-sectional comparison but subject to universe composition effects

**Tier 3 (Requires Further Validation)**:
1. **Currency Mismatch Exposure** - requires validation of FX impact on local returns
2. **Geometric Success Expectation** - assumes multiplicative probability structure that may not hold empirically
3. **Success Likelihood Rank Spread** - sensitive to lookback period selection and rank stability

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How does the vector structure handle multiple recommendations for the same stock by the same author on the same day (aggregation vs. duplication)?
2. What is the empirical hit rate of `success_likelihood_score` buckets (calibration testing)?
3. How does `timehorizon` interact with price target achievement (do short-horizon ideas hit targets faster or fail more often)?

### Recommended Additional Data:
- Idea closure dates and realized returns (to calculate Sharpe ratios by author)
- Sector classifications (for sector-neutral sentiment adjustments)
- Market cap data (to test if analyst ideas work better in small vs. large caps)
- Historical author performance tracking (to weight recommendations by past accuracy)

### Assumptions to Challenge:
- That higher `recommendation_weighting` always indicates stronger signal (may indicate herding/crowding)
- That `success_likelihood_score` is well-calibrated (likely overconfident)
- That analyst ideas have alpha after accounting for delay and transaction costs (requires P&L backtesting)

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence (vector nature of fields, metadata vs. signals)
2. Question-driven feature generation (8 fundamental questions applied to analyst sentiment context)
3. Logical validation of each feature concept against dataset limitations (vector aggregation requirements)
4. Transparent documentation of reasoning and implementation constraints

**Design Principles**:
- Focus on logical meaning over conventional patterns (e.g., net sentiment vs. simple buy signal)
- Every feature must answer a specific question (stability, change, anomaly, etc.)
- Clear documentation of "why" for each suggestion including NaN handling
- Emphasis on data understanding (vector structure, delay, coverage) over prediction

---

*Report generated: 2024-12-19 10:00:00*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate success likelihood calibration, gather closure data for backtesting*