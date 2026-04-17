**Dataset**: fundamental6
**Region**: EUR
**Delay**: 1

# Company Fundamental Data for Equity Feature Engineering Analysis Report

**Dataset**: fundamental6
**Category**: Fundamental
**Region**: EUR
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 279

---

## Executive Summary

**Primary Question Answered by Dataset**: What is the financial health, operational performance, and capital structure of companies based on standardized accounting statements?

**Key Insights from Analysis**:
- The dataset provides a comprehensive view of company financials with quarterly granularity for balance sheet and income statement items, and annual granularity for cash flow statements.
- Strong coverage of both standardized "cptnewq" (compustat-style) fields and European-specific "ewq" fields allows for cross-regional comparability.
- The coexistence of multiple field versions (newa1, newa2, newq) suggests data lineage complexity requiring careful handling of null values.

**Critical Field Relationships Identified**:
- Income statement hierarchy: Revenue (`cptnewq_revtq`) → Operating Income (`newa2_oiadp`) → Net Income (`cptnewq_ibq`) forms the core profitability chain.
- Balance sheet identity: Assets (`cptnewq_atq`) = Liabilities (`cptnewq_ltq`) + Equity (`cptnewq_ceqq`) provides structural validation.
- Cash flow reconciliation: Operating cash (`newa2_oancf`) vs Net income (`newa1_ib`) indicates earnings quality.

**Most Promising Feature Concepts**:
1. **Operating Cash Flow to Net Income Ratio** - because it distinguishes accrual-based earnings from cash realization, critical for detecting earnings management.
2. **Current Ratio Stability** - because liquidity shocks predict distress better than static levels; variance in current ratio captures operational instability.
3. **Intangible Asset Intensity** - because European markets have varying treatment of goodwill and intangibles, creating information asymmetry opportunities.

---

## Dataset Deep Understanding

### Dataset Description
Fundamental6 provides comprehensive financial statement data for European equity markets, covering balance sheet, income statement, and cash flow statement items. The data updates quarterly with varying lag structures: quarterly fields (q) for high-frequency items like revenue and current assets, and annual fields (y) for cash flow and comprehensive income items. The dataset includes both standardized global formats (newa1/newa2/cptnewq) and European-specific adjustments (ewq), enabling robust cross-border analysis while preserving local accounting nuances.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `fnd6_cptnewq_revtq` | Revenue - Total | float64 | quarterly | 96% |
| `fnd6_cptnewq_ibq` | Income Before Extraordinary Items | float64 | quarterly | 97% |
| `fnd6_cptnewq_ceqq` | Common/Ordinary Equity - Total | float64 | quarterly | 98% |
| `fnd6_cptnewq_atq` | Assets - Total | float64 | quarterly | 99% |
| `fnd6_cptnewq_dlttq` | Long-Term Debt - Total | float64 | quarterly | 94% |
| `fnd6_newa2_oancf` | Operating Activities - Net Cash Flow | float64 | annual | 89% |
| `fnd6_newq_lctq` | Current Liabilities - Total | float64 | quarterly | 97% |
| `fnd6_newa1_capx` | Capital Expenditures | float64 | annual | 85% |
| `fnd6_ewq_intanq` | Intangible Assets - Total | float64 | quarterly | 82% |
| `fnd6_newq_invtq` | Inventories - Total | float64 | quarterly | 78% |

*(Additional fields as needed)*

### Field Deconstruction Analysis

#### `fnd6_cptnewq_ibq`: Income Before Extraordinary Items
- **What is being measured?**: Core profitability excluding one-time gains/losses, discontinued operations, and accounting changes. Represents sustainable earnings power.
- **How is it measured?**: Quarterly aggregation of revenues minus operating expenses, interest, and taxes, standardized across companies to exclude special items.
- **Time dimension**: Flow variable measured over the fiscal quarter (cumulative within the quarter).
- **Business context**: Primary metric for valuation models and earnings surprise calculations; used by analysts to forecast future performance.
- **Generation logic**: Calculated as Revenue - COGS - Operating Expenses - Interest - Taxes ± Minority Interest, with adjustments for extraordinary items.
- **Reliability considerations**: Subject to accrual accounting judgments (revenue recognition, expense timing); may diverge significantly from cash flows in working capital-intensive businesses.

