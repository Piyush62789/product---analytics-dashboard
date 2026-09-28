# ⚡ Product Analytics & Experimentation Dashboard

An enterprise-grade, end-to-end Product Analytics, Conversion Funnel, Cohort Retention, and A/B Testing Experimentation platform for modern digital e-commerce products.

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.51.0-FF4B4B.svg)](https://streamlit.io/)
[![Power BI](https://img.shields.io/badge/Power_BI-Desktop-F2C811.svg)](https://powerbi.microsoft.com/)
[![SQL Standard](https://img.shields.io/badge/SQL-ANSI%20%7C%20DuckDB%20%7C%20Postgres-0284c7.svg)](https://www.iso.org/standard/63555.html)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

---

## 📁 Repository Structure

```
product-analytics-dashboard/
│
├── data/
│   ├── ecommerce_events.csv            # Raw 90-day event stream dataset (35,000+ records)
│   └── ecommerce_events_cleaned.csv    # Cleaned & feature-engineered analytical dataset
│
├── sql/
│   ├── funnel_analysis.sql             # Multi-stage conversion funnel & drop-off analytics
│   ├── retention.sql                   # N-Day & Weekly cohort retention matrices & churn analysis
│   ├── product_metrics.sql             # DAU/WAU/MAU stickiness, AOV, ARPU, CTD & category Pareto
│   └── ab_testing.sql                  # Z-score hypothesis testing, relative lift & 95% CI
│
├── python/
│   ├── data_cleaning.py                # Production ETL, schema validation & feature engineering
│   ├── analysis.py                     # Statistical inference, RFM clustering & executive reporting
│   ├── generate_data.py                # Deterministic synthetic e-commerce data generator
│   └── executive_summary.txt           # Automated executive analytical brief & recommendations
│
├── dashboard/
│   ├── Product_Analytics.pbix          # Power BI Desktop report template (Open Packaging Convention)
│   ├── create_pbix.py                  # Automation script to assemble the .pbix package
│   └── PBIX_SPECIFICATION.md           # Star-schema data model, relationships & 20+ DAX measures
│
├── app/
│   └── streamlit_app.py                # High-performance interactive analytics & experimentation web app
│
├── requirements.txt                    # Project dependency specification
└── README.md                           # Comprehensive documentation & strategic takeaways
```

---

## 📊 Dataset Schema & Event Dictionary

The dataset simulates a high-growth consumer e-commerce store with over **35,000+ granular behavioral events** across **3,800 unique users** over a 90-day observation period (Q1 2025).

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `event_id` | String | Unique event identifier (`EVT-XXXXXXX`) |
| `user_id` | String | Persistent user identifier (`USR-XXXXX`) |
| `session_id` | String | Unique session identifier (`SES-XXXXXX`) |
| `event_timestamp`| Timestamp | ISO 8601 UTC timestamp of the user action |
| `event_type` | String | Funnel step: `page_view`, `product_view`, `add_to_cart`, `initiate_checkout`, `purchase`, `add_to_wishlist` |
| `page_url` | String | Relative URL path (e.g. `/home`, `/cart`, `/checkout`) |
| `product_id` | String | Product SKU identifier (`PROD-101` to `PROD-503`) |
| `product_name` | String | Descriptive product name (22 curated SKUs across 5 categories) |
| `category` | String | Product category: *Electronics, Apparel, Home & Living, Fitness & Sports, Beauty & Wellness* |
| `price` | Float | Unit price ($15.00 – $499.00) |
| `quantity` | Integer | Quantity selected / purchased |
| `revenue` | Float | Gross order revenue (`price * quantity` on purchase, `0.0` otherwise) |
| `device` | String | Client device form-factor: *Desktop, Mobile, Tablet* |
| `traffic_source` | String | Inbound acquisition channel: *Organic Search, Paid Search, Social Media, Email Campaign, Direct, Referral* |
| `user_segment` | String | Behavioral tier: *New, Returning, VIP* |
| `ab_variant` | String | Randomized experiment assignment: `Control` (Standard Flow) vs `Treatment` (1-Click Flow) |
| `country` | String | User location: *United States, United Kingdom, Germany, Canada, France, Japan, Australia* |

---

## 🚀 Quickstart & Installation

### 1. Environment Setup
Clone the repository and install the verified dependencies:
```bash
# Clone the repository
git clone https://github.com/your-org/product-analytics-dashboard.git
cd product-analytics-dashboard

# Create and activate a virtual environment (optional)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Data Cleaning & Feature Engineering Pipeline
```bash
python python/data_cleaning.py
```
*Outputs clean dataset to `data/ecommerce_events_cleaned.csv` with session sequence numbers, bounce detection, cart abandonment flags, and cohort aging.*

### 3. Run Statistical Engine & Hypothesis Testing
```bash
python python/analysis.py
```
*Performs two-proportion Z-test, Welch's t-test for ARPU, RFM customer segmentation, and compiles `python/executive_summary.txt`.*

### 4. Launch the Interactive Streamlit Web Application
```bash
streamlit run app/streamlit_app.py
```
The application will launch automatically in your browser at `http://localhost:8501`.

---

## 🗄️ SQL Analytics Engine

All queries are written in ANSI-compliant SQL and verified against SQLite, DuckDB, PostgreSQL, BigQuery, and Snowflake:

### 1. [`sql/funnel_analysis.sql`](file:///d:/product/sql/funnel_analysis.sql)
- Evaluates the macro-conversion funnel: `Page View` $\rightarrow$ `Product View` $\rightarrow$ `Add to Cart` $\rightarrow$ `Initiate Checkout` $\rightarrow$ `Purchase`.
- Calculates micro-conversion rates, drop-off rates between steps, cumulative view-to-buy conversion, and dimensional breakdowns by Device and Acquisition Source.

### 2. [`sql/retention.sql`](file:///d:/product/sql/retention.sql)
- **Weekly Cohort Retention Matrix**: User retention percentages for Week 0 through Week 8+ using calendar date windowing.
- **Classic N-Day Retention**: Day 1, Day 7, Day 14, and Day 30 post-acquisition active rates.
- **Repeat Purchase Analysis**: Customer Lifetime Value (LTV) and average days between consecutive orders.
- **Churn Segmentation**: Categorizes users into *Active ($\le$7d)*, *Cooling (8-14d)*, *At-Risk (15-30d)*, and *Dormant (>30d)*.

### 3. [`sql/product_metrics.sql`](file:///d:/product/sql/product_metrics.sql)
- **Engagement Stickiness**: Daily Active Users (DAU), Weekly Active Users (WAU), Monthly Active Users (MAU), and the `DAU / MAU` stickiness ratio.
- **Commercial KPIs**: Average Order Value (AOV), Average Revenue Per User (ARPU), Average Revenue Per Paying User (ARPPU).
- **Merchandise Performance**: Cart-to-Detail Rate (`Cart Adds / Product Views`) and Product-level Conversion Rate.
- **Category Pareto (80/20)**: Cumulative revenue contributions across categories.
- **Cart Abandonment Rate**: Measures sessions that carted an item but failed to transact.

### 4. [`sql/ab_testing.sql`](file:///d:/product/sql/ab_testing.sql)
- Evaluates Control vs Treatment performance in pure SQL.
- Computes Pooled Proportions ($\hat{p}$), Standard Error ($SE$), Z-Statistic ($Z$), 95% Confidence Intervals, and a dynamic statistical significance verdict.

---

## 🧪 Key A/B Testing Findings & Strategic Takeaways

### Experiment Hypothesis
> *"Introducing a streamlined 1-Click Checkout Modal (Treatment) will eliminate multi-step cart friction and significantly increase the visitor-to-purchase conversion rate."*

### Empirical Experiment Results
| Metric | Control (Standard Flow) | Treatment (1-Click Flow) | Relative Lift | Statistical Significance |
| :--- | :--- | :--- | :--- | :--- |
| **Sample Size ($N$)** | 1,932 unique users | 1,868 unique users | — | — |
| **Conversions ($X$)** | 537 purchases | 607 purchases | — | — |
| **Conversion Rate ($CR$)** | **27.80%** | **32.49%** | **+16.91%** | **$Z = 3.157$, $p = 0.0016$** |
| **95% Confidence Interval**| — | — | **[+1.78%, +7.62%]** | Statistically Significant ($\alpha = 0.05$) |
| **ARPU** | $53.53 | $66.33 | **+23.91%** | Welch's $t = 2.68$, $p = 0.0073$ |
| **AOV** | $142.65 | $142.58 | -0.05% | Neutral (Maintains Basket Size) |

### Strategic Product Recommendations
1. **100% Rollout of 1-Click Checkout**:
   The treatment delivers a highly significant **+16.9% relative lift** in user conversion and an expansion of **+23.9% in Revenue Per User (ARPU)** without eroding Average Order Value. Recommend graduating the experiment and rolling out 1-Click Checkout to 100% of global traffic.
2. **Product Detail Page (PDP) Friction Optimization**:
   The funnel analysis revealed that the single largest drop-off occurs between **Product View** and **Add to Cart** (drop-off rate $\sim$58%). Implementing dynamic stock badges ("Only 3 left in stock"), authentic customer photos, and floating sticky "Add to Cart" bars on mobile will tackle this bottleneck.
3. **Cart Abandonment Automated Recovery**:
   The cart abandonment rate stands at **55.7%**. Triggering automated personalized recovery sequences (email + push notification) at 1 hour and 24 hours post-abandonment can recover an estimated 8–12% of lost orders.
4. **Day 14 Retention Interventions**:
   Cohort retention decays from 100% at Week 0 to $\sim$22% by Week 1. Automated post-purchase nurture sequences, loyalty points incentives, and replenishment reminders at Day 14 will strengthen long-term stickiness.

---

## 📈 Power BI Report (`dashboard/Product_Analytics.pbix`)

A companion Power BI report is packaged in `dashboard/Product_Analytics.pbix`. 
Detailed documentation, Star Schema entity-relationship models, and the 20+ DAX measure catalog can be reviewed in [`dashboard/PBIX_SPECIFICATION.md`](file:///d:/product/dashboard/PBIX_SPECIFICATION.md).

### Report Canvas Pages
1. **Executive KPI Overview**: High-level scorecards, revenue spline trends, category donut breakdown, and channel conversion.
2. **Funnel & Drop-off Diagnostics**: Native multi-stage funnel visualization, drop-off rates sliced by device, and cart-to-detail performance.
3. **Cohort Retention Matrix**: Week-by-week heatmap matrix visualizer with conditional color ramps.
4. **A/B Experimentation Lab**: Forest plots, error bars with 95% confidence intervals, and dynamic significance badges.

---

## 📜 License
This project is licensed under the Apache 2.0 License.
