# Case Study: BEME Dataset Analysis

## Dataset Overview

**Dataset ID**: BEME (Balance Sheet and Market Data)
**Description**: Book-to-market ratio and related financial metrics derived from balance sheet data combined with market data
**Region**: USA
**Universe**: TOP3000
**Delay**: 1
**Fields Analyzed**: 45 data fields

## Step 1: Field Deconstruction

### Key Fields Analyzed:

1. **book_value_per_share**
   - **What is it?**: Accounting net asset value divided by shares outstanding
   - **How measured?**: Quarterly financial statements (audited)
   - **Time dimension**: Quarterly snapshots (lagged)
   - **Business context**: Represents historical cost-based net worth
   - **Generation logic**: (Total assets - Total liabilities) / shares_outstanding
   - **Reliability**: High (audited), but backward-looking and conservative

2. **market_cap**
   - **What is it?**: Share price × shares outstanding (total market valuation)
   - **How measured?**: Real-time market data (continuous)
   - **Time dimension**: Instantaneous, changes continuously
   - **Business context**: Market participants' collective assessment of value
   - **Generation logic**: Last traded price × total shares
   - **Reliability**: Market-based, forward-looking, sentiment-influenced

3. **book_to_market**
   - **What is it?**: Ratio of book value to market value
   - **How measured?**: Calculated from book_value and market_cap
   - **Time dimension**: Compares slow-moving (book) with fast-moving (market)
   - **Business context**: Compares accounting perspectives with market perspective
   - **Generation logic**: book_value_per_share / (market_cap / shares)
   - **Reliability**: Useful but must understand both components

### Relationship Mapping:

**The Story**: BEME tells the story of how market perception relates to accounting reality

**Key Relationships**:
- book_to_market connects two valuation perspectives
- book_value changes slowly (quarterly, accountant-determined)
- market_cap changes quickly (continuously, market-determined)
- The gap represents market's view of intangible value

**Missing Pieces**:
- Why does the gap exist? (growth expectations, brand value, competitive position)
- How persistent is the gap? (temporary vs. structural)
- What causes gap changes? (earnings surprises, market sentiment, sector rotation)

## Step 2: Question-Driven Feature Generation

### Q1: "What is stable?" (Analyzing Invariance)

**Feature Concept**: "Market re-evaluation stability"
- **Implementation**: Rolling coefficient of variation of book_to_market over 60 days
- **Definition**: Stability of the market's valuation vs. book value assessment
- **Meaning**: Low CV = stable consensus, High CV = disagreement or uncertainty
- **Interpretation**:
  - High stability: Market has made up its mind about the company's valuation
  - Low stability: Market is uncertain or volatile in its assessment
- **Why it matters**: Stable mispricing (if book_to_market ≠ 1) can indicate structural factors

**Feature Concept**: "Book value reliability"
- **Implementation**: Autocorrelation of book_value changes over quarters
- **Definition**: Consistency of book value reporting
- **Meaning**: High autocorrelation = smooth reporting, Low = volatile changes
- **Interpretation**: Sudden changes may indicate accounting adjustments or write-downs

### Q2: "What is changing?" (Analyzing Dynamics)

**Feature Concept**: "Valuation gap velocity"
- **Implementation**: Rate of change of (market_cap - book_value × shares)
- **Definition**: How quickly is the valuation gap changing?
- **Meaning**: Fast increase = market becoming more optimistic or accounting write-downs
- **Interpretation**:
  - Positive velocity and acceleration: Market optimism increasing (bubble forming?)
  - Positive velocity, negative acceleration: Optimism plateauing
- **Why it matters**: Speed of gap change predicts sustainability

**Feature Concept**: "Book vs. market growth decomposition"
- **Implementation**: Separate book_value growth from market_cap growth
- **Definition**: book_growth = (BV_t - BV_{t-1}) / BV_{t-1}
- **Definition**: market_growth = (MC_t - MC_{t-1}) / MC_{t-1}
- **Meaning**: Which is driving the book_to_market change?
Interpretation**:
  - book_growth > market_growth: Company building real value faster than market recognizes
  - market_growth > book_growth: Market expectations running ahead of actual performance
  - **Why it matters**: Distinguishes fundamental from sentiment-driven changes

