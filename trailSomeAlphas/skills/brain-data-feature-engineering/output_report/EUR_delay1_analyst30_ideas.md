**Dataset**: analyst30
**Region**: EUR
**Delay**: 1

# Analyst30 Dividend Forecast Feature Engineering Analysis Report

**Dataset**: analyst30
**Category**: Analyst
**Region**: EUR
**Analysis Date**: 2024
**Fields Analyzed**: 4

---

## Executive Summary

**Primary Question Answered by Dataset**: What are the expected cash flow distributions to shareholders, adjusted for corporate actions, and how do they relate to fiscal reporting periods and currency denominations?

**Key Insights from Analysis**:
- The dataset captures the divergence between nominal declared dividends and economic reality post-corporate actions
- Fiscal year end dates provide critical temporal context for distinguishing final vs interim dividends
- Multi-currency payment structures indicate complex capital structures or ADR programs
- The vector structure allows analysis of dividend stability and policy consistency over multiple observations

**Critical Field Relationships Identified**:
- `adjustedgrossamt` vs `unadjustedgrossamt`: Reveals corporate action impact magnitude and direction
- `fiscalyearend` vs dividend amounts: Provides seasonality and fiscal cycle alignment context
- `currency_code` vs `adjustedgrossamt`: Defines FX exposure and cash flow currency risk

**Most Promising Feature Concepts**:
1. **Corporate Action Impact Ratio** - directly measures capital structure effects on shareholder payouts
2. **Dividend Information Ratio** - quantifies stability and reliability of income stream
3. **Fiscal Year Alignment Score** - captures timing regularity and fiscal discipline

---

## Dataset Deep Understanding

### Dataset Description
This dataset provides dividend forecast and announcement data for European equities, capturing both the originally declared dividend amounts and the adjusted amounts reflecting corporate actions such as stock splits, spin-offs, and consolidations. It includes fiscal year end dates for temporal context and payment currency codes for FX risk assessment. The data enables analysis of dividend policy stability, corporate action impacts, and cash flow predictability.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `anl30_adjustedgrossamt` | The dividend amount, adjusted for corporate actions | Vector (Float) | Daily | ~88% |
| `anl30_unadjustedgrossamt` | The originally declared dividend amount | Vector (Float) | Daily | ~88% |
| `anl30_fiscalyearend` | The last day of the company fiscal year | Vector (Date) | Annual | ~92% |
| `anl30_payment_currency_code` | Currency in which the shareholder payout is made | Vector (String) | As declared | ~100% |

### Field Deconstruction Analysis

#### `anl30_adjustedgrossamt`: Adjusted Dividend Amount
- **What is being measured?**: The actual economic cash flow per share that shareholders will receive after accounting for capital structure changes
- **How is it measured?**: Derived from declared amounts by applying corporate action adjustment factors (split ratios, spin-off distributions)
- **Time dimension**: Forward-looking point-in-time declarations with historical revisions as corporate actions occur
- **Business context**: Represents the true purchasing power of the dividend, comparable across time periods regardless of stock splits
- **Generation logic**: Calculated by data vendor using official corporate action notices and declared dividend rates
- **Reliability considerations**: Highly reliable for recent data; historical adjustments may vary by vendor methodology during complex restructurings

#### `anl30_unadjustedgrossamt`: Unadjusted Dividend Amount
- **What is being measured?**: The nominal dividend amount as originally declared by the board of directors before any adjustments
- **How is it measured?**: Direct capture of company announcements in absolute monetary terms per share
- **Time dimension**: Declaration date snapshot, fixed at announcement unless subsequently changed
- **Business context**: Maintains historical continuity for nominal cash flow planning; shows "face value" of dividend promise
- **Generation logic**: Sourced from company investor relations announcements and regulatory filings
- **Reliability considerations**: Subject to restatement if company revises dividend; does not reflect subsequent capital changes