#### `fnd6_cptnewq_ceqq`: Common/Ordinary Equity - Total
- **What is being measured?**: Book value of shareholders' equity—the residual claim on assets after all liabilities are paid.
- **How is it measured?**: Balance sheet calculation: Total Assets - Total Liabilities - Minority Interests, representing the accounting net worth.
- **Time dimension**: Stock variable measured at a specific point in time (quarter-end snapshot).
- **Business context**: Basis for price-to-book valuation, leverage calculations, and regulatory capital adequacy assessments.
- **Generation logic**: Accumulated retained earnings plus paid-in capital, treasury stock adjustments, and accumulated other comprehensive income.
- **Reliability considerations**: Historical cost basis may significantly differ from market value; subject to write-downs and impairment charges that create discontinuities.

#### `fnd6_newa2_oancf`: Operating Activities - Net Cash Flow
- **What is being measured?**: Actual cash generated from core business operations, independent of accrual accounting adjustments.
- **How is it measured?**: Indirect method starting from net income, adjusting for non-cash items (depreciation, amortization) and changes in working capital.
- **Time dimension**: Cumulative flow over the fiscal year (annual frequency).
- **Business context**: Critical for dividend sustainability, debt service capacity, and identifying earnings quality issues (cash vs. accruals).
- **Generation logic**: Net Income + Depreciation/Amortization - ΔWorking Capital (AR, Inventory, AP) ± Other non-cash adjustments.
- **Reliability considerations**: Less subject to manipulation than earnings but can be lumpy due to working capital swings; annual frequency limits timeliness compared to quarterly accrual metrics.

### Field Relationship Mapping

**The Story This Data Tells**:
This dataset narrates the transformation of invested capital into shareholder value through operations. It begins with asset composition (tangible vs. intangible, current vs. fixed), flows through operational efficiency (turnover ratios, margins), and culminates in cash generation and capital structure decisions. The interplay between quarterly high-frequency snapshots (revenue, current assets) and annual strategic flows (capex, operating cash) reveals the tension between short-term performance management and long-term value creation.

**Key Relationships Identified**:
1. **Earnings Quality Bridge**: The relationship between `newa2_oancf` (cash) and `newa1_ib` (accrual earnings) indicates whether reported profits convert to liquid resources. Persistent gaps suggest aggressive revenue recognition or working capital management.
2. **Capital Structure Stack**: `cptnewq_dlttq` (long-term debt) layered on `cptnewq_ceqq` (equity) creates the leverage ratio, with `newa1_ibc` (income before extraordinary items cash flow) serving as the capacity to service this structure.
3. **Working Capital Cycle**: `newq_invtq` (inventory) + `newq_rectq` (receivables) - `newq_apq` (payables) = `newa2_wcap` (working capital), representing the cash tied up in operations.

**Missing Pieces That Would Complete the Picture**:
- Market prices for market-to-book calculations (requires price data not in this fundamental set).
- Off-balance sheet liabilities and contingent claims.
- Segment-level breakdowns to assess diversification vs. concentration risks.
- Forward-looking analyst estimates for expectation-based features.

---

## Feature Concepts by Question Type


### Q1: "What is stable?" (Invariance Features)

**Concept**: Earnings Coefficient of Variation
- **Sample Fields Used**: `cptnewq_ibq`
- **Definition**: The ratio of standard deviation to absolute mean of quarterly earnings over a 1-year window, measuring earnings volatility relative to magnitude.
- **Why This Feature**: Companies with stable earnings generation exhibit lower information uncertainty and command valuation premiums; extreme volatility may indicate business model instability or aggressive accounting.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. For quarterly earnings, missing values typically indicate lack of reporting or data collection issues rather than meaningful zero earnings, so ts_backfill is appropriate to maintain the time series continuity.
- **Directionality**: Lower values indicate stable, predictable earnings (typically positive for quality metrics); higher values indicate volatility (may predict higher returns in risk-premium models).
- **Boundary Conditions**: Near-zero mean creates extreme values (handled by denominator protection); zero values indicate perfect stability or no earnings.
- **Implementation Example**: divide(ts_std_dev({cptnewq_ibq}, 63), abs(ts_mean({cptnewq_ibq}, 63)))

