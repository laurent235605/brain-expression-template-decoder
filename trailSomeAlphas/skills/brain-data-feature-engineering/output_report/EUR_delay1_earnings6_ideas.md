# International Findings Data (earnings6) Feature Engineering Analysis Report

**Dataset**: earnings6
**Region**: EUR
**Delay**: 1


**Dataset**: earnings6
**Category**: Earnings
**Region**: EUR
**Analysis Date**: 2024-01-15
**Fields Analyzed**: 66

---

## Executive Summary

**Primary Question Answered by Dataset**: When and how do companies report earnings, and what do the timing, magnitude, and metadata of these corporate events reveal about firm performance, management confidence, and future price movements?

**Key Insights from Analysis**:
- Dataset captures a comprehensive calendar of corporate events (earnings, dividends, splits, meetings) with both scheduled (estimated) and realized (actual) timestamps, enabling measurement of expectation vs. reality
- Core value lies in the EPS surprise calculation (actual vs. estimated) and the verification status of forward-looking dates (tentative vs. verified)
- Dividend fields provide cash flow policy signals, while meeting and split data capture governance and capital structure events
- Temporal structure is rich with fiscal year/quarter alignment, allowing for seasonal and sequential analysis

**Critical Field Relationships Identified**:
- `actual_eps` and `estimated_eps` form the expectation-reality gap that drives post-earnings drift
- `next_ed` (next earnings date) and `etype_219` (date status) combine to form a confidence-weighted forward calendar
- `x_dividend` and `dividend_status_240` interact to reveal policy stability vs. changes

**Most Promising Feature Concepts**:
1. **EPS Surprise Deviation** - because the delta between actual and estimated EPS is the primary market-moving signal in earnings data
2. **Dividend Stability Coefficient** - because consistent dividend amounts signal cash flow stability and management confidence
3. **Earnings Date Verification Premium** - because verified dates likely contain less uncertainty than tentative dates

---

## Dataset Deep Understanding

### Dataset Description
This dataset offers daily snapshots of international corporate events, including earnings announcements, conference calls, dividend declarations, shareholder meetings, and other key financial events. It provides detailed metadata such as event status, timing, fiscal period, and confirmation level, along with links to press releases and filings. By tracking the timing and revisions of earnings dates, dividend actions, and other corporate events, the dataset enables researchers and traders to anticipate market-moving disclosures, identify signals of management intent, and exploit calendar-based trading strategies. Its forward-looking coverage and granular event data are valuable for predicting price movements, volatility spikes, and abnormal returns around scheduled corporate actions.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| `actual_eps` | Realized diluted non-GAAP EPS | Number | Quarterly | 85% |
| `estimated_eps` | Estimize weighted consensus estimate | Number | Daily | 80% |
| `next_ed` | Next scheduled earnings date | Date | Daily | 90% |
| `etype_219` | Date status (Tentative/Verified/Inferred) | String | Daily | 90% |
| `x_dividend` | Dividend amount in USD | Number | Periodic | 70% |
| `dividend_status_240` | Payment status flag (Pays/Suspended/etc) | String | Periodic | 70% |
| `change_absolute_value` | Absolute EPS change from prior period | Number | Quarterly | 75% |
| `change_percentage_value` | Percentage EPS change from prior period | Number | Quarterly | 75% |
| `stock_split_ratio_243` | Split parameters (new:old) | String | As needed | 15% |
| `board_of_directors_meeting` | Scheduled governance meeting date | Date | Periodic | 60% |
| `conferencecalltime` | Time of earnings conference call | String | Quarterly | 65% |
| `range_lower_bound` | Preliminary EPS range lower bound | Number | Quarterly | 40% |
| `range_upper_bound` | Preliminary EPS range upper bound | Number | Quarterly | 40% |

*(Additional fields include fiscal year identifiers, URLs, status codes, and exchange metadata)*

### Field Deconstruction Analysis

