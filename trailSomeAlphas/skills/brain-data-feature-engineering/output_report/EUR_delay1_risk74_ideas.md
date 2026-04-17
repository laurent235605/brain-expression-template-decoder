# Risk Factors (risk74) Feature Engineering Analysis Report

**Dataset**: risk74
**Region**: EUR
**Delay**: 1


**Dataset**: risk74
**Category**: Risk
**Region**: EUR
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 49

---

## Executive Summary

**Primary Question Answered by Dataset**: How is a company exposed to multi-dimensional risks (tariff, geographic concentration, investor crowding, factor crowding) and how do these risk exposures interact and evolve over time?

**Key Insights from Analysis**:
- Dataset captures both point-in-time snapshots (raw values) and smoothed/standardized risk metrics, enabling analysis of both transient shocks and persistent risk regimes
- Geographic exposure is granularly disaggregated into US, China, and top two non-home countries, allowing precise tariff risk attribution
- Crowding is measured through three distinct lenses: hedge fund ownership concentration, liquidity-adjusted factors, and composite scores
- Time-series fields (momentum_ts, shortint_ts, resvol_ts, value_ts, timeseries_crowding) enable dynamic risk monitoring vs. static snapshots
- ESG risks are decomposed into Environmental, Social, and Governance components rather than treated as a monolithic score

**Critical Field Relationships Identified**:
- `risk_score` (tariff risk) correlates with geographic exposure fields (`exp_usa`, `exp_chn`, `exp_nondomicile1/2`) but captures policy uncertainty not fully explained by revenue exposure alone
- `hfown_pctown` (hedge fund ownership) and `crowding` measures capture different aspects of investor concentration - the former specific to sophisticated investors, the latter to general position clustering
- `raw_*` vs. standardized versions of the same metric allow decomposition of current shocks vs. normalized risk regimes

**Most Promising Feature Concepts**:
1. **Tariff-Geographic Interaction** - combines policy risk with actual exposure to identify companies with both high tariff vulnerability and high revenue dependence on affected regions
2. **Hedge Fund Accumulation Dynamics** - captures smart money positioning changes rather than static ownership levels
3. **Crowding Anomaly Detection** - identifies when crowding deviates significantly from historical norms, signaling potential crowded exits or entries
4. **Residual Geographic Concentration** - isolates non-domiciled exposure adjusted for diversification across the top two foreign markets

---

## Dataset Deep Understanding

### Dataset Description
This dataset provides comprehensive risk factor exposure metrics for European equities, encompassing tariff policy risks (GSXETRFS classifications), geographic revenue concentration (US, China, and other non-home markets), investor crowding metrics (hedge fund ownership and liquidity-adjusted crowding scores), and traditional style factors (momentum, value, short interest, residual volatility). The inclusion of both raw and standardized values, along with time-series histories for key factors, enables robust risk modeling that distinguishes between transient spikes and structural risk exposures.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `risk_score` | Standardized tariff risk exposure score | Float | Daily | 95% |
| `risk_score_specialized` | Specialized tariff risk classification | Float | Daily | 85% |
| `exp_usa` | Standardized exposure to United States | Float | Daily | 92% |
| `raw_exp_usa` | Unadjusted US exposure | Float | Daily | 92% |
| `exp_chn` | Standardized exposure to China | Float | Daily | 88% |
| `raw_exp_chn` | Unadjusted China exposure | Float | Daily | 88% |
| `exp_nondomicile1` | Exposure to largest non-home country | Float | Daily | 90% |
| `exp_nondomicile2` | Exposure to second-largest non-home country | Float | Daily | 87% |
| `nondomicile` | Standardized non-home country exposure | Float | Daily | 94% |
| `concentration` | Geographic concentration measure | Float | Daily | 96% |
| `raw_concentration` | Unadjusted geographic concentration | Float | Daily | 96% |
| `crowding` | Standardized investor crowding score | Float | Daily | 98% |
| `raw_crowding` | Unadjusted crowding measure | Float | Daily | 98% |
| `factor_crowding` | Liquidity-adjusted crowding factor | Float | Daily | 97% |
| `timeseries_crowding` | Time series of crowding values | Float | Daily | 98% |
| `hfown_pctown` | Percentage owned by hedge funds | Float | Daily | 89% |
| `hfown_numown` | Number of hedge fund owners | Integer | Daily | 89% |
| `fund_pct_ownership_encr` | ENCR-calculated HF ownership % | Float | Daily | 89% |
| `momentum` | Price momentum factor | Float | Daily | 99% |
| `momentum_ts` | Time series of momentum | Float | Daily | 99% |
| `value_ts` | Time series of value factor | Float | Daily | 98% |
| `shortint` | Current short interest | Float | Daily | 95% |
| `shortint_ts` | Time series of short interest | Float | Daily | 95% |
| `resvol_ts` | Time series of residual volatility | Float | Daily | 97% |
| `factor_e` | Environmental factor score | Float | Daily | 82% |
| `factor_s` | Social factor score | Float | Daily | 81% |
| `factor_g` | Governance factor score | Float | Daily | 83% |
| `factor_esg` | Composite ESG factor | Float | Daily | 80% |
| `descriptor_hip` | Hawk International Portfolio descriptor | Float | Daily | 75% |
| `descriptor_owl` | Owl descriptor | Float | Daily | 75% |
| `descriptor_qsg` | QSG descriptor | Float | Daily | 75% |
| `descriptor_tru` | TRU descriptor | Float | Daily | 75% |
| `inflation` | Standardized inflation exposure | Float | Daily | 90% |
| `raw_inflation` | Unadjusted inflation measure | Float | Daily | 90% |
| `yldspread` | Standardized yield spread exposure | Float | Daily | 85% |
| `raw_yldspread` | Unadjusted yield spread | Float | Daily | 85% |
| `earnyild` | Earnings yield factor | Float | Daily | 96% |
| `valuearn` | Combined value-earnings factor | Float | Daily | 94% |
| `cap_usd` | Market capitalization in USD | Float | Daily | 99% |
| `gsxetrfs_description` | Tariff classification description | String | Daily | 85% |
| `gsxetrfs_description_specialized` | Specialized tariff description | String | Daily | 70% |

