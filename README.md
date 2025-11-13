# Personalized Recommendation Feed API

This project provides a complete backend system for generating personalized product feeds for users based on a hybrid recommendation model.

## Features

- **Item-Based Collaborative Filtering**: Recommends products based on what similar users like.
- **Deep Personalization**: Analyzes individual user actions (seen, order, cancel) with time-decay for relevance.
- **Trending Items**: Boosts products that are currently popular across the platform.
- **Dynamic Weights**: A framework for adapting the recommendation blend to user behavior.
- **Flask API**: Simple and clean endpoints for fetching feeds and logging user events.

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- MongoDB instance running.

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd personalized-feed-project
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the database:**
    - Open `config.py` and ensure `MONGO_URI` points to your MongoDB instance.

### 3. Data Loading

Before running the application, you need to populate the database and pre-compute the similarity model.

1.  **Place your data:**
    - Put `Online-eCommerce.csv` inside the `data/` directory.

2.  **Run the loading script:**
    ```bash
    python scripts/load_data.py
    ```

3.  **Run the model computation script:**
    (This can take a few minutes depending on your data size)
    ```bash
    python scripts/compute_similarity_matrix.py
    ```
    *You should re-run this script periodically (e.g., as a nightly cron job) to update your recommendations.*

### 4. Running the API Server

```bash
python app.py
```
The server will start on `http://localhost:5000`.

## API Endpoints

- **Get User Feed:** `GET /api/feed/<user_id>`
  - **Example:** `curl http://localhost:5000/api/feed/adhir_samal`

- **Log a User Event:** `POST /api/event`
  - **Example:**
    ```bash
    curl -X POST -H "Content-Type: application/json" \
         -d '{"user_id": "adhir_samal", "action": "seen", "product_id": 139384}' \
         http://localhost:5000/api/event
    ```