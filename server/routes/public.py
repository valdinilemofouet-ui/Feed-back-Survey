from flask import Blueprint, request, jsonify, current_app
from bson.objectid import ObjectId
import datetime
import jwt  # <--- Import nécessaire pour décoder le token manuellement

public_bp = Blueprint('public', __name__)

def get_db():
    from app import mongo
    return mongo.db

@public_bp.route('/surveys/<survey_id>', methods=['GET'])
def get_public_survey(survey_id):
    """
    Allows anyone (unauthenticated) to fetch survey questions.
    """
    if not ObjectId.is_valid(survey_id):
        return jsonify({"error": "Invalid Survey ID"}), 400
    
    db = get_db()
    survey = db.surveys.find_one({'_id': ObjectId(survey_id)})
    
    if not survey:
        return jsonify({"error": "Survey not found"}), 404
    
    if not survey.get('is_active', True):
        return jsonify({"error": "This survey is closed"}), 403
    
    public_data = {
        "_id": str(survey['_id']),
        "title": survey.get('title'),
        "description": survey.get('description'),
        "questions": survey.get('questions', []),
        "created_by": str(survey.get('created_by')) 
    }
    
    return jsonify(public_data), 200


@public_bp.route('/surveys/<survey_id>/respond', methods=['POST'])
def submit_response(survey_id):
    """
    Saves the response. Prevents the creator from submitting if logged in.
    """
    if not ObjectId.is_valid(survey_id):
        return jsonify({"error": "Invalid ID"}), 400
        
    data = request.json
    answers = data.get('answers')

    if not answers:
        return jsonify({"error": "No answers provided"}), 400

    db = get_db()
    survey = db.surveys.find_one({'_id': ObjectId(survey_id)})
    
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    # --- BLOCK: VÉRIFICATION DU CRÉATEUR ---
    # On regarde si un token est présent dans les headers
    auth_header = request.headers.get('Authorization')
    
    if auth_header:
        try:
            # Format standard: "Bearer <token>"
            token = auth_header.split(" ")[1]
            
            # Décoder le token avec la clé secrète de l'app
            payload = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'], 
                algorithms=["HS256"]
            )
            
            # Récupérer l'ID utilisateur du token (souvent 'sub' ou 'user_id')
            # Adapte 'sub' selon ce que tu as mis dans ton auth.py lors de la création du token
            current_user_id = payload.get('sub') or payload.get('user_id')
            
            # Comparaison : ID du token vs ID du créateur du sondage
            if str(current_user_id) == str(survey.get('created_by')):
                return jsonify({
                    "error": "You cannot submit a response to your own survey."
                }), 403
                
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, IndexError):
            # Si le token est invalide ou expiré, on ignore et on traite comme anonyme
            # ou on peut renvoyer une erreur si on veut être strict.
            pass
    # ---------------------------------------

    response_doc = {
        'survey_id': ObjectId(survey_id),
        'answers': answers,
        'submitted_at': datetime.datetime.utcnow(),
        'ip_address': request.remote_addr 
    }

    db.responses.insert_one(response_doc)

    db.surveys.update_one(
        {'_id': ObjectId(survey_id)},
        {'$inc': {'response_count': 1}}
    )

    return jsonify({"message": "Response recorded successfully"}), 201