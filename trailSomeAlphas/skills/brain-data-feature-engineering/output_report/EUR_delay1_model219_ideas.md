# Canadian Equity Quantitative Models (model219) Feature Engineering Analysis Report

**Dataset**: model219
**Category**: Model
**Region**: EUR
**Delay**: 1
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 253 (per module)

---

## Executive Summary

**Primary Question Answered by Dataset**: This dataset fundamentally measures the multi-dimensional characteristics of Canadian equities through two distinct quantitative model lenses, capturing value, momentum, quality, growth, and risk factors to identify mispriced securities.

**Key Insights from Analysis**:
- The dataset provides dual-module coverage (mdl219_1 and mdl219_2) allowing for cross-validation or ensemble approaches
- Extensive industry-relative metrics enable sector-neutral strategies
- Rich analyst estimate data (FY1/FY2) supports forecast-based feature construction
- Long-term historical relatives (5-year) allow mean-reversion analysis
- Comprehensive cash flow metrics distinguish between accounting earnings and economic cash generation

**Critical Field Relationships Identified**:
- Forward-looking estimates (fc_*) vs. trailing metrics create expectation gaps
- Industry-relative metrics (curind*, indrel*) vs. absolute metrics capture sector effects
- Module 1 vs. Module 2 parallel structures enable robustness testing

**Most Promising Feature Concepts**:
1. **Estimate Dispersion-Adjusted Momentum** - combines `mrspe_cf` with `fc_stdevfy1epsp` to weight momentum by analyst conviction
2. **Cash Flow Quality Divergence** - contrasts `pctchg3yeps` with `pctchg3yfcf` to identify earnings not backed by cash
3. **Structural Leverage Efficiency** - combines `booklev` with `ocfroi` to find optimally leveraged quality companies

---

## Dataset Deep Understanding

### Dataset Description
This dataset provides quantitative financial metrics and models for Canadian equities, including composite scores for Deep Value, Earnings Momentum, Price Momentum, Relative Value, and Value Momentum models. It is designed to analyze stock performance, forecast trends, and evaluate management efficiency and leverage factors. The dual-module structure (mdl219_1 and mdl219_2) suggests either different model specifications, time periods, or estimation methodologies.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `actrtn12m` | 12-month active return representing percent change in stock price | Float | Monthly | ~95% |
| `fc_stdevfy1epsp` | Standard deviation of FY1 EPS estimates scaled by price | Float | Monthly | ~85% |
| `roe` | Return on equity calculated as net income divided by shareholder equity | Float | Quarterly | ~98% |
| `curindbp` | Industry-relative book-to-price ratio adjusted for industry averages | Float | Monthly | ~95% |
| `pctchg3yfcf` | 3-year growth in free cash flow per share calculated as percentage | Float | Quarterly | ~80% |
| `beta` | Beta calculated over 60 months measuring stock volatility relative to market | Float | Monthly | ~99% |
| `mrspe_cf` | Street revision magnitude measuring 3-month change in median earnings forecast | Float | Monthly | ~75% |
| `rel5yep` | 5-year relative EPS-to-price ratio compared to historical averages | Float | Monthly | ~90% |
| `ttmaccu` | Accounting accruals calculated as difference between net income and operating cash flow | Float | Quarterly | ~85% |
| `visiratio` | Visibility ratio calculated as recent daily trading volume divided by 50-day average | Float | Daily | ~99% |

*(Additional 243 fields per module follow similar patterns)*

### Field Deconstruction Analysis

#### `fc_stdevfy1epsp`: FY1 EPS Estimate Dispersion
- **What is being measured?**: The disagreement among analysts regarding forward earnings expectations, normalized by price
- **How is it measured?**: Standard deviation of FY1 consensus estimates divided by current stock price
- **Time dimension**: Forward-looking (next fiscal year), point-in-time snapshot
- **Business context**: Captures uncertainty/conviction in near-term earnings; high dispersion suggests information asymmetry or volatile business conditions
- **Generation logic**: Derived from broker estimate aggregation systems
- **Reliability considerations**: Coverage varies by market cap; thin coverage makes this noisy for small caps

