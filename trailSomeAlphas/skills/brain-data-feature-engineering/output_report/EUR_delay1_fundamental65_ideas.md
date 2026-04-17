# Fundamental65 (Factor Ratios and Rank Model) Feature Engineering Analysis Report

**Dataset**: fundamental65
**Region**: EUR
**Delay**: 1


**Dataset**: fundamental65
**Category**: Model
**Region**: EUR
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 665

---

## Executive Summary

**Primary Question Answered by Dataset**: This dataset provides comprehensive raw fundamental ratios and pre-computed percentile ranks (1-100) for European equities, enabling cross-sectional valuation, quality, growth, and risk analysis with both absolute and relative (industry-neutral) metrics.

**Key Insights from Analysis**:
- Dual universe structure (All Cap vs. Developed) allows for cross-universe arbitrage and liquidity-adjusted signals
- Extensive forward-looking analyst data (FY1/FY2 estimates, revisions, dispersion) contrasts with trailing-twelve-month (TTM) fundamentals, creating rich convergence/divergence opportunities
- Pre-computed 5-year historical relative metrics (rel5y*) and industry-relative metrics (curind*) enable sophisticated neutralization strategies out-of-the-box
- Rank data (1-100) alongside raw ratios supports both linear and non-linear (ordinal) modeling approaches
- Comprehensive risk metrics spanning beta, volatility, skewness, and macro-factor exposures provide multi-dimensional risk decomposition

**Critical Field Relationships Identified**:
- Forward Estimate Dispersion (`fc_stdevfy1epsp`) vs. Realized Earnings Surprise (`surp`): High dispersion predicts larger surprise volatility
- Trailing ROIC (`roic`) vs. Industry-Relative Valuation (`curindbp_`): Measures value captured by profitability advantage
- Price Momentum (`actrtn12m`) vs. Fundamental Momentum (`chg3yepsp`): Divergence indicates potential value gaps or traps

**Most Promising Feature Concepts**:
1. **Analyst Uncertainty Normalization** - Dispersion scaled by coverage (`fc_stdevfy1epsp` / `fc_numest`) distinguishes true uncertainty from sparse data noise
2. **Quality-Adjusted Industry Value** - Combining industry-relative book-to-price (`curindbp_`) with accruals (`aspanratio`) identifies "true" value vs. accounting distortions
3. **Earnings Revision Acceleration** - Second derivative of estimate changes (`fc_rev3y1` momentum) captures inflection points before price adjusts

---

## Dataset Deep Understanding

### Dataset Description
Fundamental65 provides a global time series of raw factor ratios and their corresponding ranks (1-100) used in equity factor models. The dataset covers two sub-universes (All Cap and Developed) with 665 fields spanning valuation, profitability, growth, quality, risk, and analyst expectations. Ranks are computed by sorting raw ratios and assigning percentiles (1=best, 100=worst) within the specified universe. The EUR region coverage begins 01/01/2013 with monthly updates and delay=1 availability.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `fnd65_allcap_sedol_52whigh` | 52-week high proximity ratio | Float64 | Monthly | ~98% |
| `fnd65_allcap_sedol_fc_stdevfy1epsp` | FY1 EPS forecast std dev / price | Float64 | Monthly | ~75% |
| `fnd65_allcap_sedol_aspanratio` | Accruals (change in net operating assets) | Float64 | Quarterly | ~95% |
| `fnd65_allcap_sedol_rel5ybp` | Current BP minus 5Y average (normalized) | Float64 | Monthly | ~98% |
| `fnd65_allcap_sedol_curindbp_` | Industry-relative book-to-price Z-score | Float64 | Monthly | ~98% |
| `fnd65_allcap_sedol_roic` | Return on invested capital (TTM) | Float64 | Quarterly | ~92% |
| `fnd65_allcap_sedol_slope4qeps5y` | 5-year earnings trend slope | Float64 | Monthly | ~85% |
| `fnd65_allcap_sedol_twepsrev` | Time-weighted EPS revision (FY1+FY2) | Float64 | Monthly | ~72% |
| `fnd65_allcap_sedol_beta` | Adjusted 60-month beta | Float64 | Monthly | ~99% |
| `fnd65_allcap_sedol_fc_ebop` | Edwards-Bell-Ohlson intrinsic value / price | Float64 | Monthly | ~68% |

*(Additional 655 fields covering similar categories)*

### Field Deconstruction Analysis

