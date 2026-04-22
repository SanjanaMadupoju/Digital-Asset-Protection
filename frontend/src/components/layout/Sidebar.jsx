import React from 'react'
import { useTheme } from '../../context/ThemeContext'

const STEPS = [
  { key: 'upload',             icon: '📤', label: 'Upload',         sub: 'Step 1' },
  { key: 'fingerprint',        icon: '🧠', label: 'Fingerprint',    sub: 'Step 2' },
  { key: 'scrape',             icon: '🌐', label: 'Scrape',         sub: 'Step 3' },
  { key: 'fingerprintscraped', icon: '🔍', label: 'Match scraped',  sub: 'Step 4' },
  { key: 'dashboard',          icon: '📊', label: 'Dashboard',      sub: 'Steps 5–6' },
]

export default function Sidebar({ currentPage, onNavigate }) {
  const { theme, toggleTheme } = useTheme()

  return (
    <aside className="sidebar">

      {/* Nav steps */}
      <nav className="sidebar-nav">
        <p className="sidebar-section-label">Pipeline</p>
        {STEPS.map((step, i) => (
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
    </aside>
  )
}