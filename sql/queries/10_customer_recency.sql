-- Recency is measured relative to the LAST purchase in the historical dataset,
-- NOT relative to the current date (the data ends in 2018).
WITH max_date AS (
    SELECT date(MAX(order_purchase_timestamp)) AS snapshot_date FROM orders
),
order_totals AS (
    SELECT order_id, SUM(price) AS product_sales FROM order_items GROUP BY order_id
),
buyers AS (
    SELECT c.customer_unique_id,
           COUNT(DISTINCT o.order_id) AS frequency,
           SUM(t.product_sales) AS monetary_brl,
           CAST(julianday(m.snapshot_date) -
                julianday(date(MAX(o.order_purchase_timestamp))) AS INTEGER) AS recency_days
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    JOIN order_totals AS t ON t.order_id = o.order_id
    CROSS JOIN max_date AS m
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT CASE
         WHEN frequency >= 2 AND recency_days <= 180 THEN 'repeat_recent'
         WHEN frequency >= 2 THEN 'repeat_older'
         WHEN recency_days <= 180 THEN 'one_time_recent'
         ELSE 'one_time_older'
       END AS segment,
       COUNT(*) AS buyers,
       ROUND(AVG(recency_days), 1) AS avg_recency_days,
       ROUND(AVG(frequency), 2) AS avg_orders_per_buyer,
       ROUND(AVG(monetary_brl), 2) AS avg_lifetime_sales_brl
FROM buyers
GROUP BY segment
ORDER BY buyers DESC;