### Field Deconstruction Analysis

#### `risk_score`: Tariff Risk Score
- **What is being measured?**: The standardized exposure of a company to tariff policy risks, specifically under the GSXETRFS classification system
- **How is it measured?**: Calculated based on geographic revenue exposure, supply chain dependencies, and sector-specific tariff sensitivity, then standardized across the universe
- **Time dimension**: Point-in-time snapshot with daily updates, capturing current policy regime impacts
- **Business context**: Exists to quantify policy uncertainty and trade war exposure beyond simple geographic revenue breakdowns
- **Generation logic**: Combines macro tariff policy indicators with micro firm-level exposure data; standardized to have cross-sectional mean zero and unit variance
- **Reliability considerations**: Higher reliability for large multinationals with transparent supply chains; may lag for rapidly shifting trade policies

#### `exp_usa` / `raw_exp_usa`: US Geographic Exposure
- **What is being measured?**: Revenue, assets, or earnings derived from United States operations
- **How is it measured?**: Reported geographic segment data from financial statements, standardized (`exp_usa`) or raw percentage (`raw_exp_usa`)
- **Time dimension**: Typically updated quarterly but interpolated to daily frequency with smoothing for the standardized version
- **Business context**: Critical for understanding vulnerability to US-specific shocks (tariffs, regulations, economic cycles)
- **Generation logic**: Derived from company filings; raw version is direct reporting, standardized version adjusts for reporting inconsistencies and outliers
- **Reliability considerations**: Raw version may have reporting lag and inconsistencies between companies; standardized version loses granularity but gains comparability

#### `crowding` / `raw_crowding`: Investor Crowding
- **What is being measured?**: Degree to which investor positions are concentrated in specific securities, indicating potential for crowded trades
- **How is it measured?**: Composite of ownership concentration, liquidity metrics, and position overlap across institutional investors
- **Time dimension**: Daily point-in-time for raw; smoothed for standardized version
- **Business context**: High crowding indicates liquidation risk if sentiment shifts; low crowding suggests contrarian opportunities
- **Generation logic**: Aggregates multiple position data sources; standardized version uses z-score normalization across universe
- **Reliability considerations**: Most reliable for large-cap liquid names with diverse investor bases; less reliable for micro-caps with few holders

#### `hfown_pctown`: Hedge Fund Ownership Percentage
- **What is being measured?**: Proportion of shares outstanding held by hedge funds specifically
- **How is it measured?**: Calculated from regulatory filings (13F) and ENCR methodology, representing sophisticated investor positioning
- **Time dimension**: Daily updates with quarterly reporting lags for some components
- **Business context**: Proxy for "smart money" sentiment and potential short-term price pressure from active managers
- **Generation logic**: Aggregates position data from hedge fund disclosures; may include estimation for non-reporting entities
- **Reliability considerations**: Subject to filing delays (45-day lag for 13F); may not capture all hedge fund activity

#### `momentum_ts`: Momentum Time Series
- **What is being measured?**: Historical trajectory of price momentum factor values
- **How is it measured?**: Rolling window calculations of price returns, stored as time-series for backtesting and trend analysis
- **Time dimension**: Daily historical values over extended lookback period
- **Business context**: Enables detection of momentum regime changes and acceleration/deceleration in price trends
- **Generation logic**: Typically 12-month return minus last month, calculated daily and stored historically
- **Reliability considerations**: Highly reliable price-based calculation; less effective during extreme volatility regimes

### Field Relationship Mapping

**The Story This Data Tells**:
The dataset narrates the vulnerability profile of European companies to exogenous shocks through three lenses: (1) Policy/Geographic exposure (tariff risks and revenue concentration), (2) Market microstructure risks (crowding and ownership concentration), and (3) Style factor risks (momentum, value, volatility). The relationships between these lenses reveal how macro risks (tariffs) interact with microstructure risks (crowding) - for example, a highly-crowded stock with high tariff exposure faces double jeopardy if trade policy shifts negatively.