### Q3: "What is anomalous?" (Analyzing Deviation)

**Feature Concept**: "Unusual valuation persistence"
- **Implementation**: Days since book_to_market crossed 1.0 (either direction)
- **Definition**: How long has the stock been valued differently from book?
- **Meaning**: Persistent premium/discount suggests structural factors
**Interpretation**:
  - High persistence: Market has structural view (e.g., growth company, asset-light model)
  - Low persistence: Temporary mispricing that corrects
- **Why it matters**: Persistence indicates conviction level

**Feature Concept**: "Book value surprise magnitude"
- **Implementation**: Actual book_value vs. expected (trend-based forecast)
- **Definition**: Unexpected change in book value
- **Meaning**: Large surprises may indicate accounting adjustments
- **Interpretation**: Positive surprise = asset appreciation, Negative = write-downs

### Q4: "What is combined?" (Analyzing Interactions)

**Feature Concept**: "Intangible value proportion"
- **Implementation**: (market_cap - book_value × shares) / enterprise_value
- **Definition**: What portion of enterprise value comes from non-book sources?
- **Meaning**: Quantifies growth expectations, brand, competitive advantages
**Interpretation**:
  - High proportion: Value is in intangibles (risky but potentially high-growth)
  - Low proportion: Value is in tangible assets (safer but limited growth)
- **Why it matters**: Helps understand the nature of the company's value

**Feature Concept**: "Valuation tug-of-war"
- **Implementation**: book_momentum × market_momentum (where momentum is rate of change)
- **Definition**: Are book and market moving in same or opposite directions?
- **Meaning**: Agreeing signals vs. diverging signals
**Interpretation**:
  - Positive × positive: Both growing (healthy expansion)
  - Positive × negative: Market doubts book value growth (potential concern)
  - Negative × positive: Market optimistic despite book declines (turnaround story?)
  - Negative × negative: Both declining (distressed situation)

### Q5: "What is structural?" (Analyzing Composition)

**Feature Concept**: "Value composition stability"
- **Implementation**: Rolling correlation between book_growth and market_growth
- **Definition**: How consistent is the relationship between accounting and market value?
- **Meaning**: Stable correlation = predictable relationship, Unstable = relationship breaking down
- **Interpretation**: Declining correlation suggests business model change or market re-evaluation

**Feature Concept**: "Asset backing sufficiency"
- **Implementation**: book_value / (market_cap / shares) when book_to_market > 1
- **Definition**: How much asset coverage for market valuation?
- **Meaning**: Mercantile/asset-heavy businesses should have high ratios
- **Why it matters**: Helps identify when market undervaluation may be justified (e.g., declining industry)

### Q6: "What is cumulative?" (Analyzing Accumulation)

**Feature Concept**: "Accumulated valuation premium/discount"
- **Implementation**: Time-weighted sum of (market_cap - book_value) over 1 year
- **Definition**: Cumulative deviation from book value over time
- **Meaning**: Persistent premium = sustained growth expectations
**Interpretation**:
  - High positive accumulation: Market consistently optimistic
  - Near zero: Market fluctuates around book value
  - High negative accumulation: Market consistently pessimistic

**Feature Concept**: "Book quality decay"
- **Implementation**: Age of assets (based on depreciation schedules) weighted by value
- **Definition**: How old/stale is the book value?
- **Meaning**: Older book values less reliable (assets may be obsolete)
- **Why it matters**: Book value quality affects interpretation of book_to_market

### Q7: "What is relative?" (Analyzing Comparison)

**Feature Concept**: "Sector-relative valuation gap"
- **Implementation**: Company book_to_market - sector median book_to_market
- **Definition**: How does valuation gap compare to industry peers?
- **Meaning**: Sector-relative premium or discount
**Interpretation**:
  - Premium vs. sector: Justified if company has better prospects
  - Discount vs. sector: Potential opportunity or justified by worse fundamentals