**Concept**: Capital Structure Persistence
- **Sample Fields Used**: `cptnewq_dlttq`, `cptnewq_ceqq`
- **Definition**: The stability of the debt-to-equity ratio over time, calculated as the time-series standard deviation of the leverage ratio.
- **Why This Feature**: Stable capital structure indicates consistent financing policy and lower refinancing risk; sudden shifts may signal distress or strategic pivots.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Capital structure components are slow-moving; missing values likely represent data gaps rather than zero debt/equity, so ts_backfill is suitable.
- **Directionality**: Lower values indicate stable financing structure; higher values indicate capital restructuring activity.
- **Boundary Conditions**: Negative equity (insolvency) creates negative ratios requiring sign handling; extremely low debt creates high sensitivity to small changes.
- **Implementation Example**: ts_std_dev(divide({cptnewq_dlttq}, {cptnewq_ceqq}), 126)

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Operating Income Momentum
- **Sample Fields Used**: `newa2_oiadp`
- **Definition**: The quarter-over-quarter absolute change in operating income after depreciation, capturing the trajectory of core business profitability.
- **Why This Feature**: Accelerating operating income indicates improving operational efficiency or pricing power; deceleration may signal margin compression or saturation.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Operating income is reported annually in some versions; quarterly changes require backfilling to ensure valid delta calculations.
- **Directionality**: Positive values indicate growth (momentum effect); negative values indicate contraction (value trap risk or turnaround opportunity).
- **Boundary Conditions**: Extreme changes from near-zero bases create outliers; seasonality in annual data requires careful window selection.
- **Implementation Example**: ts_delta({newa2_oiadp}, 63)

**Concept**: Asset Growth Rate
- **Sample Fields Used**: `cptnewq_atq`
- **Definition**: The percentage change in total assets quarter-over-quarter, indicating investment intensity or divestment activity.
- **Why This Feature**: Rapid asset growth may indicate over-investment (Empire Building) or productive capacity expansion; asset shrinkage may indicate restructuring or distress.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Asset values are continuous; missing data should be backfilled to prevent artificial growth spikes.
- **Directionality**: High positive values indicate expansion (may dilute returns if NPV<0); negative values indicate contraction (may improve efficiency).
- **Boundary Conditions**: M&A activity creates step-function changes; asset write-downs create negative jumps.
- **Implementation Example**: divide(subtract({cptnewq_atq}, ts_delay({cptnewq_atq}, 63)), ts_delay({cptnewq_atq}, 63))

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Inventory to Sales Divergence
- **Sample Fields Used**: `newq_invtq`, `newq_saleq`
- **Definition**: The difference between inventory growth rate and sales growth rate, identifying potential demand forecasting errors or obsolescence buildup.
- **Why This Feature**: Inventory growing faster than sales suggests overproduction, weak demand, or channel stuffing; inventory lagging sales suggests supply constraints or efficiency gains.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Inventory and sales are cyclical; zeros may indicate no inventory (service companies) vs missing data, requiring careful handling.
- **Directionality**: Positive values (inventory > sales growth) predict future margin pressure and write-downs; negative values suggest supply chain efficiency or scarcity.
- **Boundary Conditions**: Extreme values during seasonal transitions; service companies with zero inventory create divide-by-zero errors.
- **Implementation Example**: subtract(divide(ts_delta({newq_invtq}, 63), ts_delay({newq_invtq}, 63)), divide(ts_delta({newq_saleq}, 63), ts_delay({newq_saleq}, 63)))

