# fundamental6 Feature Engineering Analysis Report

**Dataset**: fundamental6
**Category**: fundamental
**Region**: USA
**Delay**: 1
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 574

---

## Executive Summary

**Primary Question Answered by Dataset**: What is the comprehensive financial health, operating performance, and capital structure of publicly traded companies, and how do these fundamentals evolve over time?

**Key Insights from Analysis**:
- The dataset provides a complete tripartite view: accrual-based earnings (income statement), resource commitments (balance sheet), and cash realization (cash flows)
- Quarterly granularity allows detection of inflection points in business performance before they appear in annual reports
- Dual presentation of GAAP earnings and S&P Core Earnings enables quality-of-earnings analysis
- Rich tax disclosure fields (deferred taxes, unrecognized benefits) provide visibility into financial engineering and liability timing

**Critical Field Relationships Identified**:
- `Assets = Liabilities + Equity` (fundamental accounting identity across `newa1v1300_at`, `newa1v1300_lt`, `newa1v1300_ceq`)
- `Operating Income` vs `Net Income` divergence indicates financial/fiscal engineering intensity
- `Cash Flow from Operations` vs `Net Income` gap measures earnings quality and accrual intensity
- `Goodwill + Intangibles` relative to `Total Assets` indicates capital-light business model intensity

**Most Promising Feature Concepts**:
1. **Accrual Anomaly Detection** - because the divergence between accounting earnings and cash generation predicts future earnings reversals
2. **Capital Structure Stability Index** - because persistent leverage ratios indicate management discipline, while volatile structures signal reactive financing or M&A activity
3. **Intangible Asset Intensity Trend** - because the shift from tangible to intangible capital fundamentally changes valuation and depreciation economics

---

## Dataset Deep Understanding

### Dataset Description
Fundamental6 provides comprehensive company fundamental data covering balance sheet, income statement, cash flow statement, and supplemental disclosures for US equities in the TOP3000 universe. Data updates quarterly with a 1-day delay, capturing both quarterly/semiannual/yearly periods. The dataset includes standard accounting items as well as S&P Core Earnings adjustments, comprehensive income components, deferred tax details, and options compensation data.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `newa1v1300_at` | Assets - Total | float | Quarterly | 99% |
| `newa1v1300_ceq` | Common/Ordinary Equity - Total | float | Quarterly | 99% |
| `newa1v1300_dltt` | Long-Term Debt - Total | float | Quarterly | 95% |
| `newqv1300_saleq` | Sales/Turnover (Net) | float | Quarterly | 98% |
| `newqv1300_cogsq` | Cost of Goods Sold | float | Quarterly | 95% |
| `cptnewqv1300_oibdpq` | Operating Income Before Depreciation - Quarterly | float | Quarterly | 97% |
| `newqv1300_ibq` | Income Before Extraordinary Items | float | Quarterly | 98% |
| `newa2v1300_oancf` | Operating Activities - Net Cash Flow | float | Annual | 96% |
| `newqv1300_rectq` | Receivables - Total | float | Quarterly | 94% |
| `newqv1300_invtq` | Inventories - Total | float | Quarterly | 85% |
| `cptnewqv1300_apq` | Accounts Payable/Creditors - Trade | float | Quarterly | 92% |
| `newa1v1300_capx` | Capital Expenditures | float | Annual | 90% |
| `cptnewqv1300_dpq` | Depreciation and Amortization - Total | float | Quarterly | 95% |
| `newqv1300_gdwlq` | Goodwill (net) | float | Quarterly | 80% |
| `newqv1300_intanoq` | Other Intangibles | float | Quarterly | 75% |
| `newqv1300_ppentq` | Property Plant and Equipment - Total (Net) | float | Quarterly | 95% |
| `newqv1300_seqq` | Stockholders' Equity - Total - Quarterly | float | Quarterly | 99% |
| `newqv1300_dlcq` | Debt in Current Liabilities | float | Quarterly | 88% |
| `newqv1300_spceq` | S&P Core Earnings | float | Quarterly | 70% |
| `newa1v1300_emp` | Employees | float | Annual | 85% |

*(Additional 554 fields covering deferred taxes, options data, comprehensive income, and industry-specific metrics)*

### Field Deconstruction Analysis