**Feature Concept**: "Relative book value trend"
- **Implementation**: Company's book_growth - sector average book_growth
- **Definition**: Is company building value faster or slower than peers?
- **Meaning**: Competitive positioning in asset creation

### Q8: "What is essential?" (Analyzing Essence)

**Feature Concept**: "Core asset efficiency"
- **Implementation**: book_value / total_assets (stripping out intangibles/goodwill)
- **Definition**: What portion of assets are "hard" vs. "soft"?
- **Meaning**: Asset-light businesses have lower ratios
**Interpretation**:
  - Low ratio: Intangible-based business (software, brands, networks)
  - High ratio: Asset-heavy business (manufacturing, real estate)
- **Why it matters**: Affects interpretation of book_to_market (intangibles not on books)

**Feature Concept**: "Fundamental value anchor"
- **Implementation**: book_value plus time-adjusted retained earnings
- **Definition**: Book value adjusted for recent profitability
- **Meaning**: Asset base plus earnings power
**Why it's essential**: Combines two fundamental value sources

## Step 3: Feature Documentation Table

| Feature Concept | Fields Used | Question Answered | Logical Meaning | Directionality | Boundary Conditions |
|----------------|-------------|-------------------|-----------------|----------------|---------------------|
| Market re-evaluation stability | book_to_market | What is stable? | Consensus stability | Low=stable, High=disagreement | Zero=no variation, ∞=unstable |
| Valuation gap velocity | market_cap, book_value | What is changing? | Gap change rate | Positive=widening, Negative=narrowing | Zero=no change |
| Unusual valuation persistence | book_to_market | What is anomalous? | Premium/discount persistence | High=persistent belief | Zero=fluctuating |
| Intangible value proportion | market_cap, book_value | What is combined? | Non-book value share | High=intangible-based | Zero=all tangible |
| Value composition stability | book_growth, market_growth | What is structural? | Relationship consistency | High=stable relationship | Zero=breaking down |
| Accumulated premium/discount | market_cap - book_value | What is cumulative? | Time-weighted deviation | High=consensus, Around zero=fluctuation | Negative=persistent pessimism |
| Sector-relative gap | book_to_market, sector median | What is relative? | Peer comparison | Positive=premium to peers | Zero=sector average |
| Core asset efficiency | book_value, total_assets | What is essential? | Hard asset proportion | High=asset-heavy, Low=intangible-based | 0-1 range |

## Step 4: Implementation Insights

### Why This Approach Works:

1. **Novel**: Not just "moving averages of book_to_market" but deep conceptual features
2. **Meaningful**: Each feature answers a specific question about the data
3. **Testable**: Can validate if features capture what they claim to
4. **Actionable**: Clear interpretation guides usage

### Key Discoveries from Analysis:

1. **book_to_market alone is incomplete**: Need to understand both components
2. **Gap dynamics matter**: How the gap changes is more informative than level
3. **Persistence is informative**: Long-term premium/discount suggests structural views
4. **Comparative context essential**: Sector-relative measures remove noise
5. **Asset composition affects interpretation**: Intangible-heavy businesses naturally have low book values

### Suggestions for Further Analysis:

1. **Add earnings data**: Connect book_to_market with profitability metrics
2. **Add growth data**: Separate growth vs. value stories
3. **Add sector context**: Industry cycles affect interpretation
4. **Add sentiment data**: Market mood explains divergences
5. **Add fundamental data**: ROE, margins, leverage affect valuation

## Conclusion

This analysis demonstrates how questioning data essence and asking fundamental questions generates meaningful features, not just mathematical transformations. Each feature:

- Answers a specific question
- Has clear logical meaning
- Is grounded in data reality
- Avoids conventional patterns
- Reveals new insights

The book_to_market ratio becomes more than just "value indicator"—it becomes a window into market psychology, accounting reliability, and fundamental vs. sentiment-driven valuation.
