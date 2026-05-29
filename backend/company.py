from flask import Blueprint, jsonify, request, session
from datetime import datetime
from backend.models import db, User, CompanyProfile, PlacementDrive, Application
from backend.auth import login_required, roles_required
from backend.caching import cache_response, evict_cache_by_pattern

company_bp = Blueprint('company', __name__)

def evict_company_related_caches():
    evict_cache_by_pattern('admin:dashboard:*')
    evict_cache_by_pattern('company:*')
    evict_cache_by_pattern('student:*')

@company_bp.route('/profile', methods=['GET'])
@login_required
@roles_required('company')
def get_profile():
    company = CompanyProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    return jsonify({
        "status": "success",
        "company": company.to_dict()
    })

@company_bp.route('/drives', methods=['GET'])
@login_required
@roles_required('company')
@cache_response('company:drives', timeout=600, user_specific=True)
def get_company_drives():
    company = CompanyProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    
    upcoming_drives = []
    closed_drives = []
    
    for d in drives:
        d_dict = d.to_dict()
        # Count student applicants for this drive
        applicant_count = Application.query.filter_by(drive_id=d.id).count()
        d_dict['applicant_count'] = applicant_count
        
        # Split drives by active state or deadline
        if d.status == 'closed' or d.deadline < datetime.utcnow():
            closed_drives.append(d_dict)
        else:
            upcoming_drives.append(d_dict)
            
    return jsonify({
        "status": "success",
        "upcoming_drives": upcoming_drives,
        "closed_drives": closed_drives
    })

@company_bp.route('/drives', methods=['POST'])
@login_required
@roles_required('company')
def create_drive():
    company = CompanyProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    
    # Core constraint: Must be approved by Admin to create drives
    if company.approval_status != 'approved':
        return jsonify({
            "status": "error",
            "message": "Access denied. Your company account is pending approval by the Admin."
        }), 403
        
    data = request.get_json() or {}
    job_title = data.get('job_title')
    job_description = data.get('job_description')
    eligibility_branch = data.get('eligibility_branch', 'All')
    eligibility_cgpa = data.get('eligibility_cgpa')
    eligibility_year = data.get('eligibility_year')
    salary = data.get('salary')
    location = data.get('location')
    deadline_str = data.get('deadline')
    
    if not all([job_title, job_description, eligibility_cgpa is not None, eligibility_year, salary, location, deadline_str]):
        return jsonify({"status": "error", "message": "Missing required fields for drive creation."}), 400
        
    try:
        cgpa_val = float(eligibility_cgpa)
        year_val = int(eligibility_year)
        salary_val = int(salary)
        deadline_dt = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid formats: Check CGPA (float), Year (integer), Salary (integer), and Deadline (ISO Date)."}), 400
        
    try:
        drive = PlacementDrive(
            company_id=company.id,
            job_title=job_title,
            job_description=job_description,
            eligibility_branch=eligibility_branch,
            eligibility_cgpa=cgpa_val,
            eligibility_year=year_val,
            salary=salary_val,
            location=location,
            deadline=deadline_dt,
            status='pending'  # Created drives require Admin approval
        )
        db.session.add(drive)
        db.session.commit()
        evict_company_related_caches()
        return jsonify({"status": "success", "message": "Placement drive created successfully. Awaiting Admin approval."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Failed to create drive: {str(e)}"}), 500

@company_bp.route('/drives/<int:drive_id>/applications', methods=['GET'])
@login_required
@roles_required('company')
def get_drive_applications(drive_id):
    company = CompanyProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()
    applications = Application.query.filter_by(drive_id=drive.id).all()
    return jsonify({
        "status": "success",
        "applications": [app.to_dict() for app in applications]
    })

@company_bp.route('/applications/<int:app_id>/status', methods=['POST'])
@login_required
@roles_required('company')
def update_application_status(app_id):
    company = CompanyProfile.query.filter_by(user_id=session['user_id']).first_or_404()
    application = Application.query.get_or_404(app_id)

    # Check if this application belongs to a drive of the current company
    if application.drive.company_id != company.id:
        return jsonify({
            "status": "error",
            "message": "Unauthorized to update this application."
        }), 403

    data = request.get_json() or {}
    new_status = data.get('status')
    remark = data.get('remark', '')

    if not new_status or new_status not in ['applied', 'shortlisted', 'selected', 'rejected']:
        return jsonify({
            "status": "error",
            "message": "Invalid status value. Must be 'applied', 'shortlisted', 'selected', or 'rejected'."
        }), 400

    try:
        application.status = new_status
        application.remark = remark
        db.session.commit()
        evict_company_related_caches()
        return jsonify({
            "status": "success",
            "message": "Application status updated successfully.",
            "application": application.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to update application status: {str(e)}"
        }), 500