#### `newa1v1300_at`: Assets - Total
- **What is being measured?**: Economic resources controlled by the enterprise from which future economic benefits are expected to flow
- **How is it measured?**: Sum of current assets (cash, receivables, inventory) and non-current assets (PPE, intangibles, investments) at historical cost less accumulated depreciation
- **Time dimension**: Stock measure (point-in-time snapshot of cumulative investment)
- **Business context**: Represents the capital base deployed to generate returns; denominator for ROA and asset turnover metrics
- **Generation logic**: Audited financial statement aggregation following GAAP recognition criteria
- **Reliability considerations**: Subject to impairment adjustments and fair value revaluations; goodwill can distort economic reality

#### `newqv1300_saleq`: Sales/Turnover (Net)
- **What is being measured?**: Revenue from sale of goods and services to customers, net of returns and allowances
- **How is it measured?**: Accrual basis recognition when performance obligations are satisfied (delivery/control transfer)
- **Time dimension**: Flow measure (cumulative over the fiscal quarter)
- **Business context**: Top-line growth indicator; raw material for margin calculations and working capital efficiency metrics
- **Generation logic**: Reported revenue recognition policies vary by industry (subscription vs. point-of-sale vs. percentage-of-completion)
- **Reliability considerations**: Subject to channel stuffing, revenue recognition timing manipulation, and trade credit extensions that inflate short-term sales

#### `cptnewqv1300_oibdpq`: Operating Income Before Depreciation - Quarterly
- **What is being measured?**: Core operating profitability before non-cash depreciation charges and financing costs
- **How is it measured?**: Sales minus operating expenses (COGS + SG&A) excluding D&A; proxy for cash-generating ability of operations
- **Time dimension**: Flow measure (quarterly accumulation)
- **Business context**: Pure operating performance metric; used to assess pricing power and cost control independent of capital structure and accounting depreciation policies
- **Generation logic**: Derived from income statement aggregation; less susceptible to accounting method choices than net income
- **Reliability considerations**: Excludes capital intensity differences (D&A); high OIBD with high capex may overstate sustainable cash generation

#### `newa2v1300_oancf`: Operating Activities - Net Cash Flow
- **What is being measured?**: Actual cash generated from principal revenue-producing activities
- **How is it measured?**: Net income adjusted for non-cash charges and changes in working capital components
- **Time dimension**: Flow measure (annual accumulation due to data availability)
- **Business context**: Reality check on earnings quality; positive earnings with negative OCF indicates accrual buildup or working capital strain
- **Generation logic**: Indirect method starting from net income or direct method from cash receipts/payments; reconciliation required in financial statements
- **Reliability considerations**: Can be manipulated through timing of payables/receivables at year-end; management has discretion over working capital management

### Field Relationship Mapping

**The Story This Data Tells**:
The dataset captures the fundamental tension between accrual accounting (earnings) and cash economics. It reveals how companies deploy capital (`newa1v1300_at`, `newa1v1300_capx`), generate returns (`cptnewqv1300_oibdpq`, `newqv1300_ibq`), and finance operations (`newa1v1300_dltt`, `newqv1300_seqq`). The quarterly frequency exposes seasonal patterns and inflection points, while the S&P Core Earnings adjustments (`newqv1300_spceq`) separate sustainable earnings from one-time items. The comprehensive income fields (`newqv1300_ciderglq`, `newqv1300_aocidergl`) capture off-income-statement value changes that bypass traditional earnings metrics.

**Key Relationships Identified**:
1. **Earnings Quality Bridge**: `newqv1300_ibq` (Net Income) - `newa2v1300_oancf` (Cash Flow) = Accruals; persistent positive accruals predict future earnings declines
2. **Capital Structure Leverage**: `newa1v1300_dltt` / `newqv1300_seqq` (Debt-to-Equity) determines financial risk and return amplification; interacts with `cptnewqv1300_oibdpq` to determine interest coverage
3. **Working Capital Cycle**: `newqv1300_rectq` (receivables) + `newqv1300_invtq` (inventory) - `cptnewqv1300_apq` (payables) represents cash tied up in operations; efficiency changes affect liquidity before earnings
4. **Intangible Capital Intensity**: (`newqv1300_gdwlq` + `newqv1300_intanoq`) / `newa1v1300_at` indicates knowledge-economy vs. industrial-economy business model; affects depreciation economics and replacement costs

