-- Test that both topics are accessible through single connection

-- Show all connections and sources
SELECT name, type FROM mz_catalog.mz_objects WHERE type IN ('connection', 'source') AND schema_id = (SELECT id FROM mz_catalog.mz_schemas WHERE name = 'public');

-- Check orders data
SELECT COUNT(*) as order_count FROM orders;
SELECT order_id, customer_name, total_amount, status, region FROM orders ORDER BY created_at DESC LIMIT 5;

-- Check customers data  
SELECT COUNT(*) as customer_count FROM customers;
SELECT customer_id, first_name || ' ' || last_name as full_name, tier, status, total_orders, lifetime_value FROM customers ORDER BY lifetime_value DESC LIMIT 5;

-- Show connection usage
SELECT 
    c.name as connection_name,
    COUNT(s.name) as sources_using_connection
FROM mz_catalog.mz_connections c
LEFT JOIN mz_catalog.mz_kafka_sources ks ON ks.connection_id = c.id
LEFT JOIN mz_catalog.mz_sources s ON s.id = ks.id
WHERE c.name = 'eventhubs_multi_kafka'
GROUP BY c.name;

-- Verify both topics are being consumed from the same connection
SELECT 
    s.name as source_name,
    c.name as connection_name,
    ks.topic as kafka_topic
FROM mz_catalog.mz_sources s
JOIN mz_catalog.mz_kafka_sources ks ON s.id = ks.id
JOIN mz_catalog.mz_connections c ON ks.connection_id = c.id
WHERE c.name = 'eventhubs_multi_kafka'
ORDER BY s.name;