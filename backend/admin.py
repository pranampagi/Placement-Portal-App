from flask import Blueprint, jsonify, request
from backend.models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application
from backend.auth import login_required, roles_required
from backend.caching import cache_response, evict_cache_by_pattern

admin_bp = Blueprint('admin', __name__)

def evict_all_placement_caches():
    # Evict everything that could change state: admin dashboard, company drives, student eligible drives, student profiles
    evict_cache_by_pattern('admin:dashboard:*')
    evict_cache_by_pattern('company:*')
    evict_cache_by_pattern('student:*')

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@roles_required('admin')
@cache_response('admin:dashboard', timeout=600)
def get_admin_dashboard():
    student_query = request.args.get('student_query', '').strip()
    company_query = request.args.get('company_query', '').strip()
    
    # 1. Total statistics counts
    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()
    total_drives = PlacementDrive.query.count()
    
    # 2. Filtered list of registered students
    students_query_obj = StudentProfile.query
    if student_query:
        students_query_obj = students_query_obj.filter(
            StudentProfile.name.like(f"%{student_query}%") |
            StudentProfile.email.like(f"%{student_query}%") |
            StudentProfile.branch.like(f"%{student_query}%")
        )
    students_list = [s.to_dict() for s in students_query_obj.all()]
    
    # Add active/deactivated state
    for s_dict in students_list:
        user = User.query.get(s_dict['user_id'])
        s_dict['is_active'] = user.is_active if user else False
        
    # 3. Filtered list of registered companies (excluding pending or rejected)
    companies_query_obj = CompanyProfile.query.filter(CompanyProfile.approval_status == 'approved')
    if company_query:
        companies_query_obj = companies_query_obj.filter(
            CompanyProfile.name.like(f"%{company_query}%") |
            CompanyProfile.hr_contact.like(f"%{company_query}%") |
            CompanyProfile.website.like(f"%{company_query}%")
        )
    companies_list = [c.to_dict() for c in companies_query_obj.all()]
    
    # Add active/deactivated state
    for c_dict in companies_list:
        user = User.query.get(c_dict['user_id'])
        c_dict['is_active'] = user.is_active if user else False
        
    # 4. Pending company registration approvals
    pending_companies = CompanyProfile.query.filter_by(approval_status='pending').all()
    pending_companies_list = [c.to_dict() for c in pending_companies]
    
    # 5. Ongoing/Approved drives
    ongoing_drives = PlacementDrive.query.filter_by(status='approved').all()
    ongoing_drives_list = [d.to_dict() for d in ongoing_drives]
    
    # Pending drives awaiting approval
    pending_drives = PlacementDrive.query.filter_by(status='pending').all()
    pending_drives_list = [d.to_dict() for d in pending_drives]
    
    # 6. Student Applications
    applications = Application.query.order_by(Application.application_date.desc()).all()
    applications_list = [a.to_dict() for a in applications]
    
    return jsonify({
        "status": "success",
        "stats": {
            "total_students": total_students,
            "total_companies": total_companies,
            "total_drives": total_drives
        },
        "registered_students": students_list,
        "registered_companies": companies_list,
        "pending_companies": pending_companies_list,
        "ongoing_drives": ongoing_drives_list,
        "pending_drives": pending_drives_list,
        "student_applications": applications_list
    })

# Approve Company Registration
@admin_bp.route('/companies/<int:company_id>/approve', methods=['POST'])
@login_required
@roles_required('admin')
def approve_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    company.approval_status = 'approved'
    db.session.commit()
    evict_all_placement_caches()
    return jsonify({"status": "success", "message": f"Company '{company.name}' registration approved successfully."})

# Reject Company Registration
@admin_bp.route('/companies/<int:company_id>/reject', methods=['POST'])
@login_required
@roles_required('admin')
def reject_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    company.approval_status = 'rejected'
    db.session.commit()
    evict_all_placement_caches()
    return jsonify({"status": "success", "message": f"Company '{company.name}' registration rejected successfully."})

# Toggle Company Blacklist status
@admin_bp.route('/companies/<int:company_id>/toggle-blacklist', methods=['POST'])
@login_required
@roles_required('admin')
def toggle_company_blacklist(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    user = User.query.get(company.user_id)
    
    # Toggle states
    company.is_blacklisted = not company.is_blacklisted
    if user:
        user.is_active = not company.is_blacklisted
        
    # Cancel all drives if company is blacklisted
    if company.is_blacklisted:
        drives = PlacementDrive.query.filter_by(company_id=company.id).all()
        for drive in drives:
            drive.status = 'closed'
            
    db.session.commit()
    evict_all_placement_caches()
    status_str = "blacklisted and deactivated" if company.is_blacklisted else "removed from blacklist and activated"
    return jsonify({"status": "success", "message": f"Company '{company.name}' has been {status_str}."})

# Approve Placement Drive
@admin_bp.route('/drives/<int:drive_id>/approve', methods=['POST'])
@login_required
@roles_required('admin')
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'approved'
    db.session.commit()
    evict_all_placement_caches()
    return jsonify({"status": "success", "message": f"Placement drive for '{drive.job_title}' approved successfully."})

# Reject Placement Drive
@admin_bp.route('/drives/<int:drive_id>/reject', methods=['POST'])
@login_required
@roles_required('admin')
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'closed'  # Closed/Rejected
    db.session.commit()
    evict_all_placement_caches()
    return jsonify({"status": "success", "message": f"Placement drive for '{drive.job_title}' has been closed."})

# Toggle Student Active/Inactive status
@admin_bp.route('/students/<int:student_id>/toggle-active', methods=['POST'])
@login_required
@roles_required('admin')
def toggle_student_active(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    
    if not user:
        return jsonify({"status": "error", "message": "User credentials not found."}), 404
        
    user.is_active = not user.is_active
    db.session.commit()
    evict_all_placement_caches()
    
    status_str = "deactivated/blacklisted" if not user.is_active else "activated/restored"
    return jsonify({"status": "success", "message": f"Student '{student.name}' account has been {status_str}."})

# Export Applications to CSV
@admin_bp.route('/export-applications', methods=['POST'])
@login_required
@roles_required('admin')
def export_applications():
    from backend.tasks import export_applications_csv
    from flask import session
    task = export_applications_csv.delay(session['user_id'], 'admin')
    return jsonify({
        "status": "success",
        "task_id": task.id,
        "message": "CSV export has been triggered in the background."
    })
