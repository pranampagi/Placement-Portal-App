# Placement Portal Application (PPA) - V2

A modern, responsive, and decoupled recruitment management system for academic institutes, companies, and students. Built with a Flask REST API backend, a Vue 3 (Vite) frontend, SQLite, Redis caching, and Celery background tasks.

---

## 🏗️ Architecture & Stack

This application follows a decoupled **Client-Server Architecture**:
- **Backend**: Flask REST API running on **port 5000**, handling authentication, profiles, drive approvals, student applications, and background jobs.
- **Frontend**: Vite + Vue 3 Single Page Application running on **port 5173** (or port 8000), using Axios to query the backend with cross-origin credentials.
- **Database**: SQLite (managed programmatically via SQLAlchemy).
- **Caching**: Redis.
- **Background Tasks**: Celery with Redis broker (handles daily reminders, monthly reports, and CSV exports).
- **Styling**: Bootstrap 5 + Bootstrap Icons + Custom CSS (featuring glassmorphism, responsive sidebars, and smooth micro-animations).

---

## 📁 Folder Structure

```
Placement Portal App/
├── backend/
│   ├── app.py              # Flask app factory, CORS, and blueprint registry
│   ├── config.py           # Configuration for DB, Redis, Celery, and uploads
│   ├── models.py           # SQLAlchemy SQLite database models
│   ├── auth.py             # Authentication endpoints and role decorators
│   ├── admin.py            # Admin dashboard and action endpoints
│   ├── tasks.py            # Celery task definitions (reminders, PDF reports, exports)
│   ├── init_db.py          # Database programmatic creation and admin seeding
│   └── placement_portal.db # SQLite database file (generated on init)
├── frontend/
│   ├── index.html          # Frontend HTML template
│   ├── package.json        # Frontend Vite, Vue, Axios, Bootstrap configurations
│   ├── vite.config.js      # Vite dev server configuration (listening on 0.0.0.0)
│   └── src/
│       ├── main.js         # Frontend JavaScript entry, imports, and Axios defaults
│       ├── App.vue         # Root Vue component with session verification
│       ├── style.css       # Core typography, glassmorphism UI variables, and animations
│       └── components/
│           ├── Login.vue       # Credentials submission panel
│           ├── Register.vue    # Role-based profile registration form
│           ├── Dashboard.vue   # Dynamic sidebar container layout
│           ├── AdminPanel.vue  # Stats, moderation toggles, and detail views
│           ├── CompanyPanel.vue# (Day 3) Drives management and candidate shortlisting
│           └── StudentPanel.vue# (Day 3) Jobs list, eligibility check, and ATS checker
├── requirements.txt        # Backend dependencies
├── README.md               # Project Readme
└── .gitignore              # Excluded file paths
```

---

## 🚀 Setup & Installation

### 1. Prerequisite Systems
Ensure you have the following installed on your system:
- Python 3.10+
- Node.js & npm (v20+)
- Redis Server (running on default port `6379`)

### 2. Backend Setup
Activate the virtual environment and install dependencies:
```bash
# Setup virtual environment
uv venv .venv
source .venv/bin/activate

# Install requirements
uv pip install -r requirements.txt
```

### 3. Database Initialisation
Create the database and seed the default Admin account:
```bash
PYTHONPATH=. python3 backend/init_db.py
```
*Seeded credentials:*
- **Username**: `admin`
- **Password**: `admin`

### 4. Frontend Setup
Install npm packages in the `frontend` directory:
```bash
cd frontend
npm install
```

---

## ⚙️ Running the Application

To run the full stack locally:

### 1. Run Backend Server (Port 5000)
Make sure you are in the project root:
```bash
PYTHONPATH=. ./.venv/bin/python3 backend/app.py
```

### 2. Run Vite Frontend Dev Server (Port 5173)
In a new terminal window:
```bash
cd frontend
npm run dev
```

Open your browser to the URL printed in the terminal (typically **`http://localhost:5173`** or **`http://127.0.0.1:5173`**).

---

## 🛠️ Background Services (Redis & Celery)

Ensure Redis is active:
```bash
redis-cli ping
```

Run the Celery worker for processing asynchronous batch jobs (such as exporting application history as CSV):
```bash
celery -A backend.tasks.celery_app worker --loglevel=info
```
