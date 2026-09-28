-- ==============================================================================
-- PROJECT: Product Analytics Dashboard
-- SCRIPT: funnel_analysis.sql
-- DESCRIPTION: End-to-end e-commerce conversion funnel analysis.
--              Evaluates progression from Landing (page_view) to Product View,
--              Cart Addition, Checkout Initiation, and Purchase.
--              Includes step conversion rates, cumulative conversion, drop-off
--              rates, and dimensional breakdown by Device, Traffic Source, and User Segment.
-- COMPATIBILITY: ANSI SQL (DuckDB, PostgreSQL, BigQuery, Snowflake, SQLite 3.25+)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. OVERALL CONVERSION FUNNEL (Session Level)
-- ------------------------------------------------------------------------------
WITH session_events AS (
    SELECT
        session_id,
        user_id,
        device,
        traffic_source,
        user_segment,
        ab_variant,
        MIN(event_timestamp) AS session_start,
        MAX(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END) AS has_page_view,
        MAX(CASE WHEN event_type = 'product_view' THEN 1 ELSE 0 END) AS has_product_view,
        MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS has_add_to_cart,
        MAX(CASE WHEN event_type = 'initiate_checkout' THEN 1 ELSE 0 END) AS has_checkout,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS has_purchase,
        SUM(revenue) AS total_revenue
    FROM ecommerce_events
    GROUP BY session_id, user_id, device, traffic_source, user_segment, ab_variant
),

funnel_counts AS (
    SELECT
        COUNT(session_id) AS total_sessions,
        SUM(has_page_view) AS step1_page_views,
        SUM(has_product_view) AS step2_product_views,
        SUM(has_add_to_cart) AS step3_add_to_cart,
        SUM(has_checkout) AS step4_checkout,
        SUM(has_purchase) AS step5_purchase,
        SUM(total_revenue) AS total_revenue
    FROM session_events
)

SELECT
    total_sessions,
    step1_page_views,
    step2_product_views,
    step3_add_to_cart,
    step4_checkout,
    step5_purchase,
    -- Step-over-Step Conversion Rates
    ROUND(100.0 * step2_product_views / NULLIF(step1_page_views, 0), 2) AS view_to_prod_view_pct,
    ROUND(100.0 * step3_add_to_cart / NULLIF(step2_product_views, 0), 2) AS prod_view_to_cart_pct,
    ROUND(100.0 * step4_checkout / NULLIF(step3_add_to_cart, 0), 2) AS cart_to_checkout_pct,
    ROUND(100.0 * step5_purchase / NULLIF(step4_checkout, 0), 2) AS checkout_to_purchase_pct,
    -- Step-over-Step Drop-off Rates
    ROUND(100.0 * (step1_page_views - step2_product_views) / NULLIF(step1_page_views, 0), 2) AS dropoff_step1_to_2_pct,
    ROUND(100.0 * (step2_product_views - step3_add_to_cart) / NULLIF(step2_product_views, 0), 2) AS dropoff_step2_to_3_pct,
    ROUND(100.0 * (step3_add_to_cart - step4_checkout) / NULLIF(step3_add_to_cart, 0), 2) AS dropoff_step3_to_4_pct,
    ROUND(100.0 * (step4_checkout - step5_purchase) / NULLIF(step4_checkout, 0), 2) AS dropoff_step4_to_5_pct,
    -- Cumulative End-to-End Funnel Conversion Rate
    ROUND(100.0 * step5_purchase / NULLIF(total_sessions, 0), 2) AS overall_conversion_rate_pct,
    ROUND(total_revenue / NULLIF(step5_purchase, 0), 2) AS average_order_value
FROM funnel_counts;


-- ------------------------------------------------------------------------------
-- 2. FUNNEL STAGES IN VERTICAL FORMAT (Normalized for BI & Visual Reporting)
-- ------------------------------------------------------------------------------
WITH session_events AS (
    SELECT
        session_id,
        MAX(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END) AS s1,
        MAX(CASE WHEN event_type = 'product_view' THEN 1 ELSE 0 END) AS s2,
        MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS s3,
        MAX(CASE WHEN event_type = 'initiate_checkout' THEN 1 ELSE 0 END) AS s4,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS s5
    FROM ecommerce_events
    GROUP BY session_id
),
staged AS (
    SELECT 1 AS stage_order, '1. Page View' AS stage_name, SUM(s1) AS sessions FROM session_events
    UNION ALL
    SELECT 2 AS stage_order, '2. Product View' AS stage_name, SUM(s2) AS sessions FROM session_events
    UNION ALL
    SELECT 3 AS stage_order, '3. Add to Cart' AS stage_name, SUM(s3) AS sessions FROM session_events
    UNION ALL
    SELECT 4 AS stage_order, '4. Checkout Initiated' AS stage_name, SUM(s4) AS sessions FROM session_events
    UNION ALL
    SELECT 5 AS stage_order, '5. Completed Purchase' AS stage_name, SUM(s5) AS sessions FROM session_events
)
SELECT
    stage_order,
    stage_name,
    sessions,
    LAG(sessions) OVER (ORDER BY stage_order) AS previous_stage_sessions,
    ROUND(100.0 * sessions / FIRST_VALUE(sessions) OVER (ORDER BY stage_order), 2) AS pct_of_top_funnel,
    ROUND(100.0 * sessions / NULLIF(LAG(sessions) OVER (ORDER BY stage_order), 0), 2) AS step_conversion_pct,
    ROUND(100.0 * (LAG(sessions) OVER (ORDER BY stage_order) - sessions) / NULLIF(LAG(sessions) OVER (ORDER BY stage_order), 0), 2) AS step_dropoff_pct
FROM staged
ORDER BY stage_order;


-- ------------------------------------------------------------------------------
-- 3. FUNNEL CONVERSION SLICED BY DEVICE TYPE
-- ------------------------------------------------------------------------------
SELECT
    device,
    COUNT(DISTINCT session_id) AS total_sessions,
    COUNT(DISTINCT CASE WHEN event_type = 'product_view' THEN session_id END) AS product_view_sessions,
    COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN session_id END) AS cart_sessions,
    COUNT(DISTINCT CASE WHEN event_type = 'initiate_checkout' THEN session_id END) AS checkout_sessions,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) AS purchase_sessions,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'product_view' THEN session_id END) / COUNT(DISTINCT session_id), 2) AS view_rate_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN session_id END) / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'product_view' THEN session_id END), 0), 2) AS cart_rate_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'initiate_checkout' THEN session_id END), 0), 2) AS checkout_completion_rate_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) / COUNT(DISTINCT session_id), 2) AS overall_conversion_rate_pct
FROM ecommerce_events
GROUP BY device
ORDER BY overall_conversion_rate_pct DESC;


-- ------------------------------------------------------------------------------
-- 4. FUNNEL CONVERSION SLICED BY TRAFFIC SOURCE
-- ------------------------------------------------------------------------------
SELECT
    traffic_source,
    COUNT(DISTINCT session_id) AS sessions,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) AS purchases,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) / COUNT(DISTINCT session_id), 2) AS session_conversion_rate_pct,
    ROUND(SUM(revenue) / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END), 0), 2) AS aov,
    ROUND(SUM(revenue) / COUNT(DISTINCT session_id), 2) AS revenue_per_session
FROM ecommerce_events
GROUP BY traffic_source
ORDER BY total_revenue DESC;