#### `anl30_fiscalyearend`: Fiscal Year End Date
- **What is being measured?**: The terminal date of the company's accounting year, which often determines final dividend timing
- **How is it measured?**: Company-specific accounting calendar, often December 31 but varies by jurisdiction and industry
- **Time dimension**: Annual recurring date with occasional changes during mergers or accounting policy shifts
- **Business context**: Provides the temporal anchor for distinguishing final (year-end) dividends from interim (quarterly/half-yearly) payments
- **Generation logic**: Derived from company statutory accounts and annual report filings
- **Reliability considerations**: Generally stable; changes indicate significant corporate events or accounting standard adoptions

#### `payment_currency_code`: Payment Currency
- **What is being measured?**: The ISO 4217 currency code denomination of the cash dividend payment
- **How is it measured?**: Determined by company treasury operations based on primary listing or shareholder residence
- **Time dimension**: Typically static but may change during redomiciliation or currency union changes
- **Business context**: Critical for FX risk management; determines the currency exposure of dividend income
- **Generation logic**: Sourced from paying agent banks and company distribution policies
- **Reliability considerations**: Reliable for primary listings; ADRs may have multiple currency layers not fully captured

### Field Relationship Mapping

**The Story This Data Tells**:
The dataset narrates the transformation of boardroom dividend promises into actual shareholder cash flows. It tracks how capital structure changes (splits, consolidations) alter the nominal value of dividends, while anchoring these payments to fiscal reporting cycles and currency denominations. The tension between `unadjustedgrossamt` (what was promised) and `adjustedgrossamt` (what is economically delivered) reveals the impact of corporate actions on shareholder value.

**Key Relationships Identified**:
1. **Corporate Action Impact**: The ratio of adjusted to unadjusted amounts reveals the dilution or concentration factor applied by recent capital changes
2. **Fiscal Cycle Alignment**: Proximity of dividend dates to `fiscalyearend` distinguishes between final (earnings-distribution) and interim (advance-payment) dividends
3. **Currency-Economic Value Interaction**: The magnitude of `adjustedgrossamt` must be interpreted through the lens of `currency_code` for real value assessment

**Missing Pieces That Would Complete the Picture**:
- Ex-dividend dates and payment dates for precise timing analysis
- Share price data to calculate dividend yield (economic context)
- Historical dividend track record for trend analysis beyond current vector window
- Dividend type classification (ordinary vs special vs capital return)

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: Dividend Stability Coefficient
- **Sample Fields Used**: `adjustedgrossamt`
- **Definition**: Coefficient of variation measuring relative stability of adjusted dividend amounts across the vector dimension
- **Why This Feature**: Identifies companies with consistent dividend policies versus those with variable or unpredictable payouts; stable coefficients indicate reliable income streams
- **Logical Meaning**: Signal-to-noise ratio of the dividend process; measures predictability of cash flows
- **is filling nan necessary**: NaN values typically indicate periods with no dividend declaration rather than zero dividends. For stability measurement, filter NaNs using `vec_filter` to avoid treating missing data as zero volatility, or use `ts_backfill` only if assuming dividend continuity across gaps.
- **Directionality**: Values approaching 0 indicate high stability; values >1 indicate high volatility relative to mean
- **Boundary Conditions**: 0 = perfectly stable (single value); theoretically unbounded but practically <5 for viable dividend payers
- **Implementation Example**: `vec_stddev({adjustedgrossamt}) / abs(vec_avg({adjustedgrossamt}))`

