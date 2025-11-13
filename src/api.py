from flask import Flask, request, jsonify, render_template
from model import PersonalizedFeed

app = Flask(__name__, template_folder='../templates')

# --- MODEL INITIALIZATION ---
DATA_FILE = 'data/Ecommerce_Consumer_Behavior_Analysis_Data.csv'
WEIGHTS_FILE = 'data/user_weight_profiles.json'
model = PersonalizedFeed(data_filepath=DATA_FILE, weights_filepath=WEIGHTS_FILE)

# --- API ENDPOINTS ---

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/recommendations/<int:user_id>', methods=['GET'])
def get_recommendations(user_id):
    recent_actions = {'search': ["Men's T-Shirt"], 'seen': ["Women's Jeans", "Sneakers"]}
    business_items = {'promoted': ["Smartwatch"], 'trending': ["Backpack"]}
    try:
        recommendations = model.get_feed_recommendations(user_id, recent_actions, business_items)
        return jsonify(recommendations)
    except KeyError:
        return jsonify({"error": f"User ID {user_id} not found in historical data."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    feedback_data = request.get_json()
    user_id = feedback_data.get('user_id')
    dominant_signal = feedback_data.get('dominant_signal')
    if not user_id or not dominant_signal:
        return jsonify({"error": "Missing 'user_id' or 'dominant_signal' in request."}), 400
    try:
        updated_weights = model.update_user_weights(user_id, dominant_signal)
        return jsonify({"message": f"Successfully updated weights for user {user_id}", "new_weights": updated_weights})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)