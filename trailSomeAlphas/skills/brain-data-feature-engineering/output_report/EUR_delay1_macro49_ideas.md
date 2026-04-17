# macro49 (Index Rebalance Dataset) Feature Engineering Analysis Report

**Dataset**: macro49
**Category**: Macro
**Region**: EUR
**Delay**: 1
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 3

---

## Executive Summary

**Primary Question Answered by Dataset**: What is the expected magnitude and liquidity impact of upcoming index rebalancing events on constituent securities?

**Key Insights from Analysis**:
- Dataset provides rare forward-looking liquidity event data, capturing expected trading flows before they occur (post-announcement, pre-effective date)
- VDA (Volume Days Ahead) serves as a normalized liquidity shock indicator, measuring rebalance volume in units of average daily trading capacity
- Notional and Shares capture absolute scale, while their ratio implicitly contains price information and structural relationships
- The dataset essentially quantifies "forced trading" pressure that passive funds must execute regardless of market conditions

**Critical Field Relationships Identified**:
- **Scale-Intensity Bridge**: Shares links absolute volume to VDA (Shares = VDA × ADV20), connecting raw flow to relative market impact
- **Value-Volume Translation**: Notional ≈ Shares × Price, allowing derivation of implied price levels and detection of anomalies between dollar and share-based signals

**Most Promising Feature Concepts**:
1. **Liquidity Pressure Z-Score** - because it identifies statistically extreme rebalancing events relative to historical norms
2. **Accumulated Forced Flow** - because cumulative VDA captures persistent liquidity drainage over multiple overlapping rebalances
3. **Liquidity-Adjusted Trade Size** - because the interaction of large notional with high VDA identifies severe capacity constraints

---

## Dataset Deep Understanding

### Dataset Description
This dataset provides post-announcement estimates for index rebalances, detailing expected changes in index constituents, share volumes, and notional values across major global indices such as Russell and MSCI. It captures the critical window between announcement date and effective date when market participants know rebalancing flows are coming but have not yet occurred. The data enables prediction of price movements and liquidity impacts from passive fund rebalancing, which represents non-discretionary, price-insensitive trading flow.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| mcr49_notional | Expected notional value to be traded as a result of index changes | Vector | Event-driven (announcement dates) | Index constituents only |
| mcr49_shares | Expected share volume to be traded as a result of changes | Vector | Event-driven (announcement dates) | Index constituents only |
| mcr49_vda | Shares to trade / 20-day average volume (days of normal volume equivalent) | Vector | Event-driven (announcement dates) | Index constituents only |

### Field Deconstruction Analysis

#### mcr49_notional: Expected Notional Trade Value
- **What is being measured?**: The total dollar value of securities that must change hands due to index additions, deletions, or weight changes
- **How is it measured?**: Calculated by index providers using constituent weights, shares outstanding, and reference prices post-announcement
- **Time dimension**: Forward-looking from announcement date through effective date; represents committed future flow
- **Business context**: Captures the absolute market value at risk from passive tracking error correction; larger notional = larger potential price impact
- **Generation logic**: Derived from index methodology calculations based on pro-forma weights vs. current weights, multiplied by assets under management tracking the index
- **Reliability considerations**: Subject to revision until effective date; assumes full index replication; actual flows may differ due to sampling strategies or anticipatory trading

#### mcr49_shares: Expected Share Volume
- **What is being measured?**: Raw share count expected to trade due to rebalancing activities
- **How is it measured?**: Derived from notional values divided by reference prices, or directly from share weight calculations
- **Time dimension**: Forward-looking volume expectation spanning announcement to effective date window
- **Business context**: Represents the actual supply/demand imbalance in share units; critical for understanding depth utilization and bid-ask pressure
- **Generation logic**: Function of weight changes, shares outstanding, and total AUM tracking the index; mechanically determined by index rules
- **Reliability considerations**: Less sensitive to intraday price fluctuations than notional; may not account for strategic trading by index funds around the effective date