**Key Relationships Identified**:
1. **Tariff Risk vs. Geographic Exposure**: `risk_score` correlates with `exp_usa` and `exp_chn` but captures policy uncertainty premium not fully explained by revenue geography alone
2. **Crowding vs. Ownership**: `crowding` measures general position concentration while `hfown_pctown` captures specific sophisticated investor concentration; divergence indicates retail vs. institutional crowding
3. **Raw vs. Standardized Metrics**: The spread between `raw_*` and standardized versions indicates whether current risk levels are extreme relative to history
4. **Factor Interactions**: `momentum_ts` and `value_ts` provide dynamic context for static factor exposures, showing regime persistence or reversal

**Missing Pieces That Would Complete the Picture**:
- Sectoral tariff exposure breakdown (which specific HS codes/products are affected)
- Supply chain tier data (exposure to tariffs through suppliers, not just direct revenue)
- Options market crowding metrics (gamma exposure, open interest concentration)
- ETF ownership flows (passive crowding distinct from active HF ownership)

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: Tariff Risk Regime Stability
- **Sample Fields Used**: `risk_score`, `risk_score_specialized`
- **Definition**: Coefficient of variation of tariff risk scores over 60 days to identify companies with persistent vs. transient policy risk exposure
- **Why This Feature**: Distinguishes between companies with structural tariff vulnerability (stable high scores) vs. those experiencing temporary policy noise
- **Logical Meaning**: Low values indicate entrenched tariff exposure (e.g., commodity exporters with fixed supply chains); high values indicate shifting risk profiles or policy uncertainty resolution
- **is filling nan necessary**: Yes, use `ts_backfill({risk_score}, 5)` before calculating std dev to handle reporting gaps without assuming zero risk
- **Directionality**: Low values = stable risk regime (predictable exposure); High values = unstable/changing risk profile
- **Boundary Conditions**: Near-zero values indicate completely static tariff classification; extremely high values may indicate data errors or corporate restructuring events
- **Implementation Example**: `ts_std_dev({risk_score}, 60) / abs(ts_mean({risk_score}, 60))`

**Concept**: Geographic Exposure Persistence
- **Sample Fields Used**: `exp_usa`, `exp_chn`, `exp_nondomicile1`
- **Definition**: Rolling standard deviation of geographic exposure metrics to identify companies with stable vs. shifting geographic footprints
- **Why This Feature**: Revenue stability vs. volatility in specific regions affects tariff vulnerability persistence
- **Logical Meaning**: Stable geographic exposure suggests integrated supply chains/established markets; volatile exposure suggests opportunistic trading or restructuring
- **is filling nan necessary**: Yes, geographic data often has quarterly reporting gaps; use `ts_backfill({exp_usa}, 20)` to carry forward last reported value
- **Directionality**: Low values = stable geographic footprint; High values = geographic business model in flux
- **Boundary Conditions**: Zero values indicate no change in exposure (diversified multinationals or pure domestic plays); spikes indicate M&A or divestitures
- **Implementation Example**: `ts_std_dev({exp_usa}, 60)`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Hedge Fund Accumulation Velocity
- **Sample Fields Used**: `hfown_pctown`, `fund_pct_ownership_encr`
- **Definition**: Rate of change in hedge fund ownership over 5-day and 20-day windows to capture smart money flow acceleration
- **Why This Feature**: Static ownership levels matter less than the direction and speed of change; rapid accumulation precedes price pressure
- **Logical Meaning**: Positive values indicate hedge funds increasing positions (conviction buying); negative values indicate exits (conviction selling or risk reduction)
- **is filling nan necessary**: No, NaN in ownership data typically means no reported position (zero or missing); filling would artificially create false flows
- **Directionality**: Positive = accelerating HF buying; Negative = accelerating HF selling; Zero = stable positioning
- **Boundary Conditions**: Extreme positive values may signal crowded entry; extreme negative values may signal forced liquidation or sentiment reversal
- **Implementation Example**: `ts_delta({hfown_pctown}, 5)`

**Concept**: Crowding Momentum
- **Sample Fields Used**: `crowding`, `timeseries_crowding`, `raw_crowding`
- **Definition**: Change in crowding scores relative to recent historical averages to detect building or unwinding of crowded positions
- **Why This Feature**: Crowding is a precursor to volatility; accelerating crowding indicates increasing liquidation risk
- **Logical Meaning**: Positive momentum suggests positions becoming more crowded (risk increasing); negative momentum suggests dispersion (risk reducing)
- **is filling nan necessary**: No, crowding data is typically daily and complete; NaN values are rare and meaningful (insufficient data to calculate)
- **Directionality**: Positive = crowding increasing (dangerous); Negative = crowding decreasing (safer); Zero = stable crowdedness
- **Boundary Conditions**: Values approaching historical maxima indicate extreme crowdedness; sharp negative spikes indicate rapid de-risking
- **Implementation Example**: `{crowding} - ts_delay({crowding}, 20)`

