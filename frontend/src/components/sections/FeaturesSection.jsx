import React from 'react'

const FEATURES = [
  {
    icon: '🛡️',
    title: 'Invisible Watermarking',
    desc: 'Every frame of your video carries a hidden mark that proves ownership. It survives re-encoding, compression, cropping and re-uploading — completely invisible to the human eye.',
  },
  {
    icon: '🧠',
    title: 'AI Fingerprinting',
    desc: 'Google Vision AI generates a unique 1408-dimensional fingerprint vector for your video. This digital identity is stored securely and used to identify copies anywhere on the web.',
  },
  {
    icon: '🌐',
    title: 'Web-wide Detection',
    desc: 'Scan YouTube, Dailymotion, Twitter/X, Facebook and the broader web using sport-specific queries. Find where your content has been re-uploaded without permission.',
  },
  {
    icon: '⚡',
    title: 'Evidence Reports',
    desc: 'Every flagged match comes with a full evidence report — URL, platform, similarity score, watermark verification status and timestamp. Ready for legal or compliance action.',
  },
]

export default function FeaturesSection() {
  return (
    <section className="features-section" id="features">
      <div className="container">
        <div className="section-title">Everything you need to protect your sports IP</div>
        <p className="section-sub">
          Built with Google Cloud AI — enterprise-grade protection without enterprise complexity.
        </p>

        <div className="features-grid">
          {FEATURES.map(f => (
            <div key={f.title} className="feature-card">
              <div className="feature-icon-wrap">{f.icon}</div>
              <div className="feature-title">{f.title}</div>
              <p className="feature-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}