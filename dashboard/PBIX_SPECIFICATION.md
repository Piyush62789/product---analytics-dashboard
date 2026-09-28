# Power BI Report Specification & Enterprise DAX Dictionary

This document details the data architecture, star schema relationships, DAX formulas, and canvas layout for `Product_Analytics.pbix`.

---

## 1. Data Model & Star Schema Architecture

The report is built upon a Kimball-style Star Schema optimized for high-performance in-memory VertiPaq tabular queries.

```
                   +------------------------+
                   |        Dim_Date        |
                   |------------------------|
                   | Date (PK)              |
                   | Year, Quarter, Month   |
                   | WeekOfYear, DayOfWeek  |
                   +-----------+------------+
                               | 1
                               |
                               | *
+--------------------+   +-----+--------------------+   +---------------------+
|    Dim_Users       |   |   Fact_Ecommerce_Events  |   |    Dim_Products     |
|--------------------|   |--------------------------|   |---------------------|
| User_ID (PK)       |1  | Event_ID (PK)            |  *| Product_ID (PK)     |
| User_Segment       +---+ User_ID (FK)             +---+ Product_Name        |
| Country, City      | * | Session_ID               | 1 | Category            |
| Acquisition_Date   |   | Event_Timestamp (FK)     |   | Unit_Price          |
+--------------------+   | Event_Type               |   +---------------------+
                         | Product_ID (FK)          |
                         | Quantity, Price, Revenue |
                         | Device, Traffic_Source   |
                         | AB_Variant               |
                         +-----------+--------------+
                                     | *
                                     |
                                     | 1
                         +-----------+--------------+
                         |       Dim_Traffic        |
                         |--------------------------|
                         | Traffic_Source (PK)      |
                         | Channel_Group            |
                         +--------------------------+
```

### Table Relationships
- `Fact_Ecommerce_Events[event_timestamp]` $\rightarrow$ `Dim_Date[Date]` (Many-to-One, Single Filter Direction)
- `Fact_Ecommerce_Events[user_id]` $\rightarrow$ `Dim_Users[User_ID]` (Many-to-One, Single Filter Direction)
- `Fact_Ecommerce_Events[product_id]` $\rightarrow$ `Dim_Products[Product_ID]` (Many-to-One, Single Filter Direction)
- `Fact_Ecommerce_Events[traffic_source]` $\rightarrow$ `Dim_Traffic[Traffic_Source]` (Many-to-One, Single Filter Direction)

---

## 2. Core DAX Measures Dictionary

Create a Dedicated Measures Table: `_Measures`.

### Commercial & Revenue Measures
```dax
Total Revenue = 
SUM(Fact_Ecommerce_Events[revenue])

Total Orders = 
CALCULATE(
    DISTINCTCOUNT(Fact_Ecommerce_Events[session_id]),
    Fact_Ecommerce_Events[event_type] = "purchase"
)

Total Units Sold = 
CALCULATE(
    SUM(Fact_Ecommerce_Events[quantity]),
    Fact_Ecommerce_Events[event_type] = "purchase"
)

Average Order Value (AOV) = 
DIVIDE([Total Revenue], [Total Orders], 0)

Average Revenue Per User (ARPU) = 
DIVIDE([Total Revenue], [Total Active Users], 0)

Average Revenue Per Paying User (ARPPU) = 
DIVIDE([Total Revenue], [Total Paying Customers], 0)
```

### Engagement & User Metrics
```dax
Total Active Users = 
DISTINCTCOUNT(Fact_Ecommerce_Events[user_id])

Total Paying Customers = 
CALCULATE(
    DISTINCTCOUNT(Fact_Ecommerce_Events[user_id]),
    Fact_Ecommerce_Events[event_type] = "purchase"
)

Total Sessions = 
DISTINCTCOUNT(Fact_Ecommerce_Events[session_id])

Daily Active Users (DAU) = 
DISTINCTCOUNT(Fact_Ecommerce_Events[user_id])

Weekly Active Users (WAU) = 
CALCULATE(
    DISTINCTCOUNT(Fact_Ecommerce_Events[user_id]),
    DATESINPERIOD(Dim_Date[Date], MAX(Dim_Date[Date]), -7, DAY)
)

Monthly Active Users (MAU) = 
CALCULATE(
    DISTINCTCOUNT(Fact_Ecommerce_Events[user_id]),
    DATESINPERIOD(Dim_Date[Date], MAX(Dim_Date[Date]), -30, DAY)
)

DAU / MAU Stickiness Ratio = 
DIVIDE([DAU], [MAU], 0)
```

