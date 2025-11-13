# delete_data.py
from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME

def delete_all_data():
    """
    Connects to the MongoDB database and deletes all collections.
    """
    try:
        print("Connecting to MongoDB...")
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]

        print(f"Deleting all collections from database: '{DATABASE_NAME}'...")

        # Get all collection names and delete them
        collections = db.list_collection_names()
        for collection in collections:
            db[collection].drop()
            print(f"  - Collection '{collection}' deleted.")

        print("All data has been successfully deleted.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Ask for confirmation to prevent accidental deletion
    confirmation = input(f"Are you sure you want to delete ALL data from the '{DATABASE_NAME}' database? This cannot be undone. (yes/no): ")
    if confirmation.lower() == 'yes':
        delete_all_data()
    else:
        print("Deletion cancelled.")