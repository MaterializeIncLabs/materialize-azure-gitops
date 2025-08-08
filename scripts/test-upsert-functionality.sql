-- Test upsert functionality with customer data

-- Check the raw source data count
SELECT COUNT(*) as raw_messages_count FROM customers_raw;

-- Check processed customer data count (should be exactly 10 customers due to upserts)
SELECT COUNT(*) as unique_customers_count FROM customers;

-- Show all current customers with their latest state
SELECT 
    customer_id, 
    first_name, 
    last_name, 
    email,
    tier, 
    status, 
    total_orders, 
    lifetime_value,
    updated_at
FROM customers 
ORDER BY customer_id;

-- Customer distribution by tier (should show current state after updates)
SELECT 
    tier,
    status,
    COUNT(*) as customer_count,
    AVG(total_orders) as avg_orders,
    SUM(lifetime_value) as total_ltv
FROM customers 
GROUP BY tier, status
ORDER BY tier, status;

-- Customers with highest lifetime value
SELECT 
    customer_id,
    first_name || ' ' || last_name as full_name,
    tier,
    total_orders,
    lifetime_value,
    updated_at
FROM customers 
ORDER BY lifetime_value DESC;

-- Show customers who have been updated (have orders or higher tier)
SELECT 
    customer_id,
    first_name || ' ' || last_name as full_name,
    tier,
    status,
    total_orders,
    lifetime_value,
    CASE 
        WHEN total_orders > 0 THEN '✅ Has Orders'
        WHEN tier IN ('gold', 'platinum') THEN '⭐ Premium Tier'
        ELSE '👤 Basic Customer'
    END as customer_type
FROM customers 
ORDER BY lifetime_value DESC, total_orders DESC;