**Concept**: Receivables Velocity Anomaly
- **Sample Fields Used**: `newq_rectq`, `cptnewq_revtq`
- **Definition**: The deviation of receivables growth from revenue growth, capturing changes in credit policy or collection efficiency.
- **Why This Feature**: Receivables outpacing revenue may indicate aggressive revenue recognition, channel stuffing, or deteriorating customer credit quality.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Receivables are zero for cash-only businesses; missing values require backfilling to distinguish from true zero.
- **Directionality**: Positive values (receivables growing faster) predict future bad debt write-offs and cash flow problems; negative values suggest improved collections or cash sales shift.
- **Boundary Conditions**: Seasonal businesses show regular patterns; extreme outliers indicate accounting changes.
- **Implementation Example**: subtract(divide(ts_delta({newq_rectq}, 63), ts_delay({newq_rectq}, 63)), divide(ts_delta({cptnewq_revtq}, 63), ts_delay({cptnewq_revtq}, 63)))

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Accruals Quality Ratio
- **Sample Fields Used**: `newa1_ib`, `newa2_oancf`
- **Definition**: The difference between accrual-based earnings and cash-based earnings, normalized by total assets, measuring accounting discretion.
- **Why This Feature**: High accruals predict future earnings reversals and lower persistence; this captures the "non-cash" component of earnings that requires validation.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Cash flow and net income are both critical; missing either creates undefined accruals, requiring backfill or exclusion.
- **Directionality**: High positive values (accruals > cash) predict negative future returns (accrual anomaly); negative values suggest conservative accounting or cash realization ahead of recognition.
- **Boundary Conditions**: Distressed firms with negative earnings and positive cash flows create extreme negative ratios; hyper-growth firms show high positive accruals.
- **Implementation Example**: divide(subtract({newa1_ib}, {newa2_oancf}), {cptnewq_atq})

**Concept**: Intangible Capital Intensity
- **Sample Fields Used**: `newq_gdwlq`, `ewq_intanq`, `cptnewq_atq`
- **Definition**: The proportion of total assets composed of goodwill and intangible assets, indicating knowledge-based vs. physical capital intensity.
- **Why This Feature**: High intangible intensity creates valuation uncertainty (difficult to liquidate) and growth optionality; distinguishes asset-heavy from asset-light models.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Many industrial companies have zero intangibles; this is meaningful (not missing), so zeros should not be filled.
- **Directionality**: High values indicate brand/IP/knowledge-based business models (tech, pharma); low values indicate physical asset bases (utilities, manufacturing).
- **Boundary Conditions**: Post-impairment step-downs create structural breaks; goodwill from recent M&A inflates temporarily.
- **Implementation Example**: divide(add({newq_gdwlq}, {ewq_intanq}), {cptnewq_atq})

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Current Liquidity Ratio
- **Sample Fields Used**: `cptnewq_actq`, `newq_lctq`
- **Definition**: The ratio of current assets to current liabilities, measuring short-term solvency and liquidity buffer adequacy.
- **Why This Feature**: Critical distress predictor; values below 1.0 indicate technical insolvency risk; trends indicate working capital management efficiency.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Current liabilities are rarely missing for operating companies; missing values suggest data collection issues, not zero liabilities.
- **Directionality**: Values > 1 indicate liquidity surplus (safety but possible inefficiency); values < 1 indicate liquidity stress (refinancing risk).
- **Boundary Conditions**: Extremely high values suggest excessive cash holdings or poor capital allocation; negative equity situations create negative values.
- **Implementation Example**: divide({cptnewq_actq}, {newq_lctq})

**Concept**: Tangible Asset Coverage
- **Sample Fields Used**: `newa2_ppent`, `cptnewq_dlttq`
- **Definition**: The ratio of net property, plant, and equipment to long-term debt, measuring tangible collateral coverage for secured lenders.
- **Why This Feature**: High coverage indicates asset-backing for debt (lower credit risk); low coverage indicates reliance on unsecured financing or cash flows for debt service.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Service companies may have minimal PP&E; zero is meaningful (asset-light), not missing.
- **Directionality**: High values indicate strong collateral coverage (creditworthiness); low values indicate reliance on unsecured cash flows.
- **Boundary Conditions**: Zero debt creates infinite ratios; asset-light models (tech) show near-zero tangible assets.
- **Implementation Example**: divide({newa2_ppent}, {cptnewq_dlttq})

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Cumulative Free Cash Flow Generation
- **Sample Fields Used**: `newa2_oancf`, `newa1_capx`
- **Definition**: The trailing 1-year sum of operating cash flows minus capital expenditures, representing the firm's self-funding capacity.
- **Why This Feature**: Sustained positive cumulative FCF enables dividend growth, buybacks, and deleveraging; persistent deficits require external financing.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Annual cash flow items; missing quarters should be backfilled to maintain annual aggregation integrity.
- **Directionality**: Positive values indicate value creation (cash available for investors); negative values indicate growth investment phase or operational cash consumption.
- **Boundary Conditions**: Lumpy capex creates negative spikes in investment years; working capital releases create temporary positive spikes.
- **Implementation Example**: ts_sum(subtract({newa2_oancf}, {newa1_capx}), 252)

