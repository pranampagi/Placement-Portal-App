import os
from flask import Flask, jsonify
from backend.config import Config

def create_app():
    # Base dir is /backend, templates and static are in /frontend
    base_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.dirname(base_dir)
    template_dir = os.path.join(project_root, 'frontend', 'templates')
    static_dir = os.path.join(project_root, 'frontend', 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config)
    
    @app.route('/ping', methods=['GET'])
    def ping():
        return jsonify({"message": "Placement Portal backend is running!", "status": "success"})
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
