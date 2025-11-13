# recommendation_engine/trending.py
from datetime import datetime, timedelta
import math
from config import TIME_DECAY_LAMBDA

class Trending:
    def __init__(self, db_events):
        self.db_events = db_events

    def get_scores(self):
        """
        Calculates trending scores based on all user actions in the last 48 hours.
        """
        # Fetch all 'order' events from the last 48 hours
        forty_eight_hours_ago = datetime.utcnow() - timedelta(hours=48)
        recent_orders = self.db_events.find({"action": "order", "timestamp": {"$gte": forty_eight_hours_ago}})
        
        product_scores = {}
        now = datetime.utcnow()

        for event in recent_orders:
            product_id = event['product_id']
            timestamp = event['timestamp']
            
            hours_diff = (now - timestamp).total_seconds() / 3600
            decay_factor = math.exp(-TIME_DECAY_LAMBDA * hours_diff)
            
            product_scores[product_id] = product_scores.get(product_id, 0) + decay_factor

        # Normalize scores
        if not product_scores:
            return {}
            
        max_score = max(product_scores.values())
        normalized_scores = {pid: score / max_score for pid, score in product_scores.items()}
        
        return normalized_scores