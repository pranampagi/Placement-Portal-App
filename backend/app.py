import os
from flask import Flask, jsonify
from flask_session import Session
from backend.config import Config
from backend.models import db, User
from backend.auth import auth_bp

def create_app():
    # Base dir is /backend, templates and static are in /frontend
    base_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.dirname(base_dir)
    template_dir = os.path.join(project_root, 'frontend', 'templates')
    static_dir = os.path.join(project_root, 'frontend', 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config)
    
    # Initialize Session
    Session(app)
    
    # Initialize DB
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    @app.route('/ping', methods=['GET'])
    def ping():
        return jsonify({"message": "Placement Portal backend is running!", "status": "success"})
        
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
