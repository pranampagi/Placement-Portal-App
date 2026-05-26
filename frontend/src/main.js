import { createApp } from 'vue'
import App from './App.vue'

// Import Bootstrap 5 CSS & JS
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import 'bootstrap-icons/font/bootstrap-icons.css'

// Import custom styles
import './style.css'

// Import Axios & Configure Defaults
import axios from 'axios'
axios.defaults.baseURL = 'http://127.0.0.1:5000'
axios.defaults.withCredentials = true

// Attach Axios globally for easy access
window.axios = axios

createApp(App).mount('#app')
