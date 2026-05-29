import os
from flask import Flask, jsonify, request
from flask_session import Session
from backend.config import Config
from backend.models import db, User
from backend.auth import auth_bp
from backend.admin import admin_bp
from backend.company import company_bp
from backend.student import student_bp

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
    app.register_blueprint(student_bp, url_prefix='/api/student')
    
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
    @app.route('/api/tasks/<task_id>', methods=['GET'])
    def get_task_status(task_id):
        from backend.tasks import celery_app
        res = celery_app.AsyncResult(task_id)
        response_data = {
            "status": "success",
            "task_id": task_id,
            "state": res.state,
            "result": res.result if res.state == 'SUCCESS' else None
        }
        if res.state == 'FAILURE':
            response_data["error"] = str(res.result)
        return jsonify(response_data)
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
