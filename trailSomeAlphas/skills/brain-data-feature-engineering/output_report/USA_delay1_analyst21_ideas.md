# Indicators of Interest Data (analyst21)

**Dataset**: analyst21
**Region**: USA
**Delay**: 1


## Dataset Overview
It is indications of interest (IOI) and trade advertisements event data. This dataset covers the TOP3000 universe in the USA region with a 1-day delay.

## Implementation Examples

### Example 1: Daily IOI Volume Monitor
Track daily indications of interest volume across the universe:
- Dataset: analyst21
- Field: {volume_suffix}
- Universe: TOP3000
- Delay: 1
- Date Range: {start_date} to {end_date}

### Example 2: Broker Advertisement Analysis
Analyze trade advertisement patterns over a specified window:
- Dataset: analyst21
- Field: {advertisement_suffix}
- Lookback Period: {lookback_days}
- Region: USA
- Aggregation: {aggregation_method}

### Example 3: Cross-Sectional IOI Signal
Generate signals based on relative IOI intensity:
- Dataset: analyst21
- Primary Field: {field_suffix_1}
- Secondary Field: {field_suffix_2}
- Calculation Date: {calculation_date}
- Universe Filter: TOP3000

## Data Specifications
- **Dataset ID**: analyst21
- **Dataset Name**: Indicators of Interest Data
- **Category**: Analyst
- **Region**: USA
- **Universe**: TOP3000
- **Delay**: 1 day
- **Field Count**: 0