#### actual_eps: Realized Earnings Per Share
- **What is being measured?**: The diluted (or basic if diluted unavailable) non-GAAP earnings per share as reported in official press releases or SEC filings
- **How is it measured?**: Extracted from company press releases or regulatory filings (SEDAR/SEC) by data vendor
- **Time dimension**: Point-in-time quarterly observation representing cumulative quarterly performance
- **Business context**: Core metric of profitability; the ground truth against which estimates are judged
- **Generation logic**: Accounting-based calculation subject to audit and restatement risk
- **Reliability considerations**: Non-GAAP adjustments may vary; restatements create look-ahead bias if not handled; delay=1 mitigates timing issues

#### estimated_eps: Consensus Earnings Estimate
- **What is being measured?**: Crowdsourced or analyst consensus expectation of upcoming EPS from Estimize platform
- **How is it measured?**: Weighted average of contributor estimates, updated continuously until earnings release
- **Time dimension**: Forward-looking expectation that converges to actual over time as information arrives
- **Business context**: Represents market expectation; the benchmark for measuring earnings surprise
- **Generation logic**: Survey-based with weighting by contributor historical accuracy
- **Reliability considerations**: Coverage varies by market cap; may be stale for illiquid names; subject to herding behavior

#### next_ed: Next Earnings Date
- **What is being measured?**: Calendar date of upcoming earnings announcement
- **How is it measured?**: Company-announced or inferred from historical patterns; verified by data vendor
- **Time dimension**: Forward-looking calendar entry that updates as companies confirm dates
- **Business context**: Critical for event-driven strategies; timing affects volatility forecasting and position management
- **Generation logic**: Mix of company announcements (verified) and algorithmic inference (tentative)
- **Reliability considerations**: Subject to change; etype_219 field indicates confidence level; cancellations rare but possible

#### x_dividend: Dividend Amount
- **What is being measured?**: Cash dividend per share declared by the board, converted to USD
- **How is it measured?**: Board declaration captured from press releases; forex conversion at entry time
- **Time dimension**: Periodic declaration (quarterly/annual/special); point-in-time amount
- **Business context**: Signal of cash flow sustainability and capital allocation policy; income component of total return
- **Generation logic**: Board discretion based on earnings and cash position
- **Reliability considerations**: Special dividends create one-time spikes; suspension/resumption flagged in dividend_status_240; currency conversion adds noise for non-USD dividends

#### etype_219: Earnings Date Status
- **What is being measured?**: Categorical classification of how the next earnings date was determined
- **How is it measured?**: Vendor classification: T (Tentative), V (Verified), I (Inferred)
- **Time dimension**: Updates as unconfirmed dates become verified through company announcements
- **Business context**: Information quality indicator; verified dates suggest higher certainty and potentially less pre-announcement volatility
- **Generation logic**: Rule-based classification depending on source of date information
- **Reliability considerations**: Verified status reduces uncertainty but doesn't eliminate date changes; inferred dates may be less reliable for event timing strategies

### Field Relationship Mapping

**The Story This Data Tells**:
The dataset narrates the corporate event lifecycle: companies schedule earnings announcements (next_ed, etype_219), analysts form expectations (estimated_eps), companies reveal performance (actual_eps, change_percentage_value), and boards allocate capital (x_dividend, dividend_status_240). Interspersed are governance events (board_of_directors_meeting) and capital structure changes (stock_split_ratio_243). The tension between estimated and actual EPS creates price discovery, while the stability or volatility of dividends signals financial health.

**Key Relationships Identified**:
1. **Expectation-Reality Gap**: actual_eps vs. estimated_eps forms the earnings surprise, a primary driver of post-event price drift
2. **Temporal Certainty**: next_ed and etype_219 combine to form a confidence-weighted timeline; verified dates should theoretically have different volatility profiles than tentative dates
3. **Cash Flow Signaling**: x_dividend amounts correlate with actual_eps levels, but the dividend_status_240 (suspended/resumed) often leads earnings deterioration or recovery
4. **Information Architecture**: Presence of preliminary ranges (range_lower_bound, range_upper_bound) vs. point estimates indicates management guidance style and potentially different surprise distributions