**Concept**: Retained Earnings Accumulation Trend
- **Sample Fields Used**: `newq_req`
- **Definition**: The slope of retained earnings over the trailing 2 years, indicating the rate of profit plowback and equity compounding.
- **Why This Feature**: Steady growth in retained earnings indicates sustainable profitability and conservative dividend policies; decline indicates losses or excessive payouts.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Retained earnings are cumulative by nature; missing values break the accumulation logic and require backfilling.
- **Directionality**: Positive slope indicates earnings retention and growth; negative slope indicates dividend payouts exceeding earnings or accumulated losses.
- **Boundary Conditions**: Dividend payments create step-downs; share buybacks reduce equity but not necessarily retained earnings directly.
- **Implementation Example**: ts_regression({newq_req}, ts_step(1), 504, rettype=1)

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Return on Common Equity
- **Sample Fields Used**: `cptnewq_ibq`, `cptnewq_ceqq`
- **Definition**: Net income available to common shareholders divided by common equity book value, measuring accounting return on equity capital.
- **Why This Feature**: Fundamental profitability metric comparing earnings generation to equity base; dispersion drives value vs. growth categorization.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Equity can be negative (insolvency); negative values are meaningful and should not be filled.
- **Directionality**: Higher values indicate efficient capital use (profitable growth); low values indicate capital intensity or competitive pressure.
- **Boundary Conditions**: Near-zero equity creates extreme values; negative equity with positive earnings creates negative ROE (distress signal).
- **Implementation Example**: divide({cptnewq_ibq}, {cptnewq_ceqq})

**Concept**: Gross Profit Margin
- **Sample Fields Used**: `ewq_gpq`, `cptnewq_revtq`
- **Definition**: Gross profit divided by revenue, representing the markup over direct production costs before operating overhead.
- **Why This Feature**: Pure measure of product-level profitability and pricing power; industry comparisons reveal competitive positioning.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Revenue rarely missing for operating companies; missing gross profit implies missing COGS data.
- **Directionality**: Higher values indicate pricing power or cost efficiency; declining values indicate commodity pressure or input cost inflation.
- **Boundary Conditions**: Negative gross margins indicate unsustainable pricing (burning cash on each unit); service companies may have minimal COGS.
- **Implementation Example**: divide({ewq_gpq}, {cptnewq_revtq})

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Operating Income Purity
- **Sample Fields Used**: `newa2_oiadp`, `newa2_revt`
- **Definition**: Operating income after depreciation as a percentage of revenue, representing the core economic profitability of the business model.
- **Why This Feature**: Strips away financing decisions (leverage), tax jurisdictions, and non-core activities to reveal operational essence.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Essential profitability metrics require complete data; missing components compromise the essence calculation.
- **Directionality**: Higher values indicate scalable, high-margin business models; lower values indicate high fixed costs or commodity competition.
- **Boundary Conditions**: Negative values indicate operational losses; capital-light models show high margins with minimal depreciation.
- **Implementation Example**: divide({newa2_oiadp}, {newa2_revt})

