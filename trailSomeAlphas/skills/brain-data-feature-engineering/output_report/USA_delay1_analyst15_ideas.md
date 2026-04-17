# analyst15 Earnings Forecasts Feature Engineering Analysis Report

**Dataset**: analyst15
**Category**: Analyst
**Region**: USA
**Delay**: 1
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 2538

---

## Executive Summary

**Primary Question Answered by Dataset**: This dataset aggregates bottom-up analyst earnings forecasts (EPS, BPS, CPS, DPS, EBT, Revenue) across GICS groupings (sector/industry/group), providing a lens into collective analyst sentiment, consensus dispersion, and revision momentum across multiple time horizons (12M, 18M, FY0-FY3 forward).

**Key Insights from Analysis**:
- The dataset captures multi-dimensional analyst sentiment through estimate counts, directional revisions (up/down), dispersion (std dev), and growth trajectories across hierarchical GICS levels
- Rich temporal structure exists with 1M/3M/6M change metrics enabling momentum and acceleration analysis
- Cross-metric relationships (EPS vs Revenue vs BPS) allow for fundamental quality assessment of earnings revisions
- The aggregation at GICS levels enables both top-down sector allocation and bottom-up stock selection signals

**Critical Field Relationships Identified**:
- `mean` (consensus estimate) and `st_dev` (dispersion) form a risk-reward spectrum where high dispersion with strong revisions indicates controversy
- `cos_up` and `cos_dn` (count of companies with estimate changes) reveal breadth of sentiment shifts vs magnitude changes
- `1m_chg`, `3m_chg`, `6m_chg` provide revision velocity and acceleration profiles
- `gro` (growth rate) and `pe` (valuation) enable growth-adjusted valuation signals at aggregate levels

**Most Promising Feature Concepts**:
1. **Revision Consensus Intensity** - combining magnitude changes with breadth of coverage because analyst agreement on direction amplifies signal strength
2. **Estimate Dispersion Trend** - tracking st_dev changes over time because narrowing dispersion often precedes price momentum
3. **Multi-Horizon Growth Consistency** - comparing FY1 vs FY2 vs FY3 growth trajectories because sustainable growth paths outperform volatile ones

---

## Dataset Deep Understanding

### Dataset Description
analyst15 provides bottom-up forecast data for earnings and other fundamental factors aggregated within GICS (Global Industry Classification Standard) hierarchies. It captures analyst estimates for EPS, Book Value Per Share (BPS), Cash Flow Per Share (CPS), Dividend Per Share (DPS), Earnings Before Tax (EBT), and Revenue (SAL) across multiple forward-looking horizons (12-month, 18-month, and fiscal years 0-3). Each metric includes weighted averages, standard deviations, counts of contributing companies, directional revision metrics, and momentum indicators (1M/3M/6M changes).

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `anl15_*_mean` | Weighted average consensus estimate | Float | Daily | 95% |
| `anl15_*_st_dev` | Weighted average standard deviation | Float | Daily | 92% |
| `anl15_*_1m_chg` | 1-month percent change in estimates | Float | Daily | 88% |
| `anl15_*_3m_chg` | 3-month percent change in estimates | Float | Daily | 88% |
| `anl15_*_6m_chg` | 6-month percent change in estimates | Float | Daily | 85% |
| `anl15_*_cos_up` | Count of companies with raised estimates | Integer | Daily | 90% |
| `anl15_*_cos_dn` | Count of companies with lowered estimates | Integer | Daily | 90% |
| `anl15_*_gro` | Year-over-year growth estimate | Float | Daily | 87% |
| `anl15_*_pe` | Price/Earnings ratio based on estimates | Float | Daily | 93% |
| `anl15_*_ests` | Total number of estimates | Integer | Daily | 96% |

*(Additional fields for trailing means, totals, and metric-specific values follow similar patterns)*

### Field Deconstruction Analysis