**Missing Pieces That Would Complete the Picture**:
- Real-time timestamps of when estimates are updated (to measure revision momentum more precisely)
- Conference call sentiment metrics or Q&A length to gauge management tone beyond numerical EPS
- Peer group identifiers to enable relative earnings surprise calculations within sectors

---

## Feature Concepts by Question Type


### Q1: "What is stable?" (Invariance Features)

**Concept**: Dividend Stability Coefficient
- **Sample Fields Used**: x_dividend
- **Definition**: Coefficient of variation (standard deviation / mean) of dividend amounts over a 252-day rolling window
- **Why This Feature**: Consistent dividend policies indicate stable cash flows and management confidence; high volatility in dividend amounts may signal earnings instability or cyclical business models
- **Logical Meaning**: Measures the regularity of dividend declarations; low values indicate stable income-focused companies, high values indicate irregular or special dividend payers
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. For dividend data, zero or null often means no dividend was declared, which is meaningful information about payout policy, so nan should be filled with 0 rather than forward-filled.
- **Directionality**: Lower values indicate stable dividend policy (potential quality signal); extremely high values indicate unpredictable payouts (potential risk or opportunity)
- **Boundary Conditions**: Near-zero values indicate perfectly consistent dividends; undefined when mean is zero (no dividends paid)
- **Implementation Example**: `divide(ts_std_dev(vec_avg({x_dividend}), 252), abs(ts_mean(vec_avg({x_dividend}), 252)))`

**Concept**: EPS Change Regularity
- **Sample Fields Used**: change_absolute_value
- **Definition**: Rolling standard deviation of absolute EPS changes over 63 days (quarterly window)
- **Why This Feature**: Measures the volatility of earnings momentum; companies with stable sequential earnings growth patterns may have different risk profiles than those with erratic changes
- **Logical Meaning**: Captures the consistency of earnings trajectory; stable businesses show low volatility in period-over-period changes
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. NaN values here likely represent missing data rather than meaningful zeros, so ts_backfill is appropriate to carry forward last known change.
- **Directionality**: Lower values indicate predictable earnings patterns (lower uncertainty); higher values indicate earnings volatility
- **Boundary Conditions**: Zero indicates perfectly smooth earnings growth; spikes indicate one-time events or inflection points
- **Implementation Example**: `ts_std_dev(ts_backfill(vec_avg({change_absolute_value}), 5), 63)`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: EPS Estimate Revision Momentum
- **Sample Fields Used**: estimated_eps
- **Definition**: Change in consensus EPS estimate over a 20-day window
- **Why This Feature**: Captures the direction and velocity of analyst sentiment shifts ahead of earnings; positive momentum may indicate information leakage or improving fundamentals
- **Logical Meaning**: Measures the slope of expectation formation; rising estimates suggest improving outlook, falling estimates suggest deterioration
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Estimates may have gaps between quarters; using ts_backfill preserves the last available estimate which remains the best guess until updated.
- **Directionality**: Positive values indicate upward revisions (bullish); negative values indicate downward revisions (bearish)
- **Boundary Conditions**: Large absolute values indicate significant news or guidance changes; zero indicates consensus stability
- **Implementation Example**: `ts_delta(ts_backfill(vec_avg({estimated_eps}), 5), 20)`

