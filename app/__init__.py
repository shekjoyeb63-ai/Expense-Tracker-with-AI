from flask import Flask, g, jsonify
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flasgger import Swagger
from datetime import timedelta
from dotenv import load_dotenv
from celery import Celery
from app.services.celery_worker import make_celery
import os

load_dotenv()


jwt = JWTManager()
bc = Bcrypt()
celery = Celery()
limiter = Limiter(get_remote_address, default_limits=["200 per day", "50 per hour"])

def create_app():
    app = Flask(__name__)

    
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["SWAGGER"] = {
        "title": "Expense Tracker API",
        "uiversion": 3,
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Enter: Bearer <your_token>"
            }
        }
    }

    
    jwt.init_app(app)
    bc.init_app(app)
    limiter.init_app(app)
    global celery
    celery = make_celery(app)
    CORS(app)
    Swagger(app)

    
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"message": "Bad request — check your input"}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"message": "Unauthorized — please login"}), 401

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"message": "Route not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"message": "Method not allowed"}), 405

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"message": "Invalid input data"}), 422

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"message": "Internal server error"}), 500
    
    @app.teardown_appcontext
    def close_db(exception=None):
        db = g.pop("db", None)
        if db is not None:
            if exception:
                db.rollback()
            db.close()
    from app.routes.auth import auth_bp
    from app.routes.expenses import expenses_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(expenses_bp)

    return app