**Missing Pieces That Would Complete the Picture**:
- Real-time daily price data to calculate market-implied expectations vs. fundamental outcomes
- Segment-level breakdowns to analyze diversification and geographic risk concentration
- Off-balance-sheet obligations (operating leases, contingent liabilities) not fully captured in current liabilities
- Management guidance and forward-looking guidance metrics to assess expectation management

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: Capital Structure Stability Coefficient
- **Sample Fields Used**: `newqv1300_dlttq`, `newqv1300_seqq`
- **Definition**: Coefficient of variation (std/mean) of debt-to-equity ratio over trailing 8 quarters, measuring management's financing consistency
- **Why This Feature**: Companies with stable capital structures typically have coherent financing strategies and disciplined M&A policies; volatile structures indicate reactive financing or asset-liability mismatch risks
- **Logical Meaning**: Measures the persistence of financial leverage policy; low values indicate committed capital structure management, high values indicate opportunistic or distressed financing adjustments
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. For capital structure, missing debt values often indicate zero debt (unlevered) which is meaningful, so use ts_backfill() with caution or treat NaN as zero if context suggests paid-off debt.
- **Directionality**: Low values (stable) generally associated with lower equity risk premiums and higher valuations; high values indicate financial distress risk or growth-stage financing volatility
- **Boundary Conditions**: Values near zero indicate unlevered or constant leverage; spikes above 0.5 indicate restructuring or cyclical leverage patterns
- **Implementation Example**: `divide(ts_std_dev(divide({dlttq}, {seqq}), 8), abs(ts_mean(divide({dlttq}, {seqq}), 8)))`

**Concept**: Gross Margin Stability Index
- **Sample Fields Used**: `newqv1300_saleq`, `newqv1300_cogsq`
- **Definition**: Rolling stability of gross profit margin (Sales - COGS)/Sales over trailing 8 quarters
- **Why This Feature**: Margin stability indicates pricing power and supply chain resilience; volatile margins suggest commodity exposure, competitive pressure, or cost control issues
- **Logical Meaning**: Measures business model resilience and industry structure; stable margins indicate moats or contracted pricing, volatile margins indicate spot-market exposure
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Missing COGS may indicate service companies with minimal direct costs; filling with zero might be appropriate here but use industry group means to avoid distortion.
- **Directionality**: Higher stability (lower coefficient of variation) associated with quality companies and lower beta; instability predicts earnings uncertainty
- **Boundary Conditions**: Near-zero values indicate perfectly stable margins (rare); values >0.3 indicate highly cyclical or distressed operations
- **Implementation Example**: `divide(ts_std_dev(subtract(1, divide({cogsq}, {saleq})), 8), abs(ts_mean(subtract(1, divide({cogsq}, {saleq})), 8)))`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Sales Growth Acceleration
- **Sample Fields Used**: `newqv1300_saleq`
- **Definition**: Change in year-over-year sales growth rate, measuring momentum inflection (acceleration or deceleration)
- **Why This Feature**: Accelerating sales often precede margin expansion and positive earnings surprises; deceleration signals saturation or competitive entry
- **Logical Meaning**: Second derivative of revenue; captures inflection points in business cycles, product adoption curves, or market share shifts before they appear in level metrics
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Sales missingness may indicate non-reporting periods; use ts_backfill() to carry last known value forward for growth calculations to avoid artificial volatility.
- **Directionality**: Positive values (accelerating growth) associated with multiple expansion and momentum; negative values (deceleration) associated with derating
- **Boundary Conditions**: Extreme positive values (>50% acceleration) may indicate small base effects or recovery from distressed levels; extreme negative values indicate demand collapse
- **Implementation Example**: `ts_delta(divide({saleq}, ts_delay({saleq}, 252)), 63)`

