-- ==============================================================================
-- PROJECT: Product Analytics Dashboard
-- SCRIPT: product_metrics.sql
-- DESCRIPTION: Core Product & Business Metrics Analysis.
--              Includes DAU/WAU/MAU Stickiness, Revenue & Order KPIs (AOV, ARPU, ARPPU),
--              Product Performance (Cart-to-Detail, View-to-Buy Conversion),
--              Category Contribution, and Cart Abandonment Rate.
-- COMPATIBILITY: ANSI SQL (DuckDB, PostgreSQL, BigQuery, Snowflake, SQLite 3.25+)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. EXECUTIVE KPI SUMMARY & MONETIZATION
-- ------------------------------------------------------------------------------
WITH base_metrics AS (
    SELECT
        COUNT(DISTINCT session_id) AS total_sessions,
        COUNT(DISTINCT user_id) AS total_active_users,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) AS paying_users,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) AS total_orders,
        SUM(CASE WHEN event_type = 'purchase' THEN quantity ELSE 0 END) AS total_units_sold,
        SUM(revenue) AS gross_revenue
    FROM ecommerce_events
)
SELECT
    total_sessions,
    total_active_users,
    paying_users,
    total_orders,
    total_units_sold,
    ROUND(gross_revenue, 2) AS gross_revenue,
    -- Average Order Value (AOV)
    ROUND(gross_revenue / NULLIF(total_orders, 0), 2) AS aov,
    -- Average Revenue Per User (ARPU)
    ROUND(gross_revenue / NULLIF(total_active_users, 0), 2) AS arpu,
    -- Average Revenue Per Paying User (ARPPU)
    ROUND(gross_revenue / NULLIF(paying_users, 0), 2) AS arppu,
    -- Overall Session Conversion Rate
    ROUND(100.0 * total_orders / NULLIF(total_sessions, 0), 2) AS session_conversion_rate_pct,
    -- User Conversion Rate
    ROUND(100.0 * paying_users / NULLIF(total_active_users, 0), 2) AS user_conversion_rate_pct
FROM base_metrics;


-- ------------------------------------------------------------------------------
-- 2. USER ENGAGEMENT & STICKINESS (DAU, WAU, MAU)
-- ------------------------------------------------------------------------------
WITH daily_active AS (
    SELECT
        DATE(event_timestamp) AS active_date,
        COUNT(DISTINCT user_id) AS dau
    FROM ecommerce_events
    GROUP BY DATE(event_timestamp)
),
stickiness_calc AS (
    SELECT
        d.active_date,
        d.dau,
        -- WAU: Distinct active users in rolling 7-day window
        (
            SELECT COUNT(DISTINCT user_id)
            FROM ecommerce_events e
            WHERE DATE(e.event_timestamp) BETWEEN DATE(d.active_date, '-6 days') AND d.active_date
        ) AS wau,
        -- MAU: Distinct active users in rolling 30-day window
        (
            SELECT COUNT(DISTINCT user_id)
            FROM ecommerce_events e
            WHERE DATE(e.event_timestamp) BETWEEN DATE(d.active_date, '-29 days') AND d.active_date
        ) AS mau
    FROM daily_active d
)
SELECT
    active_date,
    dau,
    wau,
    mau,
    ROUND(100.0 * dau / NULLIF(wau, 0), 2) AS dau_to_wau_pct,
    ROUND(100.0 * dau / NULLIF(mau, 0), 2) AS dau_to_mau_stickiness_pct
FROM stickiness_calc
WHERE mau > 0
ORDER BY active_date DESC
LIMIT 30;


