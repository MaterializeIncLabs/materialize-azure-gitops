-- EXAMPLE: Setup Materialize upsert source for customer data from Azure Event Hubs
-- This file uses environment variables - use envsubst for substitution

-- Create secret for customer Event Hub connection
CREATE SECRET customers_eventhub_connection_string AS '${EVENTHUBS_CONNECTION_STRING};EntityPath=customers';

-- Create Kafka connection for customers Event Hub
CREATE CONNECTION customers_eventhub_kafka TO KAFKA (
    BROKER '${EVENTHUBS_NAMESPACE}.servicebus.windows.net:9093',
    SASL MECHANISMS = 'PLAIN',
    SASL USERNAME = '$ConnectionString',
    SASL PASSWORD = SECRET customers_eventhub_connection_string,
    SECURITY PROTOCOL = 'SASL_SSL'
);

-- Create upsert source from customers topic
-- For Event Hubs, we need to use UPSERT with a key to handle updates properly
CREATE SOURCE customers_raw
FROM KAFKA CONNECTION customers_eventhub_kafka (TOPIC 'customers')
KEY FORMAT TEXT
VALUE FORMAT JSON
ENVELOPE UPSERT;

-- Create a view to parse and structure the customer data
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