**Concept**: Dividend Status Transition
- **Sample Fields Used**: dividend_status_240
- **Definition**: Days since last change in dividend status category (Pays, Suspended, Resumed)
- **Why This Feature**: Captures the recency of policy changes; recent resumptions or suspensions are significant corporate events that may persist in market memory
- **Logical Meaning**: Measures the stability of dividend policy categorical state; low values indicate recent policy shifts
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Status changes are discrete events; NaN likely means no status assigned yet, which should be kept distinct until first observation.
- **Directionality**: Lower values indicate recent policy changes (higher event risk/opportunity); higher values indicate long-term policy stability
- **Boundary Conditions**: Zero indicates status changed today; increasing values indicate time elapsed since last corporate action
- **Implementation Example**: `days_from_last_change(vec_avg({dividend_status_240}))`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: EPS Surprise Magnitude
- **Sample Fields Used**: actual_eps, estimated_eps
- **Definition**: Absolute deviation of realized EPS from consensus estimate
- **Why This Feature**: The core anomaly signal in earnings data; large surprises historically correlate with post-earnings drift and volatility expansion
- **Logical Meaning**: Quantifies the information shock delivered by the earnings announcement; represents the magnitude of expectation violation
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Both actual and estimated may have NaN before release; difference should only be calculated when both exist to avoid false signals.
- **Directionality**: Higher absolute values indicate larger surprises (higher immediate volatility and drift potential); zero indicates perfect consensus accuracy
- **Boundary Conditions**: Extreme positive values indicate massive beats; extreme negative values indicate massive misses; cross-sectional ranking often more important than absolute level
- **Implementation Example**: `abs(subtract(vec_avg({actual_eps}), vec_avg({estimated_eps})))`

**Concept**: Preliminary Range Uncertainty
- **Sample Fields Used**: range_lower_bound, range_upper_bound
- **Definition**: Width of preliminary earnings guidance range (upper minus lower)
- **Why This Feature**: Companies issuing wide preliminary ranges may have higher fundamental uncertainty or volatility; narrow ranges suggest confidence in forecasts
- **Logical Meaning**: Measures management's own assessment of earnings predictability; proxy for fundamental business volatility
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value itself has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Not all companies provide ranges; NaN indicates point guidance or no guidance, which is meaningful information about disclosure style and should not be filled arbitrarily.
- **Directionality**: Higher values indicate greater uncertainty or volatility in expected results; zero or NaN indicates point estimate or no guidance
- **Boundary Conditions**: Very wide ranges suggest binary outcomes or high uncertainty; tight ranges suggest high conviction
- **Implementation Example**: `subtract(vec_avg({range_upper_bound}), vec_avg({range_lower_bound}))`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: Dividend-Earnings Interaction Yield
- **Sample Fields Used**: x_dividend, actual_eps
- **Definition**: Product of dividend amount and actual EPS as a proxy for total shareholder return intensity
- **Why This Feature**: Combines income and growth components; high values in both suggest strong total return potential; dividends without earnings support may be unsustainable
- **Logical Meaning**: Captures the joint distribution of profitability and cash distribution; identifies companies rewarding shareholders from genuine earnings power
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Zero dividends should be preserved as zero (use fill 0); missing EPS should remain NaN to avoid false signals.
- **Directionality**: High positive values indicate strong earnings with high payout (income + growth); negative or low values indicate either poor earnings or no dividend
- **Boundary Conditions**: Negative values occur when EPS is negative despite dividend (potentially unsustainable); zero indicates no dividend regardless of earnings
- **Implementation Example**: `multiply(vec_avg({x_dividend}), vec_avg({actual_eps}))`

