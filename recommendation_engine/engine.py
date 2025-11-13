from collections import defaultdict, Counter
from datetime import datetime, timedelta, UTC
from .collaborative_filtering import CollaborativeFiltering
from .personalization import Personalization

class RecommendationEngine:
    def __init__(self, db):
        self.db = db
        self.personalization_filter = Personalization(self.db)
        # We no longer need the item-based collaborative filter for this section
        # self.collaborative_filter = CollaborativeFiltering()

    def get_recommendations_separated(self, list_size=10):
        # --- Get User's Full Interaction History to Avoid Duplicates ---
        historical_history = list(self.db.historical_events.find({'user_id': 'adhir_samal'}))
        live_history = list(self.db.live_events.find())
        all_seen_pids = set()
        for event in historical_history + live_history:
            try: all_seen_pids.add(int(event.get('detail', {}).get('order_number')))
            except (ValueError, TypeError, AttributeError): continue
            
        # --- Helper to Finalize Lists ---
        def finalize_list(pids):
            final_list = []
            for pid in pids:
                if pid not in all_seen_pids:
                    final_list.append(pid)
                    all_seen_pids.add(pid)
                if len(final_list) >= list_size: break
            return final_list

        # --- 💡 NEW LOGIC for "For You" (Collaborative) Recommendations ---
        collaborative_recs = []
        try:
            # 1. Get the current user's cluster ID
            user_profile = self.db.users.find_one({'user_id': 'adhir_samal'})
            if user_profile and 'cluster_id' in user_profile:
                cluster_id = user_profile['cluster_id']
                print(f"User adhir_samal belongs to cluster {cluster_id}.")

                # 2. Find other users in the same cluster
                other_users_in_cluster = list(self.db.users.find(
                    {'cluster_id': cluster_id, 'user_id': {'$ne': 'adhir_samal'}},
                    {'user_id': 1}
                ))
                other_user_ids = [u['user_id'] for u in other_users_in_cluster]

                if other_user_ids:
                    # 3. Find all historical items those users interacted with
                    cluster_events = list(self.db.historical_events.find({'user_id': {'$in': other_user_ids}}))
                    
                    # 4. Rank those items by popularity
                    pids_to_count = [int(e['detail']['order_number']) for e in cluster_events if e.get('detail', {}).get('order_number')]
                    if pids_to_count:
                        cluster_item_counter = Counter(pids_to_count)
                        collab_pids = [pid for pid, count in cluster_item_counter.most_common()]
                        collaborative_recs = finalize_list(collab_pids)
        except Exception as e:
            print(f"ENGINE_ERROR (Collaborative-Clustering): {e}")

        # --- "Based on Your Recent Activity" Recommendations (No Change) ---
        self_feed_recs = []
        try:
            self_feed_pids = self.personalization_filter.get_category_recommendations()
            self_feed_recs = finalize_list(self_feed_pids)
        except Exception as e:
            print(f"ENGINE_ERROR (Self Feed): {e}")
            
        # --- "Trending Now" Recommendations (No Change) ---
        trending_recs = []
        try:
            event_source = list(self.db.live_events.find({"serverTimestamp": {"$gte": datetime.now(UTC) - timedelta(days=2)}}))
            if not event_source: event_source = list(self.db.historical_events.find())
            pids_to_count = [int(e['detail']['order_number']) for e in event_source if e.get('detail', {}).get('order_number')]
            if pids_to_count:
                trending_pids_counter = Counter(pids_to_count)
                trending_pids = [pid for pid, count in trending_pids_counter.most_common(20)]
            trending_recs = finalize_list(trending_pids)
        except Exception as e:
            print(f"ENGINE_ERROR (Trending): {e}")

        return {
            "collaborative": collaborative_recs,
            "self_feed": self_feed_recs,
            "trending": trending_recs
        }