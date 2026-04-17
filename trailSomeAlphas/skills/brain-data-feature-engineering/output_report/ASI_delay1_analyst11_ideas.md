# ESG Scores Feature Engineering Analysis Report

**Dataset**: analyst11
**Region**: ASI
**Delay**: 1


**Dataset**: analyst11
**Category**: Analyst
**Region**: ASI
**Analysis Date**: 2024-05-15
**Fields Analyzed**: 50

---

## Executive Summary

**Primary Question Answered by Dataset**: How do companies rank within their peer groups across various ESG (Environmental, Social, Governance) dimensions, with emphasis on which ESG factors show the strongest correlation to financial returns?

**Key Insights from Analysis**:
- This dataset provides multi-layered ESG rankings: raw scores, percentile rankings, and correlation-weighted rankings
- The dataset distinguishes between "correlation-weighted" (any correlation) and "positive-correlation" (only positive correlations) metrics
- Peer group comparisons are structured hierarchically: sector > industry > subsector
- The dataset emphasizes which ESG factors matter most for financial performance, not just which companies score highest

**Critical Field Relationships Identified**:
1. Hierarchy of peer groups: sector (broadest), industry (middle), subsector (most specific)
2. Three types of ESG metrics: raw scores, correlation-weighted, positive-correlation-weighted
3. Three pillar structure: Environmental, Social, Governance, plus composite sustainability scores

**Most Promising Feature Concepts**:
1. **ESG Factor Alignment Gap** - because it measures the disconnect between a company's ESG performance and what the market actually rewards financially
2. **ESG Consensus Strength** - because it identifies companies where all peer group rankings agree, suggesting clear ESG positioning
3. **ESG Financial Relevance Score** - because it quantifies how much a company's ESG strengths align with financially material factors

---

## Dataset Deep Understanding

### Dataset Description
This dataset provides comprehensive ESG (Environmental, Social, Governance) scoring with a unique twist: it doesn't just measure ESG performance, but weights that performance by how strongly each ESG factor correlates with financial returns. The dataset includes percentile rankings within three peer group levels (sector, industry, subsector) and distinguishes between general correlation-weighted metrics and specifically positive-correlation-weighted metrics. This allows researchers to identify not just which companies are "good" at ESG, but which companies excel at the ESG factors that actually matter for financial performance.

### Field Inventory
| Field ID | Description | Data Type | Update Frequency | Coverage |
|----------|-------------|-----------|------------------|----------|
| community_maxcorr_sector_percentile | Percentile ranking within sector peer group for community score weighted by strongest correlation to financial returns. | Float | Quarterly | ~85% |
| sustainability_sector_rank | Company's rank within its sector peer group for overall sustainability score. | Integer | Quarterly | ~85% |
| governance_corr_weighted_industry_percentile | Company's percentile within its industry based on governance score weighted by KPIs most correlated to financial returns. | Float | Quarterly | ~85% |
| workforce_sector_percentile | Company's percentile within its sector based on employee-related score. | Float | Quarterly | ~85% |
| employee_training_sector_rank | Company's rank within its sector peer group for employee training, safety, and well-being. | Integer | Quarterly | ~85% |
| sustainability_corr_weighted_industry_percentile | Company's percentile within its industry based on sustainability score weighted by KPIs most correlated to financial returns. | Float | Quarterly | ~85% |
| disclosure_transparency_sector_percentile | Percentile ranking within sector peer group for disclosure, transparency, and accountability. | Float | Quarterly | ~85% |
| workforce_corr_weighted_industry_percentile | Company's percentile within its industry based on employee-related score weighted by KPIs most correlated to financial returns. | Float | Quarterly | ~85% |
| board_independence_industry_rank | Company's rank within its industry peer group for board independence and diversity. | Integer | Quarterly | ~85% |
| workforce_positive_corr_sector_position | Company's position within its sector based on employee-related score weighted by KPIs most positively correlated to financial returns. | Float | Quarterly | ~85% |

*(Additional fields follow similar patterns)*

### Field Deconstruction Analysis

#### community_maxcorr_sector_percentile: Community Max Correlation Sector Percentile
- **What is being measured?**: How a company's community engagement performance compares to sector peers, but only considering the aspects of community engagement that show the strongest statistical relationship to financial returns
- **How is it measured?**: Percentile ranking (0-100) within sector, with community score components weighted by their correlation coefficients to financial metrics
- **Time dimension**: Point-in-time snapshot, likely quarterly or annually updated
- **Business context**: Identifies companies that are good at the community engagement activities that actually impact financial performance
- **Generation logic**: 1) Calculate correlation between community engagement sub-scores and financial returns, 2) Weight community score by these correlations, 3) Rank within sector, 4) Convert to percentile
- **Reliability considerations**: Correlation stability over time, sector definition consistency, financial metric selection

