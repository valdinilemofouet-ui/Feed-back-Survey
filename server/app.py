from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_cors import CORS
import os
from dotenv import load_dotenv
from bson.objectid import ObjectId

# 1. Load environment variables (.env)
load_dotenv()

# 2. Initialize the application
app = Flask(__name__)
CORS(app) # Allow React (Frontend) to access this Server

# 3. Database Configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

# Connection verification (Optional, just for testing startup)
try:
    mongo.db.command('ping')
    print("SUCCESS: Connected to MongoDB Atlas!")
except Exception as e:
    print(f"ERROR: Could not connect to MongoDB: {e}")

# --- ROUTES (API Endpoints) ---

@app.route('/', methods=['GET'])
def home():
    """Simple health check to see if server is running"""
    return jsonify({"message": "Flask Survey Builder API is online 🚀"})

# Example: Create a survey (Quick test to verify DB write access)
@app.route('/api/test-create', methods=['POST'])
def test_create_survey():
    data = request.json
    
    # Data structure (Implicit Schema)
    # We create a dictionary that represents our survey
    survey_doc = {
        "title": data.get("title"),
        "questions": data.get("questions", []), # Empty list by default
        "active": True
    }
    
    # Insert into the "forms" collection in MongoDB
    result = mongo.db.forms.insert_one(survey_doc)
    
    # Return success message with the new ID
    return jsonify({
        "message": "Survey created successfully!",
        "id": str(result.inserted_id) # Convert ObjectId to string for JSON compatibility
    }), 201

# --- RUN SERVER ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)