#### mcr49_vda: Volume Days Ahead (Liquidity Ratio)
- **What is being measured?**: The ratio of expected rebalance volume to the stock's 20-day average daily volume (ADV)
- **How is it measured?**: Calculated as Expected Shares / ADV20, where ADV20 is trailing 20-day volume at announcement
- **Time dimension**: Relative measure comparing forward-looking event size to backward-looking liquidity capacity
- **Business context**: Normalizes absolute volume by trading capacity; 1.0 VDA implies one full day of additional volume; values >2-3 indicate severe liquidity stress and potential price dislocation
- **Generation logic**: Combines forward-looking rebalance estimate with historical liquidity profile; captures the "crowdedness" of the exit/entry
- **Reliability considerations**: ADV is historical while rebalance is forward; assumes volume stability; market-making capacity may differ from historical ADV; most critical field for impact prediction

### Field Relationship Mapping

**The Story This Data Tells**:
This dataset narrates the impending mechanical pressure on securities from passive fund rebalancing. Unlike discretionary trading, these flows are mandated by index rules and must occur regardless of price. The story progresses from absolute scale (notional) to raw share flow (shares) to relative market impact (vda). A high notional with low VDA suggests liquid large-cap rebalancing (absorbable), while low notional with high VDA signals small-cap liquidity crunches (disruptive). The dataset captures the "forced nature" of modern equity flows.

**Key Relationships Identified**:
1. **The Liquidity Transformation Chain**: Notional → Shares → VDA represents the transformation of dollar risk into share flow into liquidity stress. VDA effectively normalizes Notional by both Price and Liquidity.
2. **Implicit Price Discovery**: The ratio Notional/Shares provides an implied reference price; deviations between this and market price may indicate stale data or special situations (e.g., dual-class shares).
3. **Capacity Saturation**: The interaction between Notional and VDA (multiplicative) identifies situations where large dollar amounts must trade in illiquid names—the most dangerous combination for market impact.

**Missing Pieces That Would Complete the Picture**:
- Directional sign of flow (addition = buy pressure vs. deletion = sell pressure)
- Days until effective date (urgency/decay factor)
- Historical realized impact vs. predicted (validation data)
- Index fund AUM tracking specific indices (flow magnitude calibration)

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: Baseline Liquidity Pressure Level
- **Sample Fields Used**: vda
- **Definition**: Rolling average of VDA to establish the typical liquidity impact baseline for a security across multiple rebalance events
- **Why This Feature**: Identifies securities that consistently experience high rebalancing pressure vs. those with sporadic events; stable high VDA indicates permanently impaired liquidity during index events
- **is filling nan necessary**: Yes, rebalance data is sparse and event-driven. Use ts_backfill(vec_avg({vda}), lookback=5) to maintain the signal between announcement and effective date, filling gaps with the most recent announcement value.
- **Directionality**: High values indicate persistent liquidity stress during rebalances; low values indicate easy absorption of index flows
- **Boundary Conditions**: Near-zero values suggest either liquid large-caps or minimal index weight changes; extremely stable high values (>2.0) suggest structural liquidity mismatches in small-cap index constituents
- **Implementation Example**: `ts_mean(ts_backfill(vec_avg({vda}), lookback=5, k=1), 60)`

