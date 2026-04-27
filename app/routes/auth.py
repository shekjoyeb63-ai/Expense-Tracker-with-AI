from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import (
    jwt_required, create_access_token, get_jwt, get_jwt_identity
)
from app.models.tables import sesssionLocal, User
from app import bc, limiter, jwt
from app.services.redis_client import redis_client
from app.services.email_service import generate_otp, store_otp, verify_otp, send_otp_email
from app.services.tasks import send_otp_email_task, send_welcome_email_task

auth_bp = Blueprint("auth", __name__)


def get_db():
    if "db" not in g:
        g.db = sesssionLocal()
    return g.db


@jwt.token_in_blocklist_loader
def check_blacklisted_token(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return redis_client.get(f"blacklist:{jti}") is not None


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    """
    Register a new user
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: john@gmail.com
            password:
              type: string
              example: "mypassword123"
    responses:
      201:
        description: Registered successfully, OTP sent
      409:
        description: User already exists
    """
    if not request.json:
        return jsonify({"message": "Request body must be JSON"}), 400

    email = request.json.get("email")
    password = request.json.get("password")

    if not email or not password:
        return jsonify({"message": "Missing credentials"}), 409

    try:
        db = get_db()
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({"message": "User already exists"}), 409

        hashed = bc.generate_password_hash(password).decode("utf-8")
        user = User(email=email, password=hashed, is_verified=0)
        db.add(user)
        db.commit()

        otp = generate_otp()
        store_otp(email, otp)
        send_otp_email_task.delay(email, otp)

        return jsonify({
            "message": "Registered successfully. Check your email for OTP."
        }), 201

    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500
  

@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp_route():
    """
    Verify OTP sent to email
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: john@gmail.com
            otp:
              type: string
              example: "123456"
    responses:
      200:
        description: Email verified successfully
      400:
        description: Invalid or expired OTP
    """
    if not request.json:
        return jsonify({"message": "Request body must be JSON"}), 400

    email = request.json.get("email")
    otp = request.json.get("otp")

    if not email or not otp:
        return jsonify({"message": "Email and OTP are required"}), 400

    try:
        
        if verify_otp(email, otp):
            
            db = get_db()
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.is_verified = 1
                send_welcome_email_task.delay(email)
                db.commit()
            return jsonify({"message": "Email verified successfully ✅"}), 200
        else:
            return jsonify({"message": "Invalid or expired OTP"}), 400

    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500



@auth_bp.route("/login", methods=["POST"])
@limiter.limit("3 per minute")
def login():
    """
    Login and get JWT token
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: john@gmail.com
            password:
              type: string
              example: "mypassword123"
    responses:
      200:
        description: Returns JWT token
      401:
        description: Invalid credentials
    """
    if not request.json:
        return jsonify({"message": "Request body must be JSON"}), 400

    try:
        email = request.json.get("email")
        password = request.json.get("password")
        db = get_db()

        user = db.query(User).filter(User.email == email).first()
        if not user or not bc.check_password_hash(user.password, password):
            return jsonify({"message": "Invalid credentials"}), 401
        if user.is_verified == 0:
          return jsonify({"message": "Please verify your email first"}), 403
        token = create_access_token(identity=str(user.id))
        return jsonify({"token": token}), 200

    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500



@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Logout user and blacklist token
    ---
    tags:
      - Auth
    security:
      - BearerAuth: []
    responses:
      200:
        description: Logged out successfully
    """
    try:
        jti = get_jwt()["jti"]
        redis_client.setex(f"blacklist:{jti}", 3600, "blacklisted")
        return jsonify({"message": "Logged out successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500