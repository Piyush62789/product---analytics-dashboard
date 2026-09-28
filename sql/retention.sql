-- ==============================================================================
-- PROJECT: Product Analytics Dashboard
-- SCRIPT: retention.sql
-- DESCRIPTION: User Cohort & Retention Analysis for E-Commerce.
--              Includes Weekly Cohort Retention Matrix, N-Day Retention Rates,
--              Repeat Purchase Interval, and Customer Churn Identification.
-- COMPATIBILITY: ANSI SQL (DuckDB, PostgreSQL, BigQuery, Snowflake, SQLite 3.25+)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. WEEKLY ACQUISITION COHORT RETENTION MATRIX
--    Calculates user retention % for Week 0 through Week 8+
-- ------------------------------------------------------------------------------
WITH user_first_activity AS (
    -- Identify the acquisition (first seen) date for each user
    SELECT
        user_id,
        MIN(event_timestamp) AS first_event_time,
        DATE(MIN(event_timestamp), 'weekday 0', '-6 days') AS cohort_week -- Start of week (Monday)
    FROM ecommerce_events
    GROUP BY user_id
),

user_activities AS (
    -- Map every user activity to its respective calendar week
    SELECT DISTINCT
        e.user_id,
        f.cohort_week,
        DATE(e.event_timestamp, 'weekday 0', '-6 days') AS activity_week,
        -- Calculate the week difference between activity and acquisition
        CAST((JULIANDAY(DATE(e.event_timestamp, 'weekday 0', '-6 days')) - 
              JULIANDAY(f.cohort_week)) / 7 AS INTEGER) AS period_number
    FROM ecommerce_events e
    INNER JOIN user_first_activity f ON e.user_id = f.user_id
),

cohort_sizes AS (
    -- Total distinct users acquired in each cohort week
    SELECT
        cohort_week,
        COUNT(DISTINCT user_id) AS cohort_size
    FROM user_first_activity
    GROUP BY cohort_week
),

cohort_retention_counts AS (
    -- Count distinct active users in each subsequent period
    SELECT
        a.cohort_week,
        a.period_number,
        COUNT(DISTINCT a.user_id) AS active_users
    FROM user_activities a
    GROUP BY a.cohort_week, a.period_number
)

SELECT
    c.cohort_week,
    s.cohort_size,
    -- Retention Counts by Week Offset
    MAX(CASE WHEN c.period_number = 0 THEN c.active_users ELSE 0 END) AS w0_users,
    MAX(CASE WHEN c.period_number = 1 THEN c.active_users ELSE 0 END) AS w1_users,
    MAX(CASE WHEN c.period_number = 2 THEN c.active_users ELSE 0 END) AS w2_users,
    MAX(CASE WHEN c.period_number = 3 THEN c.active_users ELSE 0 END) AS w3_users,
    MAX(CASE WHEN c.period_number = 4 THEN c.active_users ELSE 0 END) AS w4_users,
    MAX(CASE WHEN c.period_number = 5 THEN c.active_users ELSE 0 END) AS w5_users,
    MAX(CASE WHEN c.period_number = 6 THEN c.active_users ELSE 0 END) AS w6_users,
    -- Retention Percentages (%)
    ROUND(100.0 * MAX(CASE WHEN c.period_number = 0 THEN c.active_users ELSE 0 END) / s.cohort_size, 1) AS w0_pct,
    ROUND(100.0 * MAX(CASE WHEN c.period_number = 1 THEN c.active_users ELSE 0 END) / s.cohort_size, 1) AS w1_pct,
    ROUND(100.0 * MAX(CASE WHEN c.period_number = 2 THEN c.active_users ELSE 0 END) / s.cohort_size, 1) AS w2_pct,
    ROUND(100.0 * MAX(CASE WHEN c.period_number = 3 THEN c.active_users ELSE 0 END) / s.cohort_size, 1) AS w3_pct,
    ROUND(100.0 * MAX(CASE WHEN c.period_number = 4 THEN c.active_users ELSE 0 END) / s.cohort_size, 1) AS w4_pct,
    ROUND(100.0 * MAX(CASE WHEN c.period_number = 5 THEN c.active_users ELSE 0 END) / s.cohort_size, 1) AS w5_pct,
    ROUND(100.0 * MAX(CASE WHEN c.period_number = 6 THEN c.active_users ELSE 0 END) / s.cohort_size, 1) AS w6_pct
FROM cohort_retention_counts c
INNER JOIN cohort_sizes s ON c.cohort_week = s.cohort_week
GROUP BY c.cohort_week, s.cohort_size
ORDER BY c.cohort_week;


