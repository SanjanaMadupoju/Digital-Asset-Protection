import React from 'react'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-brand">
        <div className="brand-icon">🛡️</div>
        <span className="brand-name" style={{ fontSize: 14 }}>SportGuard</span>
      </div>
      <p className="footer-text">
        AI-powered sports media protection · Built with Google Cloud + Firebase
      </p>
      <p className="footer-text">© 2024 SportGuard</p>
    </footer>
  )
}