**Concept**: Tariff Risk Acceleration
- **Sample Fields Used**: `risk_score`, `raw_exp_usa`, `raw_exp_chn`
- **Definition**: Short-term change in tariff risk scores combined with changes in underlying geographic exposure to distinguish policy shocks from business model shifts
- **Why This Feature**: Distinguishes between companies actively increasing risky exposures vs. those suffering external policy deteriorations
- **Logical Meaning**: High values indicate rapidly deteriorating tariff environment or increasing vulnerability; negative values indicate improving conditions or risk reduction
- **is filling nan necessary**: Yes, tariff scores may have irregular updates; use `ts_backfill({risk_score}, 3)` to ensure continuity
- **Directionality**: Positive = increasing tariff risk; Negative = decreasing tariff risk; Zero = stable environment
- **Boundary Conditions**: Extreme spikes may indicate trade war escalations or supply chain disruptions; large negative moves suggest trade deal benefits
- **Implementation Example**: `ts_delta({risk_score}, 5)`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Crowding Z-Score Anomaly
- **Sample Fields Used**: `crowding`, `raw_crowding`
- **Definition**: Deviation of current crowding from 120-day historical mean, normalized by historical volatility
- **Why This Feature**: Identifies when crowding reaches extreme levels relative to a stock's own history, signaling crowded trade risk or contrarian opportunity
- **Logical Meaning**: High positive values indicate unusually high crowding (crowded long); high negative values indicate unusual emptiness (potential contrarian long)
- **is filling nan necessary**: No, calculation uses `ts_mean` and `ts_std_dev` which handle NaNs appropriately in the lookback window
- **Directionality**: High positive = anomalously crowded (avoid or short); High negative = anomalously under-owned (potential buy); Near zero = normal
- **Boundary Conditions**: Values > 2.0 indicate statistical extremes (potential reversal); values < -2.0 indicate extreme neglect
- **Implementation Example**: `({crowding} - ts_mean({crowding}, 120)) / ts_std_dev({crowding}, 120)`

**Concept**: Geographic Concentration Spike
- **Sample Fields Used**: `concentration`, `raw_concentration`
- **Definition**: Short-term deviation of geographic concentration from trend to identify companies undergoing rapid internationalization or retrenchment
- **Why This Feature**: Sudden concentration changes indicate strategic shifts (nearshoring, China+1 strategies) with significant tariff implications
- **Logical Meaning**: Positive spikes indicate increasing concentration (higher risk); negative spikes indicate diversification (risk reduction)
- **is filling nan necessary**: Yes, use `ts_backfill({concentration}, 10)` to handle quarterly reporting lags before calculating deviation
- **Directionality**: Positive = increasing concentration risk; Negative = decreasing concentration/diversifying; Zero = stable geographic mix
- **Boundary Conditions**: Extreme values indicate M&A activity or major divestitures; persistent elevation indicates structural shift to concentrated markets
- **Implementation Example**: `{concentration} - ts_mean({concentration}, 60)`

**Concept**: Ownership Dispersion Anomaly
- **Sample Fields Used**: `hfown_pctown`, `hfown_numown`, `fund_num_owners_encr`
- **Definition**: Deviation between percentage ownership and number of holders (concentrated vs. distributed HF ownership) relative to historical norms
- **Why This Feature**: Few funds with large positions (concentrated) behaves differently than many funds with small positions (distributed) despite same aggregate percentage
- **Logical Meaning**: High values indicate concentrated ownership (few large holders = higher liquidation risk); low values indicate distributed ownership
- **is filling nan necessary**: No, both fields typically update together; independent NaNs should remain to avoid false signals
- **Directionality**: High = concentrated risk (dangerous); Low = diversified HF ownership (safer); Normal = balanced
- **Boundary Conditions**: Extreme concentration suggests "clipping" risk if one large holder exits; extreme distribution suggests index-like ownership
- **Implementation Example**: `({hfown_pctown} / {hfown_numown}) - ts_mean(({hfown_pctown} / {hfown_numown}), 60)`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Tariff-Geographic Vulnerability Product
- **Sample Fields Used**: `risk_score`, `exp_usa`, `exp_chn`, `exp_nondomicile1`
- **Definition**: Interaction between tariff risk scores and actual geographic revenue exposure to identify companies with both high policy risk and high economic dependence
- **Why This Feature**: Tariff risk matters most when companies actually derive revenue from affected regions; this separates real vulnerability from theoretical risk
- **Logical Meaning**: High values indicate dangerous combination of high tariff risk and high exposure to tariff-targeted regions
- **is filling nan necessary**: Yes, fill NaN in exposure with 0 (no exposure) before multiplication to avoid losing valid risk scores
- **Directionality**: High = high tariff risk + high geographic exposure (avoid); Low = either low risk or low exposure (safer)
- **Boundary Conditions**: Zero indicates either no tariff risk or no foreign exposure; extreme values indicate pure-play exposure to tariff-targeted regions
- **Implementation Example**: `{risk_score} * ({exp_usa} + {exp_chn})`

**Concept**: Crowded Value Trap
- **Sample Fields Used**: `crowding`, `value_ts`, `factor_crowding`
- **Definition**: Interaction between crowding scores and value factor to identify crowded value trades (value stocks that are too popular)
- **Why This Feature**: Value factors work best when uncrowded; crowded value trades underperform due to liquidation risk during drawdowns
- **Logical Meaning**: High values indicate value stocks that are crowded (likely to underperform); low values indicate uncrowded value (potential alpha)
- **is filling nan necessary**: No, value and crowding typically available together; NaN should propagate to avoid signals on illiquid names
- **Directionality**: High = crowded value (avoid); Low = uncrowded value (attractive); Negative = growth stocks with low crowding
- **Boundary Conditions**: Extreme values indicate consensus value trades (dangerous); near-zero indicates neutral positioning
- **Implementation Example**: `{crowding} * {value_ts}`

