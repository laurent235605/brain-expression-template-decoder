---
brain-data-feature-engineering methodology
---

# BRAIN Data Feature Engineering Workflow

**Purpose**: Automatically transform BRAIN dataset fields into deep, meaningful feature engineering ideas.

## Input Requirements

### Required Parameters:
- **data_category**: Dataset category (e.g., "fundamental", "analyst", "news", "model")
- **delay**: Data delay setting (0 or 1)
- **region**: Market region (e.g., "USA", "EUR", "ASI")

### Optional Parameters:
- **universe**: Trading universe (default: "TOP3000")
- **dataset_id**: Specific dataset ID (if known, skips discovery phase)

## Workflow Overview


### Step 2: Field Extraction and Deconstruction
- **Deconstruct each field's meaning**:
  * What is being measured? (the entity/concept)
  * How is it measured? (collection/calculation method)
  * Time dimension? (instantaneous, cumulative, rate of change)
  * Business context? (why does this field exist?)
  * Generation logic? (reliability considerations)
- **Build field profiles**: Structured understanding of each field's essence

### Step 3: Reasoning and Analysis
**performs deep analysis based on collected information:**

**A. Field Relationship Mapping**
- Analyze logical connections between fields
- Identify: independent fields, related fields, complementary fields
- Map the "story" the dataset tells
- **Key question**: What relationships are implied by these fields?

**B. Question-Driven Feature Generation (Internal Process)**
The skill asks itself these questions and generates feature concepts:

1. **"What is stable?"** → Look for invariants
   - Which fields or combinations remain relatively constant?
   - What stability measures make sense?

2. **"What is changing?"** → Analyze change patterns
   - Rate of change, acceleration, volatility
   - Trend vs. noise separation

3. **"What is anomalous?"** → Identify deviations
   - Outliers, unusual patterns, breaks from normal
   - Deviation magnitude and significance

4. **"What is combined?"** → Examine interactions
   - How fields interact, amplify, or offset each other
   - Synthesis creates new meaning

5. **"What is structural?"** → Study compositions
   - Constituent parts, proportional relationships
   - Structural changes over time

6. **"What is cumulative?"** → Explore accumulation effects
   - Building up over time, decay effects
   - Memory and persistence in data

7. **"What is relative?"** → Make comparisons
   - Relative positioning, ranking, normalization
   - Context within dataset

8. **"What is essential?"** → Distill to core meaning
   - First principles thinking
   - Strip away assumptions, get to essence

**C. Feature Concept Generation**
For each relevant question-field combination:
- Formulate feature concept that answers the question
- Define the concept clearly
- Identify the logical meaning
- Consider directionality (what high/low values mean)
- Identify boundary conditions
- Note potential issues/limitations

### Step 4: Feature Documentation
**For each generated feature concept, document:**
- **Concept Name**: Clear, descriptive name
- **Definition**: One-sentence definition
- **Logical Meaning**: What phenomenon/concept does it represent?
- **Why It's Meaningful**: Why does this feature make sense?
- **Directionality**: Interpretation of high vs. low values
- **Boundary Conditions**: What extremes indicate
- **Data Requirements**: What fields are used and any constraints
- **Potential Issues**: Known limitations or concerns

### Step 5: Output Generation
**Generate structured markdown report including:**

