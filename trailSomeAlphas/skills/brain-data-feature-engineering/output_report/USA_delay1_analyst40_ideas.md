# Information on board of director Feature Engineering Analysis Report

**Dataset**: analyst40
**Region**: USA
**Delay**: 1
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 20

---

## Executive Summary

**Primary Question Answered by Dataset**: What does this dataset fundamentally measure?
This dataset measures the composition, stability, and dynamism of corporate boards of directors, capturing demographic characteristics (gender, age diversity), tenure profiles (time in role, time to retirement), and movement dynamics (appointments, departures, turnover rates) segmented by director type (executive, supervisory, overall).

**Key Insights from Analysis**:
- The dataset contains a natural hierarchy: executive directors (ed_), supervisory directors (sd_), and overall board metrics, enabling structural analysis of governance layers
- Four distinct conceptual domains are present: board connections (implied by movement), human capital mobility (turnover rates), demographic character (gender, age), and independence (tenure differentials)
- Pre-2016 data coverage gaps exist for calculated flow fields (employmentrate, turnoverrate, netturnoverrate), requiring careful handling of NaN values for historical analysis
- Turnover metrics exist in both absolute (totalchange) and normalized forms (rates), allowing analysis of both magnitude and proportional impact

**Critical Field Relationships Identified**:
- totalchange = addin - moveout (implied by definition), though addin/moveout fields are not directly exposed in implementation templates
- employmentrate = newcount / (oldcount + newcount) and turnoverrate = moveout / (oldcount + newcount), showing complementary perspectives on board refreshment
- The ed_, sd_, and overall_ prefixes create parallel structures enabling ratio-based independence and governance structure analysis

**Most Promising Feature Concepts**:
1. **Turnover-Retirement Pressure Interaction** - because it combines immediate change dynamics with temporal urgency of upcoming retirements
2. **Executive-Supervisory Structural Gap** - because it captures governance independence through demographic and tenure differentials between control layers
3. **Cumulative Governance Flow** - because it captures the persistent effect of board refreshment policies over time beyond point-in-time snapshots

---

## Dataset Deep Understanding