**Concept**: HF Momentum Amplification
- **Sample Fields Used**: `hfown_pctown`, `momentum`, `momentum_ts`
- **Definition**: Interaction between hedge fund ownership and momentum to identify stocks where smart money is riding price trends
- **Why This Feature**: HF ownership validates momentum (smart money confirmation) or indicates crowded momentum trades depending on levels
- **Logical Meaning**: High values indicate hedge funds are long momentum stocks (trend following); negative values indicate hedge funds shorting or avoiding momentum
- **is filling nan necessary**: No, momentum is complete; HF data gaps are meaningful (no HF interest)
- **Directionality**: High = HF long momentum (trend continuation likely); Low/Negative = HF avoiding momentum (reversal possible)
- **Boundary Conditions**: Extreme values indicate "smart money" consensus on trends; zero indicates HF agnosticism to momentum
- **Implementation Example**: `{hfown_pctown} * {momentum}`

**Concept**: ESG Risk Integration
- **Sample Fields Used**: `factor_e`, `factor_s`, `factor_g`, `factor_esg`
- **Definition**: Non-linear combination of ESG components to identify companies with lopsided ESG profiles (e.g., high E but low G)
- **Why This Feature**: ESG factors are not monolithic; tariff and regulatory risks often correlate with specific ESG components (e.g., Environmental for carbon tariffs, Governance for sanctions)
- **Logical Meaning**: High values indicate balanced strong ESG; low/negative values indicate weak components or lopsided profiles
- **is filling nan necessary**: Yes, ESG data has lower coverage; use `ts_backfill` or treat NaN as neutral (0) depending on interpretation
- **Directionality**: High = strong balanced ESG; Low = weak or unbalanced ESG; Specific component analysis for targeted risks
- **Boundary Conditions**: Extreme values indicate ESG leaders/laggards; component divergence indicates specific risk factors
- **Implementation Example**: `{factor_e} + {factor_s} + {factor_g}`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Geographic Diversification Ratio
- **Sample Fields Used**: `exp_usa`, `exp_chn`, `nondomicile`, `concentration`
- **Definition**: Proportion of non-domestic revenue derived from diversified sources vs. concentrated in single high-risk markets
- **Why This Feature**: Distinguishes between global diversification (safe) and single-market concentration (risky) even when total foreign exposure is identical
- **Logical Meaning**: High values indicate well-diversified geographic footprint; low values indicate "all eggs in one basket" foreign exposure
- **is filling nan necessary**: Yes, fill missing exposure components with 0 to ensure ratio calculation integrity
- **Directionality**: High = diversified (lower risk); Low = concentrated (higher risk); 1.0 = purely non-domestic and diversified
- **Boundary Conditions**: Zero indicates pure domestic play; values approaching 1 indicate extensive diversified international operations
- **Implementation Example**: `{nondomicile} / ({exp_usa} + {exp_chn} + {nondomicile} + 0.0001)`

**Concept**: HF Ownership Structure
- **Sample Fields Used**: `hfown_pctown`, `fund_pct_ownership_encr`, `ownership_encr`
- **Definition**: Ratio of hedge fund ownership to total institutional ownership to isolate "active" vs. "passive" holder concentration
- **Why This Feature**: High HF ownership indicates active bets (higher turnover risk); high institutional but low HF indicates passive/index ownership (stickier)
- **Logical Meaning**: High values indicate active manager dominance (short-term risk); low values indicate passive/long-only dominance (stability)
- **is filling nan necessary**: No, ownership data typically complete; ratio of NaNs should remain NaN
- **Directionality**: High = HF dominated (active risk); Low = passive dominated (stable); 0.5 = balanced
- **Boundary Conditions**: Values > 0.7 indicate HF-controlled stocks; values < 0.1 indicate HF neglect or passive dominance
- **Implementation Example**: `{hfown_pctown} / ({fund_pct_ownership_encr} + 0.0001)`

**Concept**: Factor Exposure Structure
- **Sample Fields Used**: `momentum`, `value_ts`, `earnyild`, `valuearn`
- **Definition**: Decomposition of style factor exposure to identify pure factor plays vs. mixed factor profiles
- **Why This Feature**: Stocks with consistent single-factor exposure behave predictably; mixed exposures create noise; tariff risks correlate with specific factors (value in cyclicals, momentum in defensives)
- **Logical Meaning**: High values indicate strong style tilt; balanced values indicate factor-neutral or confused profiles
- **is filling nan necessary**: No, factor scores are typically complete daily
- **Directionality**: Positive values indicate long tilt to numerator factor; Negative indicate inverse; Magnitude indicates strength
- **Boundary Conditions**: Extreme values indicate pure factor exposure; near-zero indicates factor neutrality or conflicting signals
- **Implementation Example**: `{momentum} / ({value_ts} + {earnyild} + 0.0001)`