**Concept**: Capital Intensity Trajectory
- **Sample Fields Used**: `newa1v1300_capx`, `newqv1300_ppentq`
- **Definition**: Change in ratio of capital expenditures to net PP&E, indicating investment cycle phase (expansion vs. maintenance vs. liquidation)
- **Why This Feature**: Capex inflections predict future capacity, depreciation charges, and competitive positioning; high ratios indicate growth mode, low ratios indicate harvest mode or underinvestment
- **Logical Meaning**: Measures reinvestment rate relative to existing asset base; rising ratios indicate capacity expansion for anticipated demand, falling ratios indicate maturity or cash harvesting
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Capex is often lumpy; missing quarterly values should be backfilled with ts_backfill() to avoid zero-investment assumptions in rolling windows.
- **Directionality**: Rising ratios associated with growth investing and future capacity; falling ratios associated with cash generation but potential future obsolescence
- **Boundary Conditions**: Ratios >0.5 indicate aggressive expansion or replacement cycles; ratios <0.05 indicate maintenance-only or disinvestment
- **Implementation Example**: `ts_delta(divide({capx}, {ppentq}), 252)`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Abnormal Accruals Divergence
- **Sample Fields Used**: `newa2v1300_ni`, `newa2v1300_oancf`
- **Definition**: Deviation of accrual component (Net Income - Operating Cash Flow) from historical norms, scaled by total assets
- **Why This Feature**: Large positive accruals (earnings > cash flow) indicate aggressive revenue recognition or working capital strain, predicting future earnings reversals
- **Logical Meaning**: Measures earnings quality; accruals are less persistent than cash flows, so abnormal accruals indicate temporary or manipulated earnings inflation
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Annual cash flow data on quarterly timeline creates many NaNs; use ts_backfill() to carry annual values forward as trailing twelve-month approximations.
- **Directionality**: High positive values (earnings exceed cash flow) associated with future negative returns (accrual anomaly); negative values indicate conservative accounting or cash realization ahead of recognition
- **Boundary Conditions**: Values >0.05 (5% of assets) indicate significant accrual buildup; values <-0.05 indicate cash collection ahead of revenue recognition
- **Implementation Example**: `divide(subtract({ni}, {oancf}), {atq})`

**Concept**: Days Inventory Outstanding Deviation
- **Sample Fields Used**: `newqv1300_invtq`, `newqv1300_cogsq`
- **Definition**: Z-score of current days-in-inventory relative to 2-year trailing average, detecting abnormal inventory buildup or liquidation
- **Why This Feature**: Inventory spikes precede write-downs and margin pressure; inventory declines may indicate demand strength or obsolescence risk clearance
- **Logical Meaning**: Measures supply-demand imbalance; abnormally high inventory suggests overproduction or demand shortfall, abnormally low suggests supply constraints or efficient JIT systems
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Service companies lack inventory; NaN here is meaningful (zero inventory business model) and should not be filled with industry means. Use if_else to handle service vs. manufacturing.
- **Directionality**: Positive deviations (rising inventory) associated with future margin compression; negative deviations associated with tight supply chains or write-off risks
- **Boundary Conditions**: Values >2 standard deviations indicate potential distress or seasonality; values <-2 indicate potential stockouts or LIFO liquidation
- **Implementation Example**: `subtract(divide({invtq}, divide({cogsq}, 91.25)), ts_mean(divide({invtq}, divide({cogsq}, 91.25)), 504))`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Cash Conversion Cycle Efficiency
- **Sample Fields Used**: `newqv1300_rectq`, `newqv1300_invtq`, `cptnewqv1300_apq`, `newqv1300_saleq`, `newqv1300_cogsq`
- **Definition**: Net working capital tied up in operations (receivables + inventory - payables) scaled by sales, measuring working capital efficiency
- **Why This Feature**: Efficient working capital management (low or negative CCC) indicates supply chain power and cash generation capability; high CCC indicates capital intensity and financing needs
- **Logical Meaning**: Combines three operational levers (customer collection, inventory management, supplier financing) into unified efficiency metric; negative values indicate vendor financing of operations
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Missing payables for cash businesses should not be filled; use zero or handle separately.
- **Directionality**: Lower values (more negative) indicate superior working capital efficiency and free cash flow generation; high positive values indicate cash trapped in operations
- **Boundary Conditions**: Negative values indicate extended payables or negative working capital (Walmart/Amazon model); values >0.3 indicate capital-intensive operations or collection issues
- **Implementation Example**: `divide(subtract(add({rectq}, {invtq}), {apq}), {saleq})`

