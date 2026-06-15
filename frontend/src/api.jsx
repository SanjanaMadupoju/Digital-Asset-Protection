import axios from 'axios'

// In development: Vite proxy forwards /api → localhost:8000
// In production:  direct calls to Cloud Run URL
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 300000,   // 5 min timeout for long operations like fingerprinting
})

export const scrapeYoutube = payload => api.post('/api/scrape', payload)
export const runScrapedFingerprint = (videoId, limit = 5) => api.post(`/api/fingerprint-scraped/${videoId}?limit=${limit}`)
export const fetchReport = videoId => api.get(`/api/reports/${videoId}`)
export const sendAlert = (videoId, email, violationFilter = 'all') =>
  api.post(`/api/reports/${videoId}/send-email`, {
    email,
    violation_filter: violationFilter,
  })

export default api