#### `fnd65_allcap_sedol_52whigh`: 52-Week High Proximity
- **What is being measured?**: Anchoring bias and momentum persistence through price proximity to 12-month highs
- **How is it measured?**: Month-end price divided by maximum monthly closing price over trailing 12 months
- **Time dimension**: Rolling 12-month lookback, monthly resolution
- **Business context**: Behavioral finance metric identifying stocks breaking out or breaking down from long-term ranges; used for momentum and contrarian strategies
- **Generation logic**: Mechanical calculation from price time-series; robust but affected by corporate actions and splits
- **Reliability considerations**: High reliability for liquid stocks; potential stale pricing for illiquid small-caps; rank transformation (1-100) reduces outlier impact

#### `fnd65_allcap_sedol_fc_stdevfy1epsp`: Analyst Forecast Dispersion
- **What is being measured?**: Consensus uncertainty or disagreement among analysts regarding FY1 earnings
- **How is it measured?**: Standard deviation of analyst EPS forecasts divided by current stock price
- **Time dimension**: Point-in-time snapshot of current consensus
- **Business context**: Proxy for information uncertainty; high dispersion predicts higher future volatility and potential earnings surprises
- **Generation logic**: Derived from IBES-style analyst estimate aggregations; requires minimum analyst coverage to be meaningful
- **Reliability considerations**: Sparse coverage (`fc_numest` < 3) creates noisy estimates; cross-sectional variation in coverage requires normalization for comparability

#### `fnd65_allcap_sedol_aspanratio`: Operating Accruals Intensity
- **What is being measured?**: Change in net operating assets as proxy for earnings quality and accounting accruals (Sloan anomaly)
- **How is it measured?**: (Operating Assets - Operating Liabilities) deflated by lagged total assets
- **Time dimension**: Quarterly change, cumulative TTM basis
- **Business context**: High accruals indicate less persistent earnings and predict lower future returns; separates cash-based vs. accounting-based earnings
- **Generation logic**: Balance sheet and income statement derivation; sensitive to working capital management changes and M&A activity
- **Reliability considerations**: Industry-dependent baselines require cross-sectional neutralization; one-time working capital shifts create transients

### Field Relationship Mapping

**The Story This Data Tells**:
This dataset narrates the tension between market expectations (analyst forecasts, price momentum) and fundamental reality (accounting earnings, cash flows, capital structure). It tracks how efficiently companies convert assets into profits (ROIC, asset turnover), how markets price these fundamentals (valuation ratios), and how expectations evolve (revision metrics). The dual presence of raw ratios and ranks captures both the magnitude and relative positioning of these characteristics.

**Key Relationships Identified**:
1. **Expectations vs. Reality**: Forward estimates (`fc_estep`, `fc_fwdroe`) vs. trailing actuals (`roic`, `roe`) creates earnings gaps that predict revision momentum
2. **Quality vs. Value**: Accruals (`aspanratio`, `ttmaccu`) interact with valuation (`pb`, `pe_wt`) to identify "cheap for a reason" vs. quality value traps
3. **Risk-Adjusted Return**: Alpha generation (`alpha60m`, `rationalalpha`) decomposed into systematic (`beta`, `sigma`) and idiosyncratic (`varresirtn`) components
4. **Capital Structure Efficiency**: Debt levels (`ad`, `netdebt`) relative to coverage (`ebitdadebt`, `cfleverage`) indicate financial flexibility constraints

**Missing Pieces That Would Complete the Picture**:
- Short interest data to measure negative sentiment extremes
- ESG metrics for sustainability-adjusted quality factors
- Options market implied volatility for forward-looking risk measures
- Real-time news sentiment for event-driven adjustments to analyst forecasts

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: Valuation Regime Stability Score
- **Sample Fields Used**: {sedol_rel5ybp}, {sedol_rel5yep}, {sedol_rel5ysp}
- **Definition**: Coefficient of variation of historical relative valuation metrics over 5-year window to identify stocks trading within stable valuation bands versus those undergoing structural re-rating
- **Why This Feature**: Stocks with stable historical valuation ranges exhibit stronger mean-reversion predictability, while high instability suggests fundamental business model changes or persistent sentiment shifts
- **Logical Meaning**: Measures the "stickiness" of market valuation multiples; low values indicate consensus on appropriate pricing level, high values indicate disagreement or transition
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Low values (stable) predict mean-reversion; high values predict momentum continuation
- **Boundary Conditions**: Near-zero values indicate illiquid/no-change stocks; extremely high values indicate recent IPOs or distressed restructuring
- **Implementation Example**: `divide(ts_std_dev({sedol_rel5ybp}, 252), abs(ts_mean({sedol_rel5ybp}, 252)))`