#### sustainability_sector_rank: Sustainability Sector Rank
- **What is being measured?**: Absolute ranking position of a company's overall sustainability performance within its sector
- **How is it measured?**: Integer rank (1 = best) based on composite sustainability score
- **Time dimension**: Point-in-time ranking, ordinal rather than continuous
- **Business context**: Shows where a company stands relative to sector competitors on overall sustainability
- **Generation logic**: 1) Calculate composite sustainability score, 2) Sort all companies in sector by score, 3) Assign rank positions
- **Reliability considerations**: Rank is sensitive to number of companies in sector, composite score weighting methodology

#### governance_corr_weighted_industry_percentile: Governance Correlation Weighted Industry Percentile
- **What is being measured?**: Governance performance percentile within industry peer group, weighted by governance factors' correlation to financial returns
- **How is it measured?**: Percentile (0-100) within industry, with governance components weighted by their financial correlation
- **Time dimension**: Snapshot with correlation weighting that may change slowly
- **Business context**: Identifies governance leaders on factors that matter financially within specific industries
- **Generation logic**: Industry-level version of correlation-weighted percentile calculation
- **Reliability considerations**: Industry classification consistency, correlation calculation methodology

### Field Relationship Mapping

**The Story This Data Tells**:
This dataset tells a sophisticated story about ESG performance with a financial lens. Instead of just asking "who's good at ESG?", it asks "who's good at the ESG factors that actually drive financial performance?" The data is structured in three dimensions: 1) ESG pillars (Environmental, Social, Governance, plus composites), 2) Peer group levels (sector, industry, subsector), and 3) Weighting methodologies (raw, correlation-weighted, positive-correlation-weighted). This creates a rich matrix for understanding not just ESG performance, but financially material ESG performance within relevant competitive contexts.

**Key Relationships Identified**:
1. **Hierarchy consistency**: For each ESG dimension, there are parallel metrics at sector, industry, and subsector levels
2. **Weighting gradient**: Raw scores → correlation-weighted → positive-correlation-weighted represents increasing focus on financial materiality
3. **Pillar interdependence**: Social scores include workforce, community, human rights subcomponents; Governance includes board, disclosure, etc.
4. **Rank vs. Percentile duality**: Some fields provide ranks (absolute position), others percentiles (relative standing)

**Missing Pieces That Would Complete the Picture**:
- Time series of these metrics to track improvement/decline
- The actual correlation coefficients used for weighting
- Breakdown of which specific ESG factors have highest financial correlation
- Market reaction data to validate the correlation-weighted approach

---

## Feature Concepts by Question Type

### Q1: "What is stable?" (Invariance Features)

**Concept**: ESG Ranking Consistency Score
- **Sample Fields Used**: sector_percentile, industry_percentile, subsector_percentile
- **Definition**: Measures how consistent a company's ESG ranking is across different peer group levels
- **Why This Feature**: Companies with consistent rankings across sector/industry/subsector have more reliable ESG positioning
- **Logical Meaning**: High values indicate ESG performance is robust regardless of peer group definition
- **Directionality**: Higher = more consistent ESG positioning across peer groups
- **Boundary Conditions**: 100 = perfect consistency, 0 = completely inconsistent rankings
- **Implementation Example**: `abs({sector_percentile} - {industry_percentile}) + abs({industry_percentile} - {subsector_percentile})`

**Concept**: ESG Financial Materiality Stability
- **Sample Fields Used**: corr_weighted_score, positive_corr_score
- **Definition**: Difference between general correlation-weighted score and positive-correlation-only score
- **Why This Feature**: Measures stability of financial materiality signal - whether financially relevant ESG factors are consistently positive
- **Logical Meaning**: Small difference suggests ESG factors that correlate with returns do so consistently positively
- **Directionality**: Lower = more stable financial materiality signal
- **Boundary Conditions**: 0 = all correlated factors are positively correlated, large values = mixed correlation directions
- **Implementation Example**: `abs({corr_weighted_score} - {positive_corr_score})`

---

### Q2: "What is changing?" (Dynamics Features)