#### `anl15_*_mean`: Consensus Estimate
- **What is being measured?**: The weighted average of analyst estimates for a specific metric (EPS, BPS, etc.) within a GICS grouping
- **How is it measured?**: Bottom-up aggregation of individual analyst estimates weighted by company market cap or equal weight depending on sub-field
- **Time dimension**: Point-in-time snapshot of forward-looking expectations (12M, 18M, FY1-FY3 horizons)
- **Business context**: Represents the collective wisdom of analysts regarding future company performance within a sector/industry
- **Generation logic**: Calculated daily from active analyst estimates, with stale estimates excluded after a threshold period
- **Reliability considerations**: Higher reliability when `ests` is large; may lag during earnings seasons due to update delays

#### `anl15_*_st_dev`: Estimate Dispersion
- **What is being measured?**: Cross-sectional standard deviation of analyst estimates within the aggregation group
- **How is it measured?**: Statistical dispersion around the `mean` estimate, weighted by company importance
- **Time dimension**: Point-in-time measure of analyst disagreement
- **Business context**: Proxy for uncertainty or controversy surrounding earnings expectations; low dispersion suggests consensus, high dispersion suggests debate
- **Generation logic**: Calculated simultaneously with mean; sensitive to outlier estimates
- **Reliability considerations**: May spike during earnings surprises or guidance changes; useful as a normalization factor

#### `anl15_*_cos_up` / `cos_dn`: Revision Breadth
- **What is being measured?**: Count of companies within the grouping experiencing upward or downward estimate revisions from the prior month
- **How is it measured?**: Binary flag at company level aggregated to count within GICS group
- **Time dimension**: Monthly change metric capturing directional breadth
- **Business context**: Measures the breadth of sentiment shifts; more reliable than magnitude changes for detecting inflection points
- **Generation logic**: Compared against prior month's estimates; requires active coverage to be included
- **Reliability considerations**: Less noisy than percentage changes; good for identifying sector rotations

#### `anl15_*_1m_chg` / `3m_chg` / `6m_chg`: Revision Momentum
- **What is being measured?**: Percentage change in the weighted mean estimate over 1, 3, and 6 month horizons
- **How is it measured?**: Time-series percentage change of `mean` field
- **Time dimension**: Rolling window momentum indicators
- **Business context**: Captures analyst revision velocity and acceleration; 1M for immediate momentum, 3M/6M for sustained trends
- **Generation logic**: Compared against lagged values of the same series
- **Reliability considerations**: 1M can be noisy; 6M may miss recent inflections; best used in combination

### Field Relationship Mapping

**The Story This Data Tells**:
This dataset narrates the evolution of analyst sentiment across the equity universe. It begins with broad expectations (`mean`), quantifies the uncertainty around those expectations (`st_dev`), tracks how expectations are shifting (`1m_chg`, `3m_chg`), measures whether those shifts are widespread or isolated (`cos_up`, `cos_dn`), and contextualizes growth expectations relative to valuation (`pe`, `gro`). The multi-horizon structure (FY1-FY3) adds a temporal dimension, revealing whether analysts expect growth acceleration or deceleration.

**Key Relationships Identified**:
1. **Dispersion-Revision Interaction**: High `st_dev` combined with strong directional `1m_chg` indicates controversial momentum (high risk/reward), while low `st_dev` with strong `1m_chg` indicates consensus momentum (lower risk)
2. **Breadth-Magnitude Dynamics**: When `cos_up` increases but `mean` doesn't change much, analysts are upgrading smaller companies within the group; when `mean` moves significantly with stable `cos_up`, mega-caps are driving revisions
3. **Horizon Consistency**: Alignment between `12_m_gro`, `fy1_gro`, and `fy2_gro` indicates sustainable growth visibility; divergence suggests inflection points or cyclical turning points
4. **Cross-Metric Validation**: EPS revisions (`mean`) accompanied by Revenue (`sal_mean`) and Cash Flow (`cps_mean`) revisions in the same direction indicate fundamental business momentum; divergence suggests margin-driven or accounting-driven changes