**Concept**: Corporate Event Confluence
- **Sample Fields Used**: board_of_directors_meeting, actual_eps, stock_split_ratio_243
- **Definition**: Sum of binary indicators for multiple simultaneous corporate events (meeting + earnings + split)
- **Why This Feature**: Clustering of governance, earnings, and capital structure events may indicate significant corporate activity or strategic shifts; information overload or significant news days
- **Logical Meaning**: Measures the intensity of corporate disclosure activity; high values indicate busy event days that may have different liquidity/volatility profiles
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. NaN in event fields indicates absence of event; should be treated as 0 (no event) using if_else or similar.
- **Directionality**: Higher values indicate multiple simultaneous events (1-3 range); zero indicates no major events scheduled/reported
- **Boundary Conditions**: 3 indicates earnings, meeting, and split all occurring (rare, significant corporate activity); 0 indicates quiet period
- **Implementation Example**: `add(if_else(is_nan(vec_avg({board_of_directors_meeting})), 0, 1), add(if_else(is_nan(vec_avg({actual_eps})), 0, 1), if_else(is_nan(vec_avg({stock_split_ratio_243})), 0, 1)))`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: Split Ratio Structure
- **Sample Fields Used**: stock_split_ratio_243
- **Definition**: Numerical representation of stock split ratio to measure dilution or concentration event magnitude
- **Why This Feature**: Stock splits alter share structure and often signal management confidence (splits typically occur after price appreciation); reverse splits indicate distress
- **Logical Meaning**: Captures capital structure changes; high ratios indicate forward splits (liquidity increase), low ratios (or inverse) indicate reverse splits (distress)
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. NaN indicates no split; should remain NaN or be set to 1 (no change) depending on interpretation needs.
- **Directionality**: Values > 1 indicate forward splits (typically bullish signaling); values < 1 indicate reverse splits (typically bearish/distress); 1 or NaN indicates no change
- **Boundary Conditions**: Extreme values (e.g., 10:1 or 1:10) indicate major capital structure events; most values are NaN (no split)
- **Implementation Example**: `vec_avg({stock_split_ratio_243})`

**Concept**: Dividend Frequency Composition
- **Sample Fields Used**: div_freq_232
- **Definition**: Categorical density of dividend payment frequency (Annual, Semi-Annual, Quarterly, Monthly)
- **Why This Feature**: Payment frequency reveals cash flow stability and shareholder base preferences (monthly payers often REITs/utilities); changes in frequency signal policy shifts
- **Logical Meaning**: Structural component of shareholder yield; higher frequency suggests commitment to regular income distribution
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. NaN indicates non-dividend payer; should be preserved or mapped to zero frequency.
- **Directionality**: Higher encoded values indicate more frequent payments (monthly > quarterly > annual); zero/NaN indicates non-payer
- **Boundary Conditions**: Special dividends create categorical outliers; monthly payers are distinct structural category
- **Implementation Example**: `densify(vec_avg({div_freq_232}))`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: Trailing Twelve Month EPS Accumulation
- **Sample Fields Used**: actual_eps
- **Definition**: Rolling 252-day sum of actual EPS values to capture annual earnings power
- **Why This Feature**: Quarterly EPS is noisy; annual accumulation smooths seasonality and reveals underlying earnings trajectory and TTM profitability
- **Logical Meaning**: Measures the cumulative profitability over a full business cycle; less susceptible to quarterly timing artifacts
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Quarterly EPS releases create sparse data; ts_backfill necessary to carry last reported EPS forward in intervening periods to avoid summing mostly NaNs.
- **Directionality**: Higher values indicate strong annual profitability; negative values indicate annual losses; trend direction indicates improving/declining fundamentals
- **Boundary Conditions**: Zero crossing indicates break-even TTM; sustained negative values indicate distress
- **Implementation Example**: `ts_sum(ts_backfill(vec_avg({actual_eps}), 5), 252)`

