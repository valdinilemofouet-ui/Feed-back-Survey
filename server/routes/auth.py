from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from validation import UserRegisterSchema, UserLoginSchema, ValidationError

auth_bp = Blueprint('auth', __name__)

def get_db():
    from app import mongo
    return mongo.db

# --- Helper Decorator ---
def anonymous_required(f):
    """
    Decorator to ensure the user is NOT logged in.
    If a valid token is found, return an error.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if token:
            try:
                # Attempt to decode the token
                jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
                
                # If decoding is successful, the user is already authenticated
                return jsonify({
                    "error": "You are already logged in.",
                    "message": "Please logout to access this resource."
                }), 403
                
            except jwt.ExpiredSignatureError:
                # Token expired, allow them to proceed (to login again)
                pass
            except jwt.InvalidTokenError:
                # Token invalid, allow them to proceed
                pass
                
        return f(*args, **kwargs)
    return decorated

# --- Routes ---

@auth_bp.route('/register', methods=['POST'])
@anonymous_required  # <--- Prevents registered users from creating new accounts while logged in
def register():
    try:
        # Automatic validation via Pydantic
        data = UserRegisterSchema(**request.json)
    except ValidationError as e:
        return jsonify({"error": "Invalid data", "details": e.errors()}), 400

    db = get_db()
    if db.users.find_one({'email': data.email}):
        return jsonify({"error": "Email already registered"}), 409

    hashed_pw = generate_password_hash(data.password)
    
    user_doc = {
        'name': data.name,
        'email': data.email,
        'password': hashed_pw,
        'created_at': datetime.datetime.utcnow(),
        'role': 'user'
    }
    
    db.users.insert_one(user_doc)
    return jsonify({"message": "Account created successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
@anonymous_required  # <--- Prevents logged-in users from logging in again
def login():
    try:
        data = UserLoginSchema(**request.json)
    except ValidationError:
        return jsonify({"error": "Invalid format"}), 400

    db = get_db()
    user = db.users.find_one({'email': data.email})

    if not user or not check_password_hash(user['password'], data.password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Create JWT Token
    token_payload = {
        'user_id': str(user['_id']),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        "token": token,
        "user": {"name": user['name'], "email": user['email']}
    }), 200