**Missing Pieces That Would Complete the Picture**:
- Actual reported earnings to compare against estimates (surprise analysis)
- Price momentum data to compare against estimate revisions (expectations vs reality)
- Short interest data to understand if estimate dispersion correlates with short-selling activity
- Guidance data from companies to distinguish analyst-driven vs company-driven revisions

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: Estimate Dispersion Stability Ratio
- **Sample Fields Used**: 12_m_st_dev, 12_m_mean
- **Definition**: Coefficient of variation of analyst estimates measuring consensus stability within a sector
- **Why This Feature**: Low dispersion relative to mean indicates strong analyst consensus, which typically precedes lower volatility and more predictable returns
- **Logical Meaning**: Normalized measure of analyst disagreement; stable values suggest established business models, while increasing values suggest emerging uncertainty
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. In this case, NaN in st_dev typically means insufficient data points, so backfilling may be appropriate to maintain continuity.
- **Directionality**: Lower values indicate higher consensus (potentially positive for low-volatility strategies); extreme lows may indicate complacency
- **Boundary Conditions**: Approaches zero as consensus becomes perfect; undefined when mean is zero (earnings transition periods)
- **Implementation Example**: `divide({12_m_st_dev}, abs({12_m_mean}))`

**Concept**: Revision Volatility Stability
- **Sample Fields Used**: cal_fy1_1m_chg
- **Definition**: Rolling standard deviation of estimate changes measuring the stability of analyst sentiment shifts
- **Why This Feature**: Measures whether analysts are consistently updating estimates or making erratic changes; stable revision patterns suggest predictable business environments
- **Logical Meaning**: Second-order measure of estimate dynamics; low volatility of changes indicates steady-state business conditions
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Lower values indicate stable revision environments; very high values suggest earnings uncertainty or inflection points
- **Boundary Conditions**: Minimum bound at zero (no changes); increases during earnings seasons or guidance updates
- **Implementation Example**: `ts_std_dev({cal_fy1_1m_chg}, 20)`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Estimate Acceleration Profile
- **Sample Fields Used**: 1m_chg, 3m_chg, 6m_chg
- **Definition**: Difference between short-term and long-term revision momentum indicating acceleration or deceleration in sentiment
- **Why This Feature**: Captures inflection points where analyst sentiment is shifting direction; acceleration often precedes price momentum
- **Logical Meaning**: Second derivative of analyst sentiment; positive values indicate improving momentum, negative values indicate deteriorating momentum
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Positive values indicate accelerating upward revisions (bullish); negative values indicate accelerating downward revisions (bearish)
- **Boundary Conditions**: Unbounded; extreme values suggest significant inflection points
- **Implementation Example**: `subtract({1m_chg}, divide({6m_chg}, 6))`

**Concept**: Long-term Growth Trajectory Shift
- **Sample Fields Used**: cal_fy1_gro, cal_fy2_gro, cal_fy3_gro
- **Definition**: Comparison of growth expectations across forward years to identify slowing or accelerating growth profiles
- **Why This Feature**: Reveals whether analysts expect sustainable growth or cyclical peaks/troughs; steep deceleration often signals overvaluation
- **Logical Meaning**: Measures the curvature of the growth curve; flattening indicates maturation or cyclical downturns
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Positive values indicate improving long-term prospects; negative values indicate growth deceleration concerns
- **Boundary Conditions**: Extreme positive values may indicate unrealistic expectations; extreme negative values may indicate distress
- **Implementation Example**: `subtract({cal_fy2_gro}, {cal_fy1_gro})`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Revision Surprise Magnitude
- **Sample Fields Used**: 1m_chg
- **Definition**: Current estimate change deviation from its historical average, identifying unusual analyst activity
- **Why This Feature**: Unusually large revisions often follow significant corporate events or earnings surprises; detects information asymmetry moments
- **Logical Meaning**: Z-score style deviation from normal revision patterns; identifies outliers in analyst behavior
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: High positive values indicate significant positive surprises; high negative values indicate significant negative shocks
- **Boundary Conditions**: Theoretically unbounded; values beyond 2-3 standard deviations are significant anomalies
- **Implementation Example**: `subtract({1m_chg}, ts_mean({1m_chg}, 60))`