### Funnel & Conversion Measures
```dax
Sessions (Page View) = 
CALCULATE(
    DISTINCTCOUNT(Fact_Ecommerce_Events[session_id]),
    Fact_Ecommerce_Events[event_type] = "page_view"
)

Sessions (Product View) = 
CALCULATE(
    DISTINCTCOUNT(Fact_Ecommerce_Events[session_id]),
    Fact_Ecommerce_Events[event_type] = "product_view"
)

Sessions (Add to Cart) = 
CALCULATE(
    DISTINCTCOUNT(Fact_Ecommerce_Events[session_id]),
    Fact_Ecommerce_Events[event_type] = "add_to_cart"
)

Sessions (Initiate Checkout) = 
CALCULATE(
    DISTINCTCOUNT(Fact_Ecommerce_Events[session_id]),
    Fact_Ecommerce_Events[event_type] = "initiate_checkout"
)

Sessions (Purchase) = 
CALCULATE(
    DISTINCTCOUNT(Fact_Ecommerce_Events[session_id]),
    Fact_Ecommerce_Events[event_type] = "purchase"
)

Overall Session Conversion Rate % = 
DIVIDE([Sessions (Purchase)], [Total Sessions], 0)

Cart to Detail Rate % = 
DIVIDE([Sessions (Add to Cart)], [Sessions (Product View)], 0)

Cart Abandonment Rate % = 
DIVIDE([Sessions (Add to Cart)] - [Sessions (Purchase)], [Sessions (Add to Cart)], 0)
```

### A/B Experimentation & Statistical Inference Measures
```dax
CR Control = 
CALCULATE(
    [Overall Session Conversion Rate %],
    Fact_Ecommerce_Events[ab_variant] = "Control"
)

CR Treatment = 
CALCULATE(
    [Overall Session Conversion Rate %],
    Fact_Ecommerce_Events[ab_variant] = "Treatment"
)

A/B Relative Lift % = 
DIVIDE([CR Treatment] - [CR Control], [CR Control], 0)

Pooled Conversion Rate = 
VAR x1 = CALCULATE([Sessions (Purchase)], Fact_Ecommerce_Events[ab_variant] = "Control")
VAR x2 = CALCULATE([Sessions (Purchase)], Fact_Ecommerce_Events[ab_variant] = "Treatment")
VAR n1 = CALCULATE([Total Sessions], Fact_Ecommerce_Events[ab_variant] = "Control")
VAR n2 = CALCULATE([Total Sessions], Fact_Ecommerce_Events[ab_variant] = "Treatment")
RETURN
DIVIDE(x1 + x2, n1 + n2, 0)

A/B Standard Error = 
VAR p_pool = [Pooled Conversion Rate]
VAR n1 = CALCULATE([Total Sessions], Fact_Ecommerce_Events[ab_variant] = "Control")
VAR n2 = CALCULATE([Total Sessions], Fact_Ecommerce_Events[ab_variant] = "Treatment")
RETURN
SQRT(p_pool * (1 - p_pool) * (DIVIDE(1, n1, 0) + DIVIDE(1, n2, 0)))

A/B Z-Score = 
DIVIDE([CR Treatment] - [CR Control], [A/B Standard Error], 0)

Statistical Significance Flag = 
IF(
    ABS([A/B Z-Score]) >= 1.96,
    "Statistically Significant (p < 0.05)",
    "Not Significant (Insufficient Evidence)"
)
```

---

## 3. Power BI Report Page Layouts

### Page 1: Executive KPI Overview
- **Top KPI Cards**: Total Gross Revenue, Total Orders, Overall CR %, AOV, DAU/MAU Stickiness.
- **Visual 1**: Spline Line Chart — Daily Revenue vs Cumulative Orders over time.
- **Visual 2**: Donut Chart — Revenue Contribution by Product Category.
- **Visual 3**: Horizontal Bar Chart — Revenue & Conversion by Traffic Channel.
- **Slicers**: Date Range Slider, Device Filter, User Segment.

### Page 2: Funnel & Drop-off Diagnostics
- **Visual 1**: Native Power BI Funnel Chart (`Sessions` by Funnel Stage).
- **Visual 2**: Clustered Column Chart — Stage-by-Stage Drop-off Rate (%) sliced by Device.
- **Visual 3**: Matrix Table — Products sorted by Cart-to-Detail Rate vs Final View-to-Buy Rate.

### Page 3: Cohort Retention Matrix
- **Visual 1**: Matrix Heatmap:
  - Rows: `User Acquisition Cohort Week`
  - Columns: `Period Week (0, 1, 2, ... 8)`
  - Values: `Retention Rate %` with conditional formatting background color scales (Blue/Teal).
- **Visual 2**: Retention Decay Curve (Line Chart comparing Retention across Cohort vintages).

### Page 4: A/B Testing Lab
- **Visual 1**: Side-by-side KPI Cards (Control CR vs Treatment CR vs Relative Lift %).
- **Visual 2**: Forest Plot / 95% Confidence Interval error bar graphic.
- **Visual 3**: Clustered Column Chart — Funnel Progression by Variant.
- **Verdict Card**: Dynamic indicator badge showing hypothesis test resolution.