#### `curindbp`: Industry-Relative Book-to-Price
- **What is being measured?**: A stock's valuation relative to its industry peers, not in absolute terms
- **How is it measured?**: Stock's B/P ratio minus industry average B/P ratio (or ratio of ratios)
- **Time dimension**: Current period, cross-sectional relative measure
- **Business context**: Removes sector bias from value investing; financials naturally have different B/P than tech
- **Generation logic**: Requires industry classification and peer aggregation
- **Reliability considerations**: Industry classification errors create misclassification; assumes industry homogeneity

#### `pctchg3yfcf`: 3-Year FCF Growth
- **What is being measured?**: Compounded growth in free cash flow per share over trailing 3 years
- **How is it measured?**: (FCF_current / FCF_3y_ago)^(1/3) - 1, scaled by price
- **Time dimension**: Historical growth trajectory, annualized
- **Business context**: Sustainable cash generation capability; distinguishes growth from cyclicality
- **Generation logic**: Requires 3-year cash flow statement history
- **Reliability considerations**: Sensitive to one-time items; capital intensive businesses have volatile FCF

#### `actrtn12m`: 12-Month Active Return
- **What is being measured?**: Raw price momentum excluding market index movement
- **How is it measured?**: Percent change in stock price minus benchmark return
- **Time dimension**: Trailing 12-month window
- **Business context**: Captures stock-specific trend persistence; basis for momentum strategies
- **Generation logic**: Price return calculation with benchmark subtraction
- **Reliability considerations**: Skewed by low-priced stocks; assumes 12-month formation period optimal

### Field Relationship Mapping

**The Story This Data Tells**:
This dataset narrates the tension between accounting representation and economic reality, between market expectations and realized outcomes, and between absolute valuation and relative positioning. It tracks how efficiently companies convert assets to cash (efficiency), how markets price those cash flows (valuation), how expectations evolve (momentum), and how these characteristics compare to history and peers (relative value).

**Key Relationships Identified**:
1. **Expectation vs. Reality**: `fc_rev3y1` (estimate revisions) predicts future `actrtn*` (returns) while `surp` (earnings surprise) measures past accuracy of `fc_stdevfy1epsp` (dispersion)
2. **Quality vs. Price**: `roe`/`roic` (quality) should correlate with `curindbp` (value) in efficient markets; deviations suggest opportunities
3. **Cash vs. Earnings**: `pctchg3yeps` vs `pctchg3yfcf` divergence indicates accrual quality (`ttmaccu`) issues
4. **Risk vs. Return**: `beta`/`sigma` vs `actrtn*` momentum; high momentum with low beta suggests alpha vs. market exposure

**Missing Pieces That Would Complete the Picture**:
- Short interest data to identify crowded positions
- Insider trading flows to gauge management conviction
- ESG metrics for sustainability-adjusted valuations
- Options market data (implied volatility, skew) for alternative risk measures

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: Earnings Estimate Stability Score
- **Sample Fields Used**: `fc_stdevfy1epsp`, `fc_stdevfy2epsp`, `fc_numest`
- **Definition**: Inverse of coefficient of variation for analyst estimates, weighted by number of analysts
- **Why This Feature**: High estimate stability indicates business model predictability and information transparency
- **Logical Meaning**: Measures the confidence/consensus among analysts; stable estimates suggest lower future volatility and more predictable cash flows
- **is filling nan necessary**: Yes, use `ts_backfill()` for missing estimate data as lack of coverage implies instability/uncertainty should be neutralized
- **Directionality**: Higher values indicate more stable earnings expectations (bullish for low-volatility strategies)
- **Boundary Conditions**: Near-zero dispersion with high coverage = maximum stability; high dispersion = uncertainty discount
- **Implementation Example**: `divide({fc_numest}, add({fc_stdevfy1epsp}, {fc_stdevfy2epsp}, filter=true))`

