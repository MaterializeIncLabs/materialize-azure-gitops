-- Verify both topics received new data through single connection

-- Check orders count (should have increased)
SELECT COUNT(*) as total_orders FROM orders;

-- Show latest orders
SELECT order_id, customer_name, total_amount, status, created_at 
FROM orders 
ORDER BY created_at DESC 
LIMIT 8;

-- Check customers still show upserted data
SELECT 
    customer_id,
    first_name || ' ' || last_name as full_name,
    tier,
    status,
    total_orders,
    lifetime_value,
    updated_at
FROM customers 
WHERE customer_id IN ('CUST001', 'CUST004', 'CUST007')
ORDER BY customer_id;

-- Summary: Show data flowing through single connection to multiple topics
SELECT 
    'SUMMARY' as info,
    'Single connection: eventhubs_multi_kafka' as connection_info
UNION ALL
SELECT 
    'Orders' as info,
    COUNT(*)::text || ' messages from "orders" topic' as connection_info
FROM orders
UNION ALL
SELECT 
    'Customers' as info,
    COUNT(*)::text || ' unique customers from "customers" topic (upserted)' as connection_info
FROM customers;