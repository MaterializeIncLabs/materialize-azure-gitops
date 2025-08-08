#!/usr/bin/env python3

import asyncio
import json
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData

import os

# Get connection string from environment variable  
CONNECTION_STR = os.getenv('EVENTHUBS_PUBLISHER_CONNECTION_STRING')
if not CONNECTION_STR:
    print("❌ Error: EVENTHUBS_PUBLISHER_CONNECTION_STRING environment variable not set")
    print("Please source your .env file: source .env")
    exit(1)

# Add EntityPath for orders topic
CONNECTION_STR = CONNECTION_STR + ";EntityPath=orders"

async def send_test_message():
    producer = EventHubProducerClient.from_connection_string(conn_str=CONNECTION_STR)
    
    try:
        async with producer:
            event_data_batch = await producer.create_batch()
            
            test_order = {
                "order_id": "test_order_001",
                "customer_name": "Test Customer",
                "product_id": "prod_test",
                "product_name": "Test Product",
                "unit_price": 19.99,
                "quantity": 1,
                "total_amount": 19.99,
                "status": "confirmed",
                "created_at": "2025-08-08T15:30:00Z",
                "region": "US-East"
            }
            
            event_data = EventData(json.dumps(test_order))
            event_data_batch.add(event_data)
            
            await producer.send_batch(event_data_batch)
            print("✅ Test message sent successfully!")
            print(f"Order ID: {test_order['order_id']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Sending test message to Event Hub...")
    asyncio.run(send_test_message())