**Concept**: Operating Leverage Intensity
- **Sample Fields Used**: `newqv1300_ppentq`, `newqv1300_xsgaq`, `newqv1300_saleq`
- **Definition**: Interaction between fixed asset intensity (PP&E/Sales) and sales volatility, measuring operating leverage risk exposure
- **Why This Feature**: High fixed costs combined with volatile sales create earnings volatility magnification; this captures the risk of cost structure mismatch with revenue stability
- **Logical Meaning**: Measures the compounding effect of fixed costs on profit volatility; high values indicate businesses where small sales changes cause large profit swings (high beta)
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. SG&A missingness may indicate cost of sales only structure; fill with zero if COGS captures all operating costs.
- **Directionality**: High values associated with high beta and cyclical risk; low values indicate variable cost structures and defensive characteristics
- **Boundary Conditions**: Values >2 indicate highly cyclical, capital-intensive industries; values <0.1 indicate asset-light, variable cost models
- **Implementation Example**: `multiply(divide({ppentq}, {saleq}), ts_std_dev({saleq}, 63))`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Intangible Asset Intensity
- **Sample Fields Used**: `newqv1300_gdwlq`, `newqv1300_intanoq`, `newqv1300_atq`
- **Definition**: Proportion of total assets composed of goodwill and identifiable intangibles, measuring knowledge-capital vs. physical-capital intensity
- **Why This Feature**: High intangible intensity indicates brand/IP-driven businesses with different depreciation economics and replacement costs than industrial firms; affects valuation multiples and margin sustainability
- **Logical Meaning**: Measures economic shift from tangible to intangible capital; high values indicate acquisition-heavy growth or IP-centric models (software, pharma), low values indicate asset-heavy models (utilities, manufacturing)
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Missing intangibles should be treated as zero (no goodwill or intangibles recognized) rather than backfilled.
- **Directionality**: High values associated with high margins but impairment risks; low values associated with capital intensity and maintenance capex requirements
- **Boundary Conditions**: Values >0.6 indicate acquisition goodwill overhang or IP-heavy business; values <0.05 indicate pure tangible asset bases
- **Implementation Example**: `divide(add({gdwlq}, {intanoq}), {atq})`

**Concept**: Debt Maturity Structure
- **Sample Fields Used**: `newqv1300_dlcq`, `cptnewqv1300_dlttq`
- **Definition**: Proportion of total debt due within one year (current debt), measuring refinancing risk and liquidity pressure
- **Why This Feature**: High short-term debt ratios indicate refinancing risk and sensitivity to credit market conditions; affects financial flexibility during stress periods
- **Logical Meaning**: Measures liability duration mismatch; high values indicate reliance on short-term funding (commercial paper, lines of credit), low values indicate long-term committed financing
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Missing current debt likely indicates zero short-term borrowings (long-term only financing); fill with zero.
- **Directionality**: High values (>0.5) associated with rollover risk and liquidity stress; low values indicate financing stability but potentially higher interest costs
- **Boundary Conditions**: Values >0.8 indicate acute refinancing risk; values <0.1 indicate long-term capital structure security
- **Implementation Example**: `divide({dlcq}, add({dlcq}, {dlttq}))`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Cumulative Reinvestment Rate
- **Sample Fields Used**: `newa1v1300_capx`, `cptnewqv1300_dpq`
- **Definition**: Trailing 4-quarter sum of capital expenditures divided by trailing 4-quarter sum of depreciation, measuring gross vs. maintenance investment
- **Why This Feature**: Ratios >1 indicate growth investment (expanding asset base), ratios <1 indicate underinvestment or asset harvesting; persistent ratios <1 indicate potential future capacity constraints
- **Logical Meaning**: Measures real investment relative to accounting depreciation; captures whether company is maintaining physical capital or expanding/contracting operations
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Annual capex reported quarterly should be distributed or carried forward; use ts_backfill() to assume constant annual rate.
- **Directionality**: Values >1 associated with growth and future capacity; values <1 associated with cash generation but potential future obsolescence
- **Boundary Conditions**: Values >2 indicate aggressive expansion; values <0.5 indicate asset liquidation or minimal maintenance
- **Implementation Example**: `divide(ts_sum({capx}, 252), ts_sum({dpq}, 252))`

