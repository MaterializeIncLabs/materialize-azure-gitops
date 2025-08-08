-- Cleanup existing objects if any
DROP MATERIALIZED VIEW IF EXISTS orders;
DROP SOURCE IF EXISTS orders_raw;
DROP CONNECTION IF EXISTS eventhub_kafka;
DROP SECRET IF EXISTS eventhub_password;
DROP SECRET IF EXISTS eventhub_connection_string;