**Concept**: Operating Leverage Consistency
- **Sample Fields Used**: `oplev`, `pctchgqtrsales`, `bmpo`
- **Definition**: Stability of operating margin expansion relative to sales growth
- **Why This Feature**: Consistent operating leverage indicates scalable business models
- **Logical Meaning**: Measures whether margin improvements are sustainable or one-time adjustments
- **is filling nan necessary**: No, NaN indicates missing cost structure data which is meaningful (avoid imputation)
- **Directionality**: High values suggest stable cost structure; low values indicate volatile margins
- **Boundary Conditions**: Extreme positive values may indicate unsustainable margin expansion
- **Implementation Example**: `ts_corr({bmpo}, {pctchgqtrsales}, 12)`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Revision Acceleration
- **Sample Fields Used**: `fc_rev3y1`, `fc_rev6`, `mrspe_cf`
- **Definition**: Rate of change in analyst estimate revisions, capturing acceleration in sentiment
- **Why This Feature**: Accelerating revisions predict price momentum better than static revision levels
- **Logical Meaning**: Second derivative of expectations; positive values indicate improving analyst conviction
- **is filling nan necessary**: Yes, use `group_mean()` to fill missing revision data within industries
- **Directionality**: Positive values indicate accelerating positive sentiment (bullish)
- **Boundary Conditions**: Extreme values may indicate event-driven revisions (mergers, earnings) rather than organic growth
- **Implementation Example**: `subtract({fc_rev3y1}, ts_delay({fc_rev3y1}, 21))`

**Concept**: Cash Flow Trajectory Divergence
- **Sample Fields Used**: `pctchg3yfcf`, `pctchg3yeps`, `fcfghc`
- **Definition**: Difference between cash flow growth and earnings growth to identify quality of change
- **Why This Feature**: Sustainable companies grow cash faster than earnings; deteriorating companies show earnings without cash
- **Logical Meaning**: Positive values indicate cash-backed growth; negative values suggest accrual-based earnings inflation
- **is filling nan necessary**: Yes, use `ts_backfill()` with 5-day window for missing growth metrics
- **Directionality**: Positive divergence (cash > earnings growth) indicates quality improvement
- **Boundary Conditions**: Extreme divergence may indicate working capital investment cycles
- **Implementation Example**: `subtract({pctchg3yfcf}, {pctchg3yeps})`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Valuation Regime Deviation
- **Sample Fields Used**: `rel5yep`, `rel5ybp`, `rel5yfcf`
- **Definition**: Z-score of current valuation relative to 5-year historical range
- **Why This Feature**: Extreme deviations from historical valuation regimes often mean-revert
- **Logical Meaning**: Measures how unusual current valuation is compared to company-specific history
- **is filling nan necessary**: No, insufficient history should remain NaN to avoid false signals
- **Directionality**: Very negative values indicate unusually cheap (contrarian buy); very positive indicate expensive
- **Boundary Conditions**: Values beyond 2 sigma are statistically significant; business model changes invalidate historical comparison
- **Implementation Example**: `divide(subtract({rel5yep}, ts_mean({rel5yep}, 252)), ts_std_dev({rel5yep}, 252))`

