-- Verify that upserts are working by checking specific customers

-- Check the total count (should still be 10 customers)
SELECT COUNT(*) as total_customers FROM customers;

-- Show the 3 customers we just updated with their new data
SELECT 
    customer_id,
    first_name || ' ' || last_name as full_name,
    email,
    city || ', ' || state as location,
    tier,
    status,
    total_orders,
    lifetime_value,
    updated_at
FROM customers 
WHERE customer_id IN ('CUST001', 'CUST004', 'CUST007')
ORDER BY customer_id;

-- Compare before and after - show top customers by LTV now
SELECT 
    customer_id,
    first_name || ' ' || last_name as full_name,
    tier,
    status,
    total_orders,
    lifetime_value,
    CASE 
        WHEN lifetime_value > 1000 THEN '💎 VIP Customer'
        WHEN lifetime_value > 100 THEN '⭐ Premium Customer' 
        WHEN total_orders > 0 THEN '✅ Active Customer'
        ELSE '👤 Basic Customer'
    END as customer_segment,
    updated_at
FROM customers 
ORDER BY lifetime_value DESC;

-- Show tier distribution after updates
SELECT 
    tier,
    COUNT(*) as customer_count,
    AVG(total_orders) as avg_orders,
    SUM(lifetime_value) as total_ltv,
    MAX(lifetime_value) as max_ltv
FROM customers 
GROUP BY tier
ORDER BY 
    CASE tier
        WHEN 'bronze' THEN 1
        WHEN 'silver' THEN 2  
        WHEN 'gold' THEN 3
        WHEN 'platinum' THEN 4
    END;