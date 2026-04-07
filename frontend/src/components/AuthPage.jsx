// src/components/AuthPage.jsx
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

const API = 'http://localhost:8000/api/auth'

const inputStyle = {
  width: '100%', padding: '10px 14px', borderRadius: 8,
  border: '1px solid #30363d', background: '#0d1117',
  color: '#f0f6fc', fontSize: 14, outline: 'none', boxSizing: 'border-box',
}
const btnStyle = {
  width: '100%', padding: '10px', borderRadius: 8, border: 'none',
  background: '#238636', color: '#fff', fontWeight: 600,
  fontSize: 14, cursor: 'pointer', marginTop: 8,
}

export default function AuthPage() {
  const { login } = useAuth()
  const [mode, setMode] = useState('login')   // 'login' | 'register'
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handle = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const submit = async () => {
    setError('')
    setLoading(true)
    try {
      const endpoint = mode === 'login' ? '/login' : '/register'
      const body = mode === 'login'
        ? { email: form.email, password: form.password }
        : { username: form.username, email: form.email, password: form.password }

      const res = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Something went wrong')

      if (mode === 'register') {
        setMode('login')
        setError('✅ Registered! Please log in.')
      } else {
        login(data.access_token, data.username)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0d1117', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 12, padding: 32, width: 360 }}>
        
        {/* Header */}
        <h2 style={{ color: '#f0f6fc', textAlign: 'center', marginBottom: 4 }}>
          {mode === 'login' ? 'Sign In' : 'Create Account'}
        </h2>
        <p style={{ color: '#8b949e', textAlign: 'center', fontSize: 13, marginBottom: 24 }}>
          Sports Video Fingerprint System
        </p>

        {/* Fields */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {mode === 'register' && (
            <input style={inputStyle} name="username" placeholder="Username"
              value={form.username} onChange={handle} />
          )}
          <input style={inputStyle} name="email" placeholder="Email" type="email"
            value={form.email} onChange={handle} />
          <input style={inputStyle} name="password" placeholder="Password" type="password"
            value={form.password} onChange={handle} />
        </div>

        {error && (
          <p style={{ color: error.startsWith('✅') ? '#3fb950' : '#f85149', fontSize: 13, marginTop: 12 }}>
            {error}
          </p>
        )}

        <button style={btnStyle} onClick={submit} disabled={loading}>
          {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Register'}
        </button>

        {/* Toggle */}
        <p style={{ color: '#8b949e', textAlign: 'center', fontSize: 13, marginTop: 16 }}>
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <span style={{ color: '#58a6ff', cursor: 'pointer' }}
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>
            {mode === 'login' ? 'Register' : 'Sign In'}
          </span>
        </p>
      </div>
    </div>
  )
}