from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'admin', 'company', 'student'
    is_active = db.Column(db.Boolean, default=True)  # Used for blacklisting
    
    # Relationships
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    company_profile = db.relationship('CompanyProfile', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "is_active": self.is_active
        }


class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    resume_filename = db.Column(db.String(256), nullable=True)  # Store uploaded resume path
    
    # Relationship to applications
    applications = db.relationship('Application', backref='student', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "branch": self.branch,
            "cgpa": self.cgpa,
            "graduation_year": self.graduation_year,
            "resume_filename": self.resume_filename
        }


class CompanyProfile(db.Model):
    __tablename__ = 'company_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(200), nullable=False)
    approval_status = db.Column(db.String(50), default='pending')  # 'pending', 'approved', 'rejected'
    is_blacklisted = db.Column(db.Boolean, default=False)
    
    # Relationship to placement drives
    drives = db.relationship('PlacementDrive', backref='company', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "hr_contact": self.hr_contact,
            "website": self.website,
            "approval_status": self.approval_status,
            "is_blacklisted": self.is_blacklisted
        }


class PlacementDrive(db.Model):
    __tablename__ = 'placement_drives'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profiles.id', ondelete='CASCADE'), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility_branch = db.Column(db.String(256), nullable=False)  # Comma separated or 'All'
    eligibility_cgpa = db.Column(db.Float, nullable=False)
    eligibility_year = db.Column(db.Integer, nullable=False)
    salary = db.Column(db.Integer, nullable=False)  # Annual CTC
    location = db.Column(db.String(150), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'approved', 'closed'
    
    # Relationship to applications
    applications = db.relationship('Application', backref='drive', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else "Unknown Company",
            "job_title": self.job_title,
            "job_description": self.job_description,
            "eligibility_branch": self.eligibility_branch,
            "eligibility_cgpa": self.eligibility_cgpa,
            "eligibility_year": self.eligibility_year,
            "salary": self.salary,
            "location": self.location,
            "deadline": self.deadline.isoformat(),
            "status": self.status
        }


class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id', ondelete='CASCADE'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='applied')  # 'applied', 'shortlisted', 'selected', 'rejected'
    remark = db.Column(db.String(256), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.name if self.student else "Unknown Student",
            "student_email": self.student.email if self.student else "",
            "student_cgpa": self.student.cgpa if self.student else 0.0,
            "student_branch": self.student.branch if self.student else "",
            "student_year": self.student.graduation_year if self.student else 0,
            "student_resume": self.student.resume_filename if self.student else "",
            "drive_id": self.drive_id,
            "job_title": self.drive.job_title if self.drive else "Unknown Job",
            "company_name": self.drive.company.name if (self.drive and self.drive.company) else "Unknown Company",
            "application_date": self.application_date.isoformat(),
            "status": self.status,
            "remark": self.remark
        }
