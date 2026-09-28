-- ==============================================================================
-- PROJECT: Product Analytics Dashboard
-- SCRIPT: ab_testing.sql
-- DESCRIPTION: Comprehensive A/B Testing Evaluation & Statistical Inference.
--              Compares Control (Standard Checkout) vs Treatment (1-Click Checkout).
--              Calculates Conversion Rates, Relative Lift, Average Order Value (AOV),
--              Average Revenue Per User (ARPU), Pooled Variance, Standard Error,
--              Z-Score, and Statistical Significance Determination (95% CI).
-- COMPATIBILITY: ANSI SQL (DuckDB, PostgreSQL, BigQuery, Snowflake, SQLite 3.25+)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. PRIMARY A/B TEST RESULTS & STATISTICAL SIGNIFICANCE (Z-SCORE TEST)
-- ------------------------------------------------------------------------------
WITH variant_summary AS (
    SELECT
        ab_variant,
        COUNT(DISTINCT user_id) AS sample_users,
        COUNT(DISTINCT session_id) AS sample_sessions,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) AS converted_users,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) AS completed_orders,
        SUM(revenue) AS total_revenue
    FROM ecommerce_events
    WHERE ab_variant IN ('Control', 'Treatment')
    GROUP BY ab_variant
),
metrics AS (
    SELECT
        ab_variant,
        sample_users,
        sample_sessions,
        converted_users,
        completed_orders,
        ROUND(total_revenue, 2) AS total_revenue,
        -- Conversion Rate = Converted Users / Total Sample Users
        CAST(converted_users AS FLOAT) / sample_users AS user_conversion_rate,
        -- Average Order Value = Revenue / Completed Orders
        total_revenue / NULLIF(completed_orders, 0) AS aov,
        -- Average Revenue Per User = Revenue / Sample Users
        total_revenue / sample_users AS arpu
    FROM variant_summary
),
pivot_variants AS (
    SELECT
        MAX(CASE WHEN ab_variant = 'Control' THEN sample_users END) AS n_control,
        MAX(CASE WHEN ab_variant = 'Treatment' THEN sample_users END) AS n_treatment,
        MAX(CASE WHEN ab_variant = 'Control' THEN converted_users END) AS x_control,
        MAX(CASE WHEN ab_variant = 'Treatment' THEN converted_users END) AS x_treatment,
        MAX(CASE WHEN ab_variant = 'Control' THEN user_conversion_rate END) AS cr_control,
        MAX(CASE WHEN ab_variant = 'Treatment' THEN user_conversion_rate END) AS cr_treatment,
        MAX(CASE WHEN ab_variant = 'Control' THEN aov END) AS aov_control,
        MAX(CASE WHEN ab_variant = 'Treatment' THEN aov END) AS aov_treatment,
        MAX(CASE WHEN ab_variant = 'Control' THEN arpu END) AS arpu_control,
        MAX(CASE WHEN ab_variant = 'Treatment' THEN arpu END) AS arpu_treatment
    FROM metrics
),
z_test_prep AS (
    SELECT
        n_control,
        n_treatment,
        x_control,
        x_treatment,
        cr_control,
        cr_treatment,
        aov_control,
        aov_treatment,
        arpu_control,
        arpu_treatment,
        -- Relative Conversion Lift = (CR_Treatment - CR_Control) / CR_Control
        (cr_treatment - cr_control) / cr_control AS relative_cr_lift,
        -- Pooled Proportion: p_pool = (x_1 + x_2) / (n_1 + n_2)
        CAST(x_control + x_treatment AS FLOAT) / (n_control + n_treatment) AS p_pooled
    FROM pivot_variants
),
z_test_calc AS (
    SELECT
        *,
        -- Standard Error = SQRT( p_pool * (1 - p_pool) * (1/n_control + 1/n_treatment) )
        SQRT( p_pooled * (1.0 - p_pooled) * ( (1.0 / n_control) + (1.0 / n_treatment) ) ) AS se_pooled
    FROM z_test_prep
)
SELECT
    n_control,
    n_treatment,
    x_control AS conversions_control,
    x_treatment AS conversions_treatment,
    ROUND(100.0 * cr_control, 3) AS control_conversion_rate_pct,
    ROUND(100.0 * cr_treatment, 3) AS treatment_conversion_rate_pct,
    ROUND(100.0 * relative_cr_lift, 2) AS relative_conversion_lift_pct,
    ROUND(aov_control, 2) AS control_aov,
    ROUND(aov_treatment, 2) AS treatment_aov,
    ROUND(100.0 * (aov_treatment - aov_control) / aov_control, 2) AS aov_lift_pct,
    ROUND(arpu_control, 2) AS control_arpu,
    ROUND(arpu_treatment, 2) AS treatment_arpu,
    ROUND(100.0 * (arpu_treatment - arpu_control) / arpu_control, 2) AS arpu_lift_pct,
    ROUND( (cr_treatment - cr_control) / se_pooled, 4) AS z_score,
    -- 95% Confidence Interval for Difference (Z_crit = 1.96)
    ROUND(100.0 * ((cr_treatment - cr_control) - (1.96 * se_pooled)), 3) AS ci_lower_95_diff_pct,
    ROUND(100.0 * ((cr_treatment - cr_control) + (1.96 * se_pooled)), 3) AS ci_upper_95_diff_pct,
    CASE 
        WHEN ABS((cr_treatment - cr_control) / se_pooled) >= 1.96 
        THEN 'YES (Statistically Significant at α = 0.05)'
        ELSE 'NO (Inconclusive / Insufficient Evidence)'
    END AS is_significant