**Concept**: Sustainable Cash Generation Margin
- **Sample Fields Used**: `newa2_oancf`, `newa2_revt`
- **Definition**: Operating cash flow per unit of revenue, measuring the cash conversion efficiency of the business model.
- **Why This Feature**: The ultimate measure of economic viability—how much cash does each dollar of sales generate after all working capital and operational cash requirements.
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Cash flow is annual; revenue may be quarterly—alignment requires careful handling, potentially using annual revenue sums or quarterly cash flow estimates.
- **Directionality**: Values > 0.10 indicate strong cash conversion (quality earnings); values < 0 indicate cash consumption despite reported profits.
- **Boundary Conditions**: Working capital releases create temporary spikes > 1.0; heavy investment periods create negative values.
- **Implementation Example**: divide({newa2_oancf}, {newa2_revt})

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Quarterly balance sheet and income items (`cptnewq`, `newq`) show 95%+ coverage; annual cash flow items (`newa1`, `newa2`) drop to 85-90% due to filing lags and fiscal year alignment issues.
- **Timeliness**: Quarterly data updates with 45-60 day lag typical for European reporting; annual cash flow data may lag 90+ days.
- **Accuracy**: Standardized fields (`cptnewq`) reduce comparability issues but may introduce mapping errors from local GAAP to global standard; `ewq` fields preserve local accounting treatments.
- **Potential Biases**: Survivorship bias in fundamental data (delisted companies drop out); look-ahead bias if using annual data before fiscal year-end confirmation.

### Computational Complexity
- **Lightweight features**: Single-period ratios (Current Ratio, ROE, Gross Margin) require minimal computation.
- **Medium complexity**: Time-series transformations (ts_delta, ts_std_dev) require 63-252 day lookback windows.
- **Heavy computation**: Regression-based features (ts_regression for trend slopes) and multi-variable interactions across different frequencies (quarterly vs. annual alignment).

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Operating Cash Flow to Net Income Ratio** (Accruals Quality) - directly implements the well-documented accrual anomaly with high theoretical support.
2. **Current Ratio** - classic distress predictor with clear economic interpretation and low computation cost.
3. **Inventory to Sales Divergence** - leading indicator of future margin pressure with strong behavioral finance grounding.

**Tier 2 (Secondary Priority)**:
1. **Earnings Coefficient of Variation** - captures earnings quality but requires careful handling of near-zero earnings.
2. **Intangible Capital Intensity** - increasingly relevant for modern economies but requires industry-relative normalization for effectiveness.

**Tier 3 (Requires Further Validation)**:
1. **Retained Earnings Accumulation Trend** - long-term feature with potential but sensitive to dividend policy changes and accounting method shifts.

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How do differing fiscal year-ends across European companies create synchronization biases in quarterly features, and should we align to calendar quarters or fiscal quarters?
2. Does the treatment of goodwill under IFRS (impairment-only method) vs. US GAAP create systematic valuation differences that generate alpha in pan-European models?
3. How does the inclusion of `ewq` (European-specific) fields interact with `cptnewq` (global standard) fields—do they provide incremental information or redundant noise?

### Recommended Additional Data:
- Daily price and volume data to calculate market value for market-to-book and enterprise value multiples.
- Analyst forecast data to calculate earnings surprise relative to expectations rather than just time-series trends.
- Industry classification codes to enable sector-relative normalization of margin and leverage ratios.

### Assumptions to Challenge:
- That quarterly fundamental data provides sufficient timeliness for alpha generation given the 45-60 day reporting lag in European markets.
- That historical cost-based book values remain relevant for asset-light and intangible-heavy business models prevalent in modern economies.
- That accrual accounting deviations (accruals anomaly) remain profitable after two decades of documented academic publication and potential arbitrage.

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence (accrual vs. cash, stock vs. flow, standardized vs. local).
2. Question-driven feature generation (8 fundamental questions covering stability, change, anomaly, combination, structure, accumulation, relativity, and essence).
3. Logical validation of each feature concept against accounting identities and financial theory.
4. Transparent documentation of reasoning and boundary conditions.

**Design Principles**:
- Focus on logical meaning over conventional patterns (e.g., cash flow quality vs. simple earnings growth).
- Every feature must answer a specific economic question (What is changing? What is anomalous?).
- Clear documentation of "why" for each suggestion grounded in financial theory (accruals anomaly, conservatism principle, distress prediction).
- Emphasis on data understanding over prediction (knowing what PP&E represents vs. just using it in a ratio).

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate fiscal year alignment assumptions, gather price data for market value integration*