0. **Output the report markdown format** in the following format:

    # {dataset_name} Feature Engineering Analysis Report

    **Dataset**: {dataset_id}
    **Category**: {category}
    **Region**: {region}
    **Analysis Date**: {analysis_date}
    **Fields Analyzed**: {field_count}

    ---

    ## Executive Summary

    **Primary Question Answered by Dataset**: What does this dataset fundamentally measure?

    **Key Insights from Analysis**:
    - {insight_1}
    - {insight_2}
    - {insight_3}

    **Critical Field Relationships Identified**:
    - {relationship_1}
    - {relationship_2}

    **Most Promising Feature Concepts**:
    1. {top_feature_1} - because {reason_1}
    2. {top_feature_2} - because {reason_2}
    3. {top_feature_3} - because {reason_3}

    ---

    ## Dataset Deep Understanding

    ### Dataset Description
    {dataset_description}

    ### Field Inventory
    | Field ID | Description | Data Type | Update Frequency | Coverage |
    |----------|-------------|-----------|------------------|----------|
    | {field_1_id} | {field_1_desc} | {type_1} | {freq_1} | {coverage_1}% |
    | {field_2_id} | {field_2_desc} | {type_2} | {freq_2} | {coverage_2}% |
    | {field_3_id} | {field_3_desc} | {type_3} | {freq_3} | {coverage_3}% |

    *(Additional fields as needed)*

    ### Field Deconstruction Analysis

    #### {field_1_id}: {field_1_name}
    - **What is being measured?**: {measurement_object_1}
    - **How is it measured?**: {measurement_method_1}
    - **Time dimension**: {time_dimension_1}
    - **Business context**: {business_context_1}
    - **Generation logic**: {generation_logic_1}
    - **Reliability considerations**: {reliability_1}

    #### {field_2_id}: {field_2_name}
    - **What is being measured?**: {measurement_object_2}
    - **How is it measured?**: {measurement_method_2}
    - **Time dimension**: {time_dimension_2}
    - **Business context**: {business_context_2}
    - **Generation logic**: {generation_logic_2}
    - **Reliability considerations**: {reliability_2}

    *(Additional fields as needed)*

    ### Field Relationship Mapping

    **The Story This Data Tells**:
    {story_description}

    **Key Relationships Identified**:
    1. {relationship_1_desc}
    2. {relationship_2_desc}
    3. {relationship_3_desc}

    **Missing Pieces That Would Complete the Picture**:
    - {missing_1}
    - {missing_2}

    ---

    ## Feature Concepts by Question Type


    ### Q1: "What is stable?" (Invariance Features)

    **Concept**: {stability_feature_1_name}
    - **Sample Fields Used**: fields_used_1
    - **Definition**: {definition_1}
    - **Why This Feature**: {why_1}
    - **Logical Meaning**: {logical_meaning_1}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. 
    - **Directionality**: {directionality_1}
    - **Boundary Conditions**: {boundaries_1}
    - **Implementation Example**: `{implementation_1}`

    **Concept**: {stability_feature_2_name}
    - **Sample Fields Used**: fields_used_2
    - **Definition**: {definition_2}
    - **Why This Feature**: {why_2}
    - **Logical Meaning**: {logical_meaning_2}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_2}
    - **Boundary Conditions**: {boundaries_2}
    - **Implementation Example**: `{implementation_2}`

    ---

    ### Q2: "What is changing?" (Dynamics Features)

    **Concept**: {dynamics_feature_1_name}
    - **Sample Fields Used**: fields_used_3
    - **Definition**: {definition_3}
    - **Why This Feature**: {why_3}
    - **Logical Meaning**: {logical_meaning_3}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_3}
    - **Boundary Conditions**: {boundaries_3}
    - **Implementation Example**: `{implementation_3}`

    **Concept**: {dynamics_feature_2_name}
    - **Sample Fields Used**: fields_used_4
    - **Definition**: {definition_4}
    - **Why This Feature**: {why_4}
    - **Logical Meaning**: {logical_meaning_4}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_4}
    - **Boundary Conditions**: {boundaries_4}
    - **Implementation Example**: `{implementation_4}`

    ---

    ### Q3: "What is anomalous?" (Deviation Features)

    **Concept**: {anomaly_feature_1_name}
    - **Sample Fields Used**: fields_used_5
    - **Definition**: {definition_5}
    - **Why This Feature**: {why_5}
    - **Logical Meaning**: {logical_meaning_5}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_5}
    - **Boundary Conditions**: {boundaries_5}
    - **Implementation Example**: `{implementation_5}`

    **Concept**: {anomaly_feature_2_name}
    - **Sample Fields Used**: fields_used_6
    - **Definition**: {definition_6}
    - **Why This Feature**: {why_6}
    - **Logical Meaning**: {logical_meaning_6}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_6}
    - **Boundary Conditions**: {boundaries_6}
    - **Implementation Example**: `{implementation_6}`

    ---

    ### Q4: "What is combined?" (Interaction Features)

    **Concept**: {interaction_feature_1_name}
    - **Sample Fields Used**: fields_used_7
    - **Definition**: {definition_7}
    - **Why This Feature**: {why_7}
    - **Logical Meaning**: {logical_meaning_7}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_7}
    - **Boundary Conditions**: {boundaries_7}
    - **Implementation Example**: `{implementation_7}`

    **Concept**: {interaction_feature_2_name}
    - **Sample Fields Used**: fields_used_8
    - **Definition**: {definition_8}
    - **Why This Feature**: {why_8}
    - **Logical Meaning**: {logical_meaning_8}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_8}
    - **Boundary Conditions**: {boundaries_8}
    - **Implementation Example**: `{implementation_8}`

    ---

    ### Q5: "What is structural?" (Composition Features)

    **Concept**: {structure_feature_1_name}
    - **Sample Fields Used**: fields_used_9
    - **Definition**: {definition_9}
    - **Why This Feature**: {why_9}
    - **Logical Meaning**: {logical_meaning_9}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_9}
    - **Boundary Conditions**: {boundaries_9}
    - **Implementation Example**: `{implementation_9}`

    **Concept**: {structure_feature_2_name}
    - **Sample Fields Used**: fields_used_10
    - **Definition**: {definition_10}
    - **Why This Feature**: {why_10}
    - **Logical Meaning**: {logical_meaning_10}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_10}
    - **Boundary Conditions**: {boundaries_10}
    - **Implementation Example**: `{implementation_10}`

    ---

    ### Q6: "What is cumulative?" (Accumulation Features)

    **Concept**: {accumulation_feature_1_name}
    - **Sample Fields Used**: fields_used_11
    - **Definition**: {definition_11}
    - **Why This Feature**: {why_11}
    - **Logical Meaning**: {logical_meaning_11}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_11}
    - **Boundary Conditions**: {boundaries_11}
    - **Implementation Example**: `{implementation_11}`

    **Concept**: {accumulation_feature_2_name}
    - **Sample Fields Used**: fields_used_12
    - **Definition**: {definition_12}
    - **Why This Feature**: {why_12}
    - **Logical Meaning**: {logical_meaning_12}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_12}
    - **Boundary Conditions**: {boundaries_12}
    - **Implementation Example**: `{implementation_12}`

    ---

    ### Q7: "What is relative?" (Comparison Features)

    **Concept**: {relative_feature_1_name}
    - **Sample Fields Used**: fields_used_13
    - **Definition**: {definition_13}
    - **Why This Feature**: {why_13}
    - **Logical Meaning**: {logical_meaning_13}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_13}
    - **Boundary Conditions**: {boundaries_13}
    - **Implementation Example**: `{implementation_13}`

    **Concept**: {relative_feature_2_name}
    - **Sample Fields Used**: fields_used_14
    - **Definition**: {definition_14}
    - **Why This Feature**: {why_14}
    - **Logical Meaning**: {logical_meaning_14}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_14}
    - **Boundary Conditions**: {boundaries_14}
    - **Implementation Example**: `{implementation_14}`

    ---

    ### Q8: "What is essential?" (Essence Features)

    **Concept**: {essence_feature_1_name}
    - **Sample Fields Used**: fields_used_15
    - **Definition**: {definition_15}
    - **Why This Feature**: {why_15}
    - **Logical Meaning**: {logical_meaning_15}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_15}
    - **Boundary Conditions**: {boundaries_15}
    - **Implementation Example**: `{implementation_15}`

    **Concept**: {essence_feature_2_name}
    - **Sample Fields Used**: fields_used_16
    - **Definition**: {definition_16}
    - **Why This Feature**: {why_16}
    - **Logical Meaning**: {logical_meaning_16}
    - **is filling nan necessary**: we have some operators to fill nan value like ts_backfill() or group_mean() etc. however, in some cases, if the nan value itself has some meaning, then we should not fill it blindly since it may introduce some bias. so before filling nan value, we should think about whether the nan value has some meaning in the specific scenario. If yes, do use appropriate method to fill nan value in the following implementation example.
    - **Directionality**: {directionality_16}
    - **Boundary Conditions**: {boundaries_16}
    - **Implementation Example**: `{implementation_16}`

    ---

    ## Implementation Considerations

    ### Data Quality Notes
    - **Coverage**: {coverage_note}
    - **Timeliness**: {timeliness_note}
    - **Accuracy**: {accuracy_note}
    - **Potential Biases**: {bias_note}

    ### Computational Complexity
    - **Lightweight features**: {simple_features}
    - **Medium complexity**: {medium_features}
    - **Heavy computation**: {complex_features}

    ### Recommended Prioritization

    **Tier 1 (Immediate Implementation)**:
    1. {priority_1_feature} - {priority_1_reason}
    2. {priority_2_feature} - {priority_2_reason}
    3. {priority_3_feature} - {priority_3_reason}

    **Tier 2 (Secondary Priority)**:
    1. {priority_4_feature} - {priority_4_reason}
    2. {priority_5_feature} - {priority_5_reason}

    **Tier 3 (Requires Further Validation)**:
    1. {priority_6_feature} - {priority_6_reason}

    ---

    ## Critical Questions for Further Exploration

    ### Unanswered Questions:
    1. {unanswered_question_1}
    2. {unanswered_question_2}
    3. {unanswered_question_3}

    ### Recommended Additional Data:
    - {additional_data_1}
    - {additional_data_2}
    - {additional_data_3}

    ### Assumptions to Challenge:
    - {assumption_1}
    - {assumption_2}
    - {assumption_3}

    ---

    ## Methodology Notes

    **Analysis Approach**: This report was generated by:
    1. Deep field deconstruction to understand data essence
    2. Question-driven feature generation (8 fundamental questions)
    3. Logical validation of each feature concept
    4. Transparent documentation of reasoning

    **Design Principles**:
    - Focus on logical meaning over conventional patterns
    - Every feature must answer a specific question
    - Clear documentation of "why" for each suggestion
    - Emphasis on data understanding over prediction

    ---

    *Report generated: {generation_timestamp}*
    *Analysis depth: Comprehensive field deconstruction + 8-question framework*
    *Next steps: Implement Tier 1 features, validate assumptions, gather additional data as needed*



