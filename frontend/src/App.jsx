import React, { useState } from 'react'
import VideoUploader from './components/VideoUploader.jsx'
import Dashboard from './components/Dashboard.jsx'
import Fingerprint from './components/Fingerprint.jsx'
import Scrape from './components/Scrape.jsx'
import FingerprintScraped from './components/FingerprintScraped.jsx'
import { useAuth } from './context/AuthContext'
import AuthPage from './components/AuthPage'

const STEPS = [
  { key: 'upload',    label: '1 · Upload' },
  { key: 'dashboard', label: '2-6· Dashboard' },
  { key: 'fingerprint', label: '2· Fingerprint' },
  { key: 'scrape', label: '3· Scrape' },
  { key: 'fingerprintscraped', label: '4· FingerprintScraped' },
]

export default function App() {
  const { user, logout } = useAuth()
  const [tab, setTab] = useState('upload')

  if (!user) return <AuthPage />

  return (
    <div style={{ minHeight: '100vh', background: '#0d1117', padding: '40px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <div style={{ display: 'inline-block', background: '#161b22', border: '1px solid #30363d', color: '#58a6ff', fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', padding: '4px 12px', borderRadius: 20, marginBottom: 14 }}>
          Digital Asset Protection
        </div>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f0f6fc', marginBottom: 8, letterSpacing: '-0.02em' }}>
          Sports Video Fingerprint System
        </h1>
        <p style={{ fontSize: 14, color: '#8b949e' }}>
          Upload · Watermark · Fingerprint · Scrape · Match · Flag
        </p>

      {/* 👤 User info + logout */}
        <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
          <span style={{ color: '#8b949e', fontSize: 13 }}>👤 {user.username}</span>
          <button onClick={logout} style={{
            padding: '4px 12px', borderRadius: 6, border: '1px solid #30363d',
            background: 'transparent', color: '#f85149', fontSize: 12, cursor: 'pointer'
          }}>Logout</button>
        </div>
      </div>

      {/* Tab switcher */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 32, background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 4 }}>
        {STEPS.map(s => (
          <button key={s.key} onClick={() => setTab(s.key)} style={{
            padding: '8px 20px', borderRadius: 7, border: 'none',
            background: tab === s.key ? '#238636' : 'transparent',
            color:      tab === s.key ? '#ffffff' : '#8b949e',
            fontWeight: tab === s.key ? 600 : 400,
            fontSize: 13, cursor: 'pointer', transition: 'all 0.15s',
          }}>
            {s.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {tab === 'upload'    && <VideoUploader />}
      {tab === 'dashboard' && <Dashboard />}
      {tab === 'fingerprint' && <Fingerprint />}
      {tab === 'scrape' && <Scrape />}
      {tab === 'fingerprintscraped' && <FingerprintScraped />}
    </div>
  )
}