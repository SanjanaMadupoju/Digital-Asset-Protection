import React from 'react'
import { useTheme } from '../../context/ThemeContext'

export default function Navbar({ currentPage, onNavigate }) {
  const { theme, toggleTheme } = useTheme()

  const NAV_LINKS = [
    { label: 'Home',         anchor: 'home'        },
    { label: 'Features',     anchor: 'features'    },
    { label: 'How it works', anchor: 'how-it-works' },
  ]

  return (
    <nav className="navbar">
      <div className="navbar-brand" onClick={() => onNavigate('home')}>
        <div className="brand-icon">🛡️</div>
        <span className="brand-name">SportGuard</span>
      </div>

      <div className="navbar-links">
        {currentPage === 'home' ? (
          NAV_LINKS.map(l => (
            <a
              key={l.label}
              className="nav-link"
              href={`#${l.anchor}`}
            >
              {l.label}
            </a>
          ))
        ) : (
          <span
            className="nav-link btn btn-primary btn-sm"
            onClick={() => onNavigate('home')}
            style={{ color: "white" }}
          >
            ← Back to home
          </span>
        )}
      </div>

      <div className="navbar-right">
        {/* Theme toggle */}
        <button
          className="theme-toggle"
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          <div className="theme-toggle-knob">
            {theme === 'dark' ? '🌙' : '☀️'}
          </div>
        </button>

        {currentPage === 'home' && (
          <button
            className="btn btn-primary btn-sm"
            onClick={() => onNavigate('upload')}
          >
            Get started
          </button>
        )}
      </div>
    </nav>
  )
}