**Concept**: Cumulative Dividend Yield Accrual
- **Sample Fields Used**: x_dividend
- **Definition**: Rolling 252-day sum of dividends declared to capture total annual income distributed
- **Why This Feature**: Individual dividend announcements are lumpy; annual sum reveals true yield and payout consistency; identifies stable income generators
- **Logical Meaning**: Total cash returned to shareholders over annual period; fundamental input for dividend yield calculations and income strategies
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Zero dividends are meaningful (no payment); should be treated as 0 not NaN. Use fill 0 for true accumulation.
- **Directionality**: Higher values indicate high dividend payout; zero indicates non-dividend payer; declining sums indicate dividend cuts
- **Boundary Conditions**: Spike indicates special dividend year; smooth accumulation indicates regular quarterly payer
- **Implementation Example**: `ts_sum(ts_backfill(vec_avg({x_dividend}), 5), 252)`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: Relative EPS Surprise Percentage
- **Sample Fields Used**: actual_eps, estimated_eps
- **Definition**: Percentage deviation of actual from estimated EPS (surprise / |estimate|)
- **Why This Feature**: Normalizes surprise magnitude by estimate size; 0.10 surprise on $1.00 estimate is more significant than on $10.00 estimate in percentage terms
- **Logical Meaning**: Standardized measure of expectation violation; comparable across companies of different sizes and earnings scales
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Division by zero protection needed if estimated_eps is 0; use if_else to handle.
- **Directionality**: Positive values indicate beat (bullish); negative values indicate miss (bearish); magnitude indicates degree of surprise
- **Boundary Conditions**: Extreme values when estimate near zero (divide by small number); zero indicates perfect consensus accuracy
- **Implementation Example**: `divide(subtract(vec_avg({actual_eps}), vec_avg({estimated_eps})), add(abs(vec_avg({estimated_eps})), 0.01))`

**Concept**: Dividend Persistence Ratio
- **Sample Fields Used**: x_dividend
- **Definition**: Current dividend divided by trailing 252-day average dividend
- **Why This Feature**: Measures whether current dividend is consistent with historical pattern; deviations indicate increases, cuts, or special payments
- **Logical Meaning**: Relative positioning of current payout vs. historical norm; 1.0 indicates perfectly consistent with history
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Historical mean requires backfill to calculate properly; current zero dividend should be preserved.
- **Directionality**: 1.0 indicates no change; >1 indicates dividend increase or special; <1 indicates decrease or omission; 0 indicates suspension
- **Boundary Conditions**: Undefined if historical mean is zero (new payer); spikes indicate special dividends
- **Implementation Example**: `divide(vec_avg({x_dividend}), add(ts_mean(ts_backfill(vec_avg({x_dividend}), 5), 252), 0.001))`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Information Verification Premium
- **Sample Fields Used**: etype_219
- **Definition**: Binary indicator for verified (1) vs. tentative/inferred (0) earnings dates
- **Why This Feature**: Cuts to the essence of information quality; verified dates likely have different uncertainty premiums than algorithmically inferred dates
- **Logical Meaning**: Captures the categorical distinction between confirmed corporate communication and modeled estimation; proxy for information reliability
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. NaN status should be treated as unverified (0) for conservative positioning.
- **Directionality**: 1 indicates high-confidence verified date (potentially lower volatility); 0 indicates tentative/inferred (higher uncertainty, potentially higher risk premium)
- **Boundary Conditions**: Binary classification; transitions from 0 to 1 indicate corporate confirmation events
- **Implementation Example**: `if_else(equal(vec_avg({etype_219}), 1), 1, 0)`

**Concept**: Guidance Accuracy Essence
- **Sample Fields Used**: actual_eps, range_lower_bound, range_upper_bound
- **Definition**: Deviation of actual EPS from the midpoint of preliminary guidance range
- **Why This Feature**: Strips away market estimates to focus on management's own forecasting ability; measures whether management guidance was optimistic, pessimistic, or accurate
- **Logical Meaning**: Quantifies management forecasting bias; positive values indicate conservative guidance (beat midpoint), negative indicate aggressive guidance (miss midpoint)
- **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example. Only calculable when preliminary range exists; should remain NaN otherwise as absence of guidance is meaningful.
- **Directionality**: Positive values indicate actual exceeded guidance midpoint (conservative management); negative indicates missed guidance (aggressive management); zero indicates perfect guidance accuracy
- **Boundary Conditions**: Extreme values when range is tight and actual is far outside (guidance miss); zero when actual equals midpoint
- **Implementation Example**: `subtract(vec_avg({actual_eps}), divide(add(vec_avg({range_lower_bound}), vec_avg({range_upper_bound})), 2))`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: European large-cap focused (TOPCS1600) with varying coverage for estimates (~80%) and dividends (~70%); preliminary ranges only available for ~40% of observations
- **Timeliness**: Delay=1 setting ensures no lookahead bias; however, intra-day announcement timing (time_of_day_220) may create subtle differences in signal timing
- **Accuracy**: Non-GAAP EPS definitions may vary by company; currency conversion for dividends (x_dividend) uses entry-time rates which may not match portfolio measurement currency
- **Potential Biases**: Survivorship bias in that only companies holding scheduled events are included; special dividends create one-time yield spikes that may appear as anomalies

