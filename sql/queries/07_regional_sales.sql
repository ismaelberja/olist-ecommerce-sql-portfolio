-- Sales by customer's destination state; each delivered order counted once.
WITH order_totals AS (
    SELECT order_id, SUM(price) AS product_sales
    FROM order_items GROUP BY order_id
)
SELECT c.customer_state,
       COUNT(*) AS delivered_orders,
       COUNT(DISTINCT c.customer_unique_id) AS unique_buyers,
       ROUND(SUM(t.product_sales), 2) AS gross_sales_brl,
       ROUND(AVG(t.product_sales), 2) AS avg_order_value_brl
FROM orders AS o
JOIN customers AS c ON c.customer_id = o.customer_id
JOIN order_totals AS t ON t.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY gross_sales_brl DESC;
