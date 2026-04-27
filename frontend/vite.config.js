// import { defineConfig } from 'vite'
// import react from '@vitejs/plugin-react'

// export default defineConfig({
//   plugins: [react()],
//   server: {
//     port: 5173,
//     // Proxy means: any request to /api from React will be
//     // silently forwarded to FastAPI on port 8000
//     // So React never has to hardcode http://localhost:8000
//     proxy: {
//       '/api': {
//         target: 'https://sports-fingerprint-api-458979732981.asia-south1.run.app',
//         changeOrigin: true,
//       }
//     }
//   }
// })


import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BACKEND_URL = process.env.VITE_API_URL || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true,
      }
    }
  }
})