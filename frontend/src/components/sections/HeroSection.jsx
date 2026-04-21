import React from 'react'

const STATS = [
  { value: '99.2%', label: 'Detection accuracy' },
  { value: '<3s',   label: 'Fingerprint speed'  },
  { value: '50+',   label: 'Platforms monitored' },
  { value: '1408D', label: 'AI vector size'      },
]

export default function HeroSection({ onGetStarted, onDashboard }) {
  return (
    <>
      <div className="hero">
        <div className="hero-badge">
          <span className="badge badge-accent">AI-Powered Digital Asset Protection</span>
        </div>

        <h1 className="hero-title">
          Protect Your Sports<br />Media Instantly
        </h1>

        <p className="hero-subtitle">
          Upload your official sports content. Our AI embeds an invisible watermark,
          generates a unique fingerprint, and lets you scan 50+ platforms to detect
          unauthorized copies with evidence-grade reports.
        </p>

        <div className="hero-ctas">
          <button className="btn btn-primary btn-lg" onClick={onGetStarted}>
            Upload your video →
          </button>
          <button className="btn btn-secondary btn-lg" onClick={onDashboard}>
            View dashboard
          </button>
        </div>
      </div>

      <div className="hero-stats">
        {STATS.map(s => (
          <div key={s.label} style={{ textAlign: 'center' }}>
            <div className="stat-hero-val">{s.value}</div>
            <div className="stat-hero-label">{s.label}</div>
          </div>
        ))}
      </div>
    </>
  )
}