**Concept**: Rebalance Size Consistency Ratio
- **Sample Fields Used**: notional, shares
- **Definition**: Coefficient of variation (std/mean) of notional values over rolling window to measure stability of rebalance magnitude
- **Why This Feature**: Stable notional implies predictable index weight maintenance; high variation suggests volatile index membership or weight changes, indicating higher uncertainty and potential information asymmetry
- **is filling nan necessary**: Yes, ts_backfill required for notional field to ensure continuity between sparse rebalance events before calculating time-series statistics.
- **Directionality**: Low values (stable) suggest predictable passive flows; high values (volatile) suggest erratic index inclusion/exclusion or weight volatility
- **Boundary Conditions**: Near-zero CV indicates mechanical, stable index weight adjustments; CV >1.0 indicates sporadic, event-driven inclusion (e.g., IPO additions) with unpredictable size
- **Implementation Example**: `divide(ts_std_dev(ts_backfill(vec_avg({notional}), lookback=5, k=1), 60), abs(ts_mean(ts_backfill(vec_avg({notional}), lookback=5, k=1), 60)))`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Liquidity Pressure Acceleration
- **Sample Fields Used**: vda
- **Definition**: Rate of change in VDA between consecutive rebalance announcements to detect intensifying liquidity constraints
- **Why This Feature**: Accelerating VDA suggests deteriorating market structure or increasing index concentration; deceleration suggests improving liquidity or reduced index weight
- **is filling nan necessary**: Yes, use ts_backfill to ensure delta captures true sequential rebalance events rather than calendar time gaps.
- **Directionality**: Positive values indicate worsening liquidity impact (increasing days of volume); negative values indicate improving capacity to absorb rebalances
- **Boundary Conditions**: Large positive jumps (>1.0 day increase) signal potential liquidity crises; consistent negative trends suggest declining index relevance or improving market depth
- **Implementation Example**: `ts_delta(ts_backfill(vec_avg({vda}), lookback=5, k=1), 20)`

**Concept**: Rebalance Flow Momentum
- **Sample Fields Used**: notional
- **Definition**: Log returns of expected notional over rebalance event windows to capture trend in dollar flow magnitude
- **Why This Feature**: Trending notional indicates sustained accumulation or distribution by passive funds; momentum in flows may predict continuation of pressure through effective date
- **is filling nan necessary**: Yes, ts_backfill essential to bridge announcement gaps before calculating returns.
- **Directionality**: Positive momentum indicates growing dollar flows and potential price pressure; negative momentum indicates declining index weight or outflows
- **Boundary Conditions**: Extreme positive values suggest entry into major indices or massive AUM growth in tracking funds; extreme negative suggests deletion or severe weight reduction
- **Implementation Example**: `ts_returns(ts_backfill(vec_avg({notional}), lookback=5, k=1), 60, mode=1)`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Liquidity Event Z-Score
- **Sample Fields Used**: vda
- **Definition**: Standardized deviation of current VDA from its historical mean to identify statistically extreme liquidity events
- **Why This Feature**: Identifies rebalances that represent true liquidity outliers vs. normal operations; extreme Z-scores predict price dislocation and temporary volatility spikes
- **is filling nan necessary**: Yes, backfill required to maintain time-series continuity for accurate mean/std calculation.
- **Directionality**: High positive values indicate extreme liquidity pressure (potential short-term shorting opportunity or avoidance); negative values indicate unusually light rebalancing
- **Boundary Conditions**: |Z| > 2 indicates significant anomaly; Z > 3 suggests potential market breakdown where rebalance volume exceeds multiple days of normal trading
- **Implementation Example**: `divide(ts_av_diff(ts_backfill(vec_avg({vda}), lookback=5, k=1), 120), ts_std_dev(ts_backfill(vec_avg({vda}), lookback=5, k=1), 120))`

**Concept**: Notional-Volume Divergence Signal
- **Sample Fields Used**: notional, shares
- **Definition**: Deviation of the implied price (notional/shares) from recent historical levels to detect inconsistencies or special situations
- **Why This Feature**: Anomalous ratios suggest corporate actions (splits, spin-offs), dual-class share confusion, or data errors; also captures extreme price movements between announcement and effective date
- **is filling nan necessary**: Yes, backfill both fields to align timestamps before calculating ratio and its deviation.
- **Directionality**: Extreme deviations indicate corporate actions or price gaps; persistent divergence suggests stale data or complex share structures
- **Boundary Conditions**: Ratio near zero suggests missing data; extreme spikes suggest reverse splits or delisting scenarios requiring caution
- **Implementation Example**: `ts_av_diff(divide(ts_backfill(vec_avg({notional}), lookback=5, k=1), ts_backfill(vec_avg({shares}), lookback=5, k=1)), 60)`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Liquidity-Adjusted Trade Intensity
- **Sample Fields Used**: notional, vda
- **Definition**: Product of notional value and VDA to capture situations where large dollar amounts coincide with limited liquidity capacity
- **Why This Feature**: Multiplicative interaction identifies the most dangerous rebalances: high dollar value in illiquid names. This is where market impact is maximized and price dislocation most likely.
- **is filling nan necessary**: Yes, backfill both fields independently to ensure alignment before multiplication.
- **Directionality**: High values indicate severe capacity strain (large $ in illiquid name); low values indicate easy absorption (small $ or liquid name)
- **Boundary Conditions**: Exponentially increasing impact at high values; threshold effects likely around institutional liquidity capacity limits
- **Implementation Example**: `multiply(ts_backfill(vec_avg({notional}), lookback=5, k=1), ts_backfill(vec_avg({vda}), lookback=5, k=1))`