**Concept**: Fiscal Calendar Persistence
- **Sample Fields Used**: `fiscalyearend`
- **Definition**: Count of distinct fiscal year end dates present in the vector
- **Why This Feature**: Detects changes in fiscal year end dates which signal mergers, acquisitions, or accounting policy changes that may affect dividend timing
- **Logical Meaning**: Structural stability of the company's accounting calendar
- **is filling nan necessary**: NaN values represent missing fiscal data and should be excluded using `vec_filter` with value="nan" to avoid counting nulls as distinct dates
- **Directionality**: Value of 1 indicates perfect fiscal stability; >1 indicates fiscal year changes during the observation period
- **Boundary Conditions**: Integer >= 0; 0 indicates all missing data; 1 is optimal for stable enterprises
- **Implementation Example**: `vec_count({fiscalyearend})`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Corporate Action Adjustment Magnitude
- **Sample Fields Used**: `adjustedgrossamt`, `unadjustedgrossamt`
- **Definition**: Absolute difference between average unadjusted and adjusted dividend amounts
- **Why This Feature**: Quantifies the raw impact of stock splits, spin-offs, and consolidations on dividend values; large values indicate significant capital structure events
- **Logical Meaning**: The economic distance between declared promise and adjusted reality; measures corporate action intensity
- **is filling nan necessary**: Both fields must be valid for comparison. Use `ts_backfill` if analyzing time series continuity, or ensure both are finite using `is_finite` checks before subtraction to avoid NaN propagation
- **Directionality**: Positive values indicate adjustments reduced the amount (dilutionary splits); negative values indicate adjustments increased it (reverse splits)
- **Boundary Conditions**: 0 = no corporate action impact; unbounded in both directions
- **Implementation Example**: `vec_avg({unadjustedgrossamt}) - vec_avg({adjustedgrossamt})`

**Concept**: Relative Adjustment Ratio
- **Sample Fields Used**: `unadjustedgrossamt`, `adjustedgrossamt`
- **Definition**: Proportional scaling factor applied by corporate actions to the original dividend
- **Why This Feature**: Normalizes corporate action impact across different dividend scales; reveals the split ratio or consolidation factor implicitly
- **Logical Meaning**: The retention rate of dividend value through capital structure changes; <1 indicates dilution, >1 indicates accretion
- **is filling nan necessary**: Division requires protection against zero unadjusted amounts. Use `pasteurize` or `nan_out` to handle edge cases where `unadjustedgrossamt` is zero or NaN
- **Directionality**: <1 indicates dilutionary corporate actions; =1 indicates no adjustment; >1 indicates reverse splits
- **Boundary Conditions**: (0, infinity); approaches 0 for large splits, approaches infinity for large reverse splits
- **Implementation Example**: `vec_avg({adjustedgrossamt}) / vec_avg({unadjustedgrossamt})`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Dividend Distribution Skewness
- **Sample Fields Used**: `adjustedgrossamt`
- **Definition**: Skewness statistic of dividend amounts across the vector dimension
- **Why This Feature**: Detects asymmetry indicating special dividends (positive skew) or dividend cuts (negative skew) within the observation window
- **Logical Meaning**: Measures the tail risk of dividend distributions; identifies non-normal dividend patterns
- **is filling nan necessary**: Skewness calculations are sensitive to missing data. Filter NaNs using `vec_filter` before computing to prevent distortion of the distribution shape
- **Directionality**: Positive skew indicates occasional large special dividends; negative skew indicates consistent base with rare cuts; near 0 indicates normal distribution
- **Boundary Conditions**: Theoretically (-infinity, infinity); practically (-3, 3) for most financial data; |skew| > 2 indicates significant anomaly
- **Implementation Example**: `vec_skewness({adjustedgrossamt})`

