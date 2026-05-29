<script setup>
import { ref, onMounted, watch } from 'vue'

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

// Core Student State
const studentProfile = ref({
  name: '',
  email: '',
  branch: '',
  cgpa: 0.0,
  graduation_year: new Date().getFullYear(),
  resume_filename: ''
})

// Edit Form State
const editForm = ref({
  name: '',
  email: '',
  branch: '',
  cgpa: '',
  graduation_year: ''
})

// Eligible Drives and History Applications
const eligibleDrives = ref([])
const applications = ref([])

// File upload states
const fileInput = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)

const errorMsg = ref('')
const successMsg = ref('')

const fetchProfile = async () => {
  try {
    const res = await window.axios.get('/api/student/profile')
    if (res.data.status === 'success') {
      studentProfile.value = res.data.student
      // Initialize edit form
      editForm.value = {
        name: studentProfile.value.name,
        email: studentProfile.value.email,
        branch: studentProfile.value.branch,
        cgpa: studentProfile.value.cgpa,
        graduation_year: studentProfile.value.graduation_year
      }
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Failed to load student profile.'
  }
}

const fetchEligibleDrives = async () => {
  try {
    const res = await window.axios.get('/api/student/eligible-drives')
    if (res.data.status === 'success') {
      eligibleDrives.value = res.data.drives
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Failed to load eligible drives.'
  }
}

const fetchApplications = async () => {
  try {
    const res = await window.axios.get('/api/student/applications')
    if (res.data.status === 'success') {
      applications.value = res.data.applications
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Failed to load application history.'
  }
}

const handleUpdateProfile = async () => {
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const res = await window.axios.put('/api/student/profile', editForm.value)
    if (res.data.status === 'success') {
      successMsg.value = res.data.message
      studentProfile.value = res.data.student
      if (props.tab === 'dashboard') {
        fetchEligibleDrives()
      }
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Failed to update profile.'
  }
}

const handleApply = async (driveId) => {
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const res = await window.axios.post('/api/student/apply', { drive_id: driveId })
    if (res.data.status === 'success') {
      successMsg.value = res.data.message
      fetchEligibleDrives()
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Failed to submit application.'
  }
}

const triggerFileInput = () => {
  fileInput.value.click()
}

const onFileChange = (e) => {
  const files = e.target.files
  if (files.length > 0) {
    const file = files[0]
    if (file.type !== 'application/pdf') {
      errorMsg.value = 'Only PDF resume files are accepted.'
      selectedFile.value = null
      return
    }
    selectedFile.value = file
    errorMsg.value = ''
  }
}

const handleResumeUpload = async () => {
  if (!selectedFile.value) return
  errorMsg.value = ''
  successMsg.value = ''
  uploading.value = true

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const res = await window.axios.post('/api/student/upload-resume', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    if (res.data.status === 'success') {
      successMsg.value = res.data.message
      studentProfile.value.resume_filename = res.data.resume_filename
      selectedFile.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
      if (props.tab === 'dashboard') {
        fetchEligibleDrives()
      }
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Failed to upload resume.'
  } finally {
    uploading.value = false
  }
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
    const res = await window.axios.post('/api/student/export-applications')
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

// ATS Matcher States & Functions
const atsModalOpen = ref(false)
const selectedDriveForAts = ref(null)
const atsLoading = ref(false)
const atsResult = ref(null)

const openAtsChecker = async (drive) => {
  selectedDriveForAts.value = drive
  atsModalOpen.value = true
  atsLoading.value = true
  atsResult.value = null
  errorMsg.value = ''
  
  try {
    const res = await window.axios.post(`/api/student/drives/${drive.id}/ats-match`)
    if (res.data.status === 'success') {
      atsResult.value = {
        score: res.data.score,
        matched_skills: res.data.matched_skills,
        missing_skills: res.data.missing_skills
      }
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Failed to analyze resume compatibility.'
    atsModalOpen.value = false
  } finally {
    atsLoading.value = false
  }
}

const closeAtsChecker = () => {
  atsModalOpen.value = false
  selectedDriveForAts.value = null
  atsResult.value = null
}

const getScoreCircleStyle = (score) => {
  let color = '#ef4444' // Red if low
  if (score >= 70) {
    color = '#10b981' // Green if high
  } else if (score >= 40) {
    color = '#f59e0b' // Amber if mid
  }
  return {
    '--score-percent': score,
    '--score-color': color
  }
}

const getScoreFeedback = (score) => {
  if (score >= 80) return 'Excellent Match!'
  if (score >= 60) return 'Good Compatibility'
  if (score >= 40) return 'Moderate Match'
  return 'Requires Alignment'
}

// Unified data loader based on active tab
const loadTabData = () => {
  fetchProfile()
  if (props.tab === 'dashboard') {
    fetchEligibleDrives()
  } else if (props.tab === 'history') {
    fetchApplications()
  }
}

// Fetch details when mounted or tab updates
onMounted(() => {
  loadTabData()
})

watch(() => props.tab, () => {
  errorMsg.value = ''
  successMsg.value = ''
  loadTabData()
})
</script>

<template>
  <div class="container-fluid fade-in-el">
    <!-- Feedback Alerts -->
    <div v-if="successMsg" class="alert alert-success alert-dismissible fade show p-2 small mb-3" role="alert">
      {{ successMsg }}
      <button type="button" class="btn-close p-2" @click="successMsg = ''"></button>
    </div>
    <div v-if="errorMsg" class="alert alert-danger alert-dismissible fade show p-2 small mb-3" role="alert">
      {{ errorMsg }}
      <button type="button" class="btn-close p-2" @click="errorMsg = ''"></button>
    </div>

    <!-- 1. DASHBOARD VIEW -->
    <div v-if="tab === 'dashboard'">
      <div class="card glass-card border-0 p-4 mb-4">
        <h2 class="font-outfit mb-1">Welcome back, {{ studentProfile.name || user.username }}!</h2>
        <p class="text-secondary mb-0">Track your academic eligibility and manage your resumes for ongoing drives.</p>
      </div>

      <div class="row g-4 mb-4">
        <!-- Academic details overview -->
        <div class="col-md-7">
          <div class="card glass-card border-0 p-3 h-100">
            <h5 class="font-outfit mb-3">Academic Summary</h5>
            <div class="table-responsive">
              <table class="table table-sm align-middle table-borderless small">
                <tbody>
                  <tr>
                    <td class="text-muted py-2" style="width: 35%;">Full Name:</td>
                    <td class="fw-semibold py-2">{{ studentProfile.name || 'Not configured' }}</td>
                  </tr>
                  <tr>
                    <td class="text-muted py-2">Email Address:</td>
                    <td class="fw-semibold py-2">{{ studentProfile.email || 'Not configured' }}</td>
                  </tr>
                  <tr>
                    <td class="text-muted py-2">Department / Branch:</td>
                    <td class="fw-semibold py-2">{{ studentProfile.branch || 'Not configured' }}</td>
                  </tr>
                  <tr>
                    <td class="text-muted py-2">Current CGPA:</td>
                    <td class="fw-semibold py-2">
                      <span class="badge bg-primary fs-6">{{ studentProfile.cgpa ? studentProfile.cgpa.toFixed(2) : '0.00' }}</span>
                    </td>
                  </tr>
                  <tr>
                    <td class="text-muted py-2">Graduation Year:</td>
                    <td class="fw-semibold py-2">{{ studentProfile.graduation_year }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Resume status overview -->
        <div class="col-md-5">
          <div class="card glass-card border-0 p-3 h-100 text-center d-flex flex-column justify-content-center align-items-center">
            <h5 class="font-outfit mb-3 align-self-start">Resume Attachment</h5>
            
            <div v-if="studentProfile.resume_filename" class="my-auto py-2">
              <i class="bi bi-file-earmark-check-fill text-success fs-1 mb-2 d-block"></i>
              <div class="fw-semibold text-dark text-truncate px-3 mb-1" style="max-width: 250px;">{{ studentProfile.resume_filename }}</div>
              <span class="badge bg-success mb-3 text-uppercase">active resume</span>
              <div class="d-flex gap-2 justify-content-center">
                <button @click="openResume(studentProfile.resume_filename)" class="btn btn-outline-primary btn-sm rounded-pill px-3">
                  <i class="bi bi-eye me-1"></i>View File
                </button>
              </div>
            </div>
            
            <div v-else class="my-auto py-2">
              <i class="bi bi-file-earmark-arrow-up-fill text-warning fs-1 mb-2 d-block"></i>
              <div class="fw-semibold text-secondary mb-1">No resume uploaded</div>
              <p class="small text-muted px-4 mb-3">You must upload a PDF resume to apply for placement drives.</p>
              <button @click="$emit('update-tab', 'profile')" class="btn btn-primary btn-sm rounded-pill px-4">
                Upload Resume
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Eligible placement drives table -->
      <div class="card glass-card border-0 p-3 mb-4">
        <h5 class="font-outfit mb-3">Eligible Placement Drives</h5>
        
        <div v-if="eligibleDrives.length === 0" class="text-muted text-center py-4 small">
          No eligible placement drives found matching your branch, CGPA, and graduation year.
        </div>
        
        <div v-else class="table-responsive">
          <table class="table table-hover align-middle small">
            <thead>
              <tr>
                <th>Job Title</th>
                <th>Company</th>
                <th>CTC / Salary</th>
                <th>Location</th>
                <th>Deadline</th>
                <th>Status / Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="drive in eligibleDrives" :key="drive.id">
                <td class="fw-semibold">{{ drive.job_title }}</td>
                <td>{{ drive.company_name }}</td>
                <td>₹ {{ drive.salary.toLocaleString() }}</td>
                <td>{{ drive.location }}</td>
                <td>{{ new Date(drive.deadline).toLocaleString() }}</td>
                <td>
                  <div class="d-flex align-items-center gap-2">
                    <button 
                      @click="openAtsChecker(drive)"
                      :disabled="!studentProfile.resume_filename"
                      class="btn btn-outline-info btn-sm rounded px-2 py-1 text-dark"
                      style="border-color: #0dcaf0;"
                    >
                      <i class="bi bi-cpu me-1"></i>ATS Check
                    </button>
                    
                    <span v-if="drive.applied" :class="'badge badge-' + drive.application_status + ' text-uppercase px-2 py-1'">
                      {{ drive.application_status }}
                    </span>
                    <button 
                      v-else 
                      @click="handleApply(drive.id)" 
                      :disabled="!studentProfile.resume_filename"
                      class="btn btn-primary btn-sm rounded px-3 py-1"
                      :title="!studentProfile.resume_filename ? 'Please upload your resume in the Profile tab to apply.' : ''"
                    >
                      Apply Now
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 2. EDIT PROFILE VIEW -->
    <div v-else-if="tab === 'profile'">
      <div class="row g-4">
        <!-- Edit Profile Form -->
        <div class="col-lg-7">
          <div class="card glass-card border-0 p-4 mb-4">
            <h5 class="font-outfit mb-3 pb-2 border-bottom">Academic Profile Details</h5>
            <form @submit.prevent="handleUpdateProfile">
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label small fw-semibold">Full Name</label>
                  <input type="text" v-model="editForm.name" class="form-control" required>
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label small fw-semibold">Email Address</label>
                  <input type="email" v-model="editForm.email" class="form-control" required>
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label small fw-semibold">Branch / Department</label>
                  <input type="text" v-model="editForm.branch" class="form-control" required placeholder="e.g. CSE">
                </div>
                <div class="col-md-3 mb-3">
                  <label class="form-label small fw-semibold">CGPA</label>
                  <input type="number" step="0.01" min="0" max="10" v-model="editForm.cgpa" class="form-control" required placeholder="e.g. 8.5">
                </div>
                <div class="col-md-3 mb-3">
                  <label class="form-label small fw-semibold">Graduation Year</label>
                  <input type="number" v-model="editForm.graduation_year" class="form-control" required>
                </div>
              </div>
              <div class="d-flex justify-content-end mt-3">
                <button type="submit" class="btn btn-primary rounded-pill px-4">Save Changes</button>
              </div>
            </form>
          </div>
        </div>

        <!-- Resume File Upload Card -->
        <div class="col-lg-5">
          <div class="card glass-card border-0 p-4 mb-4">
            <h5 class="font-outfit mb-3 pb-2 border-bottom">Resume File Upload</h5>
            <p class="small text-secondary mb-3">Upload a clean PDF copy of your professional resume. Only PDF files up to 16MB are accepted.</p>
            
            <div class="upload-dropzone p-4 mb-3 border border-2 border-dashed rounded-3 text-center bg-light">
              <input type="file" ref="fileInput" @change="onFileChange" accept=".pdf" class="d-none">
              
              <div v-if="!selectedFile">
                <i class="bi bi-cloud-arrow-up text-primary fs-1 mb-2"></i>
                <div class="small fw-semibold text-dark">Drag and drop file here</div>
                <div class="small text-muted mb-3">or browse locally</div>
                <button type="button" @click="triggerFileInput" class="btn btn-outline-primary btn-sm px-3 rounded-pill">Choose File</button>
              </div>
              
              <div v-else>
                <i class="bi bi-file-pdf-fill text-danger fs-1 mb-2"></i>
                <div class="small fw-semibold text-dark text-truncate px-3 mb-2" style="max-width: 300px;">{{ selectedFile.name }}</div>
                <div class="small text-muted mb-3">({{(selectedFile.size / 1024).toFixed(1)}} KB)</div>
                <div class="d-flex gap-2 justify-content-center">
                  <button type="button" @click="selectedFile = null" class="btn btn-outline-secondary btn-sm px-3 rounded-pill">Cancel</button>
                  <button type="button" @click="handleResumeUpload" :disabled="uploading" class="btn btn-success btn-sm px-3 rounded-pill">
                    <span v-if="uploading" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                    {{ uploading ? 'Uploading...' : 'Upload' }}
                  </button>
                </div>
              </div>
            </div>
            
            <div v-if="studentProfile.resume_filename" class="p-3 bg-light rounded-3 border">
              <div class="d-flex align-items-center gap-2 small">
                <i class="bi bi-check-circle-fill text-success fs-5"></i>
                <div class="text-truncate">
                  <span class="d-block text-dark fw-semibold">Current Resume:</span>
                  <span class="text-muted">{{ studentProfile.resume_filename }}</span>
                </div>
                <button @click="openResume(studentProfile.resume_filename)" class="btn btn-link btn-sm ms-auto text-decoration-none">View</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 3. APPLICATION HISTORY VIEW -->
    <div v-else-if="tab === 'history'">
      <div class="card glass-card border-0 p-3 mb-4">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="font-outfit mb-0">Application History</h5>
          <button 
            @click="handleExportCSV" 
            :disabled="exportingCsv || applications.length === 0" 
            class="btn btn-outline-primary btn-sm rounded-pill px-3"
          >
            <span v-if="exportingCsv" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
            <i v-else class="bi bi-file-earmark-spreadsheet me-1"></i>
            Export CSV
          </button>
        </div>
        
        <div v-if="applications.length === 0" class="text-muted text-center py-4 small">
          You haven't applied to any placement drives yet.
        </div>
        
        <div v-else class="table-responsive">
          <table class="table table-hover align-middle small">
            <thead>
              <tr>
                <th>Job Title</th>
                <th>Company</th>
                <th>Applied Date</th>
                <th>Status</th>
                <th>Remarks / Feedback</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="app in applications" :key="app.id">
                <td class="fw-semibold">{{ app.job_title }}</td>
                <td>{{ app.company_name }}</td>
                <td>{{ new Date(app.application_date).toLocaleDateString() }}</td>
                <td>
                  <span :class="'badge badge-' + app.status + ' text-uppercase px-2 py-1'">
                    {{ app.status }}
                  </span>
                </td>
                <td>
                  <span class="text-secondary italic">{{ app.remark || 'Under Review' }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ATS Matcher Modal (Glassmorphic) -->
    <div v-if="atsModalOpen && selectedDriveForAts" class="modal-backdrop-custom fade-in-el" @click.self="closeAtsChecker">
      <div class="modal-content-custom glass-card p-4">
        <div class="d-flex justify-content-between align-items-start mb-3 border-bottom pb-2">
          <div>
            <span class="badge bg-info text-dark text-uppercase mb-1">ATS Scanner</span>
            <h4 class="font-outfit text-dark mb-0">{{ selectedDriveForAts.job_title }}</h4>
            <p class="text-muted small mb-0">{{ selectedDriveForAts.company_name }}</p>
          </div>
          <button type="button" @click="closeAtsChecker" class="btn-close" aria-label="Close"></button>
        </div>
        
        <div v-if="atsLoading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="text-secondary mt-3 mb-0">Analyzing resume content against job description...</p>
        </div>
        
        <div v-else-if="atsResult" class="modal-body-custom">
          <!-- Circular compatibility score -->
          <div class="d-flex flex-column align-items-center mb-4 text-center">
            <div class="score-circle-wrapper mb-2" :style="getScoreCircleStyle(atsResult.score)">
              <div class="score-inner">
                <span class="score-number font-outfit">{{ atsResult.score }}%</span>
                <span class="score-label text-uppercase">Match Score</span>
              </div>
            </div>
            <div class="fw-semibold text-dark">{{ getScoreFeedback(atsResult.score) }}</div>
          </div>
          
          <div class="row g-3">
            <div class="col-md-6">
              <div class="card bg-success-light border-0 p-3 h-100 rounded-3">
                <h6 class="fw-bold text-success mb-2"><i class="bi bi-check-circle-fill me-1"></i>Matched Skills</h6>
                <div v-if="atsResult.matched_skills.length === 0" class="text-muted small">
                  No overlapping skills matched.
                </div>
                <div v-else class="d-flex flex-wrap gap-1 mt-2">
                  <span v-for="skill in atsResult.matched_skills" :key="skill" class="badge bg-success-badge text-success px-2 py-1">
                    {{ skill }}
                  </span>
                </div>
              </div>
            </div>
            
            <div class="col-md-6">
              <div class="card bg-danger-light border-0 p-3 h-100 rounded-3">
                <h6 class="fw-bold text-danger mb-2"><i class="bi bi-exclamation-triangle-fill me-1"></i>Missing Skills</h6>
                <div v-if="atsResult.missing_skills.length === 0" class="text-muted small">
                  Perfect match! No missing skills found.
                </div>
                <div v-else class="d-flex flex-wrap gap-1 mt-2">
                  <span v-for="skill in atsResult.missing_skills" :key="skill" class="badge bg-danger-badge text-danger px-2 py-1">
                    {{ skill }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="mt-4 pt-3 border-top text-center">
            <p class="text-secondary small mb-0">
              <i class="bi bi-info-circle me-1"></i>
              Tip: Incorporate missing keywords into your resume to improve your ATS match rate.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-dropzone {
  transition: all 0.3s ease;
  border-color: #cbd5e1 !important;
}
.upload-dropzone:hover {
  border-color: var(--primary-color) !important;
  background-color: #f1f5f9 !important;
}

/* Custom Modal Backdrop with blur */
.modal-backdrop-custom {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
  padding: 1rem;
}

/* Modal Content Card */
.modal-content-custom {
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
  border-radius: 1.25rem;
  max-width: 550px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Circular Score Circle styling */
.score-circle-wrapper {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  background: conic-gradient(var(--score-color, #3b82f6) calc(var(--score-percent, 0) * 1%), #e2e8f0 0);
  transition: all 0.5s ease-in-out;
}
.score-inner {
  width: 104px;
  height: 104px;
  background: white;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.06);
}
.score-number {
  font-size: 1.75rem;
  font-weight: 800;
  color: #1e293b;
  line-height: 1;
}
.score-label {
  font-size: 0.6rem;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.05em;
  margin-top: 2px;
}

/* Customized colors for match boxes */
.bg-success-light {
  background-color: #f0fdf4 !important;
}
.bg-success-badge {
  background-color: #dcfce7 !important;
  color: #166534 !important;
}
.bg-danger-light {
  background-color: #fef2f2 !important;
}
.bg-danger-badge {
  background-color: #fee2e2 !important;
  color: #991b1b !important;
}
</style>
