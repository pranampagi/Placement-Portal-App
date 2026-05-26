<script setup>
import { ref } from 'vue'

const emit = defineEmits(['register-success', 'switch-view'])

const role = ref('student')
const username = ref('')
const password = ref('')
const name = ref('')
const email = ref('')
const branch = ref('Computer Science')
const cgpa = ref('')
const graduationYear = ref(new Date().getFullYear())
const hrContact = ref('')
const website = ref('')
const errorMsg = ref('')

const onSubmit = async () => {
  errorMsg.value = ''
  try {
    const payload = {
      username: username.value,
      password: password.value,
      role: role.value
    }
    
    if (role.value === 'student') {
      payload.name = name.value
      payload.email = email.value
      payload.branch = branch.value
      payload.cgpa = cgpa.value
      payload.graduation_year = graduationYear.value
    } else {
      payload.name = name.value
      payload.hr_contact = hrContact.value
      payload.website = website.value
    }
    
    const res = await window.axios.post('/api/auth/register', payload)
    if (res.data.status === 'success') {
      emit('register-success', res.data.message)
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Registration failed. Please check inputs.'
  }
}
</script>

<template>
  <div class="card glass-card p-4 m-3 fade-in-el" style="width: 100%; max-width: 500px;">
    <div class="text-center mb-4">
      <i class="bi bi-person-plus text-primary" style="font-size: 3rem;"></i>
      <h2 class="mt-2 font-outfit">Create Account</h2>
      <p class="text-muted">Register as a Student or Company Profile</p>
    </div>
    
    <div v-if="errorMsg" class="alert alert-danger p-2 small">{{ errorMsg }}</div>
    
    <form @submit.prevent="onSubmit">
      <div class="row mb-3">
        <div class="col">
          <label class="form-label small fw-semibold">I am registering as a:</label>
          <select v-model="role" class="form-select">
            <option value="student">Student</option>
            <option value="company">Company</option>
          </select>
        </div>
      </div>
      
      <div class="row">
        <div class="col-md-6 mb-3">
          <label class="form-label small fw-semibold">Username</label>
          <input type="text" v-model="username" class="form-control" required placeholder="Pick a username">
        </div>
        <div class="col-md-6 mb-3">
          <label class="form-label small fw-semibold">Password</label>
          <input type="password" v-model="password" class="form-control" required placeholder="Choose password">
        </div>
      </div>
      
      <!-- Student Specific Fields -->
      <div v-if="role === 'student'">
        <div class="mb-3">
          <label class="form-label small fw-semibold">Full Name</label>
          <input type="text" v-model="name" class="form-control" required placeholder="John Doe">
        </div>
        <div class="mb-3">
          <label class="form-label small fw-semibold">Email Address</label>
          <input type="email" v-model="email" class="form-control" required placeholder="john@institute.edu">
        </div>
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label small fw-semibold">Branch / Dept</label>
            <input type="text" v-model="branch" class="form-control" required placeholder="Computer Science">
          </div>
          <div class="col-md-3 mb-3">
            <label class="form-label small fw-semibold">CGPA</label>
            <input type="number" step="0.01" v-model="cgpa" class="form-control" required placeholder="8.5">
          </div>
          <div class="col-md-3 mb-3">
            <label class="form-label small fw-semibold">Grad Year</label>
            <input type="number" v-model="graduationYear" class="form-control" required>
          </div>
        </div>
      </div>
      
      <!-- Company Specific Fields -->
      <div v-if="role === 'company'">
        <div class="mb-3">
          <label class="form-label small fw-semibold">Company Name</label>
          <input type="text" v-model="name" class="form-control" required placeholder="Google Inc.">
        </div>
        <div class="mb-3">
          <label class="form-label small fw-semibold">HR Contact Number</label>
          <input type="text" v-model="hrContact" class="form-control" required placeholder="+91 99999 88888">
        </div>
        <div class="mb-3">
          <label class="form-label small fw-semibold">Website URL</label>
          <input type="url" v-model="website" class="form-control" required placeholder="https://careers.google.com">
        </div>
      </div>
      
      <button type="submit" class="btn btn-primary w-100 mt-2">Register Profile</button>
    </form>
    
    <div class="text-center mt-4">
      <p class="small text-muted mb-0">Already have an account? 
        <a href="#" @click.prevent="emit('switch-view', 'login')" class="text-primary fw-semibold text-decoration-none">Sign in here</a>
      </p>
    </div>
  </div>
</template>
