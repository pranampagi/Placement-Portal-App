import os
from flask import Blueprint, jsonify, request, session, current_app
from werkzeug.utils import secure_filename
from backend.models import db, StudentProfile
from backend.auth import login_required, roles_required

student_bp = Blueprint('student', __name__)

@student_bp.route('/profile', methods=['GET'])
@login_required
@roles_required('student')
def get_profile():
    student = StudentProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    return jsonify({
        "status": "success",
        "student": student.to_dict()
    })

@student_bp.route('/profile', methods=['PUT'])
@login_required
@roles_required('student')
def update_profile():
    student = StudentProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    data = request.get_json() or {}
    
    name = data.get('name')
    email = data.get('email')
    branch = data.get('branch')
    cgpa = data.get('cgpa')
    graduation_year = data.get('graduation_year')
    
    if not all([name, email, branch, cgpa is not None, graduation_year]):
        return jsonify({"status": "error", "message": "Missing required fields for profile update."}), 400
        
    try:
        cgpa_val = float(cgpa)
        year_val = int(graduation_year)
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid format for CGPA or Graduation Year."}), 400
        
    try:
        student.name = name
        student.email = email
        student.branch = branch
        student.cgpa = cgpa_val
        student.graduation_year = year_val
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Profile updated successfully.",
            "student": student.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Failed to update profile: {str(e)}"}), 500

@student_bp.route('/upload-resume', methods=['POST'])
@login_required
@roles_required('student')
def upload_resume():
    student = StudentProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part in the request."}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file."}), 400
        
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"status": "error", "message": "Invalid file format. Only PDF files are allowed."}), 400
        
    try:
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate clean, standard filename for the candidate's resume
        filename = f"resume_student_{student.id}.pdf"
        file_path = os.path.join(upload_dir, filename)
        
        file.save(file_path)
        
        student.resume_filename = filename
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Resume uploaded successfully.",
            "resume_filename": filename
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Failed to save resume: {str(e)}"}), 500
