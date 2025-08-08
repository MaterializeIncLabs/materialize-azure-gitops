-- Show the updated data after streaming more orders

-- Current message counts
SELECT COUNT(*) as total_messages FROM orders_raw;

-- Latest orders (should show more recent timestamps)
SELECT order_id, customer_name, total_amount, status, created_at, region 
FROM orders 
ORDER BY created_at DESC 
LIMIT 15;

-- Updated revenue by region and status
SELECT 
    region,
    status,
    COUNT(*) as order_count,
    ROUND(SUM(total_amount)::numeric, 2) as total_revenue
FROM orders 
GROUP BY region, status
ORDER BY region, status;