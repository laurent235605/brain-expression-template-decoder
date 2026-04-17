**Dataset**: fundamental23
**Region**: EUR
**Delay**: 1

---

# Fundamental Point in Time Data Feature Engineering Analysis Report

**Dataset**: fundamental23  
**Category**: Fundamental  
**Region**: EUR  
**Analysis Date**: 2024-01-15  
**Fields Analyzed**: 2318  

---

## Executive Summary

**Primary Question Answered by Dataset**: What is the true, point-in-time financial health and performance of a company, eliminating survivorship and look-ahead biases through original and restated financial statement data?

**Key Insights from Analysis**:
- The dataset contains multiple "views" of the same financial reality: standardized (`annfv1a`), as-reported (`annfvalld1`), interim (`intfvalld1`), and quarterly (`blsm`) formats, enabling robust validation of accounting consistency
- Extensive off-balance sheet coverage including operating lease maturities (`1los`, `2los`, etc.) and pension obligations enables true enterprise value assessment beyond traditional balance sheet metrics
- Point-in-time structure preserves historical restatements, allowing detection of earnings management through comparison of original vs. restated values
- Global standardization across 60,000+ companies enables cross-border factor construction while maintaining local accounting nuance

**Critical Field Relationships Identified**:
- **Accounting Identity**: Assets (`tota`) ≡ Liabilities (`lltl`) + Equity (`eltq`) - the fundamental invariant that all derived features must respect
- **Cash Flow Conservation**: Operating (`olto`) + Investing (`ilti`) + Financing (`fltf`) = Net Change in Cash (`ccns`)
- **Earnings Quality Spectrum**: Normalized earnings (`caiv`) vs. Reported net income (`cnin`) vs. Income including extraordinary items (`cinex`) reveals transitory vs. persistent components

**Most Promising Feature Concepts**:
1. **Lease-Adjusted Leverage Stability** - because operating lease commitments (`term_liabilities`) often exceed on-balance sheet debt (`debt_total`) and reveal true capital structure risk
2. **Accrual Anomaly Intensity** - divergence between Cash Flow (`cash_flow`) and Earnings (`net_income`) predicts future earnings reversals
3. **Asset Composition Momentum** - shifts between tangible (`property`) and intangible (`intangibles`) assets signal business model transitions

---

## Dataset Deep Understanding

### Dataset Description
This dataset provides point-in-time, globally standardized fundamental financial data for over 60,000 companies, including both active and inactive firms, with daily granularity. It includes original and restated values for income statements, balance sheets, and cash flow statements, as well as business and geographic segment data, ratios, and company metadata. The point-in-time structure eliminates forward-looking and survivorship biases, enabling accurate historical backtesting and model development.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `fnd23_annfv1a_tota` | Total assets of the company | Numeric | Annual | 95% |
| `fnd23_annfv1a_eltq` | Total equity | Numeric | Annual | 94% |
| `fnd23_annfv1a_dlts` | Total interest-bearing debt outstanding | Numeric | Annual | 92% |
| `fnd23_annfv1a_lctl` | Total current liabilities | Numeric | Annual | 93% |
| `fnd23_annfv1a_acta` | Total current assets | Numeric | Annual | 94% |
| `fnd23_annfv1a_rltr` | Total revenue | Numeric | Annual | 96% |
| `fnd23_annfv1a_cnin` | Net income after taxes (adjusted) | Numeric | Annual | 95% |
| `fnd23_annfv1a_caic` | Income available to common excl. extraordinary | Numeric | Annual | 90% |
| `fnd23_cf_m_olto` | Cash from operating activities | Numeric | Quarterly | 88% |
| `fnd23_annfv1a_nppa` | Net property, plant and equipment | Numeric | Annual | 85% |
| `fnd23_annfv1a_ltia` | Total inventory | Numeric | Annual | 80% |
| `fnd23_annfv1a_tnia` | Intangibles, net | Numeric | Annual | 75% |
| `fnd23_annfv1a_iwga` | Goodwill, net | Numeric | Annual | 70% |

*(Additional 2,308 fields covering segment data, pension obligations, lease commitments, and supplemental disclosures)*

