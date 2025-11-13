# scripts/load_data.py
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import random

from config import MONGO_URI, DATABASE_NAME

def populate_database():
    """
    Reads the eCommerce CSV, cleans the data, and populates the database
    with a SEPARATE collection for historical events.
    """
    print("Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]

    # Clear existing collections
    db.products.drop()
    db.users.drop()
    db.historical_events.drop() # 💡 CHANGED
    db.live_events.drop()      # 💡 ADDED for a clean start
    print("Cleared existing collections.")

    # --- Load and Clean Products ---
    df = pd.read_csv('data/Online-eCommerce.csv')
    df.rename(columns={'Order_Number': 'product_id', 'Product': 'product_name', 'Category': 'category', 'Brand': 'brand'}, inplace=True)
    
    df.dropna(subset=['product_id', 'product_name', 'Customer_Name'], inplace=True)
    df['product_id'] = pd.to_numeric(df['product_id'], errors='coerce', downcast='integer')
    df.dropna(subset=['product_id'], inplace=True)
    df['product_id'] = df['product_id'].astype(int)
    for col in ['product_name', 'category', 'brand', 'Customer_Name']:
        df[col] = df[col].astype(str)
    print("Data loaded and cleaned successfully.")

    products_df = df[['product_id', 'product_name', 'category', 'brand']].drop_duplicates(subset='product_id')
    products_data = products_df.to_dict(orient='records')
    db.products.insert_many(products_data)
    print(f"Inserted {len(products_data)} unique products.")

    # --- Simulate Events and Users ---
    users, events = {}, []
    unique_customers = df['Customer_Name'].unique()

    for customer_name in unique_customers:
        if isinstance(customer_name, str):
            user_id = customer_name.lower().replace(" ", "_")
            users[user_id] = { "user_id": user_id, "name": customer_name, "weights": { "w1_collaborative": 0.50, "w2_personal": 0.40, "w3_trending": 0.10 } }
            customer_orders = df[df['Customer_Name'] == customer_name]
            for _, row in customer_orders.iterrows():
                try:
                    event_time = datetime.strptime(row['Order_Date'], '%d/%m/%Y')
                    # This now creates events with the full detail structure
                    event_detail = { "category": row['category'], "order_number": str(row['product_id']), "product": row['product_name'], "brand": row['brand'] }
                    events.append({ "user_id": user_id, "action": "Order", "detail": event_detail, "serverTimestamp": event_time })
                    events.append({ "user_id": user_id, "action": "Seen", "detail": event_detail, "serverTimestamp": event_time - timedelta(minutes=random.randint(5, 60)) })
                except (ValueError, TypeError): continue

    # 💡 CHANGED: Insert into the historical collection
    db.historical_events.insert_many(events)
    db.users.insert_many(list(users.values()))
    print(f"Inserted {len(users)} users and {len(events)} HISTORICAL events.")
    print("Database population complete.")

if __name__ == "__main__":
    populate_database()