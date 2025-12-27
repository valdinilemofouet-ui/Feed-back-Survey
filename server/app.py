from flask import Flask, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Sécurité CORS : On autorise seulement le frontend React (port 3000)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

mongo = PyMongo(app)

# --- Gestion Globale des Erreurs ---
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Requête invalide", "details": str(e.description)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Ressource introuvable"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erreur interne du serveur"}), 500

# --- Importation des Routes (Blueprints) ---
from routes.auth import auth_bp
from routes.survey import survey_bp
from routes.public import public_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(survey_bp, url_prefix='/api/surveys')
app.register_blueprint(public_bp, url_prefix='/api/public')

if __name__ == '__main__':
    app.run(debug=True, port=5000)