-- ------------------------------------------------------------------------------
-- 2. CLASSIC N-DAY RETENTION (Day 1, Day 7, Day 14, Day 30)
-- ------------------------------------------------------------------------------
WITH first_seen AS (
    SELECT
        user_id,
        DATE(MIN(event_timestamp)) AS first_date
    FROM ecommerce_events
    GROUP BY user_id
),
activity_days AS (
    SELECT DISTINCT
        e.user_id,
        CAST(JULIANDAY(DATE(e.event_timestamp)) - JULIANDAY(f.first_date) AS INTEGER) AS day_diff
    FROM ecommerce_events e
    INNER JOIN first_seen f ON e.user_id = f.user_id
)
SELECT
    (SELECT COUNT(*) FROM first_seen) AS total_acquired_users,
    COUNT(DISTINCT CASE WHEN day_diff = 1 THEN user_id END) AS retained_day_1,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN day_diff = 1 THEN user_id END) / (SELECT COUNT(*) FROM first_seen), 2) AS d1_retention_pct,
    COUNT(DISTINCT CASE WHEN day_diff = 7 THEN user_id END) AS retained_day_7,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN day_diff = 7 THEN user_id END) / (SELECT COUNT(*) FROM first_seen), 2) AS d7_retention_pct,
    COUNT(DISTINCT CASE WHEN day_diff = 14 THEN user_id END) AS retained_day_14,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN day_diff = 14 THEN user_id END) / (SELECT COUNT(*) FROM first_seen), 2) AS d14_retention_pct,
    COUNT(DISTINCT CASE WHEN day_diff = 30 THEN user_id END) AS retained_day_30,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN day_diff = 30 THEN user_id END) / (SELECT COUNT(*) FROM first_seen), 2) AS d30_retention_pct
FROM activity_days;


-- ------------------------------------------------------------------------------
-- 3. REPEAT PURCHASE RETENTION & TIME BETWEEN PURCHASES
-- ------------------------------------------------------------------------------
WITH buyer_orders AS (
    SELECT
        user_id,
        event_timestamp AS order_time,
        revenue,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_timestamp) AS order_number,
        LAG(event_timestamp) OVER (PARTITION BY user_id ORDER BY event_timestamp) AS prev_order_time
    FROM ecommerce_events
    WHERE event_type = 'purchase'
),
repeat_stats AS (
    SELECT
        user_id,
        COUNT(order_number) AS total_orders,
        SUM(revenue) AS customer_ltv,
        AVG(CASE WHEN prev_order_time IS NOT NULL 
                 THEN (JULIANDAY(order_time) - JULIANDAY(prev_order_time)) 
            END) AS avg_days_between_orders
    FROM buyer_orders
    GROUP BY user_id
)
SELECT
    COUNT(DISTINCT user_id) AS total_paying_customers,
    COUNT(DISTINCT CASE WHEN total_orders > 1 THEN user_id END) AS repeat_buyers,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN total_orders > 1 THEN user_id END) / COUNT(DISTINCT user_id), 2) AS repeat_purchase_rate_pct,
    ROUND(AVG(customer_ltv), 2) AS overall_avg_customer_value,
    ROUND(AVG(CASE WHEN total_orders > 1 THEN customer_ltv END), 2) AS repeat_buyer_avg_ltv,
    ROUND(AVG(avg_days_between_orders), 1) AS avg_days_to_repeat_purchase
FROM repeat_stats;


-- ------------------------------------------------------------------------------
-- 4. USER CHURN & INACTIVITY SEGMENTATION
-- ------------------------------------------------------------------------------
WITH user_recency AS (
    SELECT
        user_id,
        user_segment,
        MAX(event_timestamp) AS last_seen,
        CAST(JULIANDAY('2025-04-01') - JULIANDAY(DATE(MAX(event_timestamp))) AS INTEGER) AS days_since_last_activity,
        COUNT(DISTINCT session_id) AS total_sessions,
        SUM(revenue) AS total_spent
    FROM ecommerce_events
    GROUP BY user_id, user_segment
)
SELECT
    CASE
        WHEN days_since_last_activity <= 7 THEN 'Active (<= 7 days)'
        WHEN days_since_last_activity <= 14 THEN 'Cooling (8-14 days)'
        WHEN days_since_last_activity <= 30 THEN 'At Risk (15-30 days)'
        ELSE 'Churned / Dormant (> 30 days)'
    END AS activity_status,
    COUNT(user_id) AS user_count,
    ROUND(100.0 * COUNT(user_id) / (SELECT COUNT(*) FROM user_recency), 2) AS pct_of_user_base,
    ROUND(AVG(total_sessions), 1) AS avg_sessions,
    ROUND(SUM(total_spent), 2) AS segment_revenue
FROM user_recency
GROUP BY 1
ORDER BY MIN(days_since_last_activity);