**Concept**: Extreme Adjustment Outlier Flag
- **Sample Fields Used**: `unadjustedgrossamt`, `adjustedgrossamt`
- **Definition**: Binary indicator when the absolute adjustment exceeds 2 standard deviations of the unadjusted amount distribution
- **Why This Feature**: Identifies unusual corporate actions or potential data errors that create extreme discrepancies between declared and adjusted values
- **Logical Meaning**: Statistical anomaly detection for corporate action impacts; flags events requiring manual review
- **is filling nan necessary**: Requires complete data for valid statistical comparison. Fill short gaps with `ts_backfill` or `group_mean` if temporary, otherwise exclude from calculation
- **Directionality**: 1 (true) indicates extreme outlier event; 0 (false) indicates normal adjustment range
- **Boundary Conditions**: Binary 0 or 1; threshold at 2-sigma (configurable)
- **Implementation Example**: `greater(abs(vec_avg({unadjustedgrossamt}) - vec_avg({adjustedgrossamt})), multiply(2, vec_stddev({unadjustedgrossamt})))`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Multi-Currency Exposure Complexity
- **Sample Fields Used**: `currency_code`
- **Definition**: Count of distinct currency codes present in the dividend vector
- **Why This Feature**: Identifies complex capital structures, ADR programs, or multi-jurisdictional operations with dividends paid in multiple currencies
- **Logical Meaning**: Operational complexity and FX exposure diversification; single currency indicates simple structure, multiple indicates complexity
- **is filling nan necessary**: NaN values represent unspecified currencies and should be filtered out before counting to avoid inflating complexity metrics
- **Directionality**: Higher values indicate multi-currency dividend structures; 1 indicates single currency uniformity
- **Boundary Conditions**: Integer >= 0; typically 1-3 for most equities; >3 indicates highly complex structures
- **Implementation Example**: `vec_count({currency_code})`

**Concept**: Complexity-Adjusted Dividend Volatility
- **Sample Fields Used**: `adjustedgrossamt`, `currency_code`
- **Definition**: Standard deviation of dividend amounts normalized by currency diversity to isolate policy volatility from structural complexity
- **Why This Feature**: Separates true dividend policy instability from volatility induced by multi-currency operations or FX effects
- **Logical Meaning**: Pure dividend policy volatility excluding structural currency noise
- **is filling nan necessary**: Ensure `currency_code` is valid for all observations; use `ts_backfill` for missing currency codes if assuming continuity, otherwise filter
- **Directionality**: Higher values indicate unstable dividend policy; lower values indicate consistent policy across currencies
- **Boundary Conditions**: >= 0; 0 indicates perfect stability regardless of complexity
- **Implementation Example**: `divide(vec_stddev({adjustedgrossamt}), max(1, vec_count({currency_code})))`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Adjusted Value Retention Ratio
- **Sample Fields Used**: `adjustedgrossamt`, `unadjustedgrossamt`
- **Definition**: Proportion of total unadjusted dividend value that remains after corporate action adjustments
- **Why This Feature**: Measures value erosion or accretion from capital structure changes; indicates how much of declared value survives adjustments
- **Logical Meaning**: The structural retention rate of dividend value through corporate actions
- **is filling nan necessary**: Division by zero risk when `unadjustedgrossamt` is zero. Use `nan_out` or `pasteurize` to handle zero denominators and ensure numerical stability
- **Directionality**: 1 = 100% retention (no adjustment); <1 indicates value dilution; >1 indicates value accretion (reverse splits)
- **Boundary Conditions**: [0, infinity); 0 = total value loss; 1 = no change
- **Implementation Example**: `divide(vec_sum({adjustedgrossamt}), vec_sum({unadjustedgrossamt}))`

**Concept**: Fiscal Year Temporal Dispersion
- **Sample Fields Used**: `fiscalyearend`
- **Definition**: Range between maximum and minimum fiscal year end dates in the vector
- **Why This Feature**: Detects fiscal year changes or multiple subsidiaries with different year-ends; measures accounting period structural stability
- **Logical Meaning**: Temporal concentration of fiscal reporting; 0 indicates consistent fiscal year, >0 indicates changes or complexity
- **is filling nan necessary**: NaN dates must be filtered using `vec_filter` before calculating range to avoid false extremes or errors
- **Directionality**: 0 indicates perfect fiscal alignment; higher values (up to 365) indicate fiscal year changes or diverse subsidiaries
- **Boundary Conditions**: 0 to 365 (days); 0 is optimal; >30 suggests fiscal year change or data inconsistency
- **Implementation Example**: `vec_range({fiscalyearend})`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Cumulative Economic Dividend Accrual
- **Sample Fields Used**: `adjustedgrossamt`
- **Definition**: Sum of all adjusted dividend amounts over the vector dimension representing total economic cash flow
- **Why This Feature**: Aggregates total expected cash flow from dividends over the observation period; useful for yield calculations and income forecasting
- **Logical Meaning**: Total shareholder value distribution after corporate action adjustments
- **is filling nan necessary**: NaN values represent missing periods; treat as 0 for cumulative sum using `add` with filter=true, or backfill if assuming dividend continuity. For strict accrual accounting, fill NaNs with 0 to avoid understating total flow
- **Directionality**: Higher values indicate greater cumulative cash flow; zero indicates no dividend activity
- **Boundary Conditions**: >= 0; theoretically unbounded; 0 indicates non-payer or all missing data
- **Implementation Example**: `vec_sum({adjustedgrossamt})`

