import React from 'react'
import { useTheme } from '../../context/ThemeContext'

const STEPS = [
  { key: 'upload',             icon: '📤', label: 'Upload',           sub: 'Step 1' },
  { key: 'fingerprint',        icon: '🧠', label: 'Fingerprint',      sub: 'Step 2' },
  { key: 'watermarked',        icon: '🛡️', label: 'Watermarked video', sub: 'Step 2b' },
  { key: 'scrape',             icon: '🌐', label: 'Scrape',            sub: 'Step 3' },
  { key: 'fingerprintscraped', icon: '🔍', label: 'Match scraped',     sub: 'Step 4' },
  { key: 'dashboard',          icon: '📊', label: 'Dashboard',         sub: 'Steps 5–6' },
]

export default function Sidebar({ currentPage, onNavigate }) {
  const { theme, toggleTheme } = useTheme()

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand" onClick={() => onNavigate('home')}>
        <div className="brand-icon">🛡️</div>
        <span className="brand-name">SportGuard</span>
      </div>

      {/* Nav steps */}
      <nav className="sidebar-nav">
        <p className="sidebar-section-label">Pipeline</p>
        {STEPS.map(step => (
          <button
            key={step.key}
            className={`sidebar-item ${currentPage === step.key ? 'active' : ''}`}
            onClick={() => onNavigate(step.key)}
          >
            <div className="sidebar-item-icon">{step.icon}</div>
            <div className="sidebar-item-text">
              <span className="sidebar-item-label">{step.label}</span>
              <span className="sidebar-item-sub">{step.sub}</span>
            </div>
            {currentPage === step.key && <div className="sidebar-active-bar" />}
          </button>
        ))}
      </nav>

      {/* Footer: home + theme toggle */}
      <div className="sidebar-footer">
        <button className="sidebar-home-btn" onClick={() => onNavigate('home')}>
          ← Back to home
        </button>
        <div className="sidebar-theme-row">
          <span className="sidebar-theme-label">
            {theme === 'dark' ? '🌙 Dark' : '☀️ Light'}
          </span>
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            title="Toggle theme"
          >
            <div className="theme-toggle-knob">
              {theme === 'dark' ? '🌙' : '☀️'}
            </div>
          </button>
        </div>
      </div>
    </aside>
  )
}