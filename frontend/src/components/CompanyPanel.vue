<script setup>
import { ref, onMounted } from 'vue'

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

// Views & Detail States
const viewMode = ref('dashboard') // 'dashboard', 'create-drive', 'drive-details', 'application-details'
const selectedDrive = ref(null)
const selectedApplication = ref(null)

// Data states
const companyDetails = ref({ name: '', hr_contact: '', website: '', approval_status: '' })
const upcomingDrives = ref([])
const closedDrives = ref([])
const driveApplications = ref([])

const statusUpdateForm = ref({
  status: 'applied',
  remark: ''
})

// Form states
const newDrive = ref({
  job_title: '',
  job_description: '',
  eligibility_branch: 'All',
  eligibility_cgpa: '',
  eligibility_year: new Date().getFullYear(),
  salary: '',
  location: '',
  deadline: ''
})

const errorMsg = ref('')
const successMsg = ref('')

const fetchCompanyProfileAndDrives = async () => {
  try {
    const profileRes = await window.axios.get('/api/company/profile')
    if (profileRes.data.status === 'success') {
      companyDetails.value = profileRes.data.company
    }
    
    const drivesRes = await window.axios.get('/api/company/drives')
    if (drivesRes.data.status === 'success') {
      upcomingDrives.value = drivesRes.data.upcoming_drives
      closedDrives.value = drivesRes.data.closed_drives
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Failed to load company profile.'
  }
}

const handleCreateDrive = async () => {
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const payload = { ...newDrive.value }
    // Convert deadline to ISO string format if needed
    if (payload.deadline) {
      payload.deadline = new Date(payload.deadline).toISOString()
    }
    const res = await window.axios.post('/api/company/drives', payload)
    if (res.data.status === 'success') {
      successMsg.value = res.data.message
      viewMode.value = 'dashboard'
      // Reset form
      newDrive.value = {
        job_title: '',
        job_description: '',
        eligibility_branch: 'All',
        eligibility_cgpa: '',
        eligibility_year: new Date().getFullYear(),
        salary: '',
        location: '',
        deadline: ''
      }
      fetchCompanyProfileAndDrives()
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Failed to create drive.'
  }
}

const showDriveDetails = async (drive) => {
  selectedDrive.value = drive
  viewMode.value = 'drive-details'
  driveApplications.value = []
  try {
    const res = await window.axios.get(`/api/company/drives/${drive.id}/applications`)
    if (res.data.status === 'success') {
      driveApplications.value = res.data.applications
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Failed to load applications for this drive.'
  }
}

const viewApplicationDetails = (app) => {
  selectedApplication.value = app
  statusUpdateForm.value.status = app.status
  statusUpdateForm.value.remark = app.remark || ''
  viewMode.value = 'application-details'
}

const openResume = (filename) => {
  if (!filename) return
  const url = `${window.axios.defaults.baseURL}/static/uploads/${filename}`
  window.open(url, '_blank')
}

const goBackToDriveDetails = () => {
  viewMode.value = 'drive-details'
}

const handleUpdateApplicationStatus = async () => {
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const res = await window.axios.post(`/api/company/applications/${selectedApplication.value.id}/status`, {
      status: statusUpdateForm.value.status,
      remark: statusUpdateForm.value.remark
    })
    if (res.data.status === 'success') {
      successMsg.value = res.data.message
      selectedApplication.value = res.data.application
      if (selectedDrive.value) {
        // Refresh drive applications list
        const appsRes = await window.axios.get(`/api/company/drives/${selectedDrive.value.id}/applications`)
        if (appsRes.data.status === 'success') {
          driveApplications.value = appsRes.data.applications
        }
      }
      viewMode.value = 'drive-details'
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Failed to update application status.'
  }
}

onMounted(() => {
  fetchCompanyProfileAndDrives()
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

    <!-- 1. CREATE DRIVE FORM VIEW -->
    <div v-if="viewMode === 'create-drive'" class="card glass-card p-4 border-0 mb-4">
      <div class="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
        <div>
          <h2 class="font-outfit text-dark mb-0">Create Placement Drive</h2>
          <p class="text-muted mb-0">Launch a new job posting for students</p>
        </div>
      </div>

      <form @submit.prevent="handleCreateDrive">
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label small fw-semibold">Job Title</label>
            <input type="text" v-model="newDrive.job_title" class="form-control" required placeholder="e.g. Software Engineer">
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label small fw-semibold">Location</label>
            <input type="text" v-model="newDrive.location" class="form-control" required placeholder="e.g. Chennai / Remote">
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label small fw-semibold">Job Description</label>
          <textarea v-model="newDrive.job_description" class="form-control" rows="5" required placeholder="Describe the role, responsibilities, and required skillsets..."></textarea>
        </div>

        <div class="row">
          <div class="col-md-4 mb-3">
            <label class="form-label small fw-semibold">Eligible Branches</label>
            <input type="text" v-model="newDrive.eligibility_branch" class="form-control" required placeholder="e.g. CSE, ECE or All">
          </div>
          <div class="col-md-4 mb-3">
            <label class="form-label small fw-semibold">Min CGPA Requirement</label>
            <input type="number" step="0.01" v-model="newDrive.eligibility_cgpa" class="form-control" required placeholder="e.g. 7.5">
          </div>
          <div class="col-md-4 mb-3">
            <label class="form-label small fw-semibold">Target Graduation Year</label>
            <input type="number" v-model="newDrive.eligibility_year" class="form-control" required>
          </div>
        </div>

        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label small fw-semibold">Salary Package (LPA)</label>
            <input type="number" v-model="newDrive.salary" class="form-control" required placeholder="e.g. 600000">
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label small fw-semibold">Application Deadline</label>
            <input type="datetime-local" v-model="newDrive.deadline" class="form-control" required>
          </div>
        </div>

        <div class="d-flex justify-content-end gap-3 mt-4 pt-3 border-top">
          <button type="button" @click="viewMode = 'dashboard'" class="btn btn-outline-secondary px-4 rounded-pill">Cancel</button>
          <button type="submit" class="btn btn-primary px-4 rounded-pill">Create & Submit</button>
        </div>
      </form>
    </div>

    <!-- 2. DRIVE DETAILS SUBVIEW -->
    <div v-else-if="viewMode === 'drive-details' && selectedDrive" class="card glass-card p-4 border-0 mb-4">
      <div class="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
        <div>
          <span class="badge bg-primary text-uppercase mb-2">Placement Event</span>
          <h2 class="font-outfit text-dark mb-0">{{ selectedDrive.job_title }}</h2>
          <p class="text-muted mb-0"><i class="bi bi-geo-alt me-1"></i>{{ selectedDrive.location }}</p>
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
          <p class="text-secondary style-desc" style="white-space: pre-line;">{{ selectedDrive.job_description }}</p>
        </div>
        <div class="col-md-4">
          <div class="card bg-light border-0 p-3 rounded-3">
            <h6 class="font-outfit fw-bold text-secondary mb-3">Specifications</h6>
            
            <div class="mb-2 small">
              <span class="text-muted">Salary Package:</span>
              <div class="fw-semibold">₹ {{ selectedDrive.salary.toLocaleString() }} LPA</div>
            </div>

            <div class="mb-2 small">
              <span class="text-muted">Eligible Branch:</span>
              <div class="fw-semibold">{{ selectedDrive.eligibility_branch }}</div>
            </div>

            <div class="mb-2 small">
              <span class="text-muted">Min CGPA Required:</span>
              <div class="fw-semibold">{{ selectedDrive.eligibility_cgpa }}</div>
            </div>

            <div class="mb-2 small">
              <span class="text-muted">Graduation Year:</span>
              <div class="fw-semibold">{{ selectedDrive.eligibility_year }}</div>
            </div>

            <div class="small">
              <span class="text-muted">Apply Deadline:</span>
              <div class="fw-semibold text-danger">{{ new Date(selectedDrive.deadline).toLocaleString() }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Received Applications List -->
      <div class="card bg-white border-0 shadow-sm p-4 mb-4 rounded-3" v-if="selectedDrive.status === 'approved'">
        <h5 class="fw-semibold font-outfit mb-3">Received Applications</h5>
        <div v-if="driveApplications.length === 0" class="text-muted text-center py-4 small">
          No student applications received yet for this placement drive.
        </div>
        <div v-else class="table-responsive">
          <table class="table table-hover align-middle small">
            <thead>
              <tr>
                <th>Student Name</th>
                <th>Branch</th>
                <th>CGPA</th>
                <th>Graduation Year</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="app in driveApplications" :key="app.id">
                <td class="fw-semibold">{{ app.student_name }}</td>
                <td>{{ app.student_branch }}</td>
                <td>{{ app.student_cgpa }}</td>
                <td>{{ app.student_year }}</td>
                <td>
                  <span :class="'badge badge-' + app.status + ' text-uppercase'">
                    {{ app.status }}
                  </span>
                </td>
                <td>
                  <button @click="viewApplicationDetails(app)" class="btn btn-outline-primary btn-sm rounded px-2">
                    Review Application
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-else class="alert alert-info mb-4 small">
        <i class="bi bi-info-circle-fill me-2"></i>Applications list will be available once the drive is approved by the Admin.
      </div>

      <div class="d-flex justify-content-start">
        <button @click="viewMode = 'dashboard'" class="btn btn-outline-secondary px-4 rounded-pill">
          <i class="bi bi-arrow-left me-2"></i>Go Back
        </button>
      </div>
    </div>

    <!-- 4. STUDENT APPLICATION DETAILS & REVIEW VIEW -->
    <div v-else-if="viewMode === 'application-details' && selectedApplication" class="card glass-card p-4 border-0 mb-4">
      <div class="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
        <div>
          <span class="badge bg-info text-dark text-uppercase mb-2">Review Student Application</span>
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
        <!-- Academic Summary -->
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

        <!-- Drive Details -->
        <div class="col-md-6">
          <div class="card bg-light border-0 p-3 h-100 rounded-3">
            <h5 class="font-outfit fw-bold text-secondary mb-3">Drive Details</h5>
            <div class="row g-3">
              <div class="col-12 small">
                <span class="text-muted d-block">Job Title:</span>
                <span class="fw-semibold text-primary fs-6">{{ selectedApplication.job_title }}</span>
              </div>
              <div class="col-12 small">
                <span class="text-muted d-block">Status:</span>
                <span class="fw-semibold text-uppercase text-secondary">{{ selectedApplication.status }}</span>
              </div>
              <div class="col-12 small" v-if="selectedApplication.remark">
                <span class="text-muted d-block">Remarks:</span>
                <span class="text-secondary italic">{{ selectedApplication.remark }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Candidate Resume Section -->
      <div class="mb-4" v-if="selectedApplication.student_resume">
        <h5 class="font-outfit fw-bold mb-3">Candidate Resume</h5>
        <div class="d-flex align-items-center gap-3 bg-white p-3 rounded-3 border">
          <i class="bi bi-file-earmark-pdf-fill text-danger fs-1"></i>
          <div>
            <div class="fw-semibold text-dark">{{ selectedApplication.student_resume }}</div>
            <div class="small text-muted">Uploaded PDF Document</div>
          </div>
          <button @click="openResume(selectedApplication.student_resume)" class="btn btn-primary btn-sm ms-auto px-3 rounded-pill">
            <i class="bi bi-eye me-1"></i>View Resume
          </button>
        </div>
      </div>
      <div v-else class="alert alert-warning mb-4">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>No resume uploaded by this candidate.
      </div>

      <!-- Application Selection Update Form -->
      <div class="card bg-light border-0 p-4 mb-4 rounded-3">
        <h5 class="font-outfit fw-bold text-dark mb-3">Update Application Status</h5>
        <form @submit.prevent="handleUpdateApplicationStatus">
          <div class="row">
            <div class="col-md-6 mb-3">
              <label class="form-label small fw-semibold">Selection Status</label>
              <select v-model="statusUpdateForm.status" class="form-select" required>
                <option value="applied">Applied (Under Review)</option>
                <option value="shortlisted">Shortlisted</option>
                <option value="selected">Selected</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            <div class="col-md-12 mb-3">
              <label class="form-label small fw-semibold">Remarks / Feedback (Optional)</label>
              <textarea v-model="statusUpdateForm.remark" class="form-control" rows="3" placeholder="Provide feedback or next steps for the candidate..."></textarea>
            </div>
          </div>
          <div class="d-flex justify-content-end gap-3 pt-3 border-top">
            <button type="button" @click="goBackToDriveDetails" class="btn btn-outline-secondary px-4 rounded-pill">Cancel</button>
            <button type="submit" class="btn btn-success px-4 rounded-pill">Update Status</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 3. MAIN DASHBOARD VIEW -->
    <div v-else>
      <!-- Company Profile Details Summary -->
      <div class="card glass-card border-0 p-4 mb-4">
        <div class="row align-items-center">
          <div class="col-md-8">
            <span class="badge bg-primary text-uppercase mb-2">Company Overview</span>
            <h2 class="font-outfit mb-1">{{ companyDetails.name }}</h2>
            <div class="d-flex align-items-center gap-3 text-secondary flex-wrap mt-2">
              <span><i class="bi bi-telephone-fill me-1 text-primary"></i>HR: {{ companyDetails.hr_contact }}</span>
              <span><i class="bi bi-globe me-1 text-primary"></i><a :href="companyDetails.website" target="_blank" class="text-decoration-none">{{ companyDetails.website }}</a></span>
            </div>
          </div>
          <div class="col-md-4 text-md-end mt-3 mt-md-0">
            <span v-if="companyDetails.approval_status === 'pending'" class="badge bg-warning p-2 text-uppercase fs-6">
              Awaiting Admin Approval
            </span>
            <span v-else-if="companyDetails.approval_status === 'approved'" class="badge bg-success p-2 text-uppercase fs-6">
              Approved Organization
            </span>
            <span v-else class="badge bg-danger p-2 text-uppercase fs-6">
              Rejected Organisation
            </span>
          </div>
        </div>
      </div>

      <!-- Drives Tables -->
      <div class="row g-4">
        <!-- Upcoming Drives Table -->
        <div class="col-md-8">
          <div class="card glass-card border-0 p-3 h-100">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h5 class="font-outfit mb-0">Upcoming Drives</h5>
              <button 
                @click="viewMode = 'create-drive'" 
                :disabled="companyDetails.approval_status !== 'approved'" 
                class="btn btn-primary btn-sm rounded-pill px-3"
                title="Create a placement drive (Requires account approval)"
              >
                <i class="bi bi-plus-lg me-1"></i>Create Drive
              </button>
            </div>

            <div v-if="upcomingDrives.length === 0" class="text-muted text-center py-4 small">
              No upcoming drives created. Click 'Create Drive' to launch one.
            </div>
            
            <div v-else class="table-responsive">
              <table class="table table-hover align-middle small">
                <thead>
                  <tr>
                    <th>Drive Title</th>
                    <th>Applicants</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="drive in upcomingDrives" :key="drive.id">
                    <td class="fw-semibold">{{ drive.job_title }}</td>
                    <td>
                      <span class="badge bg-secondary px-2 py-1">{{ drive.applicant_count }} Applicants</span>
                    </td>
                    <td>
                      <span :class="'badge bg-' + (drive.status === 'approved' ? 'success' : 'warning')">{{ drive.status }}</span>
                    </td>
                    <td>
                      <div class="btn-actions">
                        <button @click="showDriveDetails(drive)" class="btn btn-outline-primary btn-sm rounded px-2">View & Review</button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Closed Drives Table -->
        <div class="col-md-4">
          <div class="card glass-card border-0 p-3 h-100">
            <h5 class="font-outfit mb-3">Closed Drives</h5>
            
            <div v-if="closedDrives.length === 0" class="text-muted text-center py-4 small">
              No closed drives.
            </div>
            
            <div v-else class="list-group list-group-flush">
              <div v-for="drive in closedDrives" :key="drive.id" class="list-group-item bg-transparent px-0 py-2 border-bottom d-flex justify-content-between align-items-center">
                <div>
                  <h6 class="mb-0 fw-semibold">{{ drive.job_title }}</h6>
                  <div class="small text-muted">Closed: {{ new Date(drive.deadline).toLocaleDateString() }}</div>
                </div>
                <button @click="showDriveDetails(drive)" class="btn btn-outline-secondary btn-sm px-2 rounded">View</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