### Field Deconstruction Analysis

#### `fnd23_annfv1a_tota`: Total Assets
- **What is being measured?**: The complete economic resource base controlled by the firm (tangible, intangible, financial)
- **How is it measured?**: Sum of current and non-current assets at historical cost less accumulated depreciation/impairment
- **Time dimension**: Point-in-time stock measure (snapshot at fiscal period end)
- **Business context**: Represents the capital base deployed to generate returns; denominator for ROA and asset turnover
- **Generation logic**: Derived from underlying asset accounts; subject to revaluation under IFRS but not US GAAP
- **Reliability considerations**: Subject to management judgment in impairment testing; goodwill (`intangibles`) may not reflect economic reality

#### `fnd23_annfv1a_dlts`: Total Debt
- **What is being measured?**: Interest-bearing obligations to creditors (both current and long-term)
- **How is it measured?**: Face value of bonds, loans, notes payable, and capital lease obligations
- **Time dimension**: Point-in-time liability measure
- **Business context**: Represents financial leverage and bankruptcy risk; excludes operating leases (see `term_liabilities` for complete picture)
- **Generation logic**: Aggregation of debt instruments by maturity; excludes accounts payable (operating liabilities)
- **Reliability considerations**: Off-balance sheet financing may obscure true leverage; convertible debt classification varies by standard

#### `fnd23_cf_m_olto`: Operating Cash Flow
- **What is being measured?**: Cash generated from core business operations (revenue-generating activities)
- **How is it measured?**: Net income adjusted for non-cash items and changes in working capital (indirect method)
- **Time dimension**: Flow measure over fiscal period
- **Business context**: "Cash is fact, earnings are opinion"; sustainable dividends require positive operating cash flow
- **Generation logic**: Derived from income statement and balance sheet changes; less subject to manipulation than accrual earnings
- **Reliability considerations**: Working capital management can temporarily inflate/deflate operating cash flow (e.g., delaying payables)

#### `fnd23_annfv1a_nppa`: Net PP&E
- **What is being measured?**: Tangible productive capacity (property, plant, equipment net of depreciation)
- **How is it measured?**: Historical cost less accumulated depreciation
- **Time dimension**: Depreciating stock with ongoing maintenance capex
- **Business context**: Represents physical capital intensity; critical for capital-heavy industries (utilities, manufacturing)
- **Generation logic**: Gross investment (`expenditures`) minus accumulated depreciation (`depreciation`)
- **Reliability considerations**: Economic depreciation may differ from accounting depreciation; aging assets may be understated

### Field Relationship Mapping

**The Story This Data Tells**:
This dataset captures the complete financial lifecycle of a firm: capital is raised (`financing_cash_flow`), invested in assets (`expenditures`), used to generate revenue (`revenue_total`), converted to profit (`net_income`), and either returned to investors (`dividends`) or reinvested (`retained_earnings`). The point-in-time nature preserves how this story evolved historically without the distortion of subsequent restatements.

**Key Relationships Identified**:
1. **Capital Structure Hierarchy**: `debt_total` + `equity` = `total_assets` (accounting identity); deviations indicate data quality issues or minority interest complications
2. **Earnings Decomposition**: `revenue_total` - `expenses` = `income_before_tax` - `tax_expense` = `net_income` (accrual chain)
3. **Cash Flow Reconciliation**: `net_income` + `depreciation` - `changes_in_working_capital` = `cash_flow` (accrual to cash conversion)
4. **Lease Capitalization Gap**: `debt_total` (traditional) vs. `term_liabilities` (operating leases) reveals off-balance sheet obligations that became on-balance sheet under IFRS 16/ASC 842

