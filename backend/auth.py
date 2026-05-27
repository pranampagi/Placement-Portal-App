from flask import Blueprint, request, jsonify, session
from functools import wraps
from backend.models import db, User, StudentProfile, CompanyProfile

auth_bp = Blueprint('auth', __name__)

# Authentication & Role Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401
            user_role = session.get('role')
            if user_role not in roles:
                return jsonify({"status": "error", "message": f"Forbidden. Requires {roles} role(s)."}), 403
            
            # Additional check: if user is not active, block access
            user = User.query.get(session['user_id'])
            if not user or not user.is_active:
                session.clear()
                return jsonify({"status": "error", "message": "User account is blacklisted or deactivated."}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Endpoints
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')  # 'student' or 'company'
    
    if not username or not password or not role:
        return jsonify({"status": "error", "message": "Username, password and role are required."}), 400
        
    if role not in ['student', 'company']:
        return jsonify({"status": "error", "message": "Invalid role. Choose 'student' or 'company'."}), 400
        
    # Check if username exists
    if User.query.filter_by(username=username).first():
        return jsonify({"status": "error", "message": "Username already exists."}), 400
        
    try:
        # Create user
        user = User(username=username, role=role, is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id
        
        # Create profile based on role
        if role == 'student':
            name = data.get('name')
            email = data.get('email')
            branch = data.get('branch')
            cgpa = data.get('cgpa')
            graduation_year = data.get('graduation_year')
            
            if not name or not email or not branch or cgpa is None or not graduation_year:
                db.session.rollback()
                return jsonify({"status": "error", "message": "Missing student profile fields."}), 400
                
            try:
                cgpa_val = float(cgpa)
                grad_year_val = int(graduation_year)
            except ValueError:
                db.session.rollback()
                return jsonify({"status": "error", "message": "CGPA must be a decimal, year must be an integer."}), 400
                
            profile = StudentProfile(
                user_id=user.id,
                name=name,
                email=email,
                branch=branch,
                cgpa=cgpa_val,
                graduation_year=grad_year_val
            )
            db.session.add(profile)
            
        elif role == 'company':
            name = data.get('name')
            hr_contact = data.get('hr_contact')
            website = data.get('website')
            
            if not name or not hr_contact or not website:
                db.session.rollback()
                return jsonify({"status": "error", "message": "Missing company profile fields."}), 400
                
            profile = CompanyProfile(
                user_id=user.id,
                name=name,
                hr_contact=hr_contact,
                website=website,
                approval_status='pending'  # Admins must approve companies
            )
            db.session.add(profile)
            
        db.session.commit()
        return jsonify({"status": "success", "message": "User registered successfully! Pending approval for companies."}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Registration failed: {str(e)}"}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required."}), 400
        
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({"status": "error", "message": "Invalid username or password."}), 401
        
    if not user.is_active:
        return jsonify({"status": "error", "message": "Your account has been deactivated or blacklisted."}), 403
        
    # Get profile ID if it is a student or company
    profile_id = None
    approval_status = None
    if user.role == 'student':
        profile_id = user.student_profile.id if user.student_profile else None
    elif user.role == 'company':
        profile_id = user.company_profile.id if user.company_profile else None
        approval_status = user.company_profile.approval_status if user.company_profile else None
        
    # Set session details
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    session['profile_id'] = profile_id
    
    return jsonify({
        "status": "success",
        "message": "Login successful.",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "profile_id": profile_id,
            "approval_status": approval_status
        }
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success", "message": "Logged out successfully."})


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({"status": "success", "authenticated": False, "user": None})
        
    user = User.query.get(session['user_id'])
    if not user or not user.is_active:
        session.clear()
        return jsonify({"status": "success", "authenticated": False, "user": None})
        
    approval_status = None
    if user.role == 'company' and user.company_profile:
        approval_status = user.company_profile.approval_status
        
    return jsonify({
        "status": "success",
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "profile_id": session.get('profile_id'),
            "approval_status": approval_status
        }
    })