**Concept**: Dispersion Anomaly Detection
- **Sample Fields Used**: st_dev
- **Definition**: Unusual expansion or contraction in estimate dispersion relative to historical norms
- **Why This Feature**: Sudden spikes in dispersion often precede significant price volatility or earnings events; contractions may indicate information convergence
- **Logical Meaning**: Measures uncertainty shocks in analyst community; deviations from trend indicate changing information environments
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: High values indicate increasing uncertainty (potentially negative); rapid contractions may indicate resolution of uncertainty (positive)
- **Boundary Conditions**: Minimum at zero; spikes often occur around earnings seasons
- **Implementation Example**: `subtract({st_dev}, ts_median({st_dev}, 20))`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Sentiment-Valuation Interaction
- **Sample Fields Used**: cos_up, cos_dn, pe
- **Definition**: Combining revision breadth (sentiment) with valuation levels to identify expensive optimism or cheap pessimism
- **Why This Feature**: High sentiment on high valuation is risky (priced in); high sentiment on low valuation is opportunity; pure sentiment or pure valuation miss this interaction
- **Logical Meaning**: Risk-adjusted sentiment measure; accounts for the price paid for the sentiment trend
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: High values (up revisions + low PE) indicate value-sentiment alignment; low values (down revisions + high PE) indicate danger
- **Boundary Conditions**: PE near zero creates extreme values; requires winsorization
- **Implementation Example**: `multiply(divide(subtract({cos_up}, {cos_dn}), add({cos_up}, {cos_dn})), inverse({pe}))`

**Concept**: Multi-Horizon Revision Correlation
- **Sample Fields Used**: 12_m_1m_chg, cal_fy1_1m_chg
- **Definition**: Correlation between short-term (12M) and longer-term (FY1) estimate revision trends
- **Why This Feature**: High correlation indicates sustained fundamental shifts affecting all horizons; low correlation suggests near-term noise vs structural changes
- **Logical Meaning**: Measures the persistence of information across time horizons; distinguishes temporary from permanent changes
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: High positive correlation indicates sustainable trends; negative correlation suggests near-term cyclicality masking long-term concerns
- **Boundary Conditions**: Bounded between -1 and 1; requires sufficient non-NaN observations
- **Implementation Example**: `ts_corr({12_m_1m_chg}, {cal_fy1_1m_chg}, 20)`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Bullish Consensus Ratio
- **Sample Fields Used**: cos_up, cos_dn
- **Definition**: Proportion of companies experiencing estimate upgrades within the grouping
- **Why This Feature**: Breadth of upgrades often leads price moves; narrow leadership (few cos_up, large mean change) is less sustainable than broad upgrades
- **Logical Meaning**: Measures the distribution of sentiment shifts across the group; structural shifts involve broad participation
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Values > 0.5 indicate majority upgrades (bullish); < 0.5 indicate majority downgrades (bearish); extremes (>0.7 or <0.3) indicate crowded positioning
- **Boundary Conditions**: Bounded [0, 1]; undefined when both counts are zero
- **Implementation Example**: `divide({cos_up}, add({cos_up}, {cos_dn}))`

**Concept**: Estimate Coverage Concentration
- **Sample Fields Used**: cos, ests
- **Definition**: Ratio of actively covered companies to total estimated companies, measuring analyst attention concentration
- **Why This Feature**: High coverage indicates institutional interest and information efficiency; low coverage may indicate neglected opportunities or structural decline
- **Logical Meaning**: Proxy for market attention and information diffusion; structural changes often begin with coverage changes
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: High values indicate broad coverage (efficiency); very low values indicate neglect (potential alpha or value trap)
- **Boundary Conditions**: Bounded [0, 1]; sudden drops indicate delistings or coverage withdrawals
- **Implementation Example**: `divide({cos}, {ests})`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Accumulated Revision Momentum
- **Sample Fields Used**: 1m_chg
- **Definition**: Summation of estimate changes over a quarter (63 trading days) capturing persistent analyst sentiment building
- **Why This Feature**: Single-month changes can be noisy; accumulation reveals sustained institutional conviction building over time
- **Logical Meaning**: Integral of revision velocity; represents total information adjustment over the period
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Large positive values indicate sustained accumulation of positive sentiment; negative values indicate deteriorating outlook
- **Boundary Conditions**: Unbounded; scales with number of periods
- **Implementation Example**: `ts_sum({1m_chg}, 63)`