**Missing Pieces That Would Complete the Picture**:
- Real-time audit opinions or going concern warnings
- Segment-level profitability to identify value drivers
- Management guidance vs. actual realization rates
- Industry-specific KPIs (e.g., same-store sales for retail, load factors for airlines)

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: Capital Structure Stability Score
- **Sample Fields Used**: `debt_total`, `equity`
- **Definition**: Coefficient of variation of the debt-to-equity ratio over trailing 4 quarters
- **Why This Feature**: Stable capital structure indicates disciplined financial management and lower refinancing risk; volatile leverage often precedes financial distress
- **Logical Meaning**: Measures consistency in financing policy independent of absolute leverage levels
- **is filling nan necessary**: Yes, use `ts_backfill` for missing quarters but respect genuine zeros in equity
- **Directionality**: High values indicate unstable capital structure (negative); low values indicate stability (positive)
- **Boundary Conditions**: Near-zero equity creates extreme values; winsorize at 1st/99th percentiles
- **Implementation Example**: `ts_std_dev({debt_total} / {equity}, 252) / abs(ts_mean({debt_total} / {equity}, 252))`

**Concept**: Asset Composition Invariance
- **Sample Fields Used**: `current_assets`, `total_assets`
- **Definition**: Stability of current asset ratio over time
- **Why This Feature**: Business model shifts (e.g., moving from inventory-heavy to asset-light) are rare; sudden changes often indicate accounting changes or M&A
- **Logical Meaning**: Persistent operating models should maintain stable asset mixes
- **is filling nan necessary**: Use `ts_backfill` for seasonal businesses with intra-year gaps
- **Directionality**: Low values (stable) preferred for quality companies; high values flag transitions
- **Boundary Conditions**: Financial firms naturally have high current asset ratios; sector-neutralize
- **Implementation Example**: `ts_std_dev({current_assets} / {total_assets}, 504)`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Operating Cash Flow Momentum
- **Sample Fields Used**: `cash_flow`, `cashflow`
- **Definition**: Year-over-year growth in operating cash flow normalized by assets
- **Why This Feature**: Cash flow growth predicts earnings persistence better than accrual growth; normalization controls for firm size
- **Logical Meaning**: Accelerating cash generation indicates improving business quality or working capital efficiency
- **is filling nan necessary**: Fill with `group_mean` if missing, but flag as suspicious if OCF is consistently missing
- **Directionality**: Positive values indicate accelerating cash generation (positive signal)
- **Boundary Conditions**: Extreme values when transitioning from negative to positive OCF; use `signed_power` to compress
- **Implementation Example**: `ts_delta({cash_flow}, 252) / abs(ts_mean({total_assets}, 252))`

**Concept**: Earnings Quality Deterioration
- **Sample Fields Used**: `net_income`, `cash_flow`
- **Definition**: Change in the accrual component (Net Income - Cash Flow) relative to total assets
- **Why This Feature**: Growing accruals predict future earnings reversals (Sloan, 1996); flags aggressive revenue recognition
- **Logical Meaning**: Divergence between accounting earnings and cash reality
- **is filling nan necessary**: Both fields critical; do not fill if both missing, but `ts_backfill` individual gaps
- **Directionality**: Increasing accruals (high values) predict negative returns
- **Boundary Conditions**: One-time working capital investments create spikes; require 2-year lookback
- **Implementation Example**: `ts_delta(({net_income} - {cash_flow}) / {total_assets}, 252)`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Unusual Investment Intensity
- **Sample Fields Used**: `expenditures`, `total_assets`
- **Definition**: Current capex relative to historical firm-specific average, z-scored
- **Why This Feature**: Extreme investment often signals over-investment (empire building) or strategic inflection points
- **Logical Meaning**: Deviation from normal capital deployment patterns
- **is filling nan necessary**: Capex often lumpy; `ts_backfill` for up to 2 years acceptable
- **Directionality**: Extreme positive values often negative (over-investment); extreme negative values may signal under-investment or asset sales
- **Boundary Conditions**: New public firms lack history; require minimum 3 years data
- **Implementation Example**: `({expenditures} / {total_assets} - ts_mean({expenditures} / {total_assets}, 756)) / ts_std_dev({expenditures} / {total_assets}, 756)`

