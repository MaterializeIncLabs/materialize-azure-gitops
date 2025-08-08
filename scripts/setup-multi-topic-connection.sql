-- Setup single connection for multiple Event Hub topics

-- First, clean up existing connections and sources
DROP MATERIALIZED VIEW IF EXISTS customers;
DROP MATERIALIZED VIEW IF EXISTS orders;
DROP SOURCE IF EXISTS customers_raw;
DROP SOURCE IF EXISTS orders_raw;
DROP CONNECTION IF EXISTS customers_eventhub_kafka;
DROP CONNECTION IF EXISTS eventhub_kafka;
DROP SECRET IF EXISTS customers_eventhub_connection_string;
DROP SECRET IF EXISTS eventhub_connection_string;

-- Create a single secret for the namespace-level connection (no EntityPath)
CREATE SECRET eventhubs_namespace_connection AS '${EVENTHUBS_CONNECTION_STRING}';

-- Create a single Kafka connection that can access all topics
CREATE CONNECTION eventhubs_multi_kafka TO KAFKA (
    BROKER '${EVENTHUBS_NAMESPACE}.servicebus.windows.net:9093',
    SASL MECHANISMS = 'PLAIN',
    SASL USERNAME = '$ConnectionString',
    SASL PASSWORD = SECRET eventhubs_namespace_connection,
    SECURITY PROTOCOL = 'SASL_SSL'
);

-- Create orders source using the shared connection
CREATE SOURCE orders_raw
FROM KAFKA CONNECTION eventhubs_multi_kafka (TOPIC 'orders')
FORMAT JSON;

-- Create customers upsert source using the same shared connection
CREATE SOURCE customers_raw
FROM KAFKA CONNECTION eventhubs_multi_kafka (TOPIC 'customers')
KEY FORMAT TEXT
VALUE FORMAT JSON
ENVELOPE UPSERT;

-- Recreate the orders materialized view
CREATE MATERIALIZED VIEW orders AS
SELECT
    (data->>'order_id')::text as order_id,
    (data->>'customer_name')::text as customer_name,
    (data->>'product_id')::text as product_id,
    (data->>'product_name')::text as product_name,
    (data->>'unit_price')::double as unit_price,
    (data->>'quantity')::int as quantity,
    (data->>'total_amount')::double as total_amount,
    (data->>'status')::text as status,
    (data->>'created_at')::text as created_at,
    (data->>'region')::text as region
FROM orders_raw;

-- Recreate the customers materialized view
CREATE MATERIALIZED VIEW customers AS
SELECT
    (data->>'customer_id')::text as customer_id,
    (data->>'first_name')::text as first_name,
    (data->>'last_name')::text as last_name,
    (data->>'email')::text as email,
    (data->>'phone')::text as phone,
    (data->>'address')::text as address,
    (data->>'city')::text as city,
    (data->>'state')::text as state,
    (data->>'zip_code')::text as zip_code,
    (data->>'tier')::text as tier,
    (data->>'status')::text as status,
    (data->>'total_orders')::int as total_orders,
    (data->>'lifetime_value')::double as lifetime_value,
    (data->>'last_order_date')::text as last_order_date,
    (data->>'created_at')::text as created_at,
    (data->>'updated_at')::text as updated_at
FROM customers_raw
WHERE data IS NOT NULL;