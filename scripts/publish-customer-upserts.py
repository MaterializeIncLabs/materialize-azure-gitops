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

# Add EntityPath for customers topic
CONNECTION_STR = CONNECTION_STR + ";EntityPath=customers"

# Customer base data
CUSTOMERS = [
    "CUST001", "CUST002", "CUST003", "CUST004", "CUST005",
    "CUST006", "CUST007", "CUST008", "CUST009", "CUST010"
]

FIRST_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]
LAST_NAMES = ["Johnson", "Smith", "Brown", "Davis", "Wilson", "Miller", "Moore", "Taylor", "Anderson", "Thomas"]
CITIES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
STATES = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA", "TX", "CA"]
TIERS = ["bronze", "silver", "gold", "platinum"]
STATUSES = ["active", "inactive", "suspended", "pending"]

class CustomerDataGenerator:
    def __init__(self):
        # Track customer state to simulate realistic updates
        self.customer_data = {}
        self.initialize_customers()
    
    def initialize_customers(self):
        """Initialize customers with base data"""
        for i, customer_id in enumerate(CUSTOMERS):
            self.customer_data[customer_id] = {
                "customer_id": customer_id,
                "first_name": FIRST_NAMES[i],
                "last_name": LAST_NAMES[i],
                "email": f"{FIRST_NAMES[i].lower()}.{LAST_NAMES[i].lower()}@example.com",
                "phone": f"555-{random.randint(1000, 9999)}",
                "address": f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Elm Dr', 'Park Rd'])}",
                "city": CITIES[i],
                "state": STATES[i],
                "zip_code": f"{random.randint(10000, 99999)}",
                "tier": random.choice(TIERS),
                "status": "active",
                "total_orders": 0,
                "lifetime_value": 0.0,
                "last_order_date": None,
                "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat() + "Z",
                "updated_at": datetime.now().isoformat() + "Z"
            }
    
    def generate_customer_update(self):
        """Generate an update for a random customer"""
        customer_id = random.choice(CUSTOMERS)
        customer = self.customer_data[customer_id].copy()
        
        # Random update type
        update_type = random.choice([
            "phone_update", "address_update", "tier_upgrade", "status_change", 
            "order_activity", "email_update", "profile_update"
        ])
        
        current_time = datetime.now().isoformat() + "Z"
        customer["updated_at"] = current_time
        
        if update_type == "phone_update":
            customer["phone"] = f"555-{random.randint(1000, 9999)}"
            
        elif update_type == "address_update":
            customer["address"] = f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Elm Dr', 'Park Rd', 'Broadway', 'First Ave'])}"
            customer["city"] = random.choice(CITIES)
            customer["state"] = random.choice(STATES)
            customer["zip_code"] = f"{random.randint(10000, 99999)}"
            
        elif update_type == "tier_upgrade":
            current_tier_idx = TIERS.index(customer["tier"])
            if current_tier_idx < len(TIERS) - 1:
                customer["tier"] = TIERS[current_tier_idx + 1]
            
        elif update_type == "status_change":
            customer["status"] = random.choice(STATUSES)
            
        elif update_type == "order_activity":
            # Simulate new order activity
            customer["total_orders"] += random.randint(1, 3)
            order_value = round(random.uniform(25.0, 500.0), 2)
            customer["lifetime_value"] = round(customer["lifetime_value"] + order_value, 2)
            customer["last_order_date"] = current_time
            
        elif update_type == "email_update":
            # Sometimes customers update their email
            first = customer["first_name"].lower()
            last = customer["last_name"].lower()
            domain = random.choice(['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'])
            customer["email"] = f"{first}.{last}@{domain}"
            
        elif update_type == "profile_update":
            # Update multiple fields at once
            customer["phone"] = f"555-{random.randint(1000, 9999)}"
            customer["total_orders"] += 1
            customer["lifetime_value"] = round(customer["lifetime_value"] + random.uniform(10.0, 100.0), 2)
        
        # Update our tracking
        self.customer_data[customer_id] = customer
        
        return customer_id, customer

async def send_initial_customers(generator):
    """Send initial customer records"""
    producer = EventHubProducerClient.from_connection_string(conn_str=CONNECTION_STR)
    
    try:
        async with producer:
            print("📊 Sending initial customer records...")
            
            for customer_id in CUSTOMERS:
                customer = generator.customer_data[customer_id]
                
                # Create event with key for upsert behavior
                event_data = EventData(json.dumps(customer))
                
                # Send with partition key
                await producer.send_batch([event_data], partition_key=customer_id)
                print(f"✅ Initial: {customer_id} - {customer['first_name']} {customer['last_name']} ({customer['tier']}, {customer['status']})")
                
                await asyncio.sleep(0.2)  # Small delay between messages
                
    except Exception as e:
        print(f"❌ Error sending initial data: {e}")

async def send_customer_updates(generator, num_updates=20):
    """Send customer updates to simulate real-time changes"""
    producer = EventHubProducerClient.from_connection_string(conn_str=CONNECTION_STR)
    
    try:
        async with producer:
            print(f"\n🔄 Sending {num_updates} customer updates...")
            
            for i in range(num_updates):
                customer_id, updated_customer = generator.generate_customer_update()
                
                # Create event with key for upsert behavior
                event_data = EventData(json.dumps(updated_customer))
                
                await producer.send_batch([event_data], partition_key=customer_id)
                print(f"🔄 Update {i+1}: {customer_id} - {updated_customer['first_name']} {updated_customer['last_name']} "
                      f"(Tier: {updated_customer['tier']}, Orders: {updated_customer['total_orders']}, "
                      f"LTV: ${updated_customer['lifetime_value']})")
                
                await asyncio.sleep(random.uniform(1, 3))  # Random delay between updates
                
    except Exception as e:
        print(f"❌ Error sending updates: {e}")

async def continuous_updates(generator):
    """Continuously send customer updates"""
    producer = EventHubProducerClient.from_connection_string(conn_str=CONNECTION_STR)
    
    try:
        async with producer:
            print("\n🚀 Starting continuous customer updates (Press Ctrl+C to stop)...")
            update_count = 0
            
            while True:
                customer_id, updated_customer = generator.generate_customer_update()
                
                event_data = EventData(json.dumps(updated_customer))
                
                await producer.send_batch([event_data], partition_key=customer_id)
                update_count += 1
                print(f"🔄 Update #{update_count}: {customer_id} - "
                      f"{updated_customer['first_name']} {updated_customer['last_name']} "
                      f"(Tier: {updated_customer['tier']}, Orders: {updated_customer['total_orders']}, "
                      f"Status: {updated_customer['status']})")
                
                await asyncio.sleep(random.uniform(2, 5))  # Random delay between updates
                
    except KeyboardInterrupt:
        print(f"\n✋ Stopped after {update_count} updates")
    except Exception as e:
        print(f"❌ Error in continuous updates: {e}")

async def main():
    generator = CustomerDataGenerator()
    
    print("🏗️  Customer Upsert Data Generator")
    print("=" * 40)
    print(f"Target Event Hub: customers")
    print(f"Customer IDs: {', '.join(CUSTOMERS[:5])}...")
    print()
    
    # Send initial customer data
    await send_initial_customers(generator)
    
    print("\n⏳ Waiting 3 seconds...")
    await asyncio.sleep(3)
    
    # Send some updates
    await send_customer_updates(generator, 15)
    
    print("\n✅ Initial data and updates sent!")
    print("💡 You can run this script again to send more updates")
    
    # Uncomment to run continuous updates:
    # await continuous_updates(generator)

if __name__ == "__main__":
    asyncio.run(main())