## Core Analysis Principles

1. **From Data Essence**: Start with what data truly means, not what it's traditionally used for
2. **Autonomous Reasoning**: Skill performs all thinking, no user input required
3. **Question-Driven**: Internal question bank guides feature generation
4. **Meaning Over Patterns**: Prioritize logical meaning over conventional combinations
5. **Transparency**: Show reasoning process in output

## Example Output Structure

When analyzing dataset 'BEME' (Balance Sheet and Market Data), the output would include:

### Dataset Understanding
**Fields Analyzed**: book_value, market_cap, book_to_market, etc.
**Key Observations**: Dataset compares accounting values with market valuations

### Field Deconstruction
- **book_value**: Accountant's calculation of net asset value (quarterly, audited, historical cost-based)
- **market_cap**: Market participants' valuation (continuous, forward-looking, sentiment-influenced)
- **book_to_market**: Ratio comparing these two valuation perspectives

### Feature Concepts Generated

**From "What is stable?"**
- "Market reevaluation stability": Rolling coefficient of variation of book_to_market
- **Logic**: Measures whether market opinion is stable or volatile
- **Meaning**: Stable values suggest consensus, volatile values suggest disagreement/uncertainty

**From "What is changing?"**
- "Value creation vs. market reevaluation decomposition": Separate book_value growth from market_cap growth
- **Logic**: Distinguish fundamental value creation from market sentiment changes
- **Meaning**: Which component drives changes in book_to_market?