### Computational Complexity
- **Lightweight features**: EPS Surprise Magnitude, Dividend-Earnings Interaction, Split Ratio Structure (single-day arithmetic)
- **Medium complexity**: EPS Revision Momentum, Relative EPS Surprise (20-day lookback with backfill)
- **Heavy computation**: Dividend Stability Coefficient, TTM Accumulation features (252-day rolling windows with backfill requirements)

### Recommended Prioritization

**Tier 1 (Immediate Implementation)**:
1. **EPS Surprise Magnitude** - Core earnings signal with strong empirical support for post-earnings drift; computationally simple
2. **Relative EPS Surprise Percentage** - Normalized version allowing cross-sectional comparison; essential for relative value strategies
3. **Dividend Persistence Ratio** - Identifies dividend changes which are sticky, significant events with long-term price impact

**Tier 2 (Secondary Priority)**:
1. **EPS Estimate Revision Momentum** - Captures pre-earnings information leakage and analyst herding behavior
2. **Information Verification Premium** - Exploits uncertainty differential between confirmed and inferred dates

**Tier 3 (Requires Further Validation)**:
1. **Corporate Event Confluence** - Complex interaction feature requiring validation that multiple events indeed create compounded effects
2. **Guidance Accuracy Essence** - Requires careful handling of missing preliminary ranges and interpretation of management bias directionality

---

## Critical Questions for Further Exploration

### Unanswered Questions:
1. How does the dataset handle earnings restatements, and do these appear as new records or updates to historical actual_eps values?
2. What is the empirical difference in volatility between "Verified" and "Tentative" earnings dates in the European market?
3. Do special dividends (identified by dividend_status_240 or frequency changes) have different predictive power than regular dividend changes?

### Recommended Additional Data:
- Intra-day timestamps of estimate updates to build true revision momentum (not just endpoint snapshots)
- Sector classification to enable relative earnings surprise calculations within industry groups
- Conference call duration and sentiment scores to supplement numerical EPS data with qualitative management tone

### Assumptions to Challenge:
- Assumption that all EPS surprises are created equal (do small-cap surprises matter more than large-cap in this dataset?)
- Assumption that delay=1 is sufficient for all event types (do board meeting announcements require different handling than earnings?)
- Assumption that USD-converted dividends (x_dividend) are comparable across currencies without volatility adjustment

---

## Methodology Notes

**Analysis Approach**: This report was generated by:
1. Deep field deconstruction to understand data essence (actual vs. estimated, scheduled vs. realized, categorical vs. numerical)
2. Question-driven feature generation (8 fundamental questions applied to earnings, dividend, and event calendar fields)
3. Logical validation of each feature concept against financial theory (post-earnings drift, dividend signaling, information uncertainty)
4. Transparent documentation of reasoning and boundary conditions

**Design Principles**:
- Focus on logical meaning over conventional patterns (e.g., guidance accuracy vs. simple earnings yield)
- Autonomous reasoning about vector field handling using vec_avg extraction before time-series operations
- Clear documentation of nan-handling logic specific to corporate event data (where absence is often meaningful signal)
- Emphasis on European market context (EUR region, TOPCS1600 universe)

---

*Report generated: 2024-01-15*
*Analysis depth: Comprehensive field deconstruction + 8-question framework*
*Next steps: Implement Tier 1 features, validate assumptions about restatement handling, test event confluence hypothesis*