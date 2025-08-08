-- EXAMPLE: Setup Materialize to read from Azure Event Hubs (via Kafka protocol)
-- This file uses environment variables - use envsubst for substitution

-- Create secret for Event Hub connection string
CREATE SECRET eventhub_connection_string AS '${EVENTHUBS_PUBLISHER_CONNECTION_STRING};EntityPath=orders';

-- Create Kafka connection to Event Hub
CREATE CONNECTION eventhub_kafka TO KAFKA (
    BROKER '${EVENTHUBS_NAMESPACE}.servicebus.windows.net:9093',
    SASL MECHANISMS = 'PLAIN',
    SASL USERNAME = '$ConnectionString',
    SASL PASSWORD = SECRET eventhub_connection_string,
    SECURITY PROTOCOL = 'SASL_SSL'
);

-- Create source from the orders topic
CREATE SOURCE orders_raw
FROM KAFKA CONNECTION eventhub_kafka (TOPIC 'orders')
FORMAT JSON;

-- Create a materialized view to parse and transform the data
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