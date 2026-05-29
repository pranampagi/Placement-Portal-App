import os
import csv
from datetime import datetime, timedelta
from celery import Celery
from backend.config import Config
from backend.models import db, StudentProfile, PlacementDrive, Application

celery_app = Celery(
    'tasks',
    broker=Config.broker_url,
    backend=Config.result_backend
)

# Daily Deadline Reminders Task
@celery_app.task
def send_daily_deadline_reminders():
    from backend.app import create_app
    app = create_app()
    with app.app_context():
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        
        # Get all approved drives ending in the next 24 hours
        drives = PlacementDrive.query.filter(
            PlacementDrive.status == 'approved',
            PlacementDrive.deadline >= now,
            PlacementDrive.deadline <= tomorrow
        ).all()
        
        reminders_sent = 0
        for drive in drives:
            # Query eligible students
            students_query = StudentProfile.query.filter(
                StudentProfile.graduation_year == drive.eligibility_year,
                StudentProfile.cgpa >= drive.eligibility_cgpa
            )
            
            # Check branch constraints
            eligible_students = []
            if drive.eligibility_branch.lower() == 'all':
                eligible_students = students_query.all()
            else:
                allowed_branches = [b.strip().lower() for b in drive.eligibility_branch.split(',')]
                for student in students_query.all():
                    if student.branch.lower() in allowed_branches:
                        eligible_students.append(student)
            
            for student in eligible_students:
                # Check if already applied
                applied = Application.query.filter_by(student_id=student.id, drive_id=drive.id).first()
                if not applied:
                    # Simulate sending email by logging
                    print(f"[Celery Deadline Reminder] EMAIL SENT: To {student.email} ({student.name}) - "
                          f"Friendly reminder to apply for the '{drive.job_title}' drive at '{drive.company.name}'. "
                          f"Deadline: {drive.deadline.isoformat()}.")
                    reminders_sent += 1
                    
        return f"Completed sending daily reminders. Reminders sent: {reminders_sent}"

# Monthly Activity Report Task
@celery_app.task
def generate_monthly_activity_report():
    from backend.app import create_app
    app = create_app()
    with app.app_context():
        # Compute summary stats
        total_students = StudentProfile.query.count()
        total_companies = CompanyProfile.query.count()
        total_drives = PlacementDrive.query.count()
        total_applications = Application.query.count()
        
        # Calculate rates
        shortlisted = Application.query.filter_by(status='shortlisted').count()
        selected = Application.query.filter_by(status='selected').count()
        rejected = Application.query.filter_by(status='rejected').count()
        
        print(f"[Celery Monthly Report] REPORT GENERATED - "
              f"Total Students: {total_students}, Total Companies: {total_companies}, "
              f"Total Placement Drives: {total_drives}, Total Applications: {total_applications}. "
              f"Status breakdown: Shortlisted: {shortlisted}, Selected: {selected}, Rejected: {rejected}.")
              
        return "Completed generating monthly activity report."

# Async CSV Export Task
@celery_app.task(bind=True)
def export_applications_csv(self, user_id, role):
    from backend.app import create_app
    app = create_app()
    with app.app_context():
        # Resolve applications to export based on role
        if role == 'admin':
            apps = Application.query.order_by(Application.application_date.desc()).all()
        elif role == 'company':
            # company_id is user_id in this context
            apps = Application.query.join(PlacementDrive).filter(PlacementDrive.company_id == user_id).order_by(Application.application_date.desc()).all()
        elif role == 'student':
            # student_id is user_id in this context
            apps = Application.query.filter_by(student_id=user_id).order_by(Application.application_date.desc()).all()
        else:
            apps = []
            
        export_dir = os.path.join(app.root_path, 'static', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        # Use task_id for unique filename
        filename = f"export_{self.request.id}.csv"
        file_path = os.path.join(export_dir, filename)
        
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Application ID', 'Student Name', 'Student Email', 'Student Branch', 
                'Student CGPA', 'Job Title', 'Company Name', 'Applied Date', 'Status', 'Remarks'
            ])
            for app in apps:
                writer.writerow([
                    app.id,
                    app.student.name if app.student else 'Unknown',
                    app.student.email if app.student else '',
                    app.student.branch if app.student else '',
                    app.student.cgpa if app.student else 0.0,
                    app.drive.job_title if app.drive else 'Unknown',
                    app.drive.company.name if (app.drive and app.drive.company) else 'Unknown',
                    app.application_date.isoformat(),
                    app.status,
                    app.remark or ''
                ])
                
        # Return the relative URL for download
        return f"/static/exports/{filename}"