**Concept**: Persistent Growth Expectations
- **Sample Fields Used**: gro
- **Definition**: Rolling average of growth estimates over 20 days to smooth temporary fluctuations and identify stable growth trends
- **Why This Feature**: Raw growth figures can be volatile; persistence indicates sustainable business momentum vs one-time adjustments
- **Logical Meaning**: Smoothed trajectory of growth expectations; filters out earnings season noise
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: High values indicate strong sustained growth expectations; declining values indicate deteriorating prospects
- **Boundary Conditions**: Can be negative for declining earnings; extreme positive values may indicate unsustainable expectations
- **Implementation Example**: `ts_mean({gro}, 20)`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Sector Relative Revision Strength
- **Sample Fields Used**: 1m_chg
- **Definition**: Estimate changes relative to the cross-sectional mean of all groups, identifying outperforming/underperforming sectors
- **Why This Feature**: Absolute revisions matter less than relative performance; top-quintile revision sectors outperform regardless of absolute direction
- **Logical Meaning**: Ranked sentiment intensity; captures sector rotation dynamics and relative information advantage
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Positive values indicate above-average revision momentum (outperform); negative values indicate relative deterioration
- **Boundary Conditions**: Mean-reverting around zero; extreme values indicate potential mean-reversion candidates
- **Implementation Example**: `subtract({1m_chg}, group_mean({1m_chg}))`

**Concept**: Growth-Adjusted Valuation Spread
- **Sample Fields Used**: pe, gro
- **Definition**: PEG-like ratio comparing valuation to growth at the aggregate sector level
- **Why This Feature**: Identifies sectors where growth expectations are not fully reflected in valuations; classic value-growth arbitrage
- **Logical Meaning**: Efficiency metric; low values suggest growth is cheap, high values suggest paying too much for growth
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Low values indicate cheap growth (positive); high values indicate expensive growth (negative); negative growth creates extreme values
- **Boundary Conditions**: Undefined when growth is zero; requires handling of negative growth scenarios
- **Implementation Example**: `divide({pe}, {gro})`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Core Consensus Signal
- **Sample Fields Used**: mean, st_dev
- **Definition**: Consensus estimate adjusted for uncertainty, essentially filtering out noise from extreme analyst disagreements
- **Why This Feature**: Raw means can be skewed by outliers; this extracts the signal by considering only high-confidence estimates (low dispersion)
- **Logical Meaning**: Information-weighted consensus; high values with low dispersion carry more weight than high values with high dispersion
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Higher values indicate stronger consensus; sign depends on metric (EPS vs PE)
- **Boundary Conditions**: Approaches zero as dispersion increases; undefined when st_dev is zero
- **Implementation Example**: `divide({mean}, add(1, {st_dev}))`

**Concept**: Quality-Weighted Revision
- **Sample Fields Used**: 1m_chg, ests, total
- **Definition**: Estimate changes weighted by the depth of analyst coverage, prioritizing changes with more estimate backing
- **Why This Feature**: Single-analyst revisions are noise; broad-based revisions with many `ests` backing them carry more signal
- **Logical Meaning**: Information-theoretic weighting; consensus breadth validates the magnitude of change
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Positive values indicate high-quality upgrades; negative values indicate high-quality downgrades; magnitude indicates conviction
- **Boundary Conditions**: Zero when no estimates exist; scales with coverage depth
- **Implementation Example**: `multiply({1m_chg}, divide({ests}, {total}))`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Varies by metric (EPS highest at ~96%, specialized metrics like BPS/CPS lower at ~85%); cross-metric features should handle missing data gracefully
- **Timeliness**: Daily updates with monthly revision frequencies (`cos_up/dn`); `1m_chg` fields effectively lagged by the lookback period
- **Accuracy**: Aggregated data reduces individual analyst bias but inherits weighting methodology biases (market-cap weighting favors large caps)
- **Potential Biases**: Survivorship bias in `cos` counts (delisted companies disappear); lookahead bias in `cal_fy` fields during fiscal year transitions; GICS reclassification creates structural breaks

