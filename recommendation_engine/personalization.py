from collections import defaultdict

class Personalization:
    def __init__(self, db):
        self.db = db

    def get_category_recommendations(self):
        """
        Finds products from the same categories the user has recently interacted with
        in the live_events collection. This is the definitive logic.
        """
        # Define weights to prioritize categories from positive actions
        action_weights = {"seen": 1.0, "reorder": 1.5, "order": 1.2, "cancel": -2.0}
        
        # 1. Get all recent user activity from the live_events collection
        live_events = list(self.db.live_events.find())

        if not live_events:
            print("PERSONALIZATION: No live events found. 'Recent Activity' will be empty.")
            return []

        # 2. Score each CATEGORY based on the user's actions
        category_scores = defaultdict(float)
        for event in live_events:
            try:
                action = event.get('action', '').lower()
                category = event.get('detail', {}).get('category')
                if category and action in action_weights:
                    category_scores[category] += action_weights[action]
            except (AttributeError):
                continue
        
        # 3. Get the top 3 categories that have a positive score
        top_categories = [
            category for category, score in sorted(category_scores.items(), key=lambda item: item[1], reverse=True) if score > 0
        ][:3] 

        if not top_categories:
            print("PERSONALIZATION: No positively rated categories from live events.")
            return []
            
        print(f"PERSONALIZATION: Recommending from top categories: {top_categories}")

        # 4. Find all products from your product catalog that belong to these top categories
        recommended_products = list(self.db.products.find(
            {"category": {"$in": top_categories}},
            {"product_id": 1, "_id": 0} 
        ))

        # 5. Return the list of product IDs to be displayed
        return [p['product_id'] for p in recommended_products]