**Concept**: Implied Reference Price Proxy
- **Sample Fields Used**: notional, shares
- **Definition**: Ratio of notional to shares as a proxy for the reference price used by index calculators
- **Why This Feature**: Provides independent price estimate for validation; deviations from market price indicate timing differences or special situations; useful for detecting stale announcements
- **is filling nan necessary**: Yes, backfill required to ensure both numerator and denominator represent same announcement event.
- **Directionality**: Level indicates price; trend indicates drift; divergence from market price indicates stale data or corporate actions
- **Boundary Conditions**: Near-zero values impossible (division by zero protection needed); extreme values suggest penny stocks or data errors
- **Implementation Example**: `divide(ts_backfill(vec_avg({notional}), lookback=5, k=1), ts_backfill(vec_avg({shares}), lookback=5, k=1))`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Share-to-Notional Conversion Factor
- **Sample Fields Used**: shares, notional
- **Definition**: Ratio of shares to notional (inverse of price proxy) representing the share volume per dollar of rebalance value
- **Why This Feature**: Structural characteristic indicating price level and share class structure; stable ratio indicates consistent share class; shifts indicate splits or share changes
- **is filling nan necessary**: Yes, backfill both fields to calculate stable structural ratios.
- **Directionality**: High values indicate low-priced stocks (many shares per dollar); low values indicate high-priced stocks; sudden changes indicate corporate actions
- **Boundary Conditions**: Stable values indicate normal operations; sudden drops suggest forward splits; sudden spikes suggest reverse splits
- **Implementation Example**: `divide(ts_backfill(vec_avg({shares}), lookback=5, k=1), ts_backfill(vec_avg({notional}), lookback=5, k=1))`

**Concept**: Daily Rebalance Concentration
- **Sample Fields Used**: notional
- **Definition**: Share of total daily rebalance notional represented by this security (cross-sectional normalization)
- **Why This Feature**: Identifies securities bearing disproportionate burden of daily rebalancing activity; high concentration suggests idiosyncratic risk
- **is filling nan necessary**: Yes, backfill required to ensure participation in cross-sectional sum.
- **Directionality**: High values indicate dominant position in rebalance activity; low values indicate minor contributor
- **Boundary Conditions**: Values >0.5 indicate majority of daily rebalance flow; near-zero indicates negligible impact
- **Implementation Example**: `divide(ts_backfill(vec_avg({notional}), lookback=5, k=1), ts_sum(ts_backfill(vec_avg({notional}), lookback=5, k=1), 1))`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Accumulated Liquidity Drain
- **Sample Fields Used**: vda
- **Definition**: Sum of VDA over rolling window to measure total days of volume equivalent accumulated from multiple overlapping rebalances
- **Why This Feature**: Captures cumulative pressure when securities are affected by multiple index changes simultaneously or in rapid succession; persistent high cumulative VDA indicates chronic liquidity stress
- **is filling nan necessary**: Yes, backfill essential to treat sparse events as persistent pressure until effective date.
- **Directionality**: High values indicate severe cumulative pressure (multiple days of volume pending); low values indicate isolated events
- **Boundary Conditions**: Values >5 suggest severe liquidity crisis (weeks of normal flow compressed); values >10 indicate potential market structure breakdown
- **Implementation Example**: `ts_sum(ts_backfill(vec_avg({vda}), lookback=5, k=1), 60)`

