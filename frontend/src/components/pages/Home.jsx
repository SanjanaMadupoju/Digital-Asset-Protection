import React from 'react'
import HeroSection from '../sections/HeroSection'
import FeaturesSection from '../sections/FeaturesSection'
import HowItWorksSection from '../sections/HowItWorksSection'

export default function Home({ onGetStarted, onDashboard }) {
  return (
    <main id="home">
      {/* Star field background */}
      <div className="star-field" />

      {/* Hero */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        <HeroSection onGetStarted={onGetStarted} onDashboard={onDashboard} />
      </div>

      {/* Features */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        <FeaturesSection />
      </div>

      {/* How it works */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        <HowItWorksSection />
      </div>

      {/* CTA banner */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        <div className="container">
          <div className="cta-banner">
            <h2 className="cta-title">Ready to protect your content?</h2>
            <p className="cta-sub">
              Upload your first video and generate your AI fingerprint in under 2 minutes.
            </p>
            <button
              className="btn btn-primary btn-lg"
              onClick={onGetStarted}
            >
              Get started
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}