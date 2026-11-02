-- Payment amounts include freight and can span multiple transactions per order.
-- Do not interpret the number of transactions as the number of orders.
SELECT p.payment_type,
       COUNT(*) AS payment_transactions,
       COUNT(DISTINCT p.order_id) AS distinct_orders_using_method,
       ROUND(SUM(p.payment_value), 2) AS payment_amount_brl,
       ROUND(AVG(p.payment_installments), 2) AS avg_installments
FROM order_payments AS p
JOIN orders AS o ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY p.payment_type
ORDER BY payment_amount_brl DESC;
