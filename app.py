import atexit
from flask import Flask, jsonify, request, send_from_directory
from pymongo import MongoClient
from datetime import datetime, UTC
from collections import defaultdict
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import pickle

from config import MONGO_URI, DATABASE_NAME, FEED_SIZE
from recommendation_engine.engine import RecommendationEngine

# --- APP & DATABASE SETUP ---
app = Flask(__name__, static_folder='static', static_url_path='')
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
recommendation_engine = RecommendationEngine(db)


# --- AUTOMATIC MODEL UPDATE LOGIC ---
def update_recommendation_model():
    """
    Builds the global item similarity model based ONLY on historical data from all customers.
    """
    print("SCHEDULER: Starting recommendation model build from historical data...")
    try:
        # 💡 CHANGED: Read ONLY from historical_events
        events = list(db.historical_events.find({"action": {"$in": ["Seen", "Order"]}}))

        if not events:
            print("SCHEDULER: No historical events found to build model. Skipping.")
            return

        event_data = []
        for event in events:
            if event.get('detail') and event['detail'].get('order_number'):
                try:
                    event_data.append({
                        'user_id': event.get('user_id'),
                        'action': event.get('action'),
                        'product_id': int(event['detail']['order_number'])
                    })
                except (ValueError, TypeError): continue
        
        df = pd.DataFrame(event_data)
        if df.empty: return

        df['interaction_strength'] = df['action'].apply(lambda x: 2.0 if x.lower() == 'order' else 1.0)
        interaction_matrix = df.pivot_table(index='user_id', columns='product_id', values='interaction_strength').fillna(0)
        
        if interaction_matrix.empty: return
            
        sparse_matrix = csr_matrix(interaction_matrix.values)
        item_similarity = cosine_similarity(sparse_matrix.T)
        item_similarity_df = pd.DataFrame(item_similarity, index=interaction_matrix.columns, columns=interaction_matrix.columns)
        
        with open('recommendation_engine/item_similarity.pkl', 'wb') as f: pickle.dump(item_similarity_df, f)

        recommendation_engine.collaborative_filter.load_matrix()
        print("SCHEDULER: Global recommendation model updated and reloaded successfully.")

    except Exception as e:
        print(f"SCHEDULER: An error occurred during model update: {e}")


# --- SCHEDULER CONFIGURATION ---
scheduler = BackgroundScheduler()
# The model only needs to be rebuilt periodically, not constantly
scheduler.add_job(func=update_recommendation_model, trigger="interval", hours=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


# --- API ROUTES ---
@app.route('/api/feed', methods=['GET'])
def get_user_feed_separated():
    try:
        recommendations = recommendation_engine.get_recommendations_separated()
        def get_product_details(pids):
            if not pids: return []
            product_details = list(db.products.find({"product_id": {"$in": pids}}, {'_id': 0}))
            product_map = {p['product_id']: p for p in product_details}
            return [product_map.get(pid) for pid in pids if pid in product_map]

        return jsonify({
            "for_you": get_product_details(recommendations['collaborative']),
            "based_on_watchlist": get_product_details(recommendations['self_feed']),
            "trending": get_product_details(recommendations['trending'])
        })
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/items', methods=['GET'])
def get_all_items_grouped():
    try:
        products_from_db = list(db.products.find({}, {'_id': 0}))
        grouped_products = defaultdict(list)
        for product in products_from_db:
            category = product.get('category', 'Uncategorized')
            formatted_product = { 'order_number': product.get('product_id', 0), 'product': product.get('product_name', 'No Name'), 'brand': product.get('brand', 'No Brand') }
            grouped_products[category].append(formatted_product)
        return jsonify(grouped_products)
    except Exception as e: return jsonify({"error": str(e)}), 500

# 💡 Both logging functions now correctly write ONLY to live_events
@app.route('/api/event', methods=['POST'])
def log_event():
    data = request.json
    if not all(k in data for k in ['action', 'product_id']): return jsonify({"error": "Missing required fields"}), 400
    product_id = int(data['product_id'])
    product_details = db.products.find_one({"product_id": product_id}, {'_id': 0})
    if not product_details: return jsonify({"error": "Product not found"}), 404
    event = { "action": data['action'].capitalize(), "detail": { "category": product_details.get('category'), "order_number": str(product_id), "product": product_details.get('product_name'), "brand": product_details.get('brand') }, "clientTimestamp": datetime.now(UTC).isoformat().replace('+00:00', 'Z'), "serverTimestamp": datetime.now(UTC) }
    db.live_events.insert_one(event)
    return jsonify({"status": "success"}), 201

@app.route('/api/log', methods=['POST'])
def log_action():
    data = request.json
    if not all(k in data for k in ['action', 'detail', 'clientTimestamp']): return jsonify({"error": "Missing required fields"}), 400
    event = { "action": data['action'], "detail": data['detail'], "clientTimestamp": data['clientTimestamp'], "serverTimestamp": datetime.now(UTC) }
    db.live_events.insert_one(event)
    return jsonify({"status": "success"}), 201

# --- FRONTEND SERVING ROUTES ---
@app.route('/')
def serve_index(): return send_from_directory(app.static_folder, 'index.html')
@app.route('/<path:path>')
def serve_static_files(path): return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    update_recommendation_model()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)