from flask import Blueprint, jsonify, request
from backend.models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application
from backend.auth import login_required, roles_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@roles_required('admin')
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
    
    # Add block status details from User table
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
        "student_applications": applications_list
    })
