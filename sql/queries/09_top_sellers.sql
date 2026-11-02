-- Seller-level ranking; multiple sellers can contribute to the same order.
WITH seller_totals AS (
    SELECT s.seller_id, s.seller_state,
           COUNT(DISTINCT oi.order_id) AS distinct_orders,
           SUM(oi.price) AS gross_sales_brl
    FROM sellers AS s
    JOIN order_items AS oi ON oi.seller_id = s.seller_id
    JOIN orders AS o ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY s.seller_id, s.seller_state
)
SELECT DENSE_RANK() OVER (ORDER BY gross_sales_brl DESC) AS seller_rank,
       seller_id, seller_state, distinct_orders,
       ROUND(gross_sales_brl, 2) AS gross_sales_brl
FROM seller_totals
ORDER BY gross_sales_brl DESC
LIMIT 20;
