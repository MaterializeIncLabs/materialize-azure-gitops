#!/usr/bin/env python3

import asyncio
import json
import random
import time
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

SAMPLE_ORDERS = [
    {
        "order_id": "order_001",
        "customer_name": "Alice Johnson",
        "product_id": "prod_1",
        "product_name": "Wireless Headphones",
        "unit_price": 99.99,
        "quantity": 2,
        "total_amount": 199.98,
        "status": "confirmed",
        "created_at": "2025-08-08T15:25:00Z",
        "region": "US-East"
    },
    {
        "order_id": "order_002",
        "customer_name": "Bob Smith",
        "product_id": "prod_2",
        "product_name": "Smartphone Case",
        "unit_price": 19.99,
        "quantity": 1,
        "total_amount": 19.99,
        "status": "shipped",
        "created_at": "2025-08-08T15:26:00Z",
        "region": "US-West"
    },
    {
        "order_id": "order_003",
        "customer_name": "Charlie Brown",
        "product_id": "prod_3",
        "product_name": "USB Cable",
        "unit_price": 9.99,
        "quantity": 3,
        "total_amount": 29.97,
        "status": "delivered",
        "created_at": "2025-08-08T15:27:00Z",
        "region": "EU-Central"
    },
    {
        "order_id": "order_004",
        "customer_name": "Diana Prince",
        "product_id": "prod_4",
        "product_name": "Bluetooth Speaker",
        "unit_price": 49.99,
        "quantity": 1,
        "total_amount": 49.99,
        "status": "pending",
        "created_at": "2025-08-08T15:28:00Z",
        "region": "AP-Southeast"
    },
    {
        "order_id": "order_005",
        "customer_name": "Eve Adams",
        "product_id": "prod_5",
        "product_name": "Power Bank",
        "unit_price": 29.99,
        "quantity": 2,
        "total_amount": 59.98,
        "status": "confirmed",
        "created_at": "2025-08-08T15:29:00Z",
        "region": "US-East"
    }
]

async def send_sample_orders():
    producer = EventHubProducerClient.from_connection_string(conn_str=CONNECTION_STR)
    
    try:
        async with producer:
            for order in SAMPLE_ORDERS:
                event_data_batch = await producer.create_batch()
                event_data = EventData(json.dumps(order))
                event_data_batch.add(event_data)
                
                await producer.send_batch(event_data_batch)
                print(f"✅ Sent: {order['order_id']} - {order['customer_name']} - ${order['total_amount']}")
                
                # Small delay between messages
                await asyncio.sleep(0.5)
            
            print(f"\n🎉 Successfully sent {len(SAMPLE_ORDERS)} sample orders!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Sending sample orders to Event Hub...")
    asyncio.run(send_sample_orders())