### Dataset Description
This dataset about Boards of Directors has four parts now: 1) board_connection (connections between companies triggered by board directors' movements) 2) board_mobility (human capital records for boards), 3) board_character (board characters such as gender ratio, nationality mix, standard deviation for ages, etc.) 4) board_independence (independence of board according to the constitution of board directors).

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `anl40_addin` | Number of new directors | Integer | Daily | 100% (post-2016) |
| `anl40_brdcount` | Count of unique IDs of industry participants | Integer | Daily | 100% |
| `anl40_ed_genderratio` | proportion of male directors of executive directors | Float | Daily | 100% |
| `anl40_ed_timeretirement` | Average time to retirement of executive directors | Float | Daily | 100% |
| `anl40_ed_timerole` | average time in role of executive directors | Float | Daily | 100% |
| `anl40_employmentrate` | AddIn / (OldCount + NewCount) | Float | Daily | Post-20160729 |
| `anl40_moveout` | Number of leaving directors | Integer | Daily | 100% (post-2016) |
| `anl40_netturnoverrate` | TotalChanges / (OldCount + NewCount) | Float | Daily | Post-20160729 |
| `anl40_newcount` | How many directors in this company after today's movement | Integer | Daily | Post-20160729 |
| `anl40_oldcount` | How many directors in this company before today's movement | Integer | Daily | Post-20160729 |
| `anl40_overall_genderratio` | proportion of male directors of overall directors | Float | Daily | 100% |
| `anl40_overall_stdevage` | standard deviation of directors' ages of overall directors | Float | Daily | 100% |
| `anl40_overall_timeretirement` | average time to retirement of overall directors | Float | Daily | 100% |
| `anl40_overall_timerole` | average time in role of overall directors | Float | Daily | 100% |
| `anl40_sd_genderratio` | proportion of male directors of supervisory directors | Float | Daily | 100% |
| `anl40_sd_stdevage` | standard deviation of directors' ages of supervisory directors | Float | Daily | 100% |
| `anl40_sd_timeretirement` | average time to retirement of supervisory directors | Float | Daily | 100% |
| `anl40_sd_timerole` | average time in role of supervisory directors | Float | Daily | 100% |
| `anl40_totalchange` | Total changes in director members in that day | Integer | Daily | 100% |
| `anl40_turnoverrate` | MoveOut / (OldCount + NewCount) | Float | Daily | Post-20160729 |

### Field Deconstruction Analysis

#### `anl40_overall_genderratio`: Overall Board Gender Ratio
- **What is being measured?**: The proportion of male directors relative to total directors across the entire board
- **How is it measured?**: Calculated as count of male directors divided by total director count, aggregated daily
- **Time dimension**: Point-in-time snapshot with daily updates, though underlying composition changes infrequently
- **Business context**: Captures board diversity and potential governance quality; extreme values may indicate lack of diversity or potential bias
- **Generation logic**: Derived from director-level gender classifications aggregated to company level
- **Reliability considerations**: Binary classification assumption (male/not male) may miss non-binary identities; denominator changes affect ratio even if numerator constant

#### `anl40_netturnoverrate`: Net Turnover Rate
- **What is being measured?**: The net change in board membership normalized by board size, representing board refreshment velocity
- **How is it measured?**: (Additions - Departures) / (Previous Count + New Count), expressed as a rate
- **Time dimension**: Flow measure capturing daily changes relative to cumulative board size
- **Business context**: Indicates governance stability vs. dynamism; positive values suggest growth/refreshment, negative values suggest contraction/instability
- **Generation logic**: Requires tracking of individual director entries and exits matched to board size denominators
- **Reliability considerations**: Zero values may indicate true stability or data collection gaps; denominator sensitivity when board size is small (high variance)

#### `anl40_overall_timerole`: Average Time in Role
- **What is being measured?**: The average tenure (experience) of directors currently serving on the board
- **How is it measured?**: Mean of individual directors' time elapsed since appointment to current role
- **Time dimension**: Cumulative measure that increments daily for existing directors, jumps on new appointments
- **Business context**: Proxy for board experience and institutional knowledge; high values suggest entrenched governance, low values suggest new perspectives
- **Generation logic**: Calculated from appointment dates of current directors; affected by both new appointments and departures of long-tenured directors
- **Reliability considerations**: Discontinuous changes when long-tenured directors exit; sensitive to definition of "role" (board vs. committee positions)

#### `anl40_overall_timeretirement`: Average Time to Retirement
- **What is being measured?**: Expected remaining tenure until retirement for current board members
- **How is it measured?**: Calculated from individual director ages relative to typical retirement age (often 65-70) or mandatory retirement policies
- **Time dimension**: Decreasing function of time (decrements daily) with discontinuities on new appointments
- **Business context**: Indicator of impending board turnover pressure; low values suggest imminent refreshment needs, high values suggest stability
- **Generation logic**: Derived from birth dates/ages of directors; assumes standard retirement age thresholds
- **Reliability considerations**: Individual retirement decisions may not follow age thresholds; voluntary early retirement or delayed retirement creates noise

#### `anl40_overall_stdevage`: Age Diversity (Standard Deviation)
- **What is being measured?**: Dispersion of ages among board members, proxy for generational diversity and cognitive diversity
- **How is it measured?**: Standard deviation of individual director ages from the mean board age
- **Time dimension**: Stable with gradual drift; changes with appointments/departures of outlier-aged directors
- **Business context**: High values suggest age diversity (mix of young and experienced), low values suggest homogeneity; may correlate with innovation vs. stability preferences
- **Generation logic**: Statistical calculation from individual age data; sensitive to extreme values (very young or very old directors)
- **Reliability considerations**: Small boards (low brdcount) produce statistically unstable variance estimates; age data may be estimated or reported with errors

#### `anl40_brdcount`: Board Count
- **What is being measured?**: Total number of directors serving on the board (size of governance body)
- **How is it measured?**: Count of unique director IDs associated with the company
- **Time dimension**: Discrete changes on appointment/departure events
- **Business context**: Board size affects governance efficiency; too small lacks oversight capacity, too large suffers from coordination problems
- **Generation logic**: Simple aggregation of active director relationships
- **Reliability considerations**: Definition variability (inside vs. outside directors, advisory vs. voting members); double-counting risks in interlocking directorates

### Field Relationship Mapping

**The Story This Data Tells**:
This dataset narrates the evolution of corporate governance through the lens of human capital dynamics. It captures the tension between stability (tenure, time to retirement) and change (turnover rates, new appointments), moderated by structural composition (gender diversity, age diversity). The segmentation into executive vs. supervisory layers reveals how governance control is distributed between operational insiders and oversight outsiders.

**Key Relationships Identified**:
1. **The Refreshment Paradox**: High `employmentrate` combined with high `overall_timerole` suggests adding new directors to an experienced board (diversifying knowledge), while high `employmentrate` with low `overall_timerole` suggests complete board reconstruction
2. **The Retirement Pipeline**: Inverse relationship between `overall_timeretirement` and impending `turnoverrate`; as time to retirement decreases, turnover should theoretically increase (though voluntary retirement timing varies)
3. **Diversity-Tenure Tradeoff**: High `overall_stdevage` (generational diversity) may correlate with lower `overall_timerole` if younger directors are newer appointments, suggesting a diversity refreshment strategy
4. **Governance Structure Independence**: Divergence between `ed_genderratio` and `sd_genderratio` indicates different demographic composition of operational vs. oversight functions, potentially signaling independence or isolation of supervisory function

**Missing Pieces That Would Complete the Picture**:
- Committee-specific assignments (audit, compensation, nominating) to measure functional independence
- Interlocking directorate network measures (how connected is this board to others)
- Director-level expertise indicators (financial, industry, ESG expertise)
- Meeting frequency and attendance rates to measure engagement intensity
- Compensation data to align incentives analysis with composition analysis

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: Gender Composition Stability Score
- **Sample Fields Used**: overall_genderratio
- **Definition**: Rolling standard deviation of board gender ratio over 20 days to measure consistency in gender composition
- **Why This Feature**: Boards with stable gender composition suggest deliberate policy consistency, while high volatility may indicate reactive or inconsistent diversity practices
- **Logical Meaning**: Measures the consistency of board diversity policy implementation; low values indicate stable composition, high values indicate churn in gender representation
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. For gender ratio, NaN indicates missing data rather than meaningful absence, so ts_backfill is appropriate for maintaining continuity in stability measurement.
- **Directionality**: Lower values (low volatility) indicate governance stability and consistent diversity; higher values indicate composition instability
- **Boundary Conditions**: Near-zero values indicate perfectly stable gender composition; extremely high values indicate rapid turnover or data quality issues in small boards
- **Implementation Example**: ts_std_dev({overall_genderratio}, 20)

**Concept**: Tenure Consistency Index
- **Sample Fields Used**: overall_timerole
- **Definition**: Coefficient of variation (standard deviation divided by absolute mean) of average time in role over 20 days
- **Why This Feature**: Distinguishes between boards with consistent tenure profiles and those experiencing rapid tenure restructuring; normalized by mean to compare across different average tenure levels
- **Logical Meaning**: Relative volatility of board experience levels; captures whether the board is maintaining consistent institutional knowledge or undergoing experience restructuring
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Tenure data is continuous and NaN represents missing data, suitable for ts_backfill before calculating variation.
- **Directionality**: Lower values indicate stable tenure structure; higher values indicate tenure disruption or rapid appointments/departures
- **Boundary Conditions**: Values approaching zero indicate frozen tenure (no changes); values above 0.5 indicate significant tenure instability relative to average
- **Implementation Example**: divide(ts_std_dev({overall_timerole}, 20), abs(ts_mean({overall_timerole}, 20)))

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: Turnover Acceleration
- **Sample Fields Used**: netturnoverrate
- **Definition**: 5-day rate of change in net turnover rate to detect acceleration in board refreshment or contraction
- **Why This Feature**: Captures momentum in governance changes; positive acceleration suggests increasing refreshment activity, negative acceleration suggests slowing or reversing changes
- **Logical Meaning**: Second derivative of board composition change; indicates whether turnover trends are strengthening or weakening
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Net turnover rate has specific start date (20160729) where NaN before indicates no data, not zero, so ts_backfill should be used carefully or limited to available data range.
- **Directionality**: Positive values indicate accelerating board changes; negative values indicate decelerating or stabilizing board composition
- **Boundary Conditions**: Extreme positive values suggest rapid board reconstruction; extreme negative values suggest abrupt stabilization after high turnover
- **Implementation Example**: ts_delta({netturnoverrate}, 5)

**Concept**: Retirement Timeline Pressure
- **Sample Fields Used**: overall_timeretirement
- **Definition**: 10-day change in average time to retirement, reversed sign so decreasing time creates positive pressure signal
- **Why This Feature**: Boards with rapidly decreasing time to retirement face imminent succession pressure; captures urgency of upcoming mandatory turnover
- **Logical Meaning**: Proximity to retirement-driven board changes; positive values indicate increasing pressure (less time remaining), negative values indicate easing pressure
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Time to retirement decreases monotonically for existing directors, so NaN handling should preserve the decreasing trend structure.
- **Directionality**: Higher values indicate increasing retirement pressure (time running out faster); lower values indicate stable or extending retirement timelines
- **Boundary Conditions**: Large positive spikes indicate multiple directors approaching retirement simultaneously; sustained negative values unusual (directors un-retiring or data errors)
- **Implementation Example**: reverse(ts_delta({overall_timeretirement}, 10))

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: Turnover Z-Score Anomaly
- **Sample Fields Used**: netturnoverrate
- **Definition**: Standardized deviation of current net turnover from 60-day historical mean, normalized by historical volatility
- **Why This Feature**: Identifies unusual board change activity relative to company-specific historical patterns; flags potential governance crises or strategic shifts
- **Logical Meaning**: Statistical significance of current turnover level; measures how unusual current board activity is compared to the company's normal governance rhythm
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Historical window requires consistent data; NaN in historical window should be excluded from mean/std calculations rather than filled to avoid distorting baseline.
- **Directionality**: High absolute values indicate anomalous turnover (positive for unusual additions, negative for unusual departures); near-zero indicates normal turnover levels
- **Boundary Conditions**: Values beyond 2-3 standard deviations indicate extreme anomalies; values near zero indicate business-as-usual governance
- **Implementation Example**: divide(subtract({netturnoverrate}, ts_mean({netturnoverrate}, 60)), ts_std_dev({netturnoverrate}, 60))

**Concept**: Gender Parity Deviation
- **Sample Fields Used**: overall_genderratio
- **Definition**: Absolute distance of gender ratio from parity (0.5), measuring extremity of gender imbalance
- **Why This Feature**: Extreme deviations from gender parity may indicate governance diversity deficiencies or alternatively, sector-specific norms; captures extremeness of composition
- **Logical Meaning**: Degree of gender imbalance; zero indicates perfect parity, 0.5 indicates single-gender board
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Missing gender ratio should not be filled with arbitrary values before calculating deviation; use available data only.
- **Directionality**: Higher values indicate greater gender imbalance (male-dominated if >0.5, female-dominated if <0.5); lower values indicate balanced board
- **Boundary Conditions**: Value of 0 indicates perfect 50-50 split; value of 0.5 indicates all-male or all-female board; values above 0.4 indicate severe imbalance
- **Implementation Example**: abs(subtract({overall_genderratio}, 0.5))

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Experience-Diversity Interaction
- **Sample Fields Used**: overall_timerole, overall_genderratio
- **Definition**: Product of average tenure and female representation ratio (1 - male ratio), capturing boards with both high experience and high gender diversity
- **Why This Feature**: Identifies boards that achieve diversity without sacrificing experience, or conversely, experience without diversity; high values indicate rare combination of both attributes
- **Logical Meaning**: Synergy between institutional knowledge and cognitive diversity; measures governance quality through dual lens of tenure and representation
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Both fields have high coverage; cross-sectional group_mean can fill missing values if sector-specific patterns are desired.
- **Directionality**: Higher values indicate experienced and diverse boards; lower values indicate either inexperienced or homogeneous (or both) boards
- **Boundary Conditions**: Near-zero values indicate either zero tenure (new board) or zero female representation; maximum values capped by tenure limits and gender parity
- **Implementation Example**: multiply({overall_timerole}, subtract(1, {overall_genderratio}))

**Concept**: Change Pressure Index
- **Sample Fields Used**: turnoverrate, overall_timeretirement
- **Definition**: Product of current departure rate and average time to retirement, distinguishing between high turnover with distant retirements (restructuring) vs. near retirements (natural succession)
- **Why This Feature**: Distinguishes voluntary succession planning (high turnover, low time to retirement) from forced restructuring (high turnover, high time to retirement)
- **Logical Meaning**: Composite of current departures and future retirement obligations; high values indicate double pressure of current exits and upcoming mandatory turnover
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Turnover rate has limited history; truncating window to available data prevents forward-looking bias.
- **Directionality**: Higher values indicate intense turnover pressure (many leaving with many approaching retirement); lower values indicate stable board with distant retirements
- **Boundary Conditions**: Zero indicates no turnover regardless of retirement timeline; high values indicate governance crisis with simultaneous exits and pending retirements
- **Implementation Example**: multiply({turnoverrate}, {overall_timeretirement})

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Executive-Supervisory Gender Gap
- **Sample Fields Used**: ed_genderratio, sd_genderratio
- **Definition**: Difference between executive director gender ratio and supervisory director gender ratio, measuring demographic alignment between governance layers
- **Why This Feature**: Large gaps suggest different selection criteria or independence between operational and oversight functions; captures structural governance characteristics
- **Logical Meaning**: Degree of demographic alignment between board tiers; positive values indicate more male executives than supervisors, negative indicates more male supervisors
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Both fields typically available simultaneously; if one missing, the gap is undefined and should remain NaN.
- **Directionality**: Positive values indicate male-skewed executive layer relative to supervisory; negative values indicate male-skewed supervisory layer; near-zero indicates aligned gender composition
- **Boundary Conditions**: Range [-1, 1]; values near 0 indicate aligned diversity; values near ±1 indicate extreme divergence (e.g., all-male executives, all-female supervisors or vice versa)
- **Implementation Example**: subtract({ed_genderratio}, {sd_genderratio})

**Concept**: Independence Tenure Ratio
- **Sample Fields Used**: sd_timerole, overall_timerole
- **Definition**: Ratio of supervisory director tenure to overall board tenure, proxy for independence through outsider experience differentiation
- **Why This Feature**: Higher ratios suggest supervisory directors have comparable or greater tenure than average, potentially indicating insider-dominated oversight or experienced independent directors
- **Logical Meaning**: Relative experience of oversight layer vs. total board; values above 1 indicate supervisory directors are more tenured than average, below 1 indicate newer supervisory appointments
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Division by zero protection needed if overall_timerole is zero; use max(overall_timerole, small_constant) or handle via if_else.
- **Directionality**: Values above 1 indicate supervisory directors are more experienced than board average (potential entrenchment or wisdom); values below 1 indicate newer supervisory blood (potential independence or lack of experience)
- **Boundary Conditions**: Near-zero indicates new supervisory directors on experienced board; high values indicate entrenched supervisory function; undefined when overall tenure is zero
- **Implementation Example**: divide({sd_timerole}, {overall_timerole})

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Cumulative Net Governance Flow
- **Sample Fields Used**: netturnoverrate
- **Definition**: 60-day rolling sum of net turnover rates, capturing cumulative board refreshment or contraction over quarter
- **Why This Feature**: Point-in-time turnover may be noisy; cumulative measure captures persistent board building or dismantling trends over strategic timeframes
- **Logical Meaning**: Aggregate board change momentum over time; positive values indicate sustained growth/refreshment, negative values indicate sustained contraction
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Pre-2016 NaN should not be filled with zeros as that implies no turnover rather than missing data; use data only from available period.
- **Directionality**: Higher positive values indicate aggressive board expansion/refreshment; negative values indicate sustained board contraction; near-zero indicates stability over window
- **Boundary Conditions**: Theoretical unbounded but practically limited by board size constraints; extreme values indicate rapid governance transformation
- **Implementation Example**: ts_sum({netturnoverrate}, 60)

**Concept**: Cumulative Employment Intensity
- **Sample Fields Used**: employmentrate
- **Definition**: 60-day rolling sum of employment rates, measuring total board refreshment intensity independent of departures
- **Why This Feature**: Distinguishes between replacement turnover (balanced) and expansion/growth; high cumulative employment with low net turnover indicates pure replacement, high employment with high net indicates growth
- **Logical Meaning**: Total addition intensity over time; captures hiring momentum separate from net position changes
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Similar to net turnover, respect data availability boundaries.
- **Directionality**: Higher values indicate aggressive hiring/expansion; lower values indicate limited new appointments; zero indicates freeze on new directors
- **Boundary Conditions**: Maximum theoretical value constrained by 1.0 daily rate (complete board replacement); sustained high values indicate rapid board expansion strategy
- **Implementation Example**: ts_sum({employmentrate}, 60)

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Executive Tenure Premium
- **Sample Fields Used**: ed_timerole, sd_timerole
- **Definition**: Difference between average executive director tenure and supervisory director tenure, measuring experience differential between governance layers
- **Why This Feature**: Captures whether operational leadership is more entrenched than oversight; large premiums may indicate founder-dominated boards or executive capture
- **Logical Meaning**: Experience gap between operational and oversight functions; positive values indicate longer-tenured executives, negative indicate longer-tenured supervisors
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Sector-wise group_mean can fill missing values for specific director types if company has no executives or no supervisors (unusual but possible).
- **Directionality**: Positive values indicate executive experience exceeds supervisory (potential governance concern); negative values indicate experienced oversight relative to management (strong independence)
- **Boundary Conditions**: Extreme positive values indicate entrenched management with new oversight (capture risk); extreme negative values indicate experienced watchdogs with new management (acquisition scenario)
- **Implementation Example**: subtract({ed_timerole}, {sd_timerole})

**Concept**: Relative Age Diversity
- **Sample Fields Used**: sd_stdevage, overall_stdevage
- **Definition**: Ratio of supervisory director age diversity to overall board age diversity, capturing whether oversight layer has different generational composition than total board
- **Why This Feature**: Different age diversity in supervisory layer may indicate deliberate generational diversity strategy in oversight or conversely, homogeneous old-guard oversight
- **Logical Meaning**: Relative generational diversity of oversight function; values above 1 indicate more age-heterogeneous supervisors, below 1 indicate more homogeneous supervisors relative to board
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Stdev requires multiple observations; if board has few supervisors, variance may be NaN and should not be artificially filled.
- **Directionality**: Values above 1 indicate supervisors span more age ranges than board average (diverse oversight); values below 1 indicate supervisors are age-concentrated relative to board (homogeneous oversight)
- **Boundary Conditions**: Undefined when overall stdev is zero (all same age); high values indicate supervisory layer includes both very young and very old directors relative to board
- **Implementation Example**: divide({sd_stdevage}, {overall_stdevage})

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Net Governance Flow Essence
- **Sample Fields Used**: employmentrate, turnoverrate
- **Definition**: Difference between employment rate and turnover rate, capturing pure growth essence of board changes separate from replacement dynamics
- **Why This Feature**: Strips away replacement noise to reveal true board expansion or contraction; essential signal of governance scaling strategy
- **Logical Meaning**: Pure net addition rate; positive indicates growing governance body, negative indicates shrinking, zero indicates pure replacement
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Both fields have same data availability constraints; subtracting them preserves the relative timing of available data.
- **Directionality**: Positive values indicate net board expansion; negative values indicate net contraction; zero indicates balanced replacement (old out, new in)
- **Boundary Conditions**: Range constrained by [-1, 1]; +1 indicates massive hiring with no departures, -1 indicates mass exodus with no hiring, 0 indicates equilibrium
- **Implementation Example**: subtract({employmentrate}, {turnoverrate})

**Concept**: Board Experience Mass
- **Sample Fields Used**: overall_timerole, brdcount
- **Definition**: Product of average tenure and board size, representing total institutional knowledge person-years resident on the board
- **Why This Feature**: Captures the total governance capital available; large boards with long tenure represent massive institutional knowledge, small boards with short tenure represent fresh but limited oversight capacity
- **Logical Meaning**: Aggregate governance experience available to company; proxy for oversight capacity and historical continuity
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Board count rarely missing; tenure may be missing for new entities; cross-sectional median fill preserves relative sizing.
- **Directionality**: Higher values indicate massive institutional knowledge (potential entrenchment or wisdom); lower values indicate limited governance history (potential freshness or inexperience)
- **Boundary Conditions**: Near-zero indicates new startup board; values scale with company maturity; extremely high values indicate ancient, large boards (potential stagnation)
- **Implementation Example**: multiply({overall_timerole}, {brdcount})

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: Pre-2016-07-29 data gaps exist for `employmentrate`, `turnoverrate`, `netturnoverrate`, `newcount`, and `oldcount` due to historical data limitations. Features using these fields should incorporate availability checks or truncate analysis to post-2016 period.
- **Timeliness**: Daily updates with T+1 delay (as per dataset delay=1). Director movements are captured on effective date but subject to reporting delays in some jurisdictions.
- **Accuracy**: Gender ratio assumes binary classification and may not capture non-binary gender identities. Age data may be estimated from career history when exact birth dates unavailable.
- **Potential Biases**: Board size (brdcount) affects rate calculations (netturnoverrate, etc.) - small boards show higher variance in rates due to discrete nature of director counts. Turnover rates may be seasonally biased around annual meeting cycles.

### Computational Complexity
- **Lightweight features**: subtract({ed_genderratio}, {sd_genderratio}), abs(subtract({overall_genderratio}, 0.5))
- **Medium complexity**: ts_delta({netturnoverrate}, 5), divide({sd_timerole}, {overall_timerole}), ts_std_dev({overall_genderratio}, 20)
- **Heavy computation**: divide(subtract({netturnoverrate}, ts_mean({netturnoverrate}, 60)), ts_std_dev({netturnoverrate}, 60)) - requires nested time-series operations

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **Turnover-Retirement Pressure Interaction** - Combines two highly predictive governance dimensions; captures succession planning urgency with current activity
2. **Executive-Supervisory Gender Gap** - Simple subtraction with high interpretability for governance independence analysis
3. **Net Governance Flow Essence** - Fundamental decomposition of board dynamics into growth vs. replacement

**Tier 2 (Secondary Priority)**:
1. **Cumulative Net Governance Flow** - Captures trend persistence but requires careful handling of pre-2016 data gaps
2. **Independence Tenure Ratio** - Important for governance quality but sensitive to division-by-zero in small boards
3. **Turnover Acceleration** - Momentum signal useful for event detection but noisier than level measures

**Tier 3 (Requires Further Validation)**:
1. **Relative Age Diversity** - Conceptually interesting but age diversity (stdev) is statistically noisy for small boards
2. **Experience-Diversity Interaction** - Assumes positive interaction between tenure and gender diversity which may not hold across all sectors

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How do board_connection metrics (interlocking directorates) interact with the composition metrics analyzed here? Do connected boards show different turnover patterns?
2. What is the causal relationship between `overall_stdevage` (age diversity) and `netturnoverrate`? Does age diversity drive turnover or does turnover enable age diversity?
3. How do these board metrics correlate with subsequent firm performance, and do the relationships vary by industry life-cycle stage?

### Recommended Additional Data:
- Committee membership assignments (Audit, Compensation, Nominating) to calculate committee independence ratios
- Director-level expertise classifications (financial, legal, industry) to construct expertise diversity measures
- Board meeting frequency and attendance rates to measure engagement intensity beyond composition
- Peer group identification to enable relative ranking features (e.g., rank of turnover within industry)

### Assumptions to Challenge:
- **Tenure equals experience**: Assumes all tenure years are equally valuable; challenges include technological obsolescence of older directors' experience or regulatory changes invalidating historical knowledge.
- **Gender ratio as diversity proxy**: Assumes gender is the primary diversity dimension; challenges include cognitive diversity, cultural diversity, and professional background diversity not captured by gender alone.
- **Retirement age consistency**: Assumes standard retirement ages drive departures; challenges include performance-based removals, health events, and voluntary early retirement deviations.

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence across demographic, temporal, and dynamic dimensions
2. Question-driven feature generation (8 fundamental questions) applied to governance context
3. Logical validation of each feature concept against corporate governance theory
4. Transparent documentation of reasoning and implementation constraints

**Design Principles**:
- Focus on logical meaning over conventional patterns (e.g., emphasizing structural gaps between executive and supervisory layers)
- Every feature answers a specific governance question (stability, change, anomaly, etc.)
- Clear documentation of data limitations (pre-2016 gaps) and bias sources (small board effects)
- Emphasis on interaction effects between composition and dynamics rather than isolated metrics

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate turnover-retirement interaction hypothesis, gather committee assignment data for structural independence validation*