**Concept**: ESG Peer Group Ranking Divergence
- **Sample Fields Used**: sector_rank, industry_rank, subsector_rank
- **Definition**: Standard deviation of rankings across different peer group levels
- **Why This Feature**: Identifies companies whose ESG performance assessment depends heavily on peer group definition
- **Logical Meaning**: High divergence suggests ESG performance is context-dependent or peer group sensitive
- **Directionality**: Higher = more peer group dependent ESG assessment
- **Boundary Conditions**: 0 = identical ranking across all peer groups
- **Implementation Example**: `ts_std_dev({sector_rank}, 4) - ts_std_dev({industry_rank}, 4)`

**Concept**: Financial Materiality Signal Strength Trend
- **Sample Fields Used**: corr_weighted_percentile, positive_corr_percentile
- **Definition**: Rate of change in the gap between correlation-weighted and positive-correlation rankings
- **Why This Feature**: Tracks whether a company's ESG strengths are becoming more aligned with positively correlated factors
- **Logical Meaning**: Negative trend = improving alignment with positively correlated ESG factors
- **Directionality**: Downward trend = improving financial materiality alignment
- **Boundary Conditions**: Steep negative = rapid improvement in financially material ESG
- **Implementation Example**: `ts_delta({corr_weighted_percentile} - {positive_corr_percentile}, 90)`

---

### Q3: "What is anomalous?" (Deviation Features)

**Concept**: ESG Factor Alignment Gap
- **Sample Fields Used**: sector_percentile, corr_weighted_sector_percentile
- **Definition**: Difference between raw ESG percentile and correlation-weighted percentile
- **Why This Feature**: Identifies companies that are good at ESG generally but not at the ESG factors that matter financially
- **Logical Meaning**: Large positive gap = excels at ESG factors that don't correlate with returns
- **Directionality**: Higher = greater misalignment between ESG performance and financial materiality
- **Boundary Conditions**: 0 = perfect alignment, >50 = major misalignment
- **Implementation Example**: `{sector_percentile} - {corr_weighted_sector_percentile}`

**Concept**: Peer Group Ranking Anomaly
- **Sample Fields Used**: sector_rank, industry_rank
- **Definition**: Absolute difference between sector rank and industry rank, normalized by peer group size
- **Why This Feature**: Flags companies whose ESG assessment changes dramatically between sector and industry peer groups
- **Logical Meaning**: High values suggest either data issues or genuinely context-dependent ESG performance
- **Directionality**: Higher = more anomalous peer group ranking difference
- **Boundary Conditions**: >30% difference = significant anomaly worth investigating
- **Implementation Example**: `abs({sector_rank} - {industry_rank}) / max({sector_rank}, {industry_rank})`

---

### Q4: "What is combined?" (Interaction Features)

**Concept**: ESG Financial Relevance Score
- **Sample Fields Used**: corr_weighted_score, positive_corr_score, composite_score
- **Definition**: Weighted average emphasizing correlation-weighted scores over raw scores
- **Why This Feature**: Creates a single metric prioritizing financially material ESG factors
- **Logical Meaning**: Higher values indicate strong ESG performance on factors that matter for returns
- **Directionality**: Higher = better financially material ESG performance
- **Boundary Conditions**: 100 = perfect on financially material factors, 0 = poor on all dimensions
- **Implementation Example**: `0.4 * {corr_weighted_score} + 0.4 * {positive_corr_score} + 0.2 * {composite_score}`

**Concept**: ESG Consensus Strength
- **Sample Fields Used**: sector_percentile, industry_percentile, subsector_percentile
- **Definition**: Inverse of ranking dispersion across peer group levels
- **Why This Feature**: Identifies companies with consistent ESG assessment regardless of peer group definition
- **Logical Meaning**: High consensus suggests robust, unambiguous ESG positioning
- **Directionality**: Higher = more consistent ESG assessment across peer groups
- **Boundary Conditions**: 100 = perfect consensus, 0 = completely inconsistent
- **Implementation Example**: `100 - (abs({sector_percentile} - {industry_percentile}) + abs({industry_percentile} - {subsector_percentile}))`

---

### Q5: "What is structural?" (Composition Features)

**Concept**: ESG Pillar Balance Ratio
- **Sample Fields Used**: environmental_score, social_score, governance_score
- **Definition**: Ratio of strongest pillar to weakest pillar performance
- **Why This Feature**: Measures balance vs. specialization in ESG performance across pillars
- **Logical Meaning**: Lower ratio = more balanced ESG performance; higher ratio = specialized strength
- **Directionality**: Closer to 1 = more balanced; higher = more specialized
- **Boundary Conditions**: 1 = perfectly balanced, >3 = highly specialized
- **Implementation Example**: `max({environmental_score}, {social_score}, {governance_score}) / min({environmental_score}, {social_score}, {governance_score})`