**Concept**: Earnings Predictability Index
- **Sample Fields Used**: {sedol_fc_stdevfy1epsp}, {sedol_fc_numest}, {sedol_spe1yfvc_cf}
- **Definition**: Analyst forecast dispersion normalized by the log of coverage count to distinguish between genuine uncertainty (high dispersion, high coverage) and data sparsity noise (high dispersion, low coverage)
- **Why This Feature**: Raw dispersion conflates uncertainty with lack of analyst following; this adjustment isolates the information content of disagreement
- **Logical Meaning**: Measures the precision of information environment; lower values indicate more predictable earnings streams and efficient information dissemination
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Lower values predict lower future volatility and more accurate price discovery; very high values predict earnings surprises and potential volatility
- **Boundary Conditions**: Stocks with zero coverage require special handling; extreme values (>5) indicate potential distress or turnaround situations
- **Implementation Example**: `divide({sedol_fc_stdevfy1epsp}, log(add(1, {sedol_fc_numest})))`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Earnings Revision Acceleration
- **Sample Fields Used**: {sedol_fc_rev3y1}, {sedol_fc_rev6}, {sedol_mrspe_cf}
- **Definition**: Second derivative of analyst estimate changes measuring whether revision momentum is increasing (accelerating) or decreasing (decelerating)
- **Why This Feature**: First derivative (revision level) is widely known; second derivative captures inflection points before they are fully priced, identifying early-stage sentiment shifts
- **Logical Meaning**: Positive acceleration indicates strengthening business momentum likely to persist; negative acceleration suggests peak earnings or analyst herding reversal
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Positive acceleration predicts positive returns; negative acceleration predicts negative returns or volatility expansion
- **Boundary Conditions**: Extreme values may indicate one-time events (M&A, divestitures) rather than organic trend changes
- **Implementation Example**: `ts_delta({sedol_fc_rev3y1}, 63)`

**Concept**: Fundamental-Price Divergence Gap
- **Sample Fields Used**: {sedol_chg3yepsp}, {sedol_actrtn12m}, {sedol_cg3ysales}
- **Definition**: Difference between 3-year earnings growth trajectory and 12-month price performance to identify value gaps where fundamentals improve but price stagnates
- **Why This Feature**: Market inefficiencies often manifest as lag between fundamental improvement and price recognition; this quantifies the dislocation magnitude
- **Logical Meaning**: Positive divergence (earnings up, price down/sideways) suggests undervaluation; negative divergence suggests overvaluation or quality deterioration not yet recognized in earnings
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: High positive values predict mean-reversion upward; high negative values predict corrections
- **Boundary Conditions**: Extreme positive values may indicate value traps (earnings growing into deteriorating moats); requires quality overlay
- **Implementation Example**: `subtract({sedol_chg3yepsp}, {sedol_actrtn12m})`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Accrual Anomaly Intensity
- **Sample Fields Used**: {sedol_aspanratio}, {sedol_ttmaccu}, {sedol_yoychgaa}
- **Definition**: Composite accruals measure normalized by historical volatility to identify extreme earnings quality deviations from firm-specific baselines
- **Why This Feature**: Sloan (1996) accrual anomaly persists; standardizing by historical volatility distinguishes between normal seasonal accrual fluctuations and genuine accounting red flags
- **Logical Meaning**: Extreme positive values indicate low earnings quality (high accruals) predicting future earnings declines; extreme negative values indicate unusually conservative accounting or cash flow acceleration
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: High values predict negative future returns; low values predict positive drift as earnings prove more persistent than market expects
- **Boundary Conditions**: Financial sector and utility companies have naturally high accruals; industry neutralization essential
- **Implementation Example**: `divide(ts_av_diff({sedol_aspanratio}, 252), ts_std_dev({sedol_aspanratio}, 252))`

