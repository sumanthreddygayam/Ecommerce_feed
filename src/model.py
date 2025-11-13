import pandas as pd
import json
from sklearn.cluster import KMeans

# Default starting weights for new users
DEFAULT_WEIGHTS = {
    "w1_collab": 0.45, "w2_user": 0.45, "w3_business": 0.10,
    "x1_cancelled": -0.9, "x2_repeating": 1.0, "x3_search": 0.8, "x4_seen": 0.3,
}
LEARNING_RATE = 0.05

class PersonalizedFeed:
    def __init__(self, data_filepath, weights_filepath):
        self.user_item_df = pd.read_csv(data_filepath)
        self.user_item_df['rating'] = 1
        self.user_vectors = self._create_user_vectors()
        self.user_cluster_map = self._cluster_users()
        self.weights_filepath = weights_filepath
        self.user_weight_profiles = self._load_user_weights()
        print("Model initialized. User clusters and weight profiles are loaded.")

    def _create_user_vectors(self):
        matrix = self.user_item_df.pivot_table(index='Customer_ID', columns='Purchase_Category', values='rating').fillna(0)
        return matrix

    def _cluster_users(self, n_clusters=10):
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        clusters = kmeans.fit_predict(self.user_vectors)
        return pd.Series(clusters, index=self.user_vectors.index).to_dict()

    def _load_user_weights(self):
        try:
            with open(self.weights_filepath, 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return {}

    def _save_user_weights(self):
        with open(self.weights_filepath, 'w') as f: json.dump(self.user_weight_profiles, f, indent=4)

    def _get_user_weights(self, user_id):
        user_id_str = str(user_id)
        if user_id_str not in self.user_weight_profiles:
            self.user_weight_profiles[user_id_str] = DEFAULT_WEIGHTS.copy()
        return self.user_weight_profiles[user_id_str]

    def get_collab_score(self, user_id):
        if user_id not in self.user_cluster_map: return pd.Series(dtype=float)
        target_cluster = self.user_cluster_map[user_id]
        cluster_users = [u for u, c in self.user_cluster_map.items() if c == target_cluster]
        cluster_vectors = self.user_vectors.loc[cluster_users]
        return cluster_vectors.sum(axis=0) / len(cluster_users)

    def get_user_score(self, recent_user_actions, weights):
        user_scores = {}
        action_map = {"cancelled_order": "x1_cancelled", "repeating_order": "x2_repeating", "search": "x3_search", "seen": "x4_seen"}
        for action_type, items in recent_user_actions.items():
            weight_key = action_map.get(action_type)
            if weight_key:
                weight = weights.get(weight_key, 0)
                for item in items: user_scores[item] = user_scores.get(item, 0) + weight
        return pd.Series(user_scores)

    def get_business_score(self, business_items):
        business_scores = {}
        for item in business_items.get('promoted', []) + business_items.get('trending', []): business_scores[item] = 1.0
        return pd.Series(business_scores)

    def get_feed_recommendations(self, user_id, recent_user_actions, business_items, n=10):
        weights = self._get_user_weights(user_id)
        s_collab = self.get_collab_score(user_id)
        s_user = self.get_user_score(recent_user_actions, weights)
        s_business = self.get_business_score(business_items)
        final_scores = (weights['w1_collab'] * s_collab).add(weights['w2_user'] * s_user, fill_value=0).add(weights['w3_business'] * s_business, fill_value=0)
        interacted_items = self.user_vectors.loc[user_id][self.user_vectors.loc[user_id] > 0].index
        final_scores = final_scores.drop(index=interacted_items, errors='ignore')
        return final_scores.sort_values(ascending=False).head(n).to_dict()

    def update_user_weights(self, user_id, dominant_signal):
        user_id_str = str(user_id)
        weights = self._get_user_weights(user_id_str)
        if dominant_signal in ['search', 'seen', 'repeating_order']:
            weights['w2_user'] = min(1.0, weights['w2_user'] + LEARNING_RATE)
            weights['w1_collab'] = max(0.0, weights['w1_collab'] - LEARNING_RATE)
            if dominant_signal == 'search': weights['x3_search'] += LEARNING_RATE
            elif dominant_signal == 'seen': weights['x4_seen'] += LEARNING_RATE
        elif dominant_signal == 'collab':
            weights['w1_collab'] = min(1.0, weights['w1_collab'] + LEARNING_RATE)
            weights['w2_user'] = max(0.0, weights['w2_user'] - LEARNING_RATE)
        self.user_weight_profiles[user_id_str] = weights
        self._save_user_weights()
        return weights