<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const props = defineProps({
  user: {
    type: Object,
    required: true
  },
  tab: {
    type: String,
    required: true
  }
})

// Navigation & Detail States
const viewMode = ref('dashboard') // 'dashboard', 'drive-details', 'application-details'
const selectedDrive = ref(null)
const selectedApplication = ref(null)

// Dashboard states
const stats = ref({ total_students: 0, total_companies: 0, total_drives: 0 })
const registeredStudents = ref([])
const registeredCompanies = ref([])
const pendingCompanies = ref([])
const pendingDrives = ref([])
const ongoingDrives = ref([])
const studentApplications = ref([])

// Search bindings
const studentSearch = ref('')
const companySearch = ref('')

const errorMsg = ref('')
const successMsg = ref('')

// ChartJS refs
const chartCanvas = ref(null)
let chartInstance = null

const renderChart = () => {
  if (!chartCanvas.value) return
  
  const counts = {
    applied: 0,
    shortlisted: 0,
    selected: 0,
    rejected: 0
  }
  
  studentApplications.value.forEach(app => {
    const status = app.status ? app.status.toLowerCase() : 'applied'
    if (counts[status] !== undefined) {
      counts[status]++
    } else {
      counts.applied++
    }
  })
  
  const ctx = chartCanvas.value.getContext('2d')
  if (chartInstance) {
    chartInstance.destroy()
  }
  
  chartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Applied', 'Shortlisted', 'Selected', 'Rejected'],
      datasets: [{
        data: [counts.applied, counts.shortlisted, counts.selected, counts.rejected],
        backgroundColor: [
          'rgba(54, 162, 235, 0.75)',  // Blue
          'rgba(255, 193, 7, 0.75)',   // Amber/Yellow
          'rgba(40, 167, 69, 0.75)',   // Green
          'rgba(220, 53, 69, 0.75)'    // Red
        ],
        borderColor: [
          '#36a2eb',
          '#ffc107',
          '#28a745',
          '#dc3569'
        ],
        borderWidth: 1.5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            font: {
              family: 'Outfit',
              size: 11
            },
            color: '#333'
          }
        },
        title: {
          display: true,
          text: 'Applications Status Breakdown',
          font: {
            family: 'Outfit',
            size: 14,
            weight: 'bold'
          },
          color: '#333'
        }
      },
      cutout: '70%'
    }
  })
}

