<script setup>
import { ref } from 'vue'
import AdminPanel from './AdminPanel.vue'
import CompanyPanel from './CompanyPanel.vue'
import StudentPanel from './StudentPanel.vue'

const props = defineProps({
  user: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['logout-success'])

const currentTab = ref('dashboard')

const handleLogout = async () => {
  try {
    const res = await window.axios.post('/api/auth/logout')
    if (res.data.status === 'success') {
      emit('logout-success')
    }
  } catch (err) {
    console.error("Logout failed", err)
  }
}
</script>

<template>
  <div class="dashboard-wrapper">
    <!-- Sidebar Navigation -->
    <div class="sidebar d-flex flex-column p-3">
      <div class="d-flex align-items-center gap-2 mb-4 px-2">
        <i class="bi bi-mortarboard text-primary fs-3"></i>
        <h4 class="text-white mb-0 font-outfit fs-5">PPA Portal</h4>
      </div>
      
      <div class="small text-uppercase text-secondary fw-semibold px-2 mb-2">Logged in as</div>
      <div class="px-2 mb-4 d-flex align-items-center gap-2 text-white bg-dark p-2 rounded">
        <i class="bi bi-person-circle fs-5 text-primary"></i>
        <div class="w-100 overflow-hidden">
          <div class="fw-semibold text-truncate" :title="user.username">{{ user.username }}</div>
          <div class="small text-muted text-uppercase" style="font-size: 0.75rem;">{{ user.role }}</div>
        </div>
      </div>

      <!-- Sidebar Links -->
      <ul class="nav nav-pills flex-column mb-auto">
        <li class="nav-item">
          <a href="#" class="nav-link" :class="{ active: currentTab === 'dashboard' }" @click.prevent="currentTab = 'dashboard'">
            <i class="bi bi-grid-fill"></i>
            <span>Dashboard</span>
          </a>
        </li>
        <li v-if="user.role === 'student'" class="nav-item">
          <a href="#" class="nav-link" :class="{ active: currentTab === 'profile' }" @click.prevent="currentTab = 'profile'">
            <i class="bi bi-person-bounding-box"></i>
            <span>Edit Profile</span>
          </a>
        </li>
        <li v-if="user.role === 'student'" class="nav-item">
          <a href="#" class="nav-link" :class="{ active: currentTab === 'history' }" @click.prevent="currentTab = 'history'">
            <i class="bi bi-clock-history"></i>
            <span>Application History</span>
          </a>
        </li>
      </ul>
      
      <hr class="text-secondary">
      <button @click="handleLogout" class="btn btn-outline-danger w-100 btn-sm d-flex align-items-center justify-content-center gap-2">
        <i class="bi bi-box-arrow-right"></i>
        <span>Sign Out</span>
      </button>
    </div>

    <!-- Main Content Shell -->
    <div class="main-content">
      <AdminPanel v-if="user.role === 'admin'" :user="user" :tab="currentTab" />
      <CompanyPanel v-else-if="user.role === 'company'" :user="user" :tab="currentTab" />
      <StudentPanel v-else-if="user.role === 'student'" :user="user" :tab="currentTab" />
    </div>
  </div>
</template>