**Concept**: Earnings Surprise Volatility Regime
- **Sample Fields Used**: {sedol_fc_fqsurstd}, {sedol_surp}, {sedol_fqsurstd60dlag}
- **Definition**: Standardized unexpected earnings volatility relative to trailing 60-day lagged surprise patterns to detect regime changes in earnings predictability
- **Why This Feature**: Stocks exhibiting unusual earnings surprise patterns (vs. their own history) indicate changing business volatility or information environment shifts
- **Logical Meaning**: Deviations from historical surprise volatility indicate regime changes; sudden increases suggest business model instability or increased competition
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Increasing surprise volatility predicts higher future stock volatility and potential analyst coverage expansion/contraction
- **Boundary Conditions**: First-quarter earnings after IPOs or post-merger create structural breaks requiring censoring
- **Implementation Example**: `divide(abs(subtract({sedol_fc_fqsurstd}, ts_mean({sedol_fqsurstd60dlag}, 252))), ts_std_dev({sedol_fqsurstd60dlag}, 252))`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Quality-Adjusted Industry Value Spread
- **Sample Fields Used**: {sedol_curindbp_}, {sedol_aspanratio}, {sedol_curindep_}
- **Definition**: Industry-relative book-to-price adjusted by accrual quality percentile to identify "true" value stocks after accounting for earnings manipulation risk
- **Why This Feature**: Value strategies fail when buying artificially cheap stocks with poor earnings quality; this interaction filters out value traps by requiring low accruals
- **Logical Meaning**: High adjusted value indicates cheap stocks with clean accounting (quality value); low values indicate expensive or manipulative accounting stocks
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Higher values predict value premium with reduced drawdowns; negative values predict growth traps or accounting red flags
- **Boundary Conditions**: Requires careful handling when accruals are undefined (financial companies)
- **Implementation Example**: `multiply({sedol_curindbp_}, subtract(1, ts_quantile({sedol_aspanratio}, 252)))`

**Concept**: GARP Efficiency Ratio
- **Sample Fields Used**: {sedol_cg3ysales}, {sedol_pe_wt}, {sedol_cg3yroic}, {sedol_mpg}
- **Definition**: 3-year geometric growth rate (sales and ROIC) normalized by time-weighted forward P/E to measure growth generation efficiency per unit of valuation paid
- **Why This Feature**: Pure growth or pure value misses the intersection; this combines both in a single efficiency metric similar to PEG but with fundamental growth drivers
- **Logical Meaning**: Higher ratios indicate "cheaper" growth (more growth per P/E unit); lower ratios indicate expensive growth or value traps with declining fundamentals
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Higher values predict outperformance in growth-rotation regimes; very low values predict multiple compression
- **Boundary Conditions**: Negative earnings or growth rates create sign flips; requires winsorization at extremes
- **Implementation Example**: `divide(multiply({sedol_cg3ysales}, {sedol_cg3yroic}), {sedol_pe_wt})`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Capital Structure Stability Index
- **Sample Fields Used**: {sedol_ad}, {sedol_netdebt}, {sedol_mktlev}, {sedol_ed}
- **Definition**: Deviation from historical median capital structure measuring financial policy stability versus aggressive leveraging/deleveraging cycles
- **Why This Feature**: Stable capital structures indicate mature financial management and predictable cash flows; extreme deviations may signal M&A activity or distress
- **Logical Meaning**: Absolute distance from median leverage indicates stability; moderate levels optimal for tax shields without distress risk
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Moderate values predict stability; extreme high values predict distress or over-leverage; extreme low values suggest under-optimization or cash accumulation for M&A
- **Boundary Conditions**: Financial and REIT sectors have structurally different leverage; industry-relative version preferred
- **Implementation Example**: `abs(subtract({sedol_ad}, ts_median({sedol_ad}, 252)))`

**Concept**: Asset Composition Efficiency Shift
- **Sample Fields Used**: {sedol_astcomp}, {sedol_invast}, {sedol_chginvavgast}, {sedol_chg3yocfast}
- **Definition**: Change in operating cash flow efficiency relative to shifts in asset composition (current vs. fixed assets) to detect business model transitions
- **Why This Feature**: Structural shifts between asset-light and asset-heavy models affect capital intensity and ROIC persistence; this captures the efficiency of the transition
- **Logical Meaning**: Improving cash flow generation despite increasing asset intensity indicates pricing power; declining efficiency with asset-light shift indicates competitive pressure
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Positive values indicate successful operational leverage; negative values indicate diseconomies of scale
- **Boundary Conditions**: Requires 3-year history for valid asset change measurement
- **Implementation Example**: `divide({sedol_chg3yocfast}, add({sedol_astcomp}, 0.01))`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Long-term Earnings Information Ratio
- **Sample Fields Used**: {sedol_slope4qeps5y}, {sedol_y5speq4rqsr}, {sedol_aspemtty3gc}, {sedol_y5speq4vc}
- **Definition**: 5-year earnings trend slope divided by earnings volatility to measure persistence of growth per unit of uncertainty (Sharpe-like ratio for fundamentals)
- **Why This Feature**: Distinguishes between high-growth cyclicals (volatile) and steady compounders (persistent); investors overpay for volatile growth
- **Logical Meaning**: High values indicate quality growth with low uncertainty (compounding machines); low values indicate cyclical or speculative growth
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Higher ratios predict defensive growth characteristics and lower drawdowns during corrections
- **Boundary Conditions**: Negative slopes create negative values; requires sign handling for interpretation
- **Implementation Example**: `divide({sedol_slope4qeps5y}, add({sedol_y5speq4vc}, 0.001))`