**Concept**: Rolling Notional Exposure Window
- **Sample Fields Used**: notional
- **Definition**: Cumulative sum of expected notional over time to capture total dollar value of pending rebalances
- **Why This Feature**: Measures the total inventory risk building up in the market; high cumulative notional indicates potential for cascading liquidations or crowded trades
- **is filling nan necessary**: Yes, backfill to accumulate sparse announcement effects.
- **Directionality**: High values indicate large pending dollar flows; low values indicate minimal exposure
- **Boundary Conditions**: Exponentially increasing risk with cumulative size; threshold effects at institutional capacity limits
- **Implementation Example**: `ts_sum(ts_backfill(vec_avg({notional}), lookback=5, k=1), 90)`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Cross-Sectional Liquidity Rank
- **Sample Fields Used**: vda
- **Definition**: Gaussian quantile ranking of VDA across universe to identify relative liquidity stress vs. peers
- **Why This Feature**: Normalizes for market-wide rebalance activity; identifies outliers even in busy rebalance periods; ranks severity relative to opportunity set
- **is filling nan necessary**: Yes, backfill to ensure cross-sectional comparability on each date.
- **Directionality**: High values indicate most stressed liquidity in universe; low values indicate easiest absorption
- **Boundary Conditions**: Extreme tails (>2 sigma) indicate significant relative dislocation; median values indicate normal conditions
- **Implementation Example**: `quantile(ts_backfill(vec_avg({vda}), lookback=5, k=1), driver="gaussian", sigma=1.0)`

**Concept**: Liquidity-Neutralized Size Residual
- **Sample Fields Used**: notional, vda
- **Definition**: Residual of notional after regressing out VDA effect (size purged of liquidity impact)
- **Why This Feature**: Separates "big because liquid" from "big despite illiquid"; positive residuals indicate unusually large notional for given liquidity; captures information not in VDA alone
- **is filling nan necessary**: Yes, backfill both fields before regression to ensure alignment.
- **Directionality**: Positive residuals indicate large flows in liquid names (absorbable); negative residuals indicate small flows in illiquid names (still dangerous)
- **Boundary Conditions**: Extreme positive outliers indicate whale trades in blue chips; extreme negative suggests data errors or micro-cap inclusion
- **Implementation Example**: `regression_neut(ts_backfill(vec_avg({notional}), lookback=5, k=1), ts_backfill(vec_avg({vda}), lookback=5, k=1))`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Pure Forced Flow Intensity
- **Sample Fields Used**: vda, notional
- **Definition**: VDA conditioned on high notional to capture only the liquidity stress from significant dollar flows (the essence of non-discretionary market impact)
- **Why This Feature**: Isolates the essential risk: forced trading in size. Small VDA with small notional is noise; large VDA with large notional is the essence of rebalance risk.
- **is filling nan necessary**: Yes, backfill both fields; condition uses ts_mean threshold to identify "high notional" regimes.
- **Directionality**: High values capture severe liquidity events that matter; zero values indicate either liquid names or trivial flows
- **Boundary Conditions**: Activated only when notional exceeds historical mean; captures tail risk essence
- **Implementation Example**: `trade_when(ts_backfill(vec_avg({vda}), lookback=5, k=1), greater(ts_backfill(vec_avg({notional}), lookback=5, k=1), ts_mean(ts_backfill(vec_avg({notional}), lookback=5, k=1), 120)), 1)`

**Concept**: Rebalance Efficiency Ratio
- **Sample Fields Used**: notional, vda
- **Definition**: Notional per unit of VDA (dollar value per day of volume), representing the liquidity efficiency of executing the rebalance
- **Why This Feature**: First principles measure of market capacity utilization; high ratio means high dollar throughput per day of liquidity (efficient); low ratio means wasting liquidity on small dollars (inefficient)
- **is filling nan necessary**: Yes, backfill required for both components.
- **Directionality**: High values indicate efficient use of liquidity capacity (large flows in liquid names); low values indicate inefficient liquidity consumption (small flows in illiquid names)
- **Boundary Conditions**: Ratio > $100M/day indicates institutional-grade liquidity; ratio < $1M/day indicates retail-level liquidity in micro-caps
- **Implementation Example**: `divide(ts_backfill(vec_avg({notional}), lookback=5, k=1), ts_backfill(vec_avg({vda}), lookback=5, k=1))`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Limited to index constituents only; non-constituents receive NaN. Coverage expands during rebalancing windows as stocks enter/exit indices.
- **Timeliness**: Post-announcement data with delay=1 ensures no look-ahead bias, but effective date proximity unknown. Data sparse between announcement and effective date.
- **Accuracy**: High precision for major indices (MSCI, Russell) but subject to revision until effective date. VDA relies on historical ADV which may not predict future liquidity during stress events.
- **Potential Biases**: Survivorship bias in historical analysis (only see successful rebalances); selection bias toward larger, more liquid names in major indices; price impact not reflected in pre-effective estimates.

