# recommendation_engine/collaborative_filtering.py
import pandas as pd
import pickle
from config import N_SIMILAR_ITEMS

class CollaborativeFiltering:
    def __init__(self):
        self.matrix_path = 'recommendation_engine/item_similarity.pkl'
        self.similarity_matrix = pd.DataFrame()
        self.load_matrix() # Load the model when the class is created

    def load_matrix(self):
        """Loads or reloads the similarity matrix from the file."""
        try:
            with open(self.matrix_path, 'rb') as f:
                self.similarity_matrix = pickle.load(f)
                print("Collaborative filtering model loaded/reloaded successfully.")
        except FileNotFoundError:
            print(f"Warning: {self.matrix_path} not found. Run the compute script first.")
            self.similarity_matrix = pd.DataFrame()

    def get_scores(self, user_history_product_ids):
        """
        Takes a list of products a user has seen/ordered and returns a dictionary
        of similar products with their similarity scores.
        """
        if self.similarity_matrix.empty or not user_history_product_ids:
            return {}

        all_similar_items = pd.Series(dtype=float)
        
        # For each item in the user's history, find similar items and add up the scores
        for product_id in user_history_product_ids:
            if product_id in self.similarity_matrix.index:
                similar = self.similarity_matrix[product_id].sort_values(ascending=False)
                all_similar_items = all_similar_items.add(similar, fill_value=0)

        # Remove items the user has already seen
        all_similar_items.drop(user_history_product_ids, inplace=True, errors='ignore')
        
        if all_similar_items.empty:
            return {}
            
        # Normalize the scores to be between 0 and 1
        scores = all_similar_items / all_similar_items.max()
        
        return scores.nlargest(N_SIMILAR_ITEMS * 5).to_dict()