import os
from datetime import datetime
from flask import Blueprint, jsonify, request, session, current_app
from werkzeug.utils import secure_filename
from backend.models import db, StudentProfile, PlacementDrive, Application
from backend.auth import login_required, roles_required
from backend.caching import cache_response, evict_cache_by_pattern

student_bp = Blueprint('student', __name__)

def evict_student_related_caches():
    evict_cache_by_pattern('admin:dashboard:*')
    evict_cache_by_pattern('company:*')
    evict_cache_by_pattern('student:*')

@student_bp.route('/profile', methods=['GET'])
@login_required
@roles_required('student')
@cache_response('student:profile', timeout=600, user_specific=True)
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
        evict_student_related_caches()
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
        evict_student_related_caches()
        return jsonify({
            "status": "success",
            "message": "Resume uploaded successfully.",
            "resume_filename": filename
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Failed to save resume: {str(e)}"}), 500

@student_bp.route('/eligible-drives', methods=['GET'])
@login_required
@roles_required('student')
@cache_response('student:eligible_drives', timeout=600, user_specific=True)
def get_eligible_drives():
    student = StudentProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    
    # Get all approved placement drives
    drives = PlacementDrive.query.filter_by(status='approved').all()
    
    eligible_drives = []
    
    for d in drives:
        # Check graduation year match
        if d.eligibility_year != student.graduation_year:
            continue
            
        # Check CGPA constraint
        if student.cgpa < d.eligibility_cgpa:
            continue
            
        # Check branch constraint
        if d.eligibility_branch.lower() != 'all':
            allowed_branches = [b.strip().lower() for b in d.eligibility_branch.split(',')]
            if student.branch.lower() not in allowed_branches:
                continue
                
        # Check if student has already applied
        app = Application.query.filter_by(student_id=student.id, drive_id=d.id).first()
        
        d_dict = d.to_dict()
        d_dict['applied'] = app is not None
        d_dict['application_status'] = app.status if app else None
        d_dict['application_remark'] = app.remark if app else None
        
        eligible_drives.append(d_dict)
        
    return jsonify({
        "status": "success",
        "drives": eligible_drives
    })

@student_bp.route('/apply', methods=['POST'])
@login_required
@roles_required('student')
def apply_to_drive():
    student = StudentProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    
    # Must have a resume uploaded
    if not student.resume_filename:
        return jsonify({
            "status": "error",
            "message": "Please upload your resume in the 'Edit Profile' section before applying."
        }), 400
        
    data = request.get_json() or {}
    drive_id = data.get('drive_id')
    
    if not drive_id:
        return jsonify({"status": "error", "message": "Missing drive_id."}), 400
        
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    # Check if drive is approved
    if drive.status != 'approved':
        return jsonify({"status": "error", "message": "This placement drive is not active/approved."}), 400
        
    # Check if deadline has passed
    if drive.deadline < datetime.utcnow():
        return jsonify({"status": "error", "message": "The application deadline for this drive has passed."}), 400
        
    # Check if already applied
    existing_app = Application.query.filter_by(student_id=student.id, drive_id=drive.id).first()
    if existing_app:
        return jsonify({"status": "error", "message": "You have already applied to this placement drive."}), 400
        
    # Verify academic eligibility
    if student.cgpa < drive.eligibility_cgpa:
        return jsonify({"status": "error", "message": f"Your CGPA ({student.cgpa}) does not meet the minimum requirement ({drive.eligibility_cgpa})."}), 400
        
    if student.graduation_year != drive.eligibility_year:
        return jsonify({"status": "error", "message": f"Your graduation year ({student.graduation_year}) does not match the eligibility year ({drive.eligibility_year})."}), 400
        
    if drive.eligibility_branch.lower() != 'all':
        allowed_branches = [b.strip().lower() for b in drive.eligibility_branch.split(',')]
        if student.branch.lower() not in allowed_branches:
            return jsonify({"status": "error", "message": f"Your branch ({student.branch}) is not eligible for this drive."}), 400
            
    try:
        app = Application(
            student_id=student.id,
            drive_id=drive.id,
            status='applied'
        )
        db.session.add(app)
        db.session.commit()
        evict_student_related_caches()
        return jsonify({
            "status": "success",
            "message": "Successfully applied to the placement drive!",
            "application": app.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Failed to submit application: {str(e)}"}), 500

@student_bp.route('/applications', methods=['GET'])
@login_required
@roles_required('student')
@cache_response('student:applications', timeout=600, user_specific=True)
def get_applications():
    student = StudentProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    apps = Application.query.filter_by(student_id=student.id).order_by(Application.application_date.desc()).all()
    return jsonify({
        "status": "success",
        "applications": [a.to_dict() for a in apps]
    })

# Export Student Applications to CSV
@student_bp.route('/export-applications', methods=['POST'])
@login_required
@roles_required('student')
def export_applications():
    from backend.tasks import export_applications_csv
    student = StudentProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    task = export_applications_csv.delay(student.id, 'student')
    return jsonify({
        "status": "success",
        "task_id": task.id,
        "message": "CSV export has been triggered in the background."
    })

# Helper function to format keywords nicely
def format_keyword(kw):
    mapping = {
        "c++": "C++",
        "c#": "C#",
        "sql": "SQL",
        "html": "HTML",
        "css": "CSS",
        "aws": "AWS",
        "rest api": "REST API",
        "ci/cd": "CI/CD",
        "js": "JavaScript",
        "javascript": "JavaScript",
        "mongodb": "MongoDB",
        "postgresql": "PostgreSQL",
        "graphql": "GraphQL"
    }
    return mapping.get(kw.lower(), kw.title())

# ATS Resume Matcher Endpoint
@student_bp.route('/drives/<int:drive_id>/ats-match', methods=['POST'])
@login_required
@roles_required('student')
def ats_match(drive_id):
    student = StudentProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    
    if not student.resume_filename:
        return jsonify({
            "status": "error",
            "message": "No resume found. Please upload a PDF resume in 'Edit Profile' first."
        }), 400
        
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    # Predefined keyword pool
    KEYWORD_POOL = [
        "python", "vue", "javascript", "sql", "git", "docker", "flask", "java", "react", 
        "c++", "c#", "html", "css", "django", "node", "mongodb", "postgresql", "aws", 
        "kubernetes", "typescript", "machine learning", "data science", "angular", "spring", 
        "rust", "go", "php", "ruby", "swift", "kotlin", "linux", "devops", "ci/cd", 
        "rest api", "graphql"
    ]
    
    # Scan job description and title for keywords
    job_text = f"{drive.job_title} {drive.job_description}".lower()
    keywords = [kw for kw in KEYWORD_POOL if kw in job_text]
    
    # Fallback if no keywords found in job description
    if not keywords:
        keywords = ["python", "javascript", "sql", "git", "html", "css"]
        
    # Read PDF binary content
    upload_dir = current_app.config['UPLOAD_FOLDER']
    pdf_path = os.path.join(upload_dir, student.resume_filename)
    
    if not os.path.exists(pdf_path):
        return jsonify({
            "status": "error",
            "message": "Resume file does not exist on disk. Please re-upload your resume."
        }), 404
        
    try:
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read().lower()
            
        matched_skills = []
        missing_skills = []
        
        for kw in keywords:
            # Look for byte sequence of keyword in the pdf binary content
            if kw.encode('utf-8') in pdf_bytes:
                matched_skills.append(format_keyword(kw))
            else:
                missing_skills.append(format_keyword(kw))
                
        # Handle case where keywords is empty just in case
        if keywords:
            score = int((len(matched_skills) / len(keywords)) * 100)
        else:
            score = 0
            
        return jsonify({
            "status": "success",
            "score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to parse resume: {str(e)}"
        }), 500

