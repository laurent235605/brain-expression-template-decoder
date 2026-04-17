# Feature Engineering Mindset Patterns

This document provides a comprehensive framework for **thinking** about feature engineering, not a list of patterns to apply blindly.

## The Core Philosophy

**Feature engineering is not about finding predictive patterns—it's about understanding what data truly means and expressing that meaning in quantifiable ways.**

## 1. Data Semantic Understanding Framework

### Field Deconstruction Methodology

**For each field, ask these fundamental questions:**

#### What is being measured?
- Not just the surface description—what is the actual entity or concept?
- Example: Don't think "P/E ratio", think "price divided by earnings per share"
- What is the "thing" behind the numbers?

#### How is it measured?
- Data collection method (survey, sensor, calculation)
- Assumptions embedded in measurement
- Frequency and timing considerations
- Example: Book values are quarterly, audited, historical cost; market cap is continuous, forward-looking

#### What is the time dimension?
- Instantaneous snapshot (price at moment T)
- Cumulative value (total sales to date)
- Rate of change (velocity, acceleration)
- Memory/persistence (how long effects last)

#### Why does this field exist?
- What problem was it designed to solve?
- Who uses it and for what purpose?
- What business process generates it?

### Field Relationship Mapping

**Find the story the data tells:**

#### Identify connections:
- **Causal**: X causes Y (revenue → profit)
- **Complementary**: X and Y measure related aspects (price & volume)
- **Conflicting**: X and Y can diverge (book value vs. market cap)
- **Independent**: X and Y are unrelated (company location vs. stock price)

#### Build the narrative:
- What is the complete picture these fields paint?
- What are the key turning points?
- What is missing that would complete the story?

### Data Quality Assessment

**Evaluate from the source:**

#### Generation mechanisms:
- Manual entry (human error, bias, gaming)
- Automated collection (sensor precision, calibration)
- Calculated values (formula assumptions, input quality)

#### Reliability indicators:
- Audit trails and verification processes
- Consistency checks across sources
- Update frequency vs. true change rate

## 2. First-Principles Thinking

**Strip away all labels and assumptions.**

### The Process:
1. **Forget what you "know"**: Ignore domain-specific labels
2. **Identify raw components**: What are the fundamental elements?
3. **Question everything**: Why is it measured this way?
4. **Rebuild from basics**: Construct features from fundamental truths

### Example:
**Don't say**: "P/E ratio measures valuation"
**Do say**: "Price per share divided by earnings per share compares market price to accounting profit"

**First principles analysis**:
- Price: What market participants collectively believe value is
- Earnings: Accounting measure of profit generation
- Ratio: Comparison of two different perspectives on value
- **Insight**: The spread between perspectives is what matters, not the ratio itself

### Exercise:
For any field, write down:
- What is literally being measured (no jargon)
- What assumptions are built in
- What could cause it to be wrong
- What it would mean if it were very high or very low

## 3. Question-Driven Feature Generation

**Start with questions, not formulas.**

### The Question Bank:

#### Q1: "What is stable?" (Invariance)
**Purpose**: Find what doesn't change—it's often more meaningful than what does

**Leads to features about:**
- Stability measures (coefficient of variation)
- Invariant relationships (ratios that stay constant)
- Structural constants (parameters that define the system)

**Examples**:
- "Customer acquisition cost stability" = std_dev(CAC) / mean(CAC)
  - *Meaning*: Is our cost structure predictable?
  - *High value*: Costs are volatile, business model is unstable
  - *Low value*: Costs are predictable, scalable model

#### Q2: "What is changing?" (Dynamics)
**Purpose**: Understand motion, rate, and direction

**Leads to features about:**
- Velocity and acceleration
- Trend vs. noise
- Change significance

**Examples**:
- "Growth acceleration" = (revenue_t - revenue_{t-1}) - (revenue_{t-1} - revenue_{t-2})
  - *Meaning*: Is growth speeding up or slowing down?
  - *High value*: Accelerating growth
  - *Low value*: Decelerating growth
  - *Why it matters*: Acceleration is early signal of inflection points

#### Q3: "What is anomalous?" (Deviation)
**Purpose**: Identify what breaks patterns—the exceptions reveal rules

**Leads to features about:**
- Outliers and extremes
- Deviation from normal
- Pattern breaks