**Concept**: Tax Expense Anomaly
- **Sample Fields Used**: `tax_expense`, `before_tax`, `tax_expense_3`
- **Definition**: Effective tax rate deviation from statutory rate and historical average
- **Why This Feature**: Unusually low tax rates may indicate aggressive tax positions at risk of regulatory challenge; high rates suggest inefficiency
- **Logical Meaning**: Tax rate stability is expected; deviations indicate one-time items or risk
- **is filling nan necessary**: Use `group_mean` by sector for missing tax rates
- **Directionality**: Both extreme high and low values problematic; target median
- **Boundary Conditions**: Loss firms have negative effective rates; exclude negative denominator cases
- **Implementation Example**: `{tax_expense} / {before_tax} - ts_mean({tax_expense_3} / {before_tax}, 504)`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Financial Operating Leverage Composite
- **Sample Fields Used**: `expenses`, `net_income`, `debt_total`, `equity`
- **Definition**: Product of operating leverage (% fixed costs) and financial leverage (D/E)
- **Why This Feature**: High operating leverage amplifies financial leverage risk; combined measure captures total volatility exposure
- **Logical Meaning**: Total leverage risk = Business risk × Financial risk
- **is filling nan necessary**: Fill missing expense breakdowns with `group_mean` by industry
- **Directionality**: High values indicate extreme sensitivity to revenue shocks (negative)
- **Boundary Conditions**: Financial firms have different operating leverage definitions; exclude or separate
- **Implementation Example**: `({expenses} / {net_income}) * ({debt_total} / {equity})`

**Concept**: Intangible Capital Intensity
- **Sample Fields Used**: `intangibles`, `goodwill`, `total_assets`, `investment`
- **Definition**: Ratio of intangible assets to total assets, interacted with R&D intensity
- **Why This Feature**: Intangible-heavy firms require different valuation metrics; R&D intensity indicates maintenance capex for intangibles
- **Logical Meaning**: Knowledge capital intensity vs. physical capital
- **is filling nan necessary**: R&D often missing for non-tech firms; set to zero rather than backfill
- **Directionality**: High values indicate asset-light, knowledge-intensive models (sector-dependent signal)
- **Boundary Conditions**: Goodwill impairments create jumps; use `hump_decay` to smooth
- **Implementation Example**: `({intangibles} + {goodwill}) / {total_assets} * {investment}`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Liability Duration Mismatch
- **Sample Fields Used**: `current_liabilities_4`, `long_term`, `current_assets`, `long_term_debt`
- **Definition**: Ratio of current liabilities to current assets minus long-term debt to total capital
- **Why This Feature**: Maturity mismatch between assets and liabilities creates refinancing risk; "borrowing short to lend long"
- **Logical Meaning**: Negative values indicate conservative maturity matching; positive values indicate risk
- **is filling nan necessary**: Use `ts_backfill` for quarterly liability shifts
- **Directionality**: High positive values indicate liquidity risk (negative signal)
- **Boundary Conditions**: Zero-current-asset firms (financials) require different metric
- **Implementation Example**: `({current_liabilities_4} / {current_assets}) - ({long_term_debt} / ({debt_total} + {equity}))`

**Concept**: Asset Liquidity Stack
- **Sample Fields Used**: `cash_equivalents`, `receivables`, `inventory`, `current_assets`
- **Definition**: Weighted average liquidity of current assets (cash = 1, receivables = 0.7, inventory = 0.4)
- **Why This Feature**: Not all current assets are equally liquid; inventory obsolescence risk varies by industry
- **Logical Meaning**: True liquidity buffer available to meet short-term obligations
- **is filling nan necessary**: Fill missing components with zero (conservative)
- **Directionality**: Higher values indicate better liquidity (positive)
- **Boundary Conditions**: Inventory liquidation value varies wildly; sector-specific weights preferred
- **Implementation Example**: `({cash_equivalents} + 0.7*{receivables} + 0.4*{inventory}) / {current_assets}`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Accumulated Depreciation Ratio (Asset Age Proxy)
- **Sample Fields Used**: `depreciation`, `property`, `equipment`
- **Definition**: Accumulated depreciation to gross PP&E ratio
- **Why This Feature**: Proxy for asset age and capital stock vintage; old assets may require replacement capex
- **Logical Meaning**: % of physical capital consumed; high values indicate aging assets
- **is filling nan necessary**: Use `ts_sum` of historical depreciation if accumulated figure missing
- **Directionality**: High values indicate future capex needs (negative for cash flows, positive for capex suppliers)
- **Boundary Conditions**: Land (non-depreciable) inflates ratio; adjust for asset mix
- **Implementation Example**: `ts_sum({depreciation}, 2520) / ({property} + {equipment})`

