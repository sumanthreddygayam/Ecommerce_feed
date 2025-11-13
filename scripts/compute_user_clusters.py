# scripts/compute_user_clusters.py
import pandas as pd
from pymongo import MongoClient
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from config import MONGO_URI, DATABASE_NAME

def create_user_clusters(num_clusters=8):
    """
    Analyzes user interaction history with categories and groups users into clusters.
    """
    print("Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    # 1. Fetch all historical events
    events = list(db.historical_events.find({}, {"user_id": 1, "detail.category": 1}))
    df = pd.json_normalize(events)
    df.rename(columns={'detail.category': 'category'}, inplace=True)
    print(f"Fetched {len(df)} historical events.")

    if df.empty:
        print("No historical events to process for clustering.")
        return

    # 2. Create a user-category interaction matrix
    # This counts how many times each user interacted with each category
    user_category_matrix = pd.crosstab(df['user_id'], df['category'])

    # 3. Scale the data for better K-Means performance
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(user_category_matrix)

    # 4. Apply K-Means clustering
    print(f"Applying K-Means to group users into {num_clusters} clusters...")
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    user_category_matrix['cluster_id'] = kmeans.fit_predict(scaled_features)

    # 5. Update each user in the 'users' collection with their new cluster ID
    print("Updating users in the database with their assigned cluster ID...")
    for user_id, row in user_category_matrix.iterrows():
        cluster_id = int(row['cluster_id'])
        db.users.update_one(
            {'user_id': user_id},
            {'$set': {'cluster_id': cluster_id}}
        )
    
    print("User clustering complete. All users have been assigned a cluster_id.")

if __name__ == "__main__":
    create_user_clusters()