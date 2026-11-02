-- Reviews can have more than one row per order; aggregate before joining orders.
-- Descriptive association, not evidence of causation.
WITH order_reviews_agg AS (
    SELECT order_id, AVG(review_score) AS avg_review_score
    FROM order_reviews
    WHERE review_score IS NOT NULL
    GROUP BY order_id
),
classified AS (
    SELECT o.order_id, r.avg_review_score,
           CASE WHEN date(o.order_delivered_customer_date)
                  > date(o.order_estimated_delivery_date)
                THEN 'late' ELSE 'on_time' END AS delivery_group
    FROM orders AS o
    JOIN order_reviews_agg AS r ON r.order_id = o.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
)
SELECT delivery_group, COUNT(*) AS reviewed_orders,
       ROUND(AVG(avg_review_score), 2) AS avg_review_score,
       ROUND(100.0 * AVG(CASE WHEN avg_review_score <= 2 THEN 1.0 ELSE 0.0 END), 2)
         AS low_rating_pct
FROM classified
GROUP BY delivery_group
ORDER BY delivery_group;