**Concept**: Earnings Surprise Persistence
- **Sample Fields Used**: `surp`, `fc_numrevy1`, `ttmaccu`
- **Definition**: Unexpected earnings deviation weighted by accrual quality to identify genuine surprises vs. accounting artifacts
- **Why This Feature**: Genuine surprises (low accruals) persist; managed earnings (high accruals) reverse
- **Logical Meaning**: High values with low accruals indicate sustainable positive surprise; high accruals suggest manipulation
- **is filling nan necessary**: Yes, use `ts_backfill()` for surprise data as delays create artificial NaNs
- **Directionality**: Positive values indicate under-promise/over-deliver management quality
- **Boundary Conditions**: Extreme outliers often indicate one-time items; verify with `spefcn`
- **Implementation Example**: `multiply({surp}, reverse({ttmaccu}))`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Risk-Adjusted Value Momentum
- **Sample Fields Used**: `curindbp`, `actrtn6m`, `betasigma`
- **Definition**: Value positions (low B/P) with positive momentum adjusted for volatility risk
- **Why This Feature**: Pure value is risky; combining with momentum and risk filters improves Sharpe ratio
- **Logical Meaning**: Identifies cheap stocks that are already moving, with reasonable risk profiles
- **is filling nan necessary**: Yes, use `group_mean()` for missing beta within sectors
- **Directionality**: Higher values indicate better risk-adjusted value opportunities
- **Boundary Conditions**: Extreme momentum may indicate value traps reversing; verify with `chgvolpre4y`
- **Implementation Example**: `divide(multiply({curindbp}, {actrtn6m}), {betasigma})`

**Concept**: Quality Leverage Efficiency
- **Sample Fields Used**: `roic`, `booklev`, `ocfroi`
- **Definition**: Return on capital multiplied by optimal leverage level, penalizing excess cash or excess debt
- **Why This Feature**: Modigliani-Miller suggests value creation from ROIC > WACC; optimal leverage amplifies this
- **Logical Meaning**: High values indicate efficient use of financial leverage to amplify quality returns
- **is filling nan necessary**: No, NaN in leverage indicates financial companies with different capital structures
- **Directionality**: Higher values indicate optimal capital structure deployment
- **Boundary Conditions**: Very high leverage with declining ROIC signals distress
- **Implementation Example**: `multiply({roic}, tanh({booklev}))`

**Concept**: Analyst Conviction-Weighted Growth
- **Sample Fields Used**: `gspea2y_cf`, `spe1yfvc_cf`, `mktcappera`
- **Definition**: Long-term growth estimates weighted by estimate agreement and analyst coverage depth
- **Why This Feature**: Growth estimates are noisy; weighting by dispersion and coverage improves precision
- **Logical Meaning**: High values indicate consensus growth with high conviction and adequate coverage
- **is filling nan necessary**: Yes, use `ts_backfill()` for growth estimates
- **Directionality**: Higher values indicate high-quality growth opportunities
- **Boundary Conditions**: Low coverage (low `mktcappera`) makes estimates unreliable
- **Implementation Example**: `divide(multiply({gspea2y_cf}, {mktcappera}), add({spe1yfvc_cf}, 0.01))`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Capital Structure Flexibility
- **Sample Fields Used**: `booklev`, `mktlev`, `netdebt`, `cashratio`
- **Definition**: Distance from optimal capital structure based on market vs. book leverage divergence
- **Why This Feature**: Large divergence between market and book leverage indicates either undervalued assets or distress
- **Logical Meaning**: Measures the gap between accounting values and market assessment of financial risk
- **is filling nan necessary**: No, financial firms have different structures and should be excluded
- **Directionality**: Moderate positive values indicate leverage flexibility; extreme values indicate distress or over-leverage
- **Boundary Conditions**: Negative net debt (cash > debt) indicates under-leverage and value destruction via excess liquidity
- **Implementation Example**: `subtract({mktlev}, {booklev})`

