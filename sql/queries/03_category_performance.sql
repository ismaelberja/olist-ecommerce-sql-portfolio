-- Top categories. Orders may contain multiple categories (do not sum category order counts).
SELECT COALESCE(t.product_category_name_english,
                p.product_category_name, 'uncategorized') AS category,
       COUNT(*) AS items_sold,
       COUNT(DISTINCT oi.order_id) AS distinct_orders,
       ROUND(SUM(oi.price), 2) AS gross_sales_brl,
       ROUND(AVG(oi.price), 2) AS avg_item_price_brl
FROM order_items AS oi
JOIN orders AS o ON o.order_id = oi.order_id
JOIN products AS p ON p.product_id = oi.product_id
LEFT JOIN product_categories AS t
  ON t.product_category_name = p.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY category
ORDER BY gross_sales_brl DESC;
