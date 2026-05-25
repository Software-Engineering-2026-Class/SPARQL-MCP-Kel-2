// =============================================================
// main.js — Application Entry Point
// CyberSec Search — SPARQL-MCP Frontend
// =============================================================

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index.js'
import './style.css'

// Create Vue application
const app = createApp(App)

// Register Pinia state management
app.use(createPinia())

// Register Vue Router
app.use(router)

// Mount to DOM
app.mount('#app')
