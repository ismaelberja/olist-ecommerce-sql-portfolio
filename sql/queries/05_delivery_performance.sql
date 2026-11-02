-- On-time definition: actual delivery date <= Olist's estimated delivery date.
-- Only delivered orders with BOTH dates are included in the denominator.
WITH delivery AS (
    SELECT c.customer_state,
           julianday(date(o.order_delivered_customer_date)) -
           julianday(date(o.order_estimated_delivery_date)) AS days_vs_estimate,
           julianday(o.order_delivered_customer_date) -
           julianday(o.order_purchase_timestamp) AS fulfillment_days
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
)
SELECT customer_state,
       COUNT(*) AS measured_deliveries,
       ROUND(100.0 * AVG(CASE WHEN days_vs_estimate <= 0 THEN 1.0 ELSE 0.0 END), 2) AS on_time_pct,
       ROUND(AVG(fulfillment_days), 1) AS avg_delivery_days,
       ROUND(AVG(CASE WHEN days_vs_estimate > 0 THEN days_vs_estimate END), 1) AS avg_days_late_if_late
FROM delivery
GROUP BY customer_state
ORDER BY measured_deliveries DESC;