**Concept**: Asset Intensity Profile
- **Sample Fields Used**: `astcomp`, `capexast`, `fixastto`, `invast`
- **Definition**: Decomposition of asset base into working capital, fixed assets, and intangibles to identify business model type
- **Why This Feature**: Different asset structures have different economic sensitivities and capital requirements
- **Logical Meaning**: High fixed asset intensity indicates operating leverage; high working capital indicates inventory/credit risk
- **is filling nan necessary**: Yes, use `ts_backfill()` for asset composition data
- **Directionality**: High values indicate capital-light models (service/tech); low values indicate heavy industry
- **Boundary Conditions**: Extreme compositions indicate either platform companies or distressed asset sales
- **Implementation Example**: `divide({astcomp}, add({capexast}, {fixastto}))`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Reinvestment Accumulation Efficiency
- **Sample Fields Used**: `reinrate`, `roe`, `susgrowth`, `ttmcapexp`
- **Definition**: Cumulative retained earnings converted into sustainable growth, measuring reinvestment ROI
- **Why This Feature**: Sustainable value creation requires reinvestment at rates exceeding cost of capital
- **Logical Meaning**: High values indicate effective plowback of earnings into value-creating projects
- **is filling nan necessary**: Yes, use `group_mean()` for missing reinvestment rates within industries
- **Directionality**: Higher values indicate superior capital allocation discipline
- **Boundary Conditions**: Negative values indicate value destruction through growth investments
- **Implementation Example**: `multiply({reinrate}, {roe})`

**Concept**: Multi-Horizon Momentum Accumulation
- **Sample Fields Used**: `actrtn1m`, `actrtn6m`, `actrtn12m`, `actrtn24m`
- **Definition**: Weighted accumulation of returns across time horizons to distinguish trend from noise
- **Why This Feature**: Persistent momentum across horizons indicates information diffusion; single-horizon momentum is noisier
- **Logical Meaning**: High values indicate consistent price appreciation across short, medium, and long-term
- **is filling nan necessary**: No, missing return data indicates illiquidity or recent listing (meaningful signal)
- **Directionality**: Positive values indicate persistent uptrend accumulation
- **Boundary Conditions**: Divergence between short and long-term momentum indicates inflection points
- **Implementation Example**: `add({actrtn1m}, {actrtn6m}, {actrtn12m}, filter=true)`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Cross-Sectional Value Dispersion Rank
- **Sample Fields Used**: `curindbp`, `curindsp`, `curindfcf`
- **Definition**: Percentile rank of value composite within industry, adjusted for sector dispersion
- **Why This Feature**: Value works better when comparing within sectors due to accounting differences
- **Logical Meaning**: Identifies cheapest stocks within their peer groups regardless of sector valuation levels
- **is filling nan necessary**: Yes, use `ts_backfill()` for missing relative metrics
- **Directionality**: Higher ranks (top decile) indicate extreme relative value
- **Boundary Conditions**: Extreme ranks in low-dispersion industries less meaningful than in high-dispersion
- **Implementation Example**: `quantile(add({curindbp}, {curindsp}), driver="uniform")`

**Concept**: Liquidity-Adjusted Size Premium
- **Sample Fields Used**: `nlmktcap`, `visiratio`, `volpre6m`, `milliq`
- **Definition**: Size factor adjusted for trading liquidity to identify small caps that are tradable
- **Why This Feature**: Small cap premium disappears if liquidity costs exceed return premium
- **Logical Meaning**: Large values indicate small size with adequate liquidity for institutional sizing
- **is filling nan necessary**: Yes, use `ts_backfill()` for volume data
- **Directionality**: Higher values indicate exploitable small-cap opportunities
- **Boundary Conditions**: Very low liquidity makes theoretical premium unrealizable
- **Implementation Example**: `divide(reverse({nlmktcap}), add({visiratio}, {volpre6m}))`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Economic Value Added Spread
- **Sample Fields Used**: `roic`, `fcfroi`, `ocfroi`, `susgrowth`
- **Definition**: Core economic profitability exceeding reinvestment requirements, the essence of value creation
- **Why This Feature**: True alpha comes from companies earning returns above their cost of capital sustainably
- **Logical Meaning**: Measures genuine economic profit generation ability independent of accounting choices
- **is filling nan necessary**: No, inability to calculate ROIC indicates financial/insurance firms requiring different models
- **Directionality**: Higher values indicate durable competitive advantages and economic moats
- **Boundary Conditions**: Extreme values attract competition; sustainability depends on `susgrowth`
- **Implementation Example**: `subtract({roic}, {susgrowth})`