const fetchDashboardData = async () => {
  try {
    const res = await window.axios.get('/api/admin/dashboard', {
      params: {
        student_query: studentSearch.value,
        company_query: companySearch.value
      }
    })
    if (res.data.status === 'success') {
      stats.value = res.data.stats
      registeredStudents.value = res.data.registered_students
      registeredCompanies.value = res.data.registered_companies
      pendingCompanies.value = res.data.pending_companies
      pendingDrives.value = res.data.pending_drives
      ongoingDrives.value = res.data.ongoing_drives
      studentApplications.value = res.data.student_applications
      
      await nextTick()
      renderChart()
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Failed to fetch dashboard data.'
  }
}


// Action Handlers
const handleApproveCompany = async (id) => {
  try {
    const res = await window.axios.post(`/api/admin/companies/${id}/approve`)
    if (res.data.status === 'success') {
      successMsg.value = res.data.message
      fetchDashboardData()
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Action failed.'
  }
}

const handleRejectCompany = async (id) => {
  try {
    const res = await window.axios.post(`/api/admin/companies/${id}/reject`)
    if (res.data.status === 'success') {
      successMsg.value = res.data.message
      fetchDashboardData()
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Action failed.'
  }
}

const handleToggleCompanyBlacklist = async (id) => {
  try {
    const res = await window.axios.post(`/api/admin/companies/${id}/toggle-blacklist`)
    if (res.data.status === 'success') {
      successMsg.value = res.data.message
      fetchDashboardData()
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Action failed.'
  }
}

const handleToggleStudentActive = async (id) => {
  try {
    const res = await window.axios.post(`/api/admin/students/${id}/toggle-active`)
    if (res.data.status === 'success') {
      successMsg.value = res.data.message
      fetchDashboardData()
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Action failed.'
  }
}

const handleApproveDrive = async (id) => {
  try {
    const res = await window.axios.post(`/api/admin/drives/${id}/approve`)
    if (res.data.status === 'success') {
      successMsg.value = res.data.message
      fetchDashboardData()
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Action failed.'
  }
}

const handleCloseDrive = async (id) => {
  try {
    const res = await window.axios.post(`/api/admin/drives/${id}/reject`)
    if (res.data.status === 'success') {
      successMsg.value = res.data.message
      fetchDashboardData()
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Action failed.'
  }
}

// Subview routing triggers
const viewDriveDetails = (drive) => {
  selectedDrive.value = drive
  viewMode.value = 'drive-details'
}

const viewApplicationDetails = (app) => {
  selectedApplication.value = app
  viewMode.value = 'application-details'
}

const openResume = (filename) => {
  if (!filename) return
  const url = `${window.axios.defaults.baseURL}/static/uploads/${filename}`
  window.open(url, '_blank')
}

const exportingCsv = ref(false)

const handleExportCSV = async () => {
  exportingCsv.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const res = await window.axios.post('/api/admin/export-applications')
    if (res.data.status === 'success') {
      const taskId = res.data.task_id
      successMsg.value = 'CSV Export started in the background. Please wait...'
      pollExportStatus(taskId)
    }
  } catch (err) {
    exportingCsv.value = false
    errorMsg.value = err.response?.data?.message || 'Failed to trigger CSV export.'
  }
}

const pollExportStatus = (taskId) => {
  const interval = setInterval(async () => {
    try {
      const res = await window.axios.get(`/api/tasks/${taskId}`)
      if (res.data.status === 'success') {
        const state = res.data.state
        if (state === 'SUCCESS') {
          clearInterval(interval)
          exportingCsv.value = false
          successMsg.value = 'CSV Export complete! Downloading...'
          const downloadUrl = `${window.axios.defaults.baseURL}${res.data.result}`
          window.open(downloadUrl, '_blank')
        } else if (state === 'FAILURE') {
          clearInterval(interval)
          exportingCsv.value = false
          errorMsg.value = res.data.error || 'CSV Export failed.'
        }
      }
    } catch (err) {
      clearInterval(interval)
      exportingCsv.value = false
      errorMsg.value = 'Error checking CSV export task status.'
    }
  }, 1000)
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<template>
  <div class="container-fluid fade-in-el">
    <!-- Alerts -->
    <div v-if="successMsg" class="alert alert-success alert-dismissible fade show p-2 small" role="alert">
      {{ successMsg }}
      <button type="button" class="btn-close p-2" @click="successMsg = ''"></button>
    </div>
    <div v-if="errorMsg" class="alert alert-danger alert-dismissible fade show p-2 small" role="alert">
      {{ errorMsg }}
      <button type="button" class="btn-close p-2" @click="errorMsg = ''"></button>
    </div>

    <!-- 1. DRIVE DETAILS VIEW -->
    <div v-if="viewMode === 'drive-details' && selectedDrive" class="card glass-card p-4 border-0 mb-4">
      <div class="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
        <div>
          <span class="badge bg-primary text-uppercase mb-2">Drive Details</span>
          <h2 class="font-outfit text-dark mb-0">{{ selectedDrive.job_title }}</h2>
          <p class="text-muted mb-0"><i class="bi bi-building me-1"></i>{{ selectedDrive.company_name }}</p>
        </div>
        <div class="text-end">
          <span :class="'badge bg-' + (selectedDrive.status === 'approved' ? 'success' : (selectedDrive.status === 'pending' ? 'warning' : 'danger')) + ' px-3 py-2 text-uppercase'">
            {{ selectedDrive.status }}
          </span>
        </div>
      </div>

      <div class="row g-4 mb-4">
        <div class="col-md-8">
          <h5 class="fw-semibold font-outfit mb-2">Job Description</h5>
          <p class="text-secondary style-desc">{{ selectedDrive.job_description }}</p>
        </div>
        <div class="col-md-4">
          <div class="card bg-light border-0 p-3 rounded-3">
            <h6 class="font-outfit fw-bold text-secondary mb-3">Specifications</h6>
            
            <div class="mb-2 small">
              <span class="text-muted">Salary Range:</span>
              <div class="fw-semibold">₹ {{ selectedDrive.salary.toLocaleString() }} LPA</div>
            </div>
            
            <div class="mb-2 small">
              <span class="text-muted">Job Location:</span>
              <div class="fw-semibold">{{ selectedDrive.location }}</div>
            </div>

            <div class="mb-2 small">
              <span class="text-muted">Eligible Branch:</span>
              <div class="fw-semibold">{{ selectedDrive.eligibility_branch }}</div>
            </div>

            <div class="mb-2 small">
              <span class="text-muted">Min CGPA Required:</span>
              <div class="fw-semibold">{{ selectedDrive.eligibility_cgpa }}</div>
            </div>

            <div class="small">
              <span class="text-muted">Apply Deadline:</span>
              <div class="fw-semibold text-danger">{{ new Date(selectedDrive.deadline).toLocaleString() }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="d-flex justify-content-start">
        <button @click="viewMode = 'dashboard'" class="btn btn-outline-secondary px-4 rounded-pill">
          <i class="bi bi-arrow-left me-2"></i>Go Back
        </button>
      </div>
    </div>

    <!-- 2. STUDENT APPLICATION DETAILS VIEW -->
    <div v-else-if="viewMode === 'application-details' && selectedApplication" class="card glass-card p-4 border-0 mb-4">
      <div class="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
        <div>
          <span class="badge bg-info text-dark text-uppercase mb-2">Student Application</span>
          <h2 class="font-outfit text-dark mb-0">{{ selectedApplication.student_name }}</h2>
          <p class="text-muted mb-0"><i class="bi bi-envelope me-1"></i>{{ selectedApplication.student_email }}</p>
        </div>
        <div class="text-end">
          <span :class="'badge badge-' + selectedApplication.status + ' px-3 py-2 text-uppercase'">
            {{ selectedApplication.status }}
          </span>
        </div>
      </div>

      <div class="row g-4 mb-4">
        <div class="col-md-6">
          <div class="card bg-light border-0 p-3 h-100 rounded-3">
            <h5 class="font-outfit fw-bold text-secondary mb-3">Academic Summary</h5>
            <div class="row g-3">
              <div class="col-6 small">
                <span class="text-muted d-block">Department/Branch:</span>
                <span class="fw-semibold">{{ selectedApplication.student_branch }}</span>
              </div>
              <div class="col-6 small">
                <span class="text-muted d-block">CGPA:</span>
                <span class="fw-semibold">{{ selectedApplication.student_cgpa }}</span>
              </div>
              <div class="col-6 small">
                <span class="text-muted d-block">Graduation Year:</span>
                <span class="fw-semibold">{{ selectedApplication.student_year }}</span>
              </div>
              <div class="col-6 small">
                <span class="text-muted d-block">Applied Date:</span>
                <span class="fw-semibold">{{ new Date(selectedApplication.application_date).toLocaleDateString() }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-6">
          <div class="card bg-light border-0 p-3 h-100 rounded-3">
            <h5 class="font-outfit fw-bold text-secondary mb-3">Drive Information</h5>
            <div class="row g-3">
              <div class="col-12 small">
                <span class="text-muted d-block">Position:</span>
                <span class="fw-semibold text-primary fs-6">{{ selectedApplication.job_title }}</span>
              </div>
              <div class="col-12 small">
                <span class="text-muted d-block">Recruiting Organization:</span>
                <span class="fw-semibold">{{ selectedApplication.company_name }}</span>
              </div>
              <div class="col-12 small" v-if="selectedApplication.remark">
                <span class="text-muted d-block">Remarks:</span>
                <span class="text-secondary italic">{{ selectedApplication.remark }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mb-4" v-if="selectedApplication.student_resume">
        <h5 class="font-outfit fw-bold mb-3">Candidate Resume</h5>
        <div class="d-flex align-items-center gap-3 bg-white p-3 rounded-3 border">
          <i class="bi bi-file-earmark-pdf-fill text-danger fs-1"></i>
          <div>
            <div class="fw-semibold text-dark">{{ selectedApplication.student_resume }}</div>
            <div class="small text-muted">Uploaded PDF Document</div>
          </div>
          <button @click="openResume(selectedApplication.student_resume)" class="btn btn-primary btn-sm ms-auto px-3 rounded-pill">
            <i class="bi bi-eye me-1"></i>view resume
          </button>
        </div>
      </div>
      <div v-else class="alert alert-warning mb-4">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>No resume uploaded by this candidate.
      </div>

      <div class="d-flex justify-content-start">
        <button @click="viewMode = 'dashboard'" class="btn btn-outline-secondary px-4 rounded-pill">
          <i class="bi bi-arrow-left me-2"></i>back
        </button>
      </div>
    </div>

    <!-- 3. MAIN DASHBOARD VIEW -->
    <div v-else>
      <!-- Statistics Cards & Chart -->
      <div class="row g-4 mb-4">
        <div class="col-lg-8">
          <div class="row g-3">
            <div class="col-md-6">
              <div class="card glass-card p-4 text-center border-0 h-100 d-flex flex-column justify-content-center">
                <i class="bi bi-people text-primary fs-1"></i>
                <h6 class="text-uppercase text-secondary small fw-bold mt-2">Registered Students</h6>
                <h2 class="font-outfit text-dark mb-0 mt-1">{{ stats.total_students }}</h2>
              </div>
            </div>
            <div class="col-md-6">
              <div class="card glass-card p-4 text-center border-0 h-100 d-flex flex-column justify-content-center">
                <i class="bi bi-building text-success fs-1"></i>
                <h6 class="text-uppercase text-secondary small fw-bold mt-2">Registered Companies</h6>
                <h2 class="font-outfit text-dark mb-0 mt-1">{{ stats.total_companies }}</h2>
              </div>
            </div>
            <div class="col-md-12">
              <div class="card glass-card p-4 text-center border-0 h-100 d-flex flex-column justify-content-center">
                <i class="bi bi-calendar-event text-info fs-1"></i>
                <h6 class="text-uppercase text-secondary small fw-bold mt-2">Placement Drives</h6>
                <h2 class="font-outfit text-dark mb-0 mt-1">{{ stats.total_drives }}</h2>
              </div>
            </div>
          </div>
        </div>
        <div class="col-lg-4">
          <div class="card glass-card border-0 p-3 h-100 d-flex flex-column justify-content-center align-items-center">
            <div style="position: relative; height: 200px; width: 100%;">
              <canvas ref="chartCanvas"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- Pending Applications section (Company Onboarding & Drive Launches) -->
      <div class="row g-4 mb-4">
        <!-- Company Applications Card -->
        <div class="col-lg-6">
          <div class="card glass-card border-0 p-3 h-100">
            <h5 class="font-outfit mb-3">Company Applications</h5>
            <div v-if="pendingCompanies.length === 0" class="text-muted text-center py-4 small">
              No pending company registration approvals.
            </div>
            <div v-else class="list-group list-group-flush">
              <div v-for="comp in pendingCompanies" :key="comp.id" class="list-group-item bg-transparent d-flex justify-content-between align-items-center px-0 py-3 border-bottom">
                <div>
                  <h6 class="mb-0 fw-semibold">{{ comp.name }}</h6>
                  <div class="small text-muted">
                    HR: {{ comp.hr_contact }} | <a :href="comp.website" target="_blank" class="text-decoration-none text-primary">{{ comp.website }}</a>
                  </div>
                </div>
                <div class="btn-actions">
                  <button @click="handleApproveCompany(comp.id)" class="btn btn-success btn-sm px-3 rounded-pill">Approve</button>
                  <button @click="handleRejectCompany(comp.id)" class="btn btn-outline-danger btn-sm px-3 rounded-pill">Reject</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Drive Applications Card (NEW) -->
        <div class="col-lg-6">
          <div class="card glass-card border-0 p-3 h-100">
            <h5 class="font-outfit mb-3">Drive Applications</h5>
            <div v-if="pendingDrives.length === 0" class="text-muted text-center py-4 small">
              No pending placement drives awaiting approval.
            </div>
            <div v-else class="list-group list-group-flush">
              <div v-for="drive in pendingDrives" :key="drive.id" class="list-group-item bg-transparent d-flex justify-content-between align-items-center px-0 py-3 border-bottom">
                <div>
                  <h6 class="mb-0 fw-semibold">{{ drive.job_title }}</h6>
                  <div class="small text-muted">
                    Company: {{ drive.company_name }} | Salary: ₹ {{ drive.salary.toLocaleString() }}
                  </div>
                </div>
                <div class="btn-actions">
                  <button @click="handleApproveDrive(drive.id)" class="btn btn-success btn-sm px-3 rounded-pill">Approve</button>
                  <button @click="handleCloseDrive(drive.id)" class="btn btn-outline-danger btn-sm px-3 rounded-pill">Reject</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Ongoing Drives & Applications tracking -->
      <div class="row g-4 mb-4">
        <div class="col-lg-6">
          <div class="card glass-card border-0 p-3 h-100">
            <h5 class="font-outfit mb-3">Ongoing Drives</h5>
            <div v-if="ongoingDrives.length === 0" class="text-muted text-center py-4 small">
              No active placement drives currently.
            </div>
            <div v-else class="table-responsive">
              <table class="table table-sm align-middle table-hover small">
                <thead>
                  <tr>
                    <th>Job Title</th>
                    <th>Company</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="drive in ongoingDrives" :key="drive.id">
                    <td class="fw-semibold">{{ drive.job_title }}</td>
                    <td>{{ drive.company_name }}</td>
                    <td>
                      <div class="btn-actions">
                        <button @click="viewDriveDetails(drive)" class="btn btn-outline-primary btn-sm px-2 rounded">view details</button>
                        <button @click="handleCloseDrive(drive.id)" class="btn btn-outline-danger btn-sm px-2 rounded">mark as complete</button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="col-lg-6">
          <div class="card glass-card border-0 p-3 h-100">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h5 class="font-outfit mb-0">Student Applications</h5>
              <button 
                @click="handleExportCSV" 
                :disabled="exportingCsv || studentApplications.length === 0" 
                class="btn btn-outline-primary btn-sm rounded-pill px-3"
              >
                <span v-if="exportingCsv" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                <i v-else class="bi bi-file-earmark-spreadsheet me-1"></i>
                Export CSV
              </button>
            </div>
            <div v-if="studentApplications.length === 0" class="text-muted text-center py-4 small">
              No student placement applications submitted yet.
            </div>
            <div v-else class="table-responsive">
              <table class="table table-sm align-middle table-hover small">
                <thead>
                  <tr>
                    <th>Student Name</th>
                    <th>Placement Drive</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="app in studentApplications.slice(0, 5)" :key="app.id">
                    <td class="fw-semibold">{{ app.student_name }}</td>
                    <td>{{ app.job_title }}</td>
                    <td>
                      <span :class="'badge badge-' + app.status" class="px-2 py-1 text-uppercase" style="font-size: 0.7rem;">{{ app.status }}</span>
                    </td>
                    <td>
                      <button @click="viewApplicationDetails(app)" class="btn btn-outline-primary btn-sm px-2 py-0 rounded">view</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Directories & Search filters -->
      <div class="row g-4 mb-4">
        <div class="col-lg-6">
          <div class="card glass-card border-0 p-3 h-100">
            <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
              <h5 class="font-outfit mb-0">Registered Companies</h5>
              <div class="input-group input-group-sm" style="max-width: 250px;">
                <input type="text" v-model="companySearch" @input="fetchDashboardData" class="form-control" placeholder="Search companies...">
                <button class="btn btn-outline-secondary" @click="fetchDashboardData"><i class="bi bi-search"></i></button>
              </div>
            </div>
            
            <div v-if="registeredCompanies.length === 0" class="text-muted text-center py-4 small">
              No registered companies found.
            </div>
            <div v-else class="table-responsive">
              <table class="table table-sm align-middle table-hover small">
                <thead>
                  <tr>
                    <th>Company Name</th>
                    <th>HR Contact</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="comp in registeredCompanies" :key="comp.id">
                    <td class="fw-semibold">{{ comp.name }}</td>
                    <td>{{ comp.hr_contact }}</td>
                    <td>
                      <span v-if="comp.is_blacklisted" class="badge bg-danger">Blacklisted</span>
                      <span v-else class="badge bg-success">Active</span>
                    </td>
                    <td>
                      <button @click="handleToggleCompanyBlacklist(comp.id)" :class="comp.is_blacklisted ? 'btn-outline-success' : 'btn-outline-danger'" class="btn btn-sm py-1 px-2 rounded">
                        {{ comp.is_blacklisted ? 'Whitelist' : 'Blacklist' }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="col-lg-6">
          <div class="card glass-card border-0 p-3 h-100">
            <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
              <h5 class="font-outfit mb-0">Registered Students</h5>
              <div class="input-group input-group-sm" style="max-width: 250px;">
                <input type="text" v-model="studentSearch" @input="fetchDashboardData" class="form-control" placeholder="Search students...">
                <button class="btn btn-outline-secondary" @click="fetchDashboardData"><i class="bi bi-search"></i></button>
              </div>
            </div>
            
            <div v-if="registeredStudents.length === 0" class="text-muted text-center py-4 small">
              No registered students found.
            </div>
            <div v-else class="table-responsive">
              <table class="table table-sm align-middle table-hover small">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Branch / CGPA</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="stud in registeredStudents" :key="stud.id">
                    <td class="fw-semibold">{{ stud.name }}</td>
                    <td>{{ stud.branch }} ({{ stud.cgpa }})</td>
                    <td>
                      <span v-if="!stud.is_active" class="badge bg-danger">Deactivated</span>
                      <span v-else class="badge bg-success">Active</span>
                    </td>
                    <td>
                      <button @click="handleToggleStudentActive(stud.id)" :class="stud.is_active ? 'btn-outline-danger' : 'btn-outline-success'" class="btn btn-sm py-1 px-2 rounded">
                        {{ stud.is_active ? 'Deactivate' : 'Activate' }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.style-desc {
  white-space: pre-line;
  line-height: 1.6;
}
</style>