**Concept**: Accumulated Analyst Revision Pressure
- **Sample Fields Used**: {sedol_twepsrev}, {sedol_twepsstdrev}, {sedol_ratrev6m}
- **Definition**: Time-weighted accumulation of analyst revisions over 6-month window to capture persistent sentiment pressure versus transient estimate changes
- **Why This Feature**: Single-month revisions may be noise; cumulative pressure indicates sustained information flow or changing consensus
- **Logical Meaning**: Positive accumulation indicates sustained upward pressure likely to continue; near-zero indicates lack of catalyst or information
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Positive values predict upward price drift; negative values predict downgrades and underperformance
- **Boundary Conditions**: Earnings announcement periods create spikes requiring decay weighting
- **Implementation Example**: `ts_sum({sedol_twepsrev}, 126)`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Multi-Factor Industry Z-Score Composite
- **Sample Fields Used**: {sedol_curindbp_}, {sedol_curindep_}, {sedol_curindsp_}, {sedol_curindcfp_}
- **Definition**: Average of industry-relative valuation Z-scores across book, earnings, sales, and cash flow to identify stocks cheap on multiple dimensions simultaneously
- **Why This Feature**: Single-metric value can be distorted by sector-specific accounting (e.g., depreciation policies affecting EPS but not sales); composite reduces noise
- **Logical Meaning**: More negative values indicate deeper relative value; positive values indicate premium pricing across all metrics
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Lower (more negative) values predict mean-reversion outperformance within industries
- **Boundary Conditions**: Missing data in any metric biases composite; equal weighting vs. optimized weighting trade-offs
- **Implementation Example**: `divide(add(add({sedol_curindbp_}, {sedol_curindep_}), add({sedol_curindsp_}, {sedol_curindcfp_})), 4)`

**Concept**: Beta Regime Divergence
- **Sample Fields Used**: {sedol_beta}, {sedol_sigma}, {sedol_alpha60m}, {sedol_rerror60m}
- **Definition**: Current beta relative to historical average to identify stocks changing their systematic risk characteristics (defensive rotation or speculative acceleration)
- **Why This Feature**: Beta instability affects portfolio risk management; stocks with declining beta during high volatility indicate flight-to-quality or idiosyncratic drivers
- **Logical Meaning**: Increasing beta indicates increasing market sensitivity (cyclicality); decreasing beta indicates decoupling or defensive transition
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Beta expansion predicts higher volatility participation; beta contraction predicts defensive characteristics
- **Boundary Conditions**: Estimation error in beta (`rerror60m`) must be considered; low R-squared betas are unreliable
- **Implementation Example**: `subtract({sedol_beta}, ts_mean({sedol_beta}, 252))`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Economic Moat Sustainability Score
- **Sample Fields Used**: {sedol_roic}, {sedol_cg3yroic}, {sedol_susgrowth}, {sedol_nopatmargin}
- **Definition**: Return on invested capital interacted with sustainable growth rate to identify companies generating excess returns with reinvestment opportunities (Buffett-style moats)
- **Why This Feature**: ROIC alone is static; combining with sustainable growth captures the magnitude and duration of competitive advantage
- **Logical Meaning**: High values indicate wide moats with profitable reinvestment; low values indicate no-moat or declining advantage businesses
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: High values predict long-term wealth creation; declining values predict commoditization
- **Boundary Conditions**: High ROIC with zero growth indicates cash cows; negative values indicate value destruction
- **Implementation Example**: `multiply({sedol_roic}, {sedol_susgrowth})`