**Examples**:
- "Earnings surprise magnitude" = (actual - expected) / |expected|
  - *Meaning*: How much did results deviate from expectations?
  - *High value*: Significant surprise (positive or negative)
  - *Why it matters*: Surprises often trigger re-evaluation

#### Q4: "What is combined?" (Interaction)
**Purpose**: Understand how elements affect each other

**Leads to features about:**
- Synergies and conflicts
- Joint effects
- Conditional relationships

**Examples**:
- "Marketing-sales synergy" = (marketing_spend × sales_efficiency)
  - *Meaning*: Do marketing and sales amplify each other?
  - *High value*: Strong synergy (1+1=3)
  - *Low value*: Weak synergy (1+1=1.5)
  - *Why it matters*: Synergy indicates scalability

#### Q5: "What is structural?" (Composition)
**Purpose**: Decompose wholes into meaningful parts

**Leads to features about:**
- Component breakdowns
- Proportional relationships
- Structure changes

**Examples**:
- "Recurring revenue quality" = subscription_revenue / total_revenue
  - *Meaning*: What portion of revenue is predictable?
  - *High value*: High-quality recurring revenue
  - *Low value*: Low-quality one-time revenue
  - *Why it matters*: Predictability affects valuation

#### Q6: "What is cumulative?" (Accumulation)
**Purpose**: Capture time-based build-up and decay

**Leads to features about:**
- Running totals and diminishing returns
- Memory effects
- Time-weighted values

**Examples**:
- "Customer relationship depth" = Σ(purchase_value × e^{-days_ago / half_life})
  - *Meaning*: Time-decayed cumulative purchase value
  - *High value*: Deep, recent relationship
  - *Low value*: Shallow or old relationship
  - *Why it matters*: Recency and frequency predict loyalty

#### Q7: "What is relative?" (Comparison)
**Purpose**: Understand position in context

**Leads to features about:**
- Rankings and percentiles
- Normalizations
- Context-aware measures

**Examples**:
- "Relative efficiency" = company_efficiency / industry_median_efficiency
  - *Meaning*: How efficient vs. peers?
  - *High value*: More efficient than typical
  - *Low value*: Less efficient than typical
  - *Why it matters*: Competitiveness indicator

#### Q8: "What is essential?" (Essence)
**Purpose**: Distill to core truths

**Leads to features about:**
- First-principles measures
- Fundamental relationships
- Stripped-down indicators

**Examples**:
- "Core profitability" = (revenue - variable_costs) / revenue
  - *Meaning*: Profitability without fixed cost distortions
  - *Why it matters*: Shows true unit economics

### How to Use the Question Bank:

**For any dataset**:
1. Go through each question
2. Ask: "Which fields or combinations can answer this?"
3. Formulate specific feature concepts
4. Validate each concept has clear meaning
5. Document the reasoning

**Example Workflow:**
```
Dataset: Sales data with fields [customer_id, order_value, order_date, product_category]

Q: "What is stable?"
→ Average order value per customer over time
→ Favorite category per customer (most frequent)
→ Purchase frequency pattern

Q: "What is changing?"
→ Order value trend (increasing/decreasing)
→ Category preference evolution
→ Purchase interval changes

Q: "What is anomalous?"
→ Orders far from customer's typical behavior
→ Sudden category switches
→ Unusually large/small orders

Q: "What is combined?"
→ Order value × frequency = total value
→ Category diversity × consistency = loyalty measure
→ Recency × frequency = engagement score

... (continue through all questions)
```

## 4. Field Combination Logic Patterns

### When you combine fields, what are you really doing?

#### Addition: "X + Y" → What does this sum represent?
**Good when**: Combining parts of a whole
- Total revenue = product_A_revenue + product_B_revenue
**Bad when**: Adding unrelated concepts
- Price + volume (What does this mean?)

#### Subtraction: "X - Y" → What is the difference telling you?
**Good when**: Measuring gap or surplus
- Profit = revenue - costs
- Shortfall = target - actual
**Bad when**: Ignoring that difference scales with magnitude
- Revenue_2023 - revenue_2022 (better: percentage change)

#### Multiplication: "X × Y" → What is the joint effect?
**Good when**: Capturing interaction or scaling
- Total_value = price × quantity
- Weighted_importance = score × weight
**Bad when**: Mixing units without meaning
- Revenue × employee_count (What is "dollar-employees"?)