### Computational Complexity
- **Lightweight features**: `{st_dev} / {mean}`, `{cos_up} / {cos_dn}`, basic arithmetic combinations (single operations)
- **Medium complexity**: `ts_corr()`, `ts_mean()`, `ts_std_dev()` with 20-60 day windows (rolling window calculations)
- **Heavy computation**: `ts_sum()` over 63 days, cross-sectional `group_mean()` operations across 2538 fields, multi-step nested operations requiring intermediate calculations

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Accumulated Revision Momentum** (`ts_sum({1m_chg}, 63)`) - robust, well-documented alpha source with clear economic logic
2. **Bullish Consensus Ratio** (`{cos_up} / ({cos_up} + {cos_dn})`) - simple breadth measure with strong sector rotation signals
3. **Sector Relative Revision Strength** (`{1m_chg} - group_mean({1m_chg})`) - captures relative value in analyst sentiment

**Tier 2 (Secondary Priority)**:
1. **Estimate Dispersion Stability Ratio** - risk-adjusted signal for quality factors
2. **Sentiment-Valuation Interaction** - captures regime-dependent value/sentiment effects
3. **Multi-Horizon Revision Correlation** - distinguishes sustainable from temporary trends

**Tier 3 (Requires Further Validation)**:
1. **Growth-Adjusted Valuation Spread** - sensitive to negative growth outliers requiring careful handling
2. **Core Consensus Signal** - complex interpretation requiring dispersion thresholds

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How do GICS reclassifications (e.g., Tech to Communication Services) affect the continuity of aggregated estimate histories?
2. Does the relationship between estimate dispersion (`st_dev`) and subsequent volatility vary by sector (e.g., cyclicals vs defensives)?
3. How do the aggregation weights (implied by `mktcap` fields) affect the responsiveness of `mean` to small-cap estimate changes?

### Recommended Additional Data:
- **Actual realized earnings**: To calculate surprise metrics (`actual` vs `mean`) and validate forecast accuracy
- **Analyst identity data**: To distinguish between senior and junior analyst estimates (quality weighting)
- **Guidance flags**: To separate company-guided vs analyst-initiated revisions
- **Price momentum data**: To compare estimate revision timing vs price discovery timing

### Assumptions to Challenge:
- **Equal importance across horizons**: Assumes FY1 and FY2 estimates are equally reliable; in reality, FY2 may be noisier
- **GICS homogeneity**: Assumes companies within a GICS group are comparable; increasingly challenged by diversified conglomerates
- **Linear relationships**: Assumes linear relationships between metrics; may miss threshold effects (e.g., dispersion only matters above certain levels)

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence - analyzing 2538 fields across multiple metrics (EPS, BPS, CPS, DPS, EBT, Revenue) and aggregation levels (Group, Industry, Sector)
2. Question-driven feature generation (8 fundamental questions) - systematically exploring stability, change, anomalies, interactions, structure, accumulation, relativity, and essence
3. Logical validation of each feature concept against financial theory and analyst behavior
4. Transparent documentation of reasoning including directionality, boundary conditions, and data quality concerns

**Design Principles**:
- Focus on logical meaning over conventional patterns - features answer specific economic questions about analyst behavior
- Every feature must answer a specific question from the 8-question framework
- Clear documentation of "why" for each suggestion including behavioral finance rationale
- Emphasis on data understanding over prediction - features designed to capture information asymmetry and sentiment dynamics

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate assumptions, gather additional data as needed*