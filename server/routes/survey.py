from flask import Blueprint, request, jsonify, g, current_app
from functools import wraps
import jwt
from bson.objectid import ObjectId
import datetime
from validation import SurveyCreateSchema, ValidationError

survey_bp = Blueprint('survey', __name__)

def get_db():
    from app import mongo
    return mongo.db

# --- Middleware de Sécurité (Décorateur) ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # On attend le header : Authorization: Bearer <TOKEN>
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Token manquant'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user_id = data['user_id'] # On stocke l'ID dans le contexte global 'g'
        except:
            return jsonify({'error': 'Token invalide ou expiré'}), 401
            
        return f(*args, **kwargs)
    return decorated

@survey_bp.route('/', methods=['POST'])
@token_required
def create_survey():
    try:
        # Validation stricte des questions
        payload = SurveyCreateSchema(**request.json)
    except ValidationError as e:
        return jsonify({"error": "Format du sondage invalide", "details": e.errors()}), 400

    survey_doc = payload.dict()
    survey_doc.update({
        'created_by': g.user_id,
        'created_at': datetime.datetime.utcnow(),
        'is_active': True,
        'response_count': 0
    })

    db = get_db()
    res = db.surveys.insert_one(survey_doc)
    return jsonify({"message": "Sondage créé", "id": str(res.inserted_id)}), 201

@survey_bp.route('/', methods=['GET'])
@token_required
def get_my_surveys():
    db = get_db()
    cursor = db.surveys.find({'created_by': g.user_id}).sort("created_at", -1)
    
    surveys = []
    for s in cursor:
        s['_id'] = str(s['_id'])
        surveys.append(s)
    return jsonify(surveys), 200

@survey_bp.route('/<survey_id>/results', methods=['GET'])
@token_required
def get_results(survey_id):
    if not ObjectId.is_valid(survey_id):
        return jsonify({"error": "ID invalide"}), 400
        
    db = get_db()
    survey = db.surveys.find_one({'_id': ObjectId(survey_id)})
    
    if not survey: return jsonify({"error": "Introuvable"}), 404
    if survey['created_by'] != g.user_id:
        return jsonify({"error": "Accès interdit"}), 403
        
    responses = list(db.responses.find({'survey_id': ObjectId(survey_id)}))
    
    # 1. Préparation de la structure des résultats
    # On crée une liste qui respecte l'ordre des questions du sondage
    stats = []

    for question in survey.get('questions', []):
        q_id = str(question.get('id'))
        q_type = question.get('type')
        
        # Structure de base pour chaque question
        question_stat = {
            "id": q_id,
            "text": question.get('text'),
            "type": q_type,
            "total_answers": 0, # Combien de gens ont répondu à CETTE question
            "data": {} # Contiendra les comptes (ex: "Oui": 5) ou la moyenne
        }

        # On isole toutes les réponses données spécifiquement pour cette question
        # r.get('answers', {}) permet d'éviter un crash si 'answers' manque
        raw_answers = [
            r.get('answers', {}).get(q_id) 
            for r in responses 
            if r.get('answers', {}).get(q_id) is not None
        ]
        
        question_stat['total_answers'] = len(raw_answers)

        # --- LOGIQUE SELON LE TYPE DE QUESTION ---

        # CAS A : Choix Unique (Radio / Select)
        if q_type in ['radio', 'select']:
            # Initialiser les compteurs à 0 pour toutes les options définies
            counts = {opt: 0 for opt in question.get('options', [])}
            
            for ans in raw_answers:
                # On ne compte que si la réponse fait partie des options valides
                if ans in counts:
                    counts[ans] += 1
                else:
                    # Optionnel : gérer les valeurs "autres" ou inattendues
                    counts["Autre"] = counts.get("Autre", 0) + 1
            
            question_stat['data'] = counts

        # CAS B : Choix Multiples (Checkbox) - La réponse est une liste (ex: ["A", "C"])
        elif q_type == 'checkbox':
            counts = {opt: 0 for opt in question.get('options', [])}
            
            for ans_list in raw_answers:
                if isinstance(ans_list, list):
                    for item in ans_list:
                        if item in counts:
                            counts[item] += 1
            
            question_stat['data'] = counts

        # CAS C : Notation / Étoiles (Rating) - On veut la moyenne
        elif q_type == 'rating':
            # Convertir en entiers et filtrer les erreurs
            numeric_answers = []
            distribution = {} # Pour savoir combien de "5 étoiles", combien de "4", etc.
            
            for ans in raw_answers:
                try:
                    val = int(ans)
                    numeric_answers.append(val)
                    distribution[val] = distribution.get(val, 0) + 1
                except (ValueError, TypeError):
                    continue
            
            if numeric_answers:
                average = sum(numeric_answers) / len(numeric_answers)
                question_stat['data'] = {
                    "average": round(average, 2), # Arrondi à 2 décimales
                    "min": min(numeric_answers),
                    "max": max(numeric_answers),
                    "distribution": distribution
                }
            else:
                question_stat['data'] = {"average": 0, "distribution": {}}

        # CAS D : Texte libre
        elif q_type == 'text':
            # On renvoie juste les 5 dernières réponses pour aperçu (sinon c'est trop lourd)
            question_stat['data'] = {
                "recent_answers": raw_answers[-5:] # Les 5 derniers
            }

        stats.append(question_stat)

    # 2. Sérialisation finale
    # On transforme l'objet Survey pour qu'il soit propre au format JSON
    survey['_id'] = str(survey['_id'])
    survey['created_by'] = str(survey['created_by']) # Si besoin

    return jsonify({
        "survey_info": survey,
        "results": stats,
        "total_respondents": len(responses)
    }), 200