#### Division: "X / Y" → What ratio or rate are you computing?
**Good when**: Creating relative measures
- Efficiency = output / input
- Concentration = part / whole
**Bad when**: Denominator can be zero or meaningless
- Revenue / days_since_founded (early days distort heavily)

#### Conditional: "If X then Y" → What condition matters?
**Good when**: Threshold effects exist
- If temperature > 100°C then phase = "gas"
- If churn_risk > 0.8 then intervene = true
**Bad when**: Arbitrary thresholds without justification
- If customer_age > 30 then category = "old" (why 30?)

### The Deeper Question:
**"What new information does this combination create?"**

A good combination:
- Reveals something the individual fields hide
- Creates a new concept with clear meaning
- Has intuitive interpretation

A bad combination:
- Just applies math to numbers
- Creates meaningless units (dollar-days per employee)
- Is hard to explain

## 5. Escaping Conventional Thinking Traps

### Trap 1: "This is a [field type], so I should..."
**Wrong**: "This is price data, so I should calculate moving averages"
**Right**: "This is a time series of transaction values—what patterns exist?"

**Escaping method**: Pretend you don't know the field name or domain. Just look at:
- Data type (number, category, date)
- Update frequency
- Distribution
- Missingness pattern

**Ask**: What would a data scientist from a different field see?

### Trap 2: "Everyone uses [conventional feature], so I will too"
**Wrong**: Building P/E, moving averages, RSI because "that's what you do"
**Right**: Asking "What does this ratio truly mean? Is there a better way to express that concept?"

**Example with P/E**:
- Conventional: P/E = price / earnings ("valuation metric")
- First principles: Compares market's forward-looking assessment to accounting record
- Deeper question: Why do these diverge? What does divergence mean?
- Better feature: Track divergence trend, not just level

### Trap 3: "Complexity = better"
**Wrong**: Adding more variables, interactions, conditions to improve "sophistication"
**Right**: Simpler is often more robust and interpretable

**Test**: Can you explain the feature in one sentence to a non-expert?
- If no → It's too complex
- If yes → It might be valuable

### Trap 4: "Feature engineering is separate from domain knowledge"
**Wrong**: Applying math without understanding what fields mean
**Right**: Deep domain understanding → Better features

**Process**:
1. Understand the business process that generates each field
2. Identify pain points and edge cases in that process
3. Build features that capture those nuances
4. Validate with domain experts

## 6. Feature Validation Checklist

### Before finalizing any feature, verify:

#### □ Clear Definition
- [ ] Can be explained in one sentence
- [ ] Uses precise language
- [ ] Avoids jargon and buzzwords

#### □ Logical Meaning
- [ ] Represents a real phenomenon or concept
- [ ] Not just a mathematical operation
- [ ] Has intuitive interpretation

#### □ Business Relevance
- [ ] Connects to real-world decision-making
- [ ] Answers a meaningful question
- [ ] Reveals actionable insight

#### □ Directional Understanding
- [ ] What does high value mean?
- [ ] What does low value mean?
- [ ] Is there an optimal range?

#### □ Boundary Conditions
- [ ] What do extreme values indicate?
- [ ] What happens at zero/infinity?
- [ ] Are there theoretical limits?

#### □ Data Quality Awareness
- [ ] What are sources of noise?
- [ ] When might this be unreliable?
- [ ] What biases could affect it?

#### □ Novelty Check
- [ ] Does this reveal something new?
- [ ] Or just repackage existing information?
- [ ] Would an expert learn something?

### Example Validation:

**Feature**: Customer purchase velocity = total_purchases / account_age_days

- **Clear definition**: "Average number of purchases per day since account creation"
- **Logical meaning**: Measures purchase frequency over customer lifetime
- **Business relevance**: Indicates customer engagement and habit formation
- **Directional**: High = frequent buyer, Low = infrequent buyer
- **Boundaries**: Zero = no purchases, Very high = possible data error or bulk buyer
- **Data quality**: Affected by returns, multi-item orders, gift purchases
- **Novelty**: Reveals engagement pattern beyond simple total purchases

## 7. Creative Thinking Techniques

### A. Lateral Thinking (Borrow from other domains)

**Ask**: How would a physicist/biologist/sociologist approach this?
