import React, { useState } from 'react'
import axios from 'axios'

function RadarViz({ active }) {
  const dots = [
    { top: '30%', left: '65%', delay: '0s' },
    { top: '60%', left: '40%', delay: '0.8s' },
    { top: '45%', left: '25%', delay: '1.4s' },
  ]
  return (
    <div className="fingerprint-viz">
      <div className="radar-container">
        <div className="radar-circle" />
        <div className="radar-circle" />
        <div className="radar-circle" />
        <div className="radar-circle" />
        {active && <div className="radar-sweep" />}
        <div className="radar-center" />
        {active && dots.map((d, i) => (
          <div key={i} className="radar-dot" style={{ top: d.top, left: d.left, animationDelay: d.delay }} />
        ))}
      </div>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8, textAlign: 'center' }}>
        {active ? 'Generating AI fingerprint...' : 'Ready to fingerprint'}
      </p>
    </div>
  )
}

export default function FingerprintPage() {
  const [videoId, setVideoId]   = useState('')
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)
  const [error, setError]       = useState(null)
  const [logs, setLogs]         = useState([])

  const addLog = msg => setLogs(l => [...l, msg])

  const run = async () => {
    if (!videoId.trim()) return
    setLoading(true); setError(null); setResult(null); setLogs([])
    addLog('Starting fingerprint pipeline...')
    addLog('Extracting frames with OpenCV...')
    addLog('Embedding invisible watermark...')
    addLog('Running Google Vision AI...')
    try {
      const res = await axios.post(`/api/fingerprint/${videoId.trim()}`)
      addLog('Mean-pooling frame embeddings...')
      addLog('Saving to Firebase + Qdrant...')
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Fingerprint failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-up">
      <div className="page-heading">
        <div className="page-heading-badge"><span className="badge badge-accent">Step 2</span></div>
        <h2 className="page-heading-title">Generate AI fingerprint</h2>
        <p className="page-heading-sub">Watermarks frames and creates a 1408-dim Google Vision AI vector</p>
      </div>

      {/* Radar visualization */}
      <RadarViz active={loading} />

      {/* Processing log */}
      {logs.length > 0 && (
        <div className="card mb-16" style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          {logs.map((log, i) => (
            <div key={i} className="animate-slide-in" style={{ padding: '4px 0', color: i === logs.length - 1 ? 'var(--text-accent)' : 'var(--text-muted)', borderBottom: '1px solid var(--border)', display: 'flex', gap: 8, animationDelay: `${i * 0.15}s`, opacity: 0 }}>
              <span style={{ color: 'var(--text-success)' }}>›</span>
              {log}
              {i === logs.length - 1 && loading && <div className="processing-spinner" style={{ marginLeft: 'auto' }} />}
            </div>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="card">
        <label style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8, display: 'block' }}>Video ID from Step 1</label>
        <div className="flex" style={{ gap: 10 }}>
          <input
            className="input input-mono"
            placeholder="e.g. 9b332136-734d-4002-b6dc-a25c7a2cff4c"
            value={videoId}
            onChange={e => setVideoId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && run()}
          />
          <button className="btn btn-primary" onClick={run} disabled={!videoId.trim() || loading}>
            {loading ? <><div className="processing-spinner" /> Processing</> : 'Generate'}
          </button>
        </div>

        {error && <div className="alert alert-danger mt-16">{error}</div>}

        {result && (
          <div className="success-burst mt-16">
            <div className="alert alert-success mb-12">✅ Fingerprint generated successfully</div>
            <div className="fingerprint-result-grid">
              {[
                { k: 'Frames processed', v: result.frames_processed },
                { k: 'Vector dimensions', v: result.vector_dimensions },
                { k: 'Watermarked',       v: result.watermarked ? 'Yes ✅' : 'No' },
                { k: 'Saved to',          v: result.saved_to?.join(', ') },
              ].map(({ k, v }) => (
                <div key={k} className="stat-cell">
                  <div className="stat-value" style={{ fontSize: 15 }}>{v}</div>
                  <div className="stat-label">{k}</div>
                </div>
              ))}
            </div>
            <div className="alert alert-info mt-12" style={{ fontSize: 12 }}>
              Next: Go to <strong>Step 3 · Scrape</strong> to scan the web for copies.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}