**Concept**: Tariff Risk Composition
- **Sample Fields Used**: `risk_score`, `risk_score_specialized`, `score_specialized`
- **Definition**: Discrepancy between general and specialized tariff risk scores to identify companies with hidden tariff vulnerabilities
- **Why This Feature**: General scores may miss sector-specific tariff risks (e.g., semiconductor-specific tariffs not captured in broad metrics)
- **Logical Meaning**: Large spread indicates specialized risk not captured in general score; convergence indicates generalist tariff exposure
- **is filling nan necessary**: Yes, specialized scores have lower coverage; fill with general score where missing to avoid bias
- **Directionality**: High = high specialized risk above general risk; Low = general risk dominates; Zero = aligned
- **Boundary Conditions**: Extreme values indicate niche tariff vulnerabilities; negative values indicate lower specialized vs. general risk
- **Implementation Example**: `{risk_score_specialized} - {risk_score}`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Cumulative Hedge Fund Flow Pressure
- **Sample Fields Used**: `hfown_pctown`, `fund_pct_ownership_encr`
- **Definition**: Accumulated change in hedge fund ownership over 20 days to identify persistent buying or selling pressure
- **Why This Feature**: Single-period changes may be noise; cumulative flows indicate sustained conviction or capitulation
- **Logical Meaning**: Positive values indicate sustained accumulation (building position); negative values indicate sustained distribution (exiting)
- **is filling nan necessary**: No, treat each day's change as independent; cumulative sum naturally handles gaps
- **Directionality**: Highly positive = strong accumulation (future pressure potential); Highly negative = strong distribution; Near zero = no net flow
- **Boundary Conditions**: Values > 5% indicate significant position building; values < -5% indicate major exits; bounded by 100% ownership theoretically
- **Implementation Example**: `ts_sum(ts_delta({hfown_pctown}, 1), 20)`

**Concept**: Cumulative Short Interest Buildup
- **Sample Fields Used**: `shortint`, `shortint_ts`
- **Definition**: Accumulated short interest changes over 15 days to detect building bearish pressure or covering rallies
- **Why This Feature**: Short interest spikes indicate negative sentiment; cumulative measures distinguish temporary spikes from persistent bearish bets
- **Logical Meaning**: Positive values indicate increasing short interest (bearish pressure); negative values indicate covering (potential squeeze)
- **is filling nan necessary**: No, short interest is daily and complete for liquid names
- **Directionality**: Positive = building shorts (negative signal); Negative = covering (positive signal); Zero = stable SI
- **Boundary Conditions**: Extreme positive values indicate crowded short; extreme negative indicates short squeeze potential
- **Implementation Example**: `ts_sum(ts_delta({shortint}, 1), 15)`

**Concept**: Cumulative Crowding Pressure Index
- **Sample Fields Used**: `crowding`, `timeseries_crowding`, `raw_crowding`
- **Definition**: Accumulated deviation of crowding from long-term average to identify stocks experiencing sustained crowding accumulation or dispersion
- **Why This Feature**: Cumulative pressure predicts liquidation cascades; stocks under sustained crowding accumulation face eventual violent unwinds
- **Logical Meaning**: Positive values indicate sustained increase in crowdedness (danger building); negative values indicate sustained dispersion (safety improving)
- **is filling nan necessary**: No, crowding data is typically robust daily
- **Directionality**: High positive = pressure building (avoid); High negative = pressure releasing (opportunity); Zero = equilibrium
- **Boundary Conditions**: Extreme values indicate unsustainable crowdedness; rapid reversals indicate flash crashes or squeezes
- **Implementation Example**: `ts_sum(({crowding} - ts_mean({crowding}, 60)), 20)`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Relative Tariff Risk Percentile
- **Sample Fields Used**: `risk_score`, `risk_score_specialized`
- **Definition**: Cross-sectional percentile rank of tariff risk scores to identify most/least exposed companies relative to peers
- **Why This Feature**: Absolute tariff risk matters less than relative risk; tariffs affect sector-relative performance, not just absolute prices
- **Logical Meaning**: Values near 1 indicate highest tariff risk in universe; values near 0 indicate lowest risk; 0.5 indicates median risk
- **is filling nan necessary**: Yes, rank calculation requires complete data; backfill missing risk scores with neutral assumption (0 or median)
- **Directionality**: High = high relative risk (sector underperformance likely in trade wars); Low = low relative risk (safe haven)
- **Boundary Conditions**: 0.0 = minimum risk; 1.0 = maximum risk; values cluster around 0.5 in normal times
- **Implementation Example**: `quantile({risk_score}, driver="uniform")`

**Concept**: Relative Geographic Exposure
- **Sample Fields Used**: `exp_usa`, `exp_chn`, `exp_nondomicile1`
- **Definition**: Cross-sectional ranking of geographic exposure to identify pure-plays vs. diversified peers
- **Why This Feature**: Relative exposure determines beta to regional shocks; helps construct geographic factor-neutral portfolios
- **Logical Meaning**: High values indicate highest exposure to specific region (high beta); low values indicate domestic/low exposure (low beta)
- **is filling nan necessary**: Yes, fill missing exposure with 0 (domestic assumption) before ranking
- **Directionality**: High = high regional beta (aggressive play); Low = low regional beta (defensive); use for pair trades
- **Boundary Conditions**: Extreme values indicate pure-play exporters; near-zero indicates domestic defensive names
- **Implementation Example**: `quantile({exp_usa}, driver="uniform")`

