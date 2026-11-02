-- Monthly trends. Purchase date determines month; deliveries may happen later.
WITH order_totals AS (
    SELECT order_id, SUM(price) AS product_sales
    FROM order_items
    GROUP BY order_id
)
SELECT substr(o.order_purchase_timestamp, 1, 7) AS month,
       COUNT(*) AS delivered_orders,
       ROUND(SUM(t.product_sales), 2) AS gross_sales_brl,
       ROUND(AVG(t.product_sales), 2) AS avg_order_value_brl
FROM orders AS o
JOIN order_totals AS t ON t.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp IS NOT NULL
GROUP BY substr(o.order_purchase_timestamp, 1, 7)
ORDER BY month;