**Concept**: Cumulative Nominal Dividend Liability
- **Sample Fields Used**: `unadjustedgrossamt`
- **Definition**: Sum of unadjusted dividend amounts representing total declared obligations before adjustments
- **Why This Feature**: Measures the raw cash commitment from corporate treasury perspective; useful for liquidity analysis
- **Logical Meaning**: Total nominal liability of the company for dividend payments prior to capital structure adjustments
- **is filling nan necessary**: Similar to adjusted amounts; NaNs should be treated as 0 for liability accumulation or backfilled if analyzing continuous obligations
- **Directionality**: Higher values indicate heavy dividend obligations; lower values indicate conservative payout policies
- **Boundary Conditions**: >= 0; 0 indicates no declared dividends
- **Implementation Example**: `vec_sum({unadjustedgrossamt})`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Dividend Median Relative Position
- **Sample Fields Used**: `adjustedgrossamt`
- **Definition**: Ratio of median dividend amount to maximum amount within the vector
- **Why This Feature**: Measures how close typical dividends are to peak dividends; distinguishes between regular sustainable payouts and occasional special dividends
- **Logical Meaning**: Relative positioning of median payout within the observed range; indicates special dividend contribution
- **is filling nan necessary**: Percentile calculations require clean data; filter NaNs using `vec_filter` before computing median to avoid bias toward zero
- **Directionality**: 0.5 indicates symmetric distribution; <0.5 indicates positive skew (occasional large specials); >0.5 indicates negative skew
- **Boundary Conditions**: 0 to 1; 1 indicates flat dividend (all same); near 0 indicates highly skewed with occasional massive payouts
- **Implementation Example**: `divide(vec_percentage({adjustedgrossamt}, percentage=0.5), vec_max({adjustedgrossamt}))`

**Concept**: Corporate Action Impact Depth
- **Sample Fields Used**: `unadjustedgrossamt`, `adjustedgrossamt`
- **Definition**: Relative size of corporate action adjustment as percentage of original unadjusted amount
- **Why This Feature**: Normalizes adjustment magnitude to compare impact across companies of different sizes and dividend scales
- **Logical Meaning**: Percentage of dividend value affected by capital structure changes; measures corporate action severity
- **is filling nan necessary**: Ensure no division by zero; use `nan_out` on denominator to handle zero unadjusted amounts, and fill missing values appropriately
- **Directionality**: 0 = no impact; positive values indicate percentage reduction (splits); negative values indicate enhancement (reverse splits)
- **Boundary Conditions**: (-infinity, 1]; 1 = 100% reduction (total loss); 0 = no change
- **Implementation Example**: `divide(subtract(vec_avg({unadjustedgrossamt}), vec_avg({adjustedgrossamt})), vec_avg({unadjustedgrossamt}))`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Pure Economic Dividend Signal
- **Sample Fields Used**: `adjustedgrossamt`
- **Definition**: The mean adjusted dividend amount representing the true economic cash flow stripped of nominal artifacts
- **Why This Feature**: Captures the first-principles cash flow that investors actually receive, adjusted for all capital structure changes
- **Logical Meaning**: Ground truth purchasing power of dividend distributions; the "real" value after all adjustments
- **is filling nan necessary**: For essential signal extraction, temporary NaNs may be filled using `ts_backfill` if assuming dividend policy continuity, but permanent NaNs (no dividend) should be preserved to avoid false positive income signals
- **Directionality**: Higher values indicate superior income generation; zero indicates no economic dividend
- **Boundary Conditions**: >= 0; 0 indicates non-payer; higher is better for income investors
- **Implementation Example**: `vec_avg({adjustedgrossamt})`

