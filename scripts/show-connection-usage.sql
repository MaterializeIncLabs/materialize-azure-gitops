-- Show connection details and usage

-- Show connections
SELECT name, type FROM mz_catalog.mz_connections WHERE name = 'eventhubs_multi_kafka';

-- Show sources using Kafka
SELECT 
    s.name as source_name,
    'kafka' as source_type
FROM mz_catalog.mz_sources s
JOIN mz_catalog.mz_kafka_sources ks ON s.id = ks.id
WHERE s.name IN ('orders_raw', 'customers_raw')
ORDER BY s.name;

-- Alternative way to verify - show all Kafka sources
SELECT name, type FROM mz_catalog.mz_objects WHERE name IN ('orders_raw', 'customers_raw', 'eventhubs_multi_kafka');

-- Test both data streams are working
SELECT 'orders' as stream, COUNT(*) as message_count FROM orders
UNION ALL
SELECT 'customers' as stream, COUNT(*) as message_count FROM customers
ORDER BY stream;