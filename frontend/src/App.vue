<script setup>
import { ref, onMounted } from 'vue'
import Login from './components/Login.vue'
import Register from './components/Register.vue'
import Dashboard from './components/Dashboard.vue'

const loading = ref(true)
const isAuthenticated = ref(false)
const currentUser = ref(null)
const currentView = ref('login') // 'login', 'register', 'dashboard'

const errorMsg = ref('')
const successMsg = ref('')

// Load user session on mount
const checkSession = async () => {
  try {
    const res = await window.axios.get('/api/auth/me')
    if (res.data.status === 'success') {
      currentUser.value = res.data.user
      isAuthenticated.value = true
      currentView.value = 'dashboard'
    }
  } catch (err) {
    isAuthenticated.value = false
    currentUser.value = null
    currentView.value = 'login'
  } finally {
    loading.value = false
  }
}

const handleLoginSuccess = (user) => {
  currentUser.value = user
  isAuthenticated.value = true
  currentView.value = 'dashboard'
  errorMsg.value = ''
  successMsg.value = ''
}

const handleLogoutSuccess = () => {
  isAuthenticated.value = false
  currentUser.value = null
  currentView.value = 'login'
  errorMsg.value = ''
  successMsg.value = ''
}

const handleRegisterSuccess = (message) => {
  successMsg.value = message
  currentView.value = 'login'
  errorMsg.value = ''
}

onMounted(() => {
  checkSession()
})
</script>

<template>
  <div class="app-container">
    <!-- Loading Spinner -->
    <div v-if="loading" class="d-flex justify-content-center align-items-center vh-100 bg-light">
      <div class="text-center">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <h5 class="mt-3 text-secondary font-outfit">Loading Placement Portal...</h5>
      </div>
    </div>

    <!-- Main View Switcher -->
    <div v-else>
      <!-- Decoupled Auth Views -->
      <div v-if="!isAuthenticated" class="auth-wrapper d-flex align-items-center justify-content-center">
        <Login
          v-if="currentView === 'login'"
          :success-msg="successMsg"
          @login-success="handleLoginSuccess"
          @switch-view="currentView = $event"
        />
        
        <Register
          v-if="currentView === 'register'"
          @register-success="handleRegisterSuccess"
          @switch-view="currentView = $event"
        />
      </div>

      <!-- Dashboard View -->
      <Dashboard
        v-else
        :user="currentUser"
        @logout-success="handleLogoutSuccess"
      />
    </div>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
}
</style>
