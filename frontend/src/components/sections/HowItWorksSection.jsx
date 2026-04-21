import React from 'react'

const STEPS = [
  {
    number: '01',
    title:  'Upload your sports video',
    desc:   'Upload any sports media file — match highlights, press conferences, exclusive interviews. Supports MP4, MOV, AVI, MKV and WebM up to 500MB.',
    tag:    'Step 1',
    tagStyle: 'badge-accent',
  },
  {
    number: '02',
    title:  'AI embeds watermark and generates fingerprint',
    desc:   'Google Vision AI processes every frame — embedding an invisible ownership mark and generating a unique 1408-dimensional fingerprint vector stored in Qdrant and Firebase.',
    tag:    'Step 2 · AI',
    tagStyle: 'badge-accent',
  },
  {
    number: '03',
    title:  'Trigger a web scan',
    desc:   'When you\'re ready, trigger a scan with your sport and keywords. The system searches YouTube, Dailymotion, Twitter/X, Facebook and Google — collecting candidate URLs.',
    tag:    'Step 3',
    tagStyle: 'badge-muted',
  },
  {
    number: '04',
    title:  'AI compares fingerprints',
    desc:   'Each candidate URL\'s frames are downloaded and fingerprinted. Cosine similarity matching compares them against your original. Watermark extraction adds a second layer of proof.',
    tag:    'Step 4 · AI',
    tagStyle: 'badge-accent',
  },
  {
    number: '05',
    title:  'Review flagged violations',
    desc:   'The dashboard shows every match ranked by confidence score with risk level — Critical, High, Medium or Low. Generate a full evidence report for any flagged video in one click.',
    tag:    'Step 5–6',
    tagStyle: 'badge-danger',
  },
]

export default function HowItWorksSection() {
  return (
    <section className="how-section" id="how-it-works">
      <div className="container">
        <div className="section-title">How it works</div>
        <p className="section-sub">
          Five steps from upload to evidence report — no technical knowledge required.
        </p>

        <div className="steps-list">
          {STEPS.map(s => (
            <div key={s.number} className="step-item">
              <div className="step-number">{s.number}</div>
              <div className="step-content-wrap">
                <div className="step-title">{s.title}</div>
                <p className="step-desc">{s.desc}</p>
                <div className="step-tag">
                  <span className={`badge ${s.tagStyle}`}>{s.tag}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}