**From "What is combined?"**
- "Intangible value proportion": (market_cap - book_value) / enterprise_value
- **Logic**: Quantify proportion of value from intangibles (brand, growth, etc.)
- **Meaning**: What percentage of valuation isn't captured on the balance sheet?

**(Additional question-based features would follow...)**

## Implementation Notes

### The skill should:
1. **Analyze first, then generate**: Fully understand dataset before proposing features
2. **Show reasoning**: Explain why each feature concept makes sense
3. **Be specific**: Reference actual field names and their characteristics
4. **Be critical**: Question assumptions and identify limitations
5. **Be creative**: Look beyond traditional financial metrics

### The skill should NOT:
1. **Ask users to think**: All thinking is internal to the skill
2. **Provide generic templates**: Each analysis should be specific to the dataset
3. **Rely on conventional wisdom**: Challenge traditional approaches
4. **Output patterns without meaning**: Every suggestion must have clear logic

## Quality Assurance

**Self-Check Process:**
- [ ] All fields analyzed, not just skimmed
- [ ] Field meanings understood beyond descriptions
- [ ] Multiple question types explored
- [ ] Each feature has clear logical meaning
- [ ] Reasoning is explicit, not implicit
- [ ] Limitations are acknowledged
- [ ] Output is dataset-specific, not generic

**Validation Questions:**
- Would this analysis help someone truly understand the data?
- Are feature concepts novel yet meaningful?
- Is the reasoning process transparent?
- Does it avoid conventional thinking traps?

---

*This skill performs deep analysis of BRAIN datasets, generating meaningful feature engineering concepts based on data essence and logical reasoning.*
