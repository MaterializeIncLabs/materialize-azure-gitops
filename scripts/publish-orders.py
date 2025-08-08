#!/usr/bin/env python3

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
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

# Sample data
CUSTOMERS = ["Alice Johnson", "Bob Smith", "Charlie Brown", "Diana Prince", "Eve Adams", "Frank Miller"]
PRODUCTS = [
    {"id": "prod_1", "name": "Wireless Headphones", "price": 99.99},
    {"id": "prod_2", "name": "Smartphone Case", "price": 19.99},
    {"id": "prod_3", "name": "USB Cable", "price": 9.99},
    {"id": "prod_4", "name": "Bluetooth Speaker", "price": 49.99},
    {"id": "prod_5", "name": "Power Bank", "price": 29.99},
    {"id": "prod_6", "name": "Screen Protector", "price": 12.99}
]

def generate_order():
    """Generate a random order"""
    order_id = f"order_{int(time.time() * 1000)}{random.randint(100, 999)}"
    customer = random.choice(CUSTOMERS)
    product = random.choice(PRODUCTS)
    quantity = random.randint(1, 5)
    total = round(product["price"] * quantity, 2)
    
    # Random timestamp within last 24 hours
    base_time = datetime.utcnow()
    random_offset = timedelta(minutes=random.randint(-1440, 0))  # -24 hours to now
    created_at = (base_time + random_offset).isoformat() + "Z"
    
    return {
        "order_id": order_id,
        "customer_name": customer,
        "product_id": product["id"],
        "product_name": product["name"],
        "unit_price": product["price"],
        "quantity": quantity,
        "total_amount": total,
        "status": random.choice(["pending", "confirmed", "shipped", "delivered"]),
        "created_at": created_at,
        "region": random.choice(["US-East", "US-West", "EU-Central", "AP-Southeast"])
    }

async def send_batch_to_eventhub():
    """Send a batch of orders to Event Hub"""
    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STR
    )
    
    try:
        async with producer:
            # Create a batch of events
            event_data_batch = await producer.create_batch()
            
            # Generate 10 orders for this batch
            orders_sent = 0
            for _ in range(10):
                order = generate_order()
                order_json = json.dumps(order)
                event_data = EventData(order_json)
                
                try:
                    event_data_batch.add(event_data)
                    orders_sent += 1
                    print(f"Added order: {order['order_id']} - {order['customer_name']} - ${order['total_amount']}")
                except ValueError:
                    # Batch is full, send it and create a new one
                    await producer.send_batch(event_data_batch)
                    print(f"Sent batch of {orders_sent} orders")
                    event_data_batch = await producer.create_batch()
                    event_data_batch.add(event_data)
                    orders_sent = 1

            # Send remaining events in the batch
            if len(event_data_batch) > 0:
                await producer.send_batch(event_data_batch)
                print(f"Sent final batch of {orders_sent} orders")
                
    except Exception as e:
        print(f"Error sending to Event Hub: {e}")
    finally:
        await producer.close()

async def continuous_publishing():
    """Continuously publish orders every few seconds"""
    print("Starting continuous order publishing to Event Hub...")
    print("Press Ctrl+C to stop")
    
    batch_count = 0
    try:
        while True:
            batch_count += 1
            print(f"\n--- Batch {batch_count} ---")
            await send_batch_to_eventhub()
            
            # Wait 5 seconds between batches
            await asyncio.sleep(5)
            
    except KeyboardInterrupt:
        print(f"\nStopped after {batch_count} batches")

if __name__ == "__main__":
    # Check if required package is available
    try:
        from azure.eventhub.aio import EventHubProducerClient
        from azure.eventhub import EventData
    except ImportError:
        print("Please install the azure-eventhub package:")
        print("pip install azure-eventhub")
        exit(1)
    
    print("Event Hub Order Publisher")
    print("========================")
    print(f"Target: {CONNECTION_STR.split(';')[0].split('=')[1]}")
    print()
    
    # Run continuous publishing
    asyncio.run(continuous_publishing())