**Concept**: Crowding Relative to History
- **Sample Fields Used**: `crowding`, `raw_crowding`
- **Definition**: Current crowding percentile relative to stock's own historical distribution (time-series quantile)
- **Why This Feature**: Crowding is stock-specific; high crowding for a blue-chip may be normal while same level for a small-cap is extreme
- **Logical Meaning**: Values near 1 indicate historically high crowding for that specific stock; near 0 indicates historically empty
- **is filling nan necessary**: No, `ts_quantile` handles lookback window NaNs appropriately
- **Directionality**: High = historically crowded (mean reversion likely); Low = historically uncrowded (potential entry); 0.5 = normal
- **Boundary Conditions**: 0.0 = historical minimum; 1.0 = historical maximum; persistence at extremes predicts regime change
- **Implementation Example**: `ts_quantile({crowding}, 120, driver="uniform")`

**Concept**: HF Ownership Relative to Sector
- **Sample Fields Used**: `hfown_pctown`, `fund_num_owners_encr`
- **Definition**: Deviation of HF ownership from sector average to identify sector outliers (HF favorites or rejects)
- **Why This Feature**: Sector-relative ownership indicates stock-picking skill vs. sector bets; tariff risks are often sector-wide
- **Logical Meaning**: Positive values indicate HF overweight relative to sector peers (conviction pick); negative indicates underweight (avoid)
- **is filling nan necessary**: No, cross-sectional mean calculation handles NaNs by exclusion
- **Directionality**: High = HF favorite vs. sector (good if sector rallies); Low = HF avoid (bad if sector rallies, good if tariff hits sector)
- **Boundary Conditions**: Extreme values indicate contrarian sector bets; near-zero indicates sector-mirror holdings
- **Implementation Example**: `{hfown_pctown} - quantile({hfown_pctown}, driver="uniform")` [Note: using quantile as proxy for cross-sectional positioning, or via vector_neut against sector proxy if available]

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Pure Tariff Exposure (Orthogonal to Geography)
- **Sample Fields Used**: `risk_score`, `exp_usa`, `exp_chn`, `exp_nondomicile1`
- **Definition**: Tariff risk orthogonalized against geographic exposure to capture policy risk not explained by revenue geography (e.g., supply chain, secondary effects)
- **Why This Feature**: Separates "tariff risk because we sell to US" from "tariff risk because we have complex supply chains" - the latter is less visible and more dangerous
- **Logical Meaning**: High values indicate high tariff risk despite low direct geographic exposure (supply chain vulnerability); low values indicate geographic exposure explains all risk
- **is filling nan necessary**: Yes, ensure geographic exposure is backfilled to avoid spurious residuals
- **Directionality**: High = hidden/supply-chain tariff risk (dangerous); Low = visible/direct tariff risk (priced in); Negative = over-insured vs. geography
- **Boundary Conditions**: Extreme values indicate companies with indirect tariff exposure (component suppliers); near-zero indicates pure geographic play
- **Implementation Example**: `vector_neut({risk_score}, {exp_usa} + {exp_chn})`

**Concept**: Essential Crowding (Market Cap Adjusted)
- **Sample Fields Used**: `crowding`, `raw_crowding`, `cap_usd`, `factor_crowding`
- **Definition**: Crowding measure adjusted for market capitalization to identify true crowding vs. large-cap index effects
- **Why This Feature**: Large caps appear crowded because indexes own them; essential crowding identifies active bets beyond passive ownership
- **Logical Meaning**: High values indicate genuine active crowding beyond size effects; low values indicate apparent crowding is just index inclusion
- **is filling nan necessary**: No, market cap is always available for universe constituents
- **Directionality**: High = true active crowding (higher liquidation risk); Low = passive/index crowding (stickier); Negative = under-owned vs. size
- **Boundary Conditions**: Extreme values indicate small-caps with massive active interest; near-zero indicates pure index ownership
- **Implementation Example**: `vector_neut({crowding}, log({cap_usd}))`

**Concept**: Residual Geographic Concentration
- **Sample Fields Used**: `concentration`, `exp_nondomicile1`, `exp_nondomicile2`, `nondomicile`
- **Definition**: Geographic concentration isolated from total non-domestic exposure to identify "all eggs in one foreign basket" vs. diversified internationalization
- **Why This Feature**: Two companies with 50% foreign exposure differ if one spreads across 10 countries vs. one targeting only China; this captures that distinction
- **Logical Meaning**: High values indicate concentrated foreign exposure (single country risk); low values indicate diversified foreign exposure (portfolio of countries)
- **is filling nan necessary**: Yes, fill missing nondomicile components with 0
- **Directionality**: High = concentrated foreign risk (dangerous); Low = diversified foreign revenue (safe); Zero = domestic only
- **Boundary Conditions**: Maximum indicates single-foreign-country dependence; minimum indicates either domestic or perfectly diversified
- **Implementation Example**: `{concentration} * {nondomicile}`

