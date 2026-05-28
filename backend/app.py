import os
from flask import Flask, jsonify, request
from flask_session import Session
from backend.config import Config
from backend.models import db, User
from backend.auth import auth_bp
from backend.admin import admin_bp
from backend.company import company_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize Session
    Session(app)
    
    # Initialize DB
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(company_bp, url_prefix='/api/company')
    
    # CORS Manual Setup (with credentials support for cookie-based session tracking)
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Cookie'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        return response

    @app.route('/<path:path>', methods=['OPTIONS'])
    def options_handler(path):
        return '', 200
        
    @app.route('/ping', methods=['GET'])
    def ping():
        return jsonify({"message": "Placement Portal API is running!", "status": "success"})
        
    @app.route('/test-db', methods=['GET'])
    def test_db():
        try:
            admin_count = User.query.filter_by(role='admin').count()
            return jsonify({"status": "success", "admin_count": admin_count})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