**Concept**: Financial Materiality Concentration
- **Sample Fields Used**: corr_weighted_percentile, positive_corr_percentile
- **Definition**: Proportion of correlation-weighted performance captured by positive-correlation factors
- **Why This Feature**: Measures whether a company's financially material ESG strengths are in positively correlated areas
- **Logical Meaning**: Higher = ESG strengths concentrated in factors with positive financial correlation
- **Directionality**: Higher = better concentration in positively correlated factors
- **Boundary Conditions**: 1 = all correlated factors are positive, 0.5 = mixed, 0 = all negative correlation
- **Implementation Example**: `{positive_corr_percentile} / {corr_weighted_percentile}`

---

### Q6: "What is cumulative?" (Accumulation Features)

**Concept**: ESG Improvement Momentum
- **Sample Fields Used**: sector_percentile, industry_percentile
- **Definition**: Weighted moving average of percentile improvements across time
- **Why This Feature**: Captures sustained improvement trajectory in ESG rankings
- **Logical Meaning**: Positive = improving ESG standing over time
- **Directionality**: Higher = stronger improvement momentum
- **Boundary Conditions**: >0 = improving, <0 = deteriorating
- **Implementation Example**: `ts_sum(ts_delta({sector_percentile}, 30), 180)`

**Concept**: Financial Materiality Alignment Trend
- **Sample Fields Used**: corr_weighted_score, composite_score
- **Definition**: Cumulative improvement in alignment between overall ESG and financially material ESG
- **Why This Feature**: Tracks whether company is shifting ESG focus toward financially relevant factors
- **Logical Meaning**: Positive = improving alignment with financially material ESG factors
- **Directionality**: Higher = faster alignment improvement
- **Boundary Conditions**: Steep positive = rapid strategic shift toward material ESG
- **Implementation Example**: `ts_sum({corr_weighted_score} - {composite_score}, 360)`

---

### Q7: "What is relative?" (Comparison Features)

**Concept**: ESG Relative Advantage Score
- **Sample Fields Used**: sector_percentile, industry_percentile
- **Definition**: Difference between sector and industry percentile rankings
- **Why This Feature**: Measures whether a company performs better relative to broader or narrower peer groups
- **Logical Meaning**: Positive = stronger relative to sector than industry; suggests competitive advantage erodes in closer peer comparison
- **Directionality**: Positive = better in broader peer group; Negative = better in closer peers
- **Boundary Conditions**: Large positive = "big fish in big pond"; Large negative = "specialist in niche"
- **Implementation Example**: `{sector_percentile} - {industry_percentile}`

**Concept**: Financial Materiality Premium
- **Sample Fields Used**: corr_weighted_percentile, sector_percentile
- **Definition**: Percentage improvement in ranking when considering only financially material factors
- **Why This Feature**: Quantifies how much a company's ESG standing improves when focusing on what matters financially
- **Logical Meaning**: Positive = company is better at financially material ESG than ESG overall
- **Directionality**: Higher = greater financial materiality advantage
- **Boundary Conditions**: >0 = stronger on material factors; <0 = weaker on material factors
- **Implementation Example**: `({corr_weighted_percentile} - {sector_percentile}) / {sector_percentile}`

---

### Q8: "What is essential?" (Essence Features)

**Concept**: Core ESG Financial Alignment
- **Sample Fields Used**: positive_corr_score, composite_score
- **Definition**: Ratio of positive-correlation-weighted score to overall composite score
- **Why This Feature**: Distills ESG performance to its financially essential core - what actually matters for returns
- **Logical Meaning**: Measures proportion of ESG value that is financially material and positively correlated
- **Directionality**: Higher = greater proportion of ESG value is financially essential
- **Boundary Conditions**: 1 = all ESG value is financially essential; 0 = none is financially essential
- **Implementation Example**: `{positive_corr_score} / {composite_score}`

**Concept**: Peer Group Invariant ESG Strength
- **Sample Fields Used**: sector_percentile, industry_percentile, subsector_percentile
- **Definition**: Minimum percentile across all peer group levels
- **Why This Feature**: Conservative measure of ESG strength that holds regardless of peer group definition
- **Logical Meaning**: Worst-case ESG ranking across all relevant peer comparisons
- **Directionality**: Higher = stronger minimum guaranteed ESG standing
- **Boundary Conditions**: 100 = top performer in all peer groups; 0 = bottom in at least one group
- **Implementation Example**: `min({sector_percentile}, {industry_percentile}, {subsector_percentile})`

---

## Implementation Considerations

### Data Quality Notes
- **Coverage**: ~85% coverage for ASI