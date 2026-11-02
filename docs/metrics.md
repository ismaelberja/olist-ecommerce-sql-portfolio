# Metric definitions and methodological notes

This portfolio uses the public Olist dataset. All times refer to the historical dataset, not the current retail market.

| Metric | Definition | Caveat |
|---|---|---|
| Delivered orders | Distinct orders with `order_status = 'delivered'` and at least one line item | Not equal to all placed orders |
| Gross item sales (BRL) | Sum of `order_items.price` for delivered orders | Excludes freight; not net revenue, profit or recognized accounting revenue |
| Average order value (BRL) | Gross item sales divided by delivered orders with items | Each order counted once; never average across item rows |
| Shipping charged (BRL) | Sum of `order_items.freight_value` for delivered orders | Not actual carrier expense |
| On-time delivery | Actual delivery calendar date on/before estimated date, among delivered orders with both dates | Not a causal measure of service quality |
| Unique buyers | Distinct `customers.customer_unique_id` | `customer_id` is assigned once per checkout, so it is NOT a buyer identifier |
| Repeat buyers | Unique buyers with at least two delivered orders | Historical observation window limits repeat estimates |
| Payment amount | Sum of payment transactions for delivered orders | Includes freight; can have multiple transactions per order |
| Average review | Average of one order-level review aggregate across reviewed orders | Reviews are not available for every order; association is not causation |
| Recency | Days since buyer's last delivered order, relative to max order purchase date in the original dataset | **Do not use today's date** on this historical dataset |

## Data model and join-grain warning

- `orders`: one row per order.
- `order_items`: many items per order.
- `order_payments`: sometimes more than one payment per order.
- `order_reviews`: may have multiple review rows per order.
- Joining items, payments and reviews directly at row level **multiplies values**. Preaggregate those tables to order grain before combining them.

## Dataset scope and limitations

- Brazilian e-commerce orders, approximately 2016–2018. It does not represent the full Brazilian retail market.
- Prices are in **BRL**; no inflation or currency conversion applied.
- Only delivered orders are used for sales analyses. Cancellations are intentionally excluded.
- Some dates are null; missing delivery dates must not be interpreted as late deliveries.
- The original publisher licenses the dataset under **CC BY-NC-SA 4.0**; this repository does **not** redistribute the source CSV files.
- Descriptive patterns do not establish causal relationships.