**Concept**: Dividend Information Ratio
- **Sample Fields Used**: `adjustedgrossamt`
- **Definition**: Signal-to-noise ratio of dividend payments calculated as mean divided by standard deviation
- **Why This Feature**: Distinguishes high-quality stable income generators from volatile uncertain dividend payers; essential for risk-adjusted income analysis
- **Logical Meaning**: Quality and reliability metric for dividend income; higher ratios indicate predictable cash flows
- **is filling nan necessary**: Standard deviation requires sufficient non-NaN observations. Use `ts_backfill` for short gaps to maintain statistical validity, or ensure minimum data coverage before calculation
- **Directionality**: Higher values indicate high-quality stable dividends (desirable); lower values indicate noisy uncertain payouts (risky)
- **Boundary Conditions**: Infinity (perfect stability) to 0 (infinite volatility); values >2 indicate excellent stability
- **Implementation Example**: `vec_ir({adjustedgrossamt})`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Dividend fields show ~88% coverage for dividend-paying stocks; zero coverage for non-payers (expected)
- **Timeliness**: Adjusted amounts update immediately upon corporate action announcements; unadjusted amounts fixed at declaration
- **Accuracy**: High accuracy for ordinary dividends; special dividends may have timing discrepancies between declaration and adjustment
- **Potential Biases**: Survivorship bias in historical adjusted data for merged entities; currency codes may reflect settlement rather than declaration currency

### Computational Complexity
- **Lightweight features**: `vec_avg`, `vec_sum`, `vec_count` operations on single fields
- **Medium complexity**: `vec_stddev`, `vec_skewness`, `vec_ir` requiring multi-pass calculations
- **Heavy computation**: Cross-field interactions requiring alignment of `adjustedgrossamt` and `unadjustedgrossamt` with NaN handling

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Corporate Action Impact Ratio** - Directly captures dataset's unique value proposition (adjusted vs unadjusted)
2. **Dividend Information Ratio** - Essential stability metric using `vec_ir` operator
3. **Pure Economic Dividend Signal** - Core value metric `vec_avg({adjustedgrossamt})`

**Tier 2 (Secondary Priority)**:
1. **Cumulative Economic Dividend Accrual** - Important for income strategies using `vec_sum`
2. **Relative Adjustment Depth** - Contextualizes corporate action impact

**Tier 3 (Requires Further Validation)**:
1. **Fiscal Year Temporal Dispersion** - Requires validation of date handling in vector operations

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How does the vector dimension align with time (is it historical dividends or multiple forecasts)?
2. What is the typical lag between `fiscalyearend` and associated final dividend payments?
3. How often do companies change `payment_currency_code` during redomiciliations?

### Recommended Additional Data:
- Ex-dividend dates and payment dates for precise timing analysis
- Share price data (pv1) to calculate dividend yields from these amounts
- Dividend type flags (interim vs final vs special) for classification
- Historical corporate action details to validate adjustment ratios

### Assumptions to Challenge:
- That `adjustedgrossamt` is always the economically correct measure (sometimes unadjusted is better for historical comparison)
- That fiscal year end proximity implies final dividend (some companies pay final dividends months after year-end)
- That multiple currencies in the vector indicate complexity (could indicate data errors or ticker changes)

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand dividend data essence (nominal vs economic value)
2. Question-driven feature generation (8 fundamental questions)
3. Logical validation of each feature concept against corporate finance principles
4. Transparent documentation of reasoning and NaN handling considerations

**Design Principles**:
- Focus on logical meaning over conventional dividend yield calculations
- Emphasis on the unique adjusted vs unadjusted relationship in this dataset
- Vector operator usage mandatory due to data structure
- Clear documentation of "why" for each suggestion

---

*Report generated: 2024*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate adjustment ratios against known corporate actions*