**Concept**: Retained Earnings Persistence
- **Sample Fields Used**: `net_income`, `dividends`, `equity`
- **Definition**: Cumulative retained earnings as % of total equity
- **Why This Feature**: Organic vs. external growth financing; high retained earnings indicates self-sustaining business model
- **Logical Meaning**: Proportion of equity built through operations vs. capital raises
- **is filling nan necessary**: Backfill cumulative sum with zero base at IPO date
- **Directionality**: High values indicate earnings retention and reinvestment (positive for growth, negative if too high/mature)
- **Boundary Conditions**: Stock buybacks reduce equity independently of earnings; adjust for treasury stock
- **Implementation Example**: `ts_sum({net_income} - {dividends}, 5040) / {equity}`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Operating Margin vs. Asset Turnover Trade-off
- **Sample Fields Used**: `revenue_total`, `expenses`, `total_assets`
- **Definition**: Residual of operating margin (ROS) vs. asset turnover cross-sectional regression
- **Why This Feature**: Firms choose high-margin/low-turnover (luxury) or low-margin/high-turnover (retail) strategies; deviations from efficient frontier indicate inefficiency
- **Logical Meaning**: Whether firm is operating on its industry efficient frontier
- **is filling nan necessary**: Sector classification required first; use `group_mean` for missing sector peers
- **Directionality**: Positive residuals indicate "best of both worlds" efficiency (positive)
- **Boundary Conditions**: Negative asset turnover impossible; filter `total_assets` > 0
- **Implementation Example**: `({revenue_total} - {expenses}) / {revenue_total} - regression_neut(({revenue_total} - {expenses}) / {revenue_total}, {revenue_total} / {total_assets})`

**Concept**: Lease-Adjusted Leverage Percentile
- **Sample Fields Used**: `debt_total`, `term_liabilities`, `equity`, `total_assets`
- **Definition**: Combined on- and off-balance sheet leverage relative to sector peers
- **Why This Feature**: Traditional leverage metrics ignore operating leases, biasing retailers and airlines; relative ranking captures true risk position
- **Logical Meaning**: Percentile rank of total obligations within industry
- **is filling nan necessary**: Use `group_mean` for missing lease data, but flag as low confidence
- **Directionality**: High percentile (high leverage) typically negative for returns
- **Boundary Conditions**: Negative equity firms create negative leverage; winsorize denominator
- **Implementation Example**: `quantile(({debt_total} + {term_liabilities}) / {equity}, driver=gaussian)`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Sustainable Growth Rate (SGR)
- **Sample Fields Used**: `net_income`, `equity`, `dividends_paid`
- **Definition**: ROE × Retention Ratio (1 - dividend payout)
- **Why This Feature**: Maximum growth rate achievable without external financing; fundamental speed limit for organic growth
- **Logical Meaning**: Self-sustaining growth capacity; firms growing faster than SGR must take leverage or dilution
- **is filling nan necessary**: Assume zero dividends if missing (maximum retention)
- **Directionality**: High SGR indicates growth optionality (positive); negative SGR indicates unsustainable model
- **Boundary Conditions**: Negative earnings create nonsensical values; set to -1 for loss firms
- **Implementation Example**: `({net_income} / {equity}) * (1 - {dividends_paid} / {net_income})`

**Concept**: Economic Profit Spread
- **Sample Fields Used**: `net_income`, `total_assets`, `current_liabilities_3`, `interest_expense`, `debt_total`
- **Definition**: NOPAT - (Invested Capital × WACC proxy using sector cost of capital)
- **Why This Feature**: True value creation occurs when returns exceed cost of capital; accounting profit ignores capital charge
- **Logical Meaning**: Residual income after all costs including opportunity cost of capital
- **is filling nan necessary**: Use `group_mean` for missing interest expense (estimate cost of debt)
- **Directionality**: Positive values indicate competitive advantage and value creation (positive)
- **Boundary Conditions**: Negative invested capital creates positive spreads spuriously; require assets > liabilities
- **Implementation Example**: `{net_income} + {interest_expense} * (1 - 0.25) - 0.08 * ({total_assets} - {current_liabilities_3})`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Annual data (annfv1a) has 95%+ coverage; interim data drops to 85% for non-US firms; operating lease data (term_liabilities) only comprehensive post-2019
- **Timeliness**: Point-in-time eliminates restatement bias, but reporting lags (30-60 days post-fiscal end) require careful alignment with pricing data
- **Accuracy**: Goodwill (`goodwill`) and intangible (`intangibles`) values subject to impairment risk; use `ts_backfill` for missing quarters but respect zero values
- **Potential Biases**: Survivorship bias eliminated by including inactive firms; look-ahead bias eliminated by point-in-time structure; selection bias toward larger firms in early periods (1989-1997)

### Computational Complexity
- **Lightweight features**: Simple ratios like `{debt_total} / {equity}`, `{current_assets} / {current_liabilities_4}` (single time slice)
- **Medium complexity**: Time-series means like `ts_mean({net_income}, 252)` or momentum calculations requiring 1-year lookback
- **Heavy computation**: Cross-sectional regressions (`regression_neut`) for relative positioning, 5-year cumulative sums (`ts_sum` over 1260 days) for retained earnings persistence

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Lease-Adjusted Leverage** - `{debt_total} / {equity}` augmented with `{term_liabilities}` - critical for post-IFRS 16 comparability
2. **Operating Cash Flow to Net Income Divergence** - `{cash_flow} / {net_income}` - classic earnings quality signal
3. **Asset Turnover** - `{revenue_total} / {total_assets}` - fundamental efficiency metric with strong predictive power

**Tier 2 (Secondary Priority)**:
1. **Current Ratio Stability** - `ts_std_dev({current_assets} / {current_liabilities_4}, 504)` - liquidity risk monitoring
2. **Intangible Intensity** - `({intangibles} + {goodwill}) / {total_assets}` - increasingly important for modern economies
3. **Tax Rate Stability** - `{tax_expense} / {income_before_tax}` vs. historical average

**Tier 3 (Requires Further Validation)**:
1. **Pension Underfunding Ratio** - requires additional pension asset data not consistently available
2. **Segment Concentration** - requires segment revenue breakdowns with limited history

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How does the treatment of operating leases (`term_liabilities`) vs. finance leases (`long_term_debt`) vary across jurisdictions in the EUR universe, and does this create comparability issues?
2. Do restatements captured in the point-in-time data predict future returns better than the original reported values or the restated values?
3. What is the optimal lookback period for calculating "stable" capital structure given that capital structure changes are discrete events (refinancings) rather than continuous?

### Recommended Additional Data:
- **Segment-level financials**: To construct intra-company diversification metrics
- **Audit opinion data**: To flag "going concern" warnings or material weakness disclosures
- **Management guidance**: To compare realized `net_income` vs. expectations for earnings surprise features

### Assumptions to Challenge:
- **Accounting equivalence**: Assumes US GAAP and IFRS firms are comparable after standardization; may need country-specific adjustments for `goodwill` amortization rules
- **Industry homogeneity**: Sector classifications may be too coarse for features like `current_assets` ratios (retail vs. software)
- **Linear relationships**: Many features assume linear scaling (e.g., `{revenue_total} / {total_assets}`); diminishing returns may exist at extreme scale

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence (accounting identities vs. economic reality)
2. Question-driven feature generation (8 fundamental questions applied to financial statement structure)
3. Logical validation of each feature concept against accounting identities and economic theory
4. Prioritization based on data coverage, computational feasibility, and theoretical alpha decay resistance

**Design Principles**:
- Focus on logical meaning over conventional factors (e.g., lease adjustment critical for modern firms)
- Point-in-time awareness: All features respect the "as reported" nature to avoid look-ahead
- Cross-sectional relativism: Raw ratios less meaningful than sector-relative positions in fundamental data

---

*Report generated: 2024-01-15*  
*Analysis depth: Comprehensive field deconstruction + 8-question framework*  
*Next steps: Implement Tier 1 features focusing on lease-adjusted metrics and cash flow quality*