<script setup>
import { ref } from 'vue'

const props = defineProps({
  successMsg: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['login-success', 'switch-view'])

const username = ref('')
const password = ref('')
const errorMsg = ref('')
const successText = ref(props.successMsg)

const onSubmit = async () => {
  errorMsg.value = ''
  successText.value = ''
  try {
    const res = await window.axios.post('/api/auth/login', {
      username: username.value,
      password: password.value
    })
    if (res.data.status === 'success') {
      emit('login-success', res.data.user)
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'Login failed. Please try again.'
  }
}
</script>

<template>
  <div class="card glass-card p-4 m-3 fade-in-el" style="width: 100%; max-width: 420px;">
    <div class="text-center mb-4">
      <i class="bi bi-mortarboard text-primary" style="font-size: 3rem;"></i>
      <h2 class="mt-2 font-outfit">Placement Portal</h2>
      <p class="text-muted">Sign in to your account</p>
    </div>
    
    <div v-if="errorMsg" class="alert alert-danger p-2 small">{{ errorMsg }}</div>
    <div v-if="successText" class="alert alert-success p-2 small">{{ successText }}</div>
    
    <form @submit.prevent="onSubmit">
      <div class="mb-3">
        <label class="form-label small fw-semibold">Username</label>
        <input type="text" v-model="username" class="form-control" placeholder="Enter username" required>
      </div>
      <div class="mb-3">
        <label class="form-label small fw-semibold">Password</label>
        <input type="password" v-model="password" class="form-control" placeholder="Enter password" required>
      </div>
      <button type="submit" class="btn btn-primary w-100 mt-2">Log In</button>
    </form>
    
    <div class="text-center mt-4">
      <p class="small text-muted mb-0">Don't have an account? 
        <a href="#" @click.prevent="emit('switch-view', 'register')" class="text-primary fw-semibold text-decoration-none">Register here</a>
      </p>
    </div>
  </div>
</template>