**Concept**: Retained Earnings Accumulation Efficiency
- **Sample Fields Used**: `cptnewqv1300_req`, `newqv1300_ibq`
- **Definition**: Change in retained earnings relative to net income, measuring dividend payout and earnings retention policy consistency
- **Why This Feature**: Measures how much of earnings are retained for reinvestment vs. distributed; declining retained earnings despite positive income indicates dividend overpayment or prior period adjustments
- **Logical Meaning**: Cumulative measure of earnings retention policy; tracks the build-up of internal capital over time and sustainability of dividend policies
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Retained earnings restatements create discontinuities; do not backfill across restatement dates.
- **Directionality**: High retention ratios associated with growth investing; low or negative ratios indicate mature cash distribution or earnings inadequacy to cover dividends
- **Boundary Conditions**: Ratios >1 indicate earnings retention (growth mode); ratios <0 indicate dividend payout exceeding earnings or negative earnings
- **Implementation Example**: `divide(ts_delta({req}, 252), abs({ibq}))`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Operating Profitability Percentile Rank
- **Sample Fields Used**: `cptnewqv1300_oibdpq`, `newqv1300_atq`
- **Definition**: Cross-sectional Gaussian quantile of operating income before depreciation divided by total assets (Operating ROA)
- **Why This Feature**: Relative positioning in profitability distribution identifies industry leaders vs. laggards; controls for industry-wide margin differences better than absolute levels
- **Logical Meaning**: Measures competitive positioning and operational excellence relative to peer group; top decile indicates pricing power or cost advantage, bottom decile indicates distress or structural disadvantage
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Quantile operator handles NaNs by exclusion; no filling necessary before ranking.
- **Directionality**: Higher percentiles associated with quality factor and lower risk; lower percentiles associated with value trap risk or turnaround potential
- **Boundary Conditions**: Values >1.5 (top 7%) indicate elite profitability; values <-1.5 (bottom 7%) indicate deep distress or capital-intensive startup phases
- **Implementation Example**: `quantile(divide({oibdpq}, {atq}), driver=gaussian)`

**Concept**: Leverage Relative to Asset Base
- **Sample Fields Used**: `cptnewqv1300_dlttq`, `newqv1300_atq`
- **Definition**: Cross-sectional ranking of long-term debt to total assets, measuring financial risk relative to collateral capacity
- **Why This Feature**: Absolute leverage ignores asset tangibility; this measures debt against available collateral, distinguishing between secured industrial debt and unsecured service company debt
- **Logical Meaning**: Relative measure of financial leverage safety margin; high values indicate limited borrowing capacity and covenant risk, low values indicate financial flexibility
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Zero debt (NaN in some datasets) should be treated as zero leverage rather than missing; convert NaN to 0 before ranking.
- **Directionality**: High relative leverage associated with financial distress risk; low relative leverage associated with acquisition capacity and recession resilience
- **Boundary Conditions**: Top decile indicates highly levered balance sheets; bottom decile indicates unlevered or net-cash positions
- **Implementation Example**: `quantile(divide({dlttq}, {atq}), driver=gaussian)`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Economic Value Added Spread
- **Sample Fields Used**: `cptnewqv1300_oibdpq`, `newqv1300_atq`, `newqv1300_xintq`, `cptnewqv1300_dlttq`, `newqv1300_seqq`
- **Definition**: Operating return on assets minus weighted average cost of capital proxy (interest expense/total capital), measuring true economic profit generation
- **Why This Feature**: Accounting earnings ignore cost of capital; this measures whether operations generate returns exceeding financing costs, indicating genuine value creation vs. value destruction
- **Logical Meaning**: Essential driver of intrinsic value; positive spreads indicate competitive advantages generating excess returns, negative spreads indicate commoditized businesses destroying value
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. Zero interest expense for unlevered companies is meaningful (cost of equity only); ensure NaN interest is treated as zero before calculation.
- **Directionality**: Positive values indicate value creation and sustainable competitive advantage; negative values indicate value destruction even if accounting profits are positive
- **Boundary Conditions**: Spreads >0.05 (5%) indicate strong franchises; spreads <-0.02 indicate structural decline or commodity traps
- **Implementation Example**: `subtract(divide({oibdpq}, {atq}), divide({xintq}, add({dlttq}, {seqq})))`

