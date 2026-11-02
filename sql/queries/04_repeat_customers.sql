-- customer_id identifies a particular checkout; customer_unique_id identifies a buyer.
WITH order_totals AS (
    SELECT order_id, SUM(price) AS product_sales
    FROM order_items GROUP BY order_id
),
buyer_totals AS (
    SELECT c.customer_unique_id,
           COUNT(DISTINCT o.order_id) AS num_orders,
           SUM(t.product_sales) AS lifetime_sales
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    JOIN order_totals AS t ON t.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT CASE WHEN num_orders >= 2 THEN 'repeat_buyer' ELSE 'one_time_buyer' END AS buyer_segment,
       COUNT(*) AS buyers,
       SUM(num_orders) AS orders,
       ROUND(AVG(lifetime_sales), 2) AS avg_buyer_spend_brl
FROM buyer_totals
GROUP BY buyer_segment
ORDER BY buyers DESC;
