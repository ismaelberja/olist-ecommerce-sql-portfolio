-- Executive scorecard. Grain: ONE row per delivered order.
-- Sales = sum of order-item prices, excluding freight. Payment totals are NOT joined
-- to avoid many-to-many fanout between items and transactions.
WITH order_totals AS (
    SELECT order_id,
           SUM(price) AS product_sales,
           SUM(freight_value) AS freight_cost
    FROM order_items
    GROUP BY order_id
),
delivered AS (
    SELECT o.order_id, c.customer_unique_id,
           t.product_sales, t.freight_cost,
           o.order_delivered_customer_date, o.order_estimated_delivery_date
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    JOIN order_totals AS t ON t.order_id = o.order_id
    WHERE o.order_status = 'delivered'
)
SELECT COUNT(*) AS delivered_orders,
       COUNT(DISTINCT customer_unique_id) AS unique_buyers,
       ROUND(SUM(product_sales), 2) AS gross_sales_brl,
       ROUND(AVG(product_sales), 2) AS avg_order_value_brl,
       ROUND(SUM(freight_cost), 2) AS shipping_charged_brl,
       ROUND(100.0 * SUM(CASE WHEN order_delivered_customer_date IS NOT NULL
                                 AND order_estimated_delivery_date IS NOT NULL
                                 AND date(order_delivered_customer_date) <= date(order_estimated_delivery_date)
                            THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN order_delivered_customer_date IS NOT NULL
                                    AND order_estimated_delivery_date IS NOT NULL
                               THEN 1 ELSE 0 END), 0), 2) AS on_time_delivery_pct
FROM delivered;
