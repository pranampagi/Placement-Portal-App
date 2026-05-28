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
const viewMode = ref('dashboard') // 'dashboard', 'create-drive', 'drive-details'
const selectedDrive = ref(null)

// Data states
const companyDetails = ref({ name: '', hr_contact: '', website: '', approval_status: '' })
const upcomingDrives = ref([])
const closedDrives = ref([])

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

const showDriveDetails = (drive) => {
  selectedDrive.value = drive
  viewMode.value = 'drive-details'
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

      <div class="d-flex justify-content-start">
        <button @click="viewMode = 'dashboard'" class="btn btn-outline-secondary px-4 rounded-pill">
          <i class="bi bi-arrow-left me-2"></i>Go Back
        </button>
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
                        <button @click="showDriveDetails(drive)" class="btn btn-outline-primary btn-sm rounded px-2">view details</button>
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
                <button class="btn btn-outline-secondary btn-sm px-2 rounded">update</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