**Concept**: Information Asymmetry Index
- **Sample Fields Used**: `skew90drtn`, `skew90cortn`, `fc_stdevfy1epsp`, `milliq`
- **Definition**: Composite of return skewness, estimate dispersion, and illiquidity capturing information uncertainty
- **Why This Feature**: Markets compensate investors for bearing information risk; this quantifies that risk
- **Logical Meaning**: High values indicate high information asymmetry between insiders/institutions and public markets
- **is filling nan necessary**: Yes, use `group_mean()` for missing skewness within size deciles
- **Directionality**: Higher values indicate higher required risk premium (potential higher returns)
- **Boundary Conditions**: Extreme asymmetry may indicate distress or fraud risk rather than opportunity
- **Implementation Example**: `multiply({skew90drtn}, add({fc_stdevfy1epsp}, {milliq}))`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Analyst estimate fields (`fc_*`) have ~75-85% coverage vs. market data at ~99%
- **Timeliness**: Model data has delay=1, ensuring no look-ahead bias in estimates
- **Accuracy**: Industry-relative metrics assume correct GICS/sector classifications; verify with `indrelcroe`
- **Potential Biases**: Small-cap stocks in Canadian market have thinner analyst coverage; features using `fc_numest` should be coverage-filtered

### Computational Complexity
- **Lightweight features**: Simple ratios using `divide`, `multiply`, `add` (e.g., Value combinations)
- **Medium complexity**: Time-series operations like `ts_corr`, `ts_mean` (e.g., Stability features)
- **Heavy computation**: Cross-sectional `quantile` operations with multiple inputs; consider `ts_decay_linear` for smoothing

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Risk-Adjusted Value Momentum** - combines proven factors with risk filter
2. **Cash Flow Trajectory Divergence** - captures quality dimension often missed by earnings-only models
3. **Analyst Conviction-Weighted Growth** - utilizes unique estimate dispersion data in dataset

**Tier 2 (Secondary Priority)**:
1. **Earnings Estimate Stability Score** - contrarian play on analyst overconfidence
2. **Capital Structure Flexibility** - mean-reversion on market/book leverage gaps
3. **Multi-Horizon Momentum Accumulation** - robust momentum definition

**Tier 3 (Requires Further Validation)**:
1. **Information Asymmetry Index** - requires validation of premium capture vs. distress risk
2. **Reinvestment Accumulation Efficiency** - sensitive to ROIC calculation methodology variations

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. What is the correlation structure between Module 1 and Module 2 fields? Do they provide independent information or redundant signals?
2. How do Canadian-specific accounting standards (IFRS vs. US GAAP differences) affect accruals (`ttmaccu`) comparability?
3. What is the optimal holding period for features based on estimate revisions given the delay=1 constraint?

### Recommended Additional Data:
- Canadian dollar strength/weakness to adjust for commodity exporter sensitivity
- TSX sector indices for more granular industry-neutral calculations
- Options implied volatility surfaces for alternative risk measures

### Assumptions to Challenge:
- That 5-year historical relatives (`rel5y*`) are stationary; structural shifts (commodity supercycles) may invalidate this
- That industry classifications remain stable; reclassifications create look-ahead bias
- That analyst estimates are unbiased; Canadian banking oligopoly may create systematic optimism in certain sectors

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence across 253 fields per module
2. Question-driven feature generation (8 fundamental questions)
3. Logical validation of each feature concept against economic theory
4. Transparent documentation of reasoning and implementation constraints

**Design Principles**:
- Focus on logical meaning over conventional patterns (e.g., cash flow > earnings emphasis)
- Every feature answers a specific investment question (value, momentum, quality, risk)
- Explicit handling of NaN values based on economic meaning of missingness
- Emphasis on Canadian market specificity (commodity sensitivity, banking concentration)

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate assumptions, gather additional data as needed*