-- ------------------------------------------------------------------------------
-- 3. PRODUCT-LEVEL CONVERSION & CART-TO-DETAIL (CTD) PERFORMANCE
-- ------------------------------------------------------------------------------
SELECT
    product_id,
    product_name,
    category,
    COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) AS product_views,
    COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) AS cart_adds,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS purchases,
    SUM(CASE WHEN event_type = 'purchase' THEN quantity ELSE 0 END) AS units_sold,
    ROUND(SUM(revenue), 2) AS total_revenue,
    -- Cart-to-Detail (CTD) Rate = Cart Adds / Product Views
    ROUND(100.0 * COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) / 
          NULLIF(COUNT(CASE WHEN event_type = 'product_view' THEN 1 END), 0), 2) AS cart_to_detail_rate_pct,
    -- Product Conversion Rate = Purchases / Product Views
    ROUND(100.0 * COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) / 
          NULLIF(COUNT(CASE WHEN event_type = 'product_view' THEN 1 END), 0), 2) AS view_to_purchase_rate_pct,
    -- Cart Abandonment Rate for this product
    ROUND(100.0 * (COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) - 
                   COUNT(CASE WHEN event_type = 'purchase' THEN 1 END)) / 
          NULLIF(COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END), 0), 2) AS cart_abandonment_pct
FROM ecommerce_events
WHERE product_id IS NOT NULL
GROUP BY product_id, product_name, category
ORDER BY total_revenue DESC;


-- ------------------------------------------------------------------------------
-- 4. CATEGORY CONTRIBUTION & CUMULATIVE REVENUE (PARETO 80/20)
-- ------------------------------------------------------------------------------
WITH category_rev AS (
    SELECT
        category,
        COUNT(DISTINCT session_id) AS category_sessions,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) AS category_orders,
        ROUND(SUM(revenue), 2) AS category_revenue
    FROM ecommerce_events
    WHERE category IS NOT NULL
    GROUP BY category
),
category_calc AS (
    SELECT
        category,
        category_sessions,
        category_orders,
        category_revenue,
        ROUND(100.0 * category_revenue / SUM(category_revenue) OVER (), 2) AS revenue_share_pct,
        ROUND(100.0 * SUM(category_revenue) OVER (ORDER BY category_revenue DESC) / 
              SUM(category_revenue) OVER (), 2) AS cumulative_revenue_pct
    FROM category_rev
)
SELECT * FROM category_calc
ORDER BY category_revenue DESC;


-- ------------------------------------------------------------------------------
-- 5. OVERALL CART ABANDONMENT RATE (Session Level)
-- ------------------------------------------------------------------------------
WITH cart_sessions AS (
    SELECT
        session_id,
        device,
        traffic_source,
        MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS added_to_cart,
        MAX(CASE WHEN event_type = 'initiate_checkout' THEN 1 ELSE 0 END) AS initiated_checkout,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS completed_purchase
    FROM ecommerce_events
    GROUP BY session_id, device, traffic_source
)
SELECT
    COUNT(CASE WHEN added_to_cart = 1 THEN 1 END) AS total_cart_sessions,
    COUNT(CASE WHEN initiated_checkout = 1 THEN 1 END) AS checkout_sessions,
    COUNT(CASE WHEN completed_purchase = 1 THEN 1 END) AS purchased_sessions,
    COUNT(CASE WHEN added_to_cart = 1 AND completed_purchase = 0 THEN 1 END) AS abandoned_cart_sessions,
    -- Cart Abandonment Rate = (Cart Sessions - Purchase Sessions) / Cart Sessions
    ROUND(100.0 * COUNT(CASE WHEN added_to_cart = 1 AND completed_purchase = 0 THEN 1 END) / 
          NULLIF(COUNT(CASE WHEN added_to_cart = 1 THEN 1 END), 0), 2) AS cart_abandonment_rate_pct,
    -- Checkout Dropoff Rate = (Checkout Sessions - Purchase Sessions) / Checkout Sessions
    ROUND(100.0 * COUNT(CASE WHEN initiated_checkout = 1 AND completed_purchase = 0 THEN 1 END) / 
          NULLIF(COUNT(CASE WHEN initiated_checkout = 1 THEN 1 END), 0), 2) AS checkout_dropoff_rate_pct
FROM cart_sessions;
