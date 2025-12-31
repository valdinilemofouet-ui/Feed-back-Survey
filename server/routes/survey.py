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

# --- Security Middleware (Decorator) ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Expecting header: Authorization: Bearer <TOKEN>
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Missing token'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user_id = data['user_id'] # Store ID in global context 'g'
        except:
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        return f(*args, **kwargs)
    return decorated

@survey_bp.route('/', methods=['POST'])
@token_required
def create_survey():
    try:
        # Strict validation of survey structure
        payload = SurveyCreateSchema(**request.json)
    except ValidationError as e:
        return jsonify({"error": "Invalid survey format", "details": e.errors()}), 400

    survey_doc = payload.dict()
    survey_doc.update({
        'created_by': g.user_id,
        'created_at': datetime.datetime.utcnow(),
        'is_active': True,
        'response_count': 0
    })

    db = get_db()
    res = db.surveys.insert_one(survey_doc)
    return jsonify({"message": "Survey created", "id": str(res.inserted_id)}), 201

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
        return jsonify({"error": "Invalid ID"}), 400
        
    db = get_db()
    survey = db.surveys.find_one({'_id': ObjectId(survey_id)})
    
    if not survey: return jsonify({"error": "Survey not found"}), 404
    if survey['created_by'] != g.user_id:
        return jsonify({"error": "Access denied"}), 403
        
    responses = list(db.responses.find({'survey_id': ObjectId(survey_id)}))
    
    # --- STATISTICS CALCULATION ---
    stats = []

    for question in survey.get('questions', []):
        q_id = str(question.get('id'))
        q_type = question.get('type')
        
        question_stat = {
            "id": q_id,
            "text": question.get('text'),
            "type": q_type,
            "total_answers": 0,
            "data": {} 
        }

        # Extract specific answers for this question
        raw_answers = [
            r.get('answers', {}).get(q_id) 
            for r in responses 
            if r.get('answers', {}).get(q_id) is not None
        ]
        
        question_stat['total_answers'] = len(raw_answers)

        # A: Radio / Select
        if q_type in ['radio', 'select']:
            counts = {opt: 0 for opt in question.get('options', [])}
            for ans in raw_answers:
                if ans in counts:
                    counts[ans] += 1
                else:
                    counts["Other"] = counts.get("Other", 0) + 1
            question_stat['data'] = counts

        # B: Checkbox
        elif q_type == 'checkbox':
            counts = {opt: 0 for opt in question.get('options', [])}
            for ans_list in raw_answers:
                if isinstance(ans_list, list):
                    for item in ans_list:
                        if item in counts:
                            counts[item] += 1
            question_stat['data'] = counts

        # C: Rating
        elif q_type == 'rating':
            numeric_answers = []
            distribution = {}
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
                    "average": round(average, 2),
                    "min": min(numeric_answers),
                    "max": max(numeric_answers),
                    "distribution": distribution
                }
            else:
                question_stat['data'] = {"average": 0, "distribution": {}}

        # D: Text
        elif q_type == 'text':
            question_stat['data'] = {
                "recent_answers": raw_answers[-5:] 
            }

        stats.append(question_stat)

    survey['_id'] = str(survey['_id'])
    survey['created_by'] = str(survey['created_by'])

    return jsonify({
        "survey_info": survey,
        "results": stats,
        "total_respondents": len(responses)
    }), 200

# ---------------------------------------------------------
# NEW ROUTES ADDED BELOW (DELETE & TOGGLE STATUS)
# ---------------------------------------------------------

@survey_bp.route('/<survey_id>', methods=['DELETE'])
@token_required
def delete_survey(survey_id):
    if not ObjectId.is_valid(survey_id):
        return jsonify({"error": "Invalid ID"}), 400

    db = get_db()
    
    # 1. Check if survey exists
    survey = db.surveys.find_one({'_id': ObjectId(survey_id)})

    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    # 2. Check ownership (Security)
    if survey['created_by'] != g.user_id:
        return jsonify({"error": "Unauthorized action"}), 403

    # 3. Delete the survey
    db.surveys.delete_one({'_id': ObjectId(survey_id)})
    
    # 4. Clean up associated responses (Optional but recommended)
    db.responses.delete_many({'survey_id': ObjectId(survey_id)})

    return jsonify({"message": "Survey deleted successfully"}), 200

@survey_bp.route('/<survey_id>/status', methods=['PATCH'])
@token_required
def toggle_survey_status(survey_id):
    if not ObjectId.is_valid(survey_id):
        return jsonify({"error": "Invalid ID"}), 400

    db = get_db()
    
    # 1. Check if survey exists
    survey = db.surveys.find_one({'_id': ObjectId(survey_id)})

    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    # 2. Check ownership
    if survey['created_by'] != g.user_id:
        return jsonify({"error": "Unauthorized action"}), 403

    # 3. Toggle logic
    current_status = survey.get('is_active', True)
    new_status = not current_status

    db.surveys.update_one(
        {'_id': ObjectId(survey_id)},
        {'$set': {'is_active': new_status}}
    )

    return jsonify({
        "message": "Status updated", 
        "is_active": new_status
    }), 200