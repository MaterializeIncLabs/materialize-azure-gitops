-- Test the data pipeline from Azure Event Hubs to Materialize

-- Show all objects
\d

-- Check the raw source
SELECT COUNT(*) as raw_message_count FROM orders_raw;

-- Check the processed orders
SELECT COUNT(*) as processed_order_count FROM orders;

-- Show sample processed orders
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;

-- Aggregate some data
SELECT 
    region,
    status,
    COUNT(*) as order_count,
    SUM(total_amount) as total_revenue
FROM orders 
GROUP BY region, status
ORDER BY region, status;

-- Top customers by revenue
SELECT 
    customer_name,
    COUNT(*) as order_count,
    SUM(total_amount) as total_spent
FROM orders 
GROUP BY customer_name
ORDER BY total_spent DESC;