FROM z_test_calc;


-- ------------------------------------------------------------------------------
-- 2. FUNNEL STAGE CONVERSIONS BY A/B VARIANT
--    Inspects exactly which stage of the funnel drives the treatment's lift
-- ------------------------------------------------------------------------------
WITH variant_stages AS (
    SELECT
        ab_variant,
        COUNT(DISTINCT session_id) AS total_sessions,
        COUNT(DISTINCT CASE WHEN event_type = 'product_view' THEN session_id END) AS prod_views,
        COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN session_id END) AS cart_adds,
        COUNT(DISTINCT CASE WHEN event_type = 'initiate_checkout' THEN session_id END) AS checkouts,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) AS purchases
    FROM ecommerce_events
    WHERE ab_variant IN ('Control', 'Treatment')
    GROUP BY ab_variant
)
SELECT
    ab_variant,
    total_sessions,
    prod_views,
    cart_adds,
    checkouts,
    purchases,
    ROUND(100.0 * prod_views / total_sessions, 2) AS view_rate_pct,
    ROUND(100.0 * cart_adds / prod_views, 2) AS cart_add_rate_pct,
    ROUND(100.0 * checkouts / cart_adds, 2) AS cart_to_checkout_pct,
    -- Checkout completion rate is the primary expected difference
    ROUND(100.0 * purchases / checkouts, 2) AS checkout_to_purchase_completion_pct,
    ROUND(100.0 * purchases / total_sessions, 2) AS session_conversion_rate_pct
FROM variant_stages;


-- ------------------------------------------------------------------------------
-- 3. HETEROGENEOUS TREATMENT EFFECTS BY DEVICE
--    Determines if mobile vs desktop experiences differential impact
-- ------------------------------------------------------------------------------
WITH segment_metrics AS (
    SELECT
        device,
        ab_variant,
        COUNT(DISTINCT user_id) AS users,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) AS buyers,
        ROUND(SUM(revenue), 2) AS revenue
    FROM ecommerce_events
    WHERE ab_variant IN ('Control', 'Treatment')
    GROUP BY device, ab_variant
)
SELECT
    device,
    MAX(CASE WHEN ab_variant = 'Control' THEN users END) AS control_users,
    MAX(CASE WHEN ab_variant = 'Treatment' THEN users END) AS treatment_users,
    ROUND(100.0 * MAX(CASE WHEN ab_variant = 'Control' THEN buyers END) / 
          MAX(CASE WHEN ab_variant = 'Control' THEN users END), 2) AS control_cr_pct,
    ROUND(100.0 * MAX(CASE WHEN ab_variant = 'Treatment' THEN buyers END) / 
          MAX(CASE WHEN ab_variant = 'Treatment' THEN users END), 2) AS treatment_cr_pct,
    ROUND(100.0 * (
        (CAST(MAX(CASE WHEN ab_variant = 'Treatment' THEN buyers END) AS FLOAT) / MAX(CASE WHEN ab_variant = 'Treatment' THEN users END)) -
        (CAST(MAX(CASE WHEN ab_variant = 'Control' THEN buyers END) AS FLOAT) / MAX(CASE WHEN ab_variant = 'Control' THEN users END))
    ) / (CAST(MAX(CASE WHEN ab_variant = 'Control' THEN buyers END) AS FLOAT) / MAX(CASE WHEN ab_variant = 'Control' THEN users END)), 2) AS relative_lift_pct
FROM segment_metrics
GROUP BY device
ORDER BY device;