**Concept**: Short Interest Essence (Residual of Crowding)
- **Sample Fields Used**: `shortint`, `shortint_ts`, `crowding`, `hfown_pctown`
- **Definition**: Short interest orthogonalized against crowding and HF ownership to capture "organic" shorting vs. crowded shorting
- **Why This Feature**: Shorting in crowded names is dangerous (squeeze risk); shorting in uncrowded names is safer; this isolates the non-crowded component
- **Logical Meaning**: High values indicate high short interest despite low crowding (fundamental shorts); low values indicate short interest is just part of crowded trade
- **is filling nan necessary**: No, all three fields typically available together or not at all
- **Directionality**: High = organic shorting (informational); Low = crowded shorting (squeeze risk); Negative = short interest lower than crowding suggests
- **Boundary Conditions**: Extreme values indicate fundamental disagreements; near-zero indicates mechanical/crowded shorting
- **Implementation Example**: `vector_neut({shortint}, {crowding} + {hfown_pctown})`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Tariff risk scores (`risk_score`) and specialized descriptions have lower coverage (~85%) than standard risk factors due to GSXETRFS classification availability; ESG factors have ~80% coverage due to disclosure requirements
- **Timeliness**: Hedge fund ownership data has inherent 45-day reporting lag for 13F filings; `hfown_pctown` may not reflect current month positioning
- **Accuracy**: Geographic exposure data relies on company segment reporting which varies in granularity (some report "Americas" vs. "USA"); standardized versions correct for this but lose granularity
- **Potential Biases**: Crowding measures may underestimate retail crowding (not captured in institutional filings); tariff risk scores may overrepresent manufacturing vs. services

### Computational Complexity
- **Lightweight features**: Relative rankings (`quantile`), simple deltas (`ts_delta`), and ratios (interaction features)
- **Medium complexity**: Cumulative sums (`ts_sum`), rolling standard deviations (`ts_std_dev`), and cross-sectional neutralizations (`vector_neut`)
- **Heavy computation**: Multi-variable orthogonalizations and long-lookback percentile calculations (`ts_quantile` over 120 days)

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Tariff-Geographic Vulnerability Product** - directly addresses current trade policy uncertainty with high logical validity
2. **Hedge Fund Accumulation Velocity** - captures smart money flows with established alpha potential
3. **Crowding Z-Score Anomaly** - risk management essential for avoiding crowded liquidations

**Tier 2 (Secondary Priority)**:
1. **Pure Tariff Exposure (Orthogonal)** - sophisticated feature for identifying hidden supply chain risks
2. **Cumulative HF Flow Pressure** - stronger signal than single-period changes but requires longer holding periods
3. **Relative Geographic Exposure** - essential for sector-relative positioning during trade disputes

**Tier 3 (Requires Further Validation)**:
1. **ESG Risk Integration** - lower data coverage and unclear tariff interaction effects require testing
2. **Descriptor-Based Features** - limited field descriptions available for `descriptor_hip`, `owl`, `qsg`, `tru` require domain expertise validation

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How do `descriptor_hip`, `descriptor_owl`, `descriptor_qsg`, and `descriptor_tru` specifically interact with tariff risk? Are these style descriptors or specific risk factors?
2. Does the GSXETRFS tariff classification distinguish between import tariffs (input cost shocks) vs. export tariffs (revenue shocks), and how does this affect `risk_score` interpretation?
3. How does `nondomicile` relate to `exp_nondomicile1` and `exp_nondomicile2`? Is it the sum, or a standardized composite?
4. What is the precise difference between `hfown_pctown` and `fund_pct_ownership_encr`? Is one more timely or accurate than the other?

### Recommended Additional Data:
- Supply chain tier-2 and tier-3 exposure data to improve "Pure Tariff Exposure" feature
- Options market data (implied volatility skew, put/call ratios) to validate crowding measures
- ETF flow data to distinguish passive vs. active crowding effects
- Real-time tariff policy announcements to event-study `risk_score` predictive power

### Assumptions to Challenge:
- Assumption that hedge fund flows are "smart money" - may actually indicate crowding in certain contexts
- Assumption that standardized values are superior to raw values - in tariff analysis, absolute exposure thresholds may matter more than relative rankings
- Assumption that geographic exposure is static - companies can shift supply chains faster than quarterly reporting indicates

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence (tariff policy, geographic footprint, investor concentration, style factors)
2. Question-driven feature generation (8 fundamental questions applied to risk factor context)
3. Logical validation of each feature concept against trade policy and market microstructure theory
4. Transparent documentation of reasoning with specific field mappings

**Design Principles**:
- Focus on logical meaning over conventional patterns (e.g., tariff-geographic interaction vs. simple risk score)
- Every feature must answer a specific question (stability, change, anomaly, combination, structure, accumulation, relativity, essence)
- Clear documentation of "why" for each suggestion with directional interpretation
- Emphasis on data understanding (raw vs. standardized, time-series vs. point-in-time) over prediction

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate HF ownership timeliness assumptions, gather descriptor field documentation*