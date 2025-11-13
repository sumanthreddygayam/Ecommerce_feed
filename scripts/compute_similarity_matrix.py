# scripts/compute_similarity_matrix.py
import pandas as pd
from pymongo import MongoClient
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import pickle

# Make sure this file is in your root directory
from config import MONGO_URI, DATABASE_NAME

def compute_and_save_matrix():
    """
    Computes the item-item similarity matrix based on user interaction data
    and saves it to a file for fast lookup by the recommendation engine.
    """
    print("Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    # Fetch all 'seen' and 'order' events to understand user behavior
    events = list(db.events.find({"action": {"$in": ["seen", "order"]}}))
    df = pd.DataFrame(events)
    print(f"Fetched {len(df)} user interaction events.")

    # We assign a higher weight to 'order' events than 'seen' events
    df['interaction_strength'] = df['action'].apply(lambda x: 2.0 if x == 'order' else 1.0)
    
    # Create a user-item interaction matrix (rows=users, columns=products)
    interaction_matrix = df.pivot_table(index='user_id', columns='product_id', values='interaction_strength').fillna(0)
    
    # Convert to a sparse matrix for memory efficiency
    sparse_matrix = csr_matrix(interaction_matrix.values)
    
    # Compute cosine similarity between items (the columns of the matrix)
    print("Computing item-item similarity...")
    item_similarity = cosine_similarity(sparse_matrix.T)
    
    # Create a DataFrame for easy lookup
    item_similarity_df = pd.DataFrame(item_similarity, index=interaction_matrix.columns, columns=interaction_matrix.columns)
    
    # Save the resulting model to a file
    with open('recommendation_engine/item_similarity.pkl', 'wb') as f:
        pickle.dump(item_similarity_df, f)

    print("Item similarity model ('item_similarity.pkl') has been computed and saved.")

if __name__ == "__main__":
    compute_and_save_matrix()