### Computational Complexity
- **Lightweight features**: `divide(vec_avg({notional}), vec_avg({shares}))` - simple vector arithmetic
- **Medium complexity**: `ts_mean(ts_backfill(vec_avg({vda}), lookback=5, k=1), 60)` - requires backfill then time-series mean
- **Heavy computation**: `regression_neut(ts_backfill(vec_avg({notional}), lookback=5, k=1), ts_backfill(vec_avg({vda}), lookback=5, k=1))` - cross-sectional regression on backfilled data

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Liquidity Pressure Z-Score** - Classic statistical anomaly detection on VDA; robust to different index types; high interpretability
2. **Liquidity-Adjusted Trade Intensity** - Simple multiplicative interaction capturing the core economic insight of the dataset; strong theoretical basis
3. **Accumulated Liquidity Drain** - Cumulative sum captures the persistence of rebalance effects; essential for multi-day event windows

**Tier 2 (Secondary Priority)**:
1. **Cross-Sectional Liquidity Rank** - Relative ranking removes market-wide rebalance activity noise; useful for relative value strategies
2. **Rebalance Flow Momentum** - Trend detection in notional flows; captures accelerating passive flows

**Tier 3 (Requires Further Validation)**:
1. **Pure Forced Flow Intensity** - Conditional logic may introduce sample bias; requires careful threshold tuning
2. **Notional-Volume Divergence Signal** - Complex interpretation; may capture data errors rather than alpha

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How does the VDA measure perform during market stress when ADV expands or contracts significantly from historical 20-day levels?
2. What is the decay profile of rebalance impact between announcement and effective date? Is the pressure front-loaded or evenly distributed?
3. How do addition vs. deletion events differ in their price impact patterns, and can we construct directional indicators from this dataset alone?

### Recommended Additional Data:
- **Effective Date Proximity**: Days remaining until rebalance execution to model urgency/decay
- **Directional Sign**: Addition (buy) vs. Deletion (sell) indicators to construct signed pressure metrics
- **Historical Realized Impact**: Post-effective date price changes to validate VDA predictive power and calibrate thresholds
- **Index AUM Data**: Total assets tracking each index to scale notional expectations by actual passive fund size

### Assumptions to Challenge:
- **Assumption**: VDA is the optimal liquidity measure. Challenge: Should we use 5-day or 60-day ADV instead of 20-day? Does median volume outperform mean?
- **Assumption**: Rebalance pressure is linear. Challenge: Is there a threshold effect where VDA > 2.0 has disproportionate impact vs. VDA < 0.5?
- **Assumption**: All rebalances are equal. Challenge: Do quarterly rebalances differ from annual? Do index additions differ from deletions in predictability?

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand the mechanical nature of index rebalancing flows
2. Question-driven feature generation (8 fundamental questions) applied to liquidity event data
3. Logical validation of each feature concept against market microstructure theory
4. Transparent documentation of reasoning with emphasis on sparse data handling via backfill operators

**Design Principles**:
- Focus on liquidity transformation (notional → shares → VDA) as the core dataset narrative
- Prioritize features that capture non-discretionary flow characteristics unique to index rebalancing
- Emphasize handling of sparse, event-driven data through explicit backfill operators
- Distinguish between absolute scale (notional), raw flow (shares), and relative impact (VDA)

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate VDA predictive power against realized volatility, gather directional flow data*