**Concept**: Intrinsic Value Convergence Potential
- **Sample Fields Used**: {sedol_fc_ebop}, {sedol_pb}, {sedol_grahamnum}, {sedol_pvan}
- **Definition**: Ratio of model-based intrinsic value estimates (EBO, Graham Number) to current price metrics to identify stocks with largest theoretical value gaps
- **Why This Feature**: Multiple valuation models converging on undervaluation provides stronger signal than any single metric; represents first-principles value investing
- **Logical Meaning**: Values > 1 indicate undervaluation; values < 1 indicate overvaluation relative to conservative intrinsic value estimates
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
- **Directionality**: Higher values predict mean-reversion toward intrinsic value; very low values predict growth optionality or value traps
- **Boundary Conditions**: Negative book values or earnings create undefined ratios; financial companies require model adjustments
- **Implementation Example**: `divide({sedol_fc_ebop}, {sedol_pb})`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Analyst forecast fields (`fc_*`) have ~70-75% coverage vs. ~95%+ for accounting fundamentals; composite features must handle mixed coverage gracefully
- **Timeliness**: Monthly updates with delay=1 mean features are tradable at month-end; intramonth signals require price data overlay
- **Accuracy**: Pre-computed ranks (1-100) handle outliers but lose granularity at extremes; raw ratios preferred for continuous modeling
- **Potential Biases**: Survivorship bias minimized by including delisted stocks in historical calculations; look-ahead bias prevented by strict delay=1 enforcement

### Computational Complexity
- **Lightweight features**: Single-field transformations, simple ratios (`divide`, `subtract`) - suitable for high-frequency refresh
- **Medium complexity**: 1-year time series operations (`ts_mean`, `ts_std_dev`, `ts_sum`) - standard computational load
- **Heavy computation**: 5-year rolling windows (`slope4qeps5y`, `rel5y*` calculations) with cross-sectional rankings - require caching and incremental updates

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Quality-Adjusted Industry Value Spread** - Combines two proven anomalies (value + quality) with industry neutralization; robust across market regimes
2. **Earnings Revision Acceleration** - Captures high-frequency information diffusion; strong in European markets with monthly reporting delays
3. **Analyst Uncertainty Normalization** - Addresses data sparsity issue common in European small-caps; improves forecast precision

**Tier 2 (Secondary Priority)**:
1. **Long-term Earnings Information Ratio** - Distinguishes cyclical vs. secular growth; essential for drawdown control
2. **Accrual Anomaly Intensity** - Classic Sloan anomaly with volatility adjustment; works best when combined with industry neutralization
3. **Multi-Factor Industry Z-Score** - Diversifies single-metric value risk; reduces sector concentration

**Tier 3 (Requires Further Validation)**:
1. **Beta Regime Divergence** - Beta instability predictive power varies with volatility regime; requires market-timing overlay
2. **Intrinsic Value Convergence** - Model-dependent (EBO assumptions); requires sensitivity analysis to discount rate assumptions

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How does the dual universe structure (All Cap vs. Developed) interact with signal decay? Do All Cap signals lead Developed signals due to liquidity premia?
2. What is the optimal decay function for analyst revision features (`twepsrev`) given European reporting seasonality (concentrated in Q1/Q3)?
3. Do macro-factor exposures (`inflation`, `oilprice`, `pi`, `prc`) predict factor performance rotation in European markets (e.g., value vs. growth during inflation regimes)?

### Recommended Additional Data:
- **Short interest data** (borrow costs, utilization) to identify crowded short positions that may amplify mean-reversion in accrual anomalies
- **ESG ratings** to test whether quality factors (`aspanratio`, `roic`) are capturing ESG risks not priced in traditional metrics
- **Options implied volatility** to compare with historical realized (`sigma`) for volatility risk premium extraction

### Assumptions to Challenge:
- **Industry classification stability**: Current industry-relative metrics assume static GICS/ICB classifications; how do classification changes affect historical Z-scores?
- **Accounting harmonization**: Do International Accounting Standards (IFRS) adoption differences across European countries create measurement error in accruals (`ttmaccu`)?
- **Analyst coverage bias**: Are `fc_numest` and dispersion metrics biased toward larger, more liquid stocks, creating survivorship in prediction models?

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence (valuation multiples vs. growth metrics vs. risk measures)
2. Question-driven feature generation (8 fundamental questions) applied to fundamental ratio relationships
3. Logical validation of each feature concept against known factor anomalies (Sloan accruals, GARP, earnings revisions)
4. Transparent documentation of reasoning with explicit handling of European market microstructure (delay=1, monthly reporting)

**Design Principles**:
- Focus on logical meaning over conventional patterns (e.g., second derivative of revisions vs. simple revision level)
- Every feature answers a specific investment question (stability, change, anomaly detection)
- Clear documentation of "why" for each suggestion with directionality and boundary conditions
- Emphasis on data understanding over prediction (focusing on economic mechanisms)

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate assumptions regarding industry classifications, gather additional short interest data as recommended*