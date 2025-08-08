#!/usr/bin/env python3

import asyncio
import json
from datetime import datetime
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData

import os

# Get connection string from environment variable
CONNECTION_STR = os.getenv('EVENTHUBS_PUBLISHER_CONNECTION_STRING')
if not CONNECTION_STR:
    print("❌ Error: EVENTHUBS_PUBLISHER_CONNECTION_STRING environment variable not set")
    print("Please source your .env file: source .env")
    exit(1)

# Add EntityPath for customers topic
CONNECTION_STR = CONNECTION_STR + ";EntityPath=customers"

async def send_specific_updates():
    """Send specific updates to demonstrate upsert behavior"""
    producer = EventHubProducerClient.from_connection_string(conn_str=CONNECTION_STR)
    
    # Define specific updates to show upsert behavior clearly
    updates = [
        {
            "customer_id": "CUST001",
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice.johnson.new@gmail.com",  # Email change
            "phone": "555-1111",
            "address": "123 New Street",
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94105",
            "tier": "platinum",
            "status": "active",
            "total_orders": 5,  # New orders
            "lifetime_value": 899.99,  # Updated LTV
            "last_order_date": datetime.now().isoformat() + "Z",
            "created_at": "2024-12-15T10:00:00Z",
            "updated_at": datetime.now().isoformat() + "Z"
        },
        {
            "customer_id": "CUST004",
            "first_name": "Diana",
            "last_name": "Davis", 
            "email": "diana.davis@gmail.com",
            "phone": "555-4444",
            "address": "456 Oak Avenue",
            "city": "Seattle", 
            "state": "WA",
            "zip_code": "98101",
            "tier": "gold",  # Upgraded from bronze
            "status": "active",
            "total_orders": 8,  # Added orders
            "lifetime_value": 1299.99,  # High LTV
            "last_order_date": datetime.now().isoformat() + "Z",
            "created_at": "2024-11-20T15:30:00Z",
            "updated_at": datetime.now().isoformat() + "Z"
        },
        {
            "customer_id": "CUST007",
            "first_name": "Grace",
            "last_name": "Moore",
            "email": "grace.moore@outlook.com",  # Different domain
            "phone": "555-7777",
            "address": "789 Pine Street",
            "city": "Portland",
            "state": "OR", 
            "zip_code": "97201",
            "tier": "platinum",  # Major upgrade from silver
            "status": "active",  # Reactivated from suspended
            "total_orders": 12,  # Lots of orders
            "lifetime_value": 2199.50,  # Highest LTV
            "last_order_date": datetime.now().isoformat() + "Z",
            "created_at": "2024-10-05T12:00:00Z",
            "updated_at": datetime.now().isoformat() + "Z"
        }
    ]
    
    try:
        async with producer:
            print("🔄 Sending specific customer updates to demonstrate upsert...")
            
            for i, update in enumerate(updates, 1):
                customer_id = update["customer_id"]
                event_data = EventData(json.dumps(update))
                
                await producer.send_batch([event_data], partition_key=customer_id)
                print(f"✅ Update {i}: {customer_id} - {update['first_name']} {update['last_name']} "
                      f"(Tier: {update['tier']}, Orders: {update['total_orders']}, "
                      f"LTV: ${update['lifetime_value']}, Status: {update['status']})")
                
                await asyncio.sleep(1)
            
            print(f"\n🎉 Sent {len(updates)} targeted updates!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("📊 Customer Upsert Test - Targeted Updates")
    print("=" * 45)
    asyncio.run(send_specific_updates())