**Concept**: Core Earnings Purity Ratio
- **Sample Fields Used**: `newqv1300_spceq`, `newqv1300_ibq`
- **Definition**: S&P Core Earnings (sustainable, excluding one-time items) divided by reported Net Income, measuring earnings quality and non-recurring item dependency
- **Why This Feature**: Distills sustainable earnings power from accounting noise; low ratios indicate reliance on asset sales, tax benefits, or other non-operational items for reported profits
- **Logical Meaning**: Measures the proportion of earnings derived from core operations vs. financial engineering; essential for forecasting persistence of earnings
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. S&P Core Earnings coverage is incomplete (70%); missing values indicate lack of S&P coverage rather than zero core earnings. Do not fill; exclude from universe or use alternative core earnings proxy.
- **Directionality**: Ratios near 1 indicate high-quality earnings; ratios <0.5 indicate heavy reliance on one-time items or aggressive accounting
- **Boundary Conditions**: Ratios >1.2 indicate conservative accounting (core > reported); ratios <0.3 indicate low-quality, non-recurring earnings
- **Implementation Example**: `divide({spceq}, {ibq})`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Quarterly fields (newqv1300_) have ~95% coverage; annual fields (newa1v1300_, newa2v1300_) have similar coverage but lower frequency requiring careful time-series alignment
- **Timeliness**: 1-day delay ensures data is available for trading but may miss intra-quarter developments or pre-announcements
- **Accuracy**: GAAP accounting subject to management judgment in revenue recognition, depreciation lives, and impairment timing; S&P Core Earnings adjustments provide second opinion on sustainability
- **Potential Biases**: Survivorship bias in historical data (failed companies drop out); look-ahead bias in restatements (data corrected retroactively)

### Computational Complexity
- **Lightweight features**: `divide({dlttq}, {seqq})`, `subtract({rectq}, {apq})` - single arithmetic operations
- **Medium complexity**: `ts_std_dev(divide({saleq}, ts_delay({saleq}, 252)), 8)`, `quantile(divide({oibdpq}, {atq}))` - time-series or cross-sectional operators
- **Heavy computation**: `ts_regression`, `ts_corr` across multiple fundamental fields with different update frequencies requiring alignment

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Cash Conversion Cycle Efficiency** - Strong theoretical link to working capital management and free cash flow; robust across industries with clear interpretation
2. **Accrual Anomaly Divergence** - Well-documented accounting anomaly with persistent alpha; simple calculation using annual fields
3. **Operating Profitability Percentile** - Pure quality factor; cross-sectional normalization handles industry differences

**Tier 2 (Secondary Priority)**:
1. **Intangible Asset Intensity** - Captures economic shift to knowledge capital; important for sector-neutral portfolios
2. **Capital Structure Stability** - Predicts financial distress and management consistency; requires 8-quarter history
3. **Core Earnings Purity** - Direct earnings quality measure; limited by S&P coverage but powerful where available

**Tier 3 (Requires Further Validation)**:
1. **Economic Value Added Spread** - Theoretically appealing but cost of capital proxy (using interest expense) imperfect for low-debt companies
2. **Operating Leverage Intensity** - Interaction effect requires careful handling of sales volatility outliers
3. **Debt Maturity Structure** - Refinancing risk important but current debt classification may miss off-balance-sheet obligations

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How do deferred tax asset valuation allowances (`newqv1300_txdbaq`) interact with future earnings persistence and regulatory tax rate changes?
2. What is the predictive power of comprehensive income components (`newqv1300_ciderglq`, `newqv1300_cisecglq`) versus net income for future returns?
3. How does options compensation expense (`newqv1300_optfvgrq`) predict future dilution and management incentive alignment?

### Recommended Additional Data:
- Segment-level financials to analyze diversification benefits and geographic risk exposure
- Management guidance and analyst forecast data to calculate surprise metrics against fundamental trends
- Off-balance-sheet obligations (operating leases, purchase commitments) to complete capital structure analysis

### Assumptions to Challenge:
- Assumption that quarterly changes in working capital are operational rather than timing-related year-end window dressing
- Assumption that GAAP accounting depreciation approximates economic depreciation for capital-intensive industries
- Assumption that goodwill impairment tests occur promptly rather than being delayed to avoid earnings hits

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence (accrual vs. cash, stock vs. flow, GAAP vs. economic)
2. Question-driven feature generation (8 fundamental questions covering stability, change, anomaly, interaction, structure, accumulation, relativity, and essence)
3. Logical validation of each feature concept against accounting identities and financial theory
4. Transparent documentation of reasoning and data quality considerations

**Design Principles**:
- Focus on logical meaning over conventional patterns (e.g., accruals vs. earnings quality rather than simple P/E)
- Emphasis on triangulation between income statement, balance sheet, and cash flow statement
- Recognition that quarterly data allows detection of inflection points invisible in annual data
- Clear documentation of "why" for each suggestion linking to economic value creation

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate accrual anomaly persistence, gather options compensation data for dilution analysis*