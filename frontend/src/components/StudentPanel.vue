<script setup>
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
</script>

<template>
  <div class="container-fluid fade-in-el">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="h3 font-outfit mb-0">Student Dashboard</h1>
    </div>
    
    <div class="alert alert-info">
      <i class="bi bi-info-circle-fill me-2"></i>Welcome, {{ user.username }}. The student dashboard, profile, application eligibility forms, and ATS matches will be integrated next.
    </div>
  </div>
</template>
