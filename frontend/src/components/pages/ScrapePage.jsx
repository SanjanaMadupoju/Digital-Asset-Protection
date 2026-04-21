import React, { useState } from 'react'
import axios from 'axios'

const PLATFORMS = [
  { id: 'youtube',     label: 'YouTube',     icon: '▶️' },
  { id: 'dailymotion', label: 'Dailymotion', icon: '🎞️' },
  { id: 'twitter',     label: 'Twitter/X',   icon: '🐦' },
  { id: 'facebook',    label: 'Facebook',    icon: '📘' },
  { id: 'web',         label: 'Web search',  icon: '🌐' },
]

function WaveformViz({ active }) {
  const heights = [20,35,55,70,45,60,80,50,40,65,75,55,35,50,70,45,60,80,40,55]
  return (
    <div className="scrape-viz">
      {active && <div className="scan-line" />}
      <div className="waveform-bars">
        {heights.map((h, i) => (
          <div
            key={i}
            className="waveform-bar"
            style={{
              height: active ? h : 20,
              background: active ? 'var(--border-accent)' : 'var(--border)',
              animationDelay: `${i * 0.08}s`,
              transition: 'height 0.3s ease',
            }}
          />
        ))}
      </div>
      <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
        {active ? 'Scanning platforms...' : 'Ready to scan'}
      </p>
    </div>
  )
}

export default function ScrapePage() {
  const [videoId,   setVideoId]   = useState('')
  const [sport,     setSport]     = useState('')
  const [keywords,  setKeywords]  = useState('')
  const [maxResults,setMaxResults]= useState(5)
  const [channels,  setChannels]  = useState('')
  const [loading,   setLoading]   = useState(false)
  const [result,    setResult]    = useState(null)
  const [error,     setError]     = useState(null)
  const [activePlat,setActivePlat]= useState(null)

  const run = async () => {
    if (!videoId.trim() || !sport.trim() || !keywords.trim()) return
    setLoading(true); setError(null); setResult(null)

    const platformOrder = ['youtube', 'web', 'dailymotion', 'twitter', 'facebook']
    let i = 0
    const interval = setInterval(() => {
      setActivePlat(platformOrder[i % platformOrder.length])
      i++
    }, 1800)

    try {
      const res = await axios.post('/api/scrape', {
        video_id:            videoId.trim(),
        sport:               sport.trim(),
        keywords:            keywords.trim(),
        suspicious_channels: channels.trim() ? channels.split('\n').map(c => c.trim()).filter(Boolean) : [],
        max_results:         maxResults,
      })
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Scrape failed')
    } finally {
      clearInterval(interval)
      setActivePlat(null)
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-up">
      <div className="page-heading">
        <div className="page-heading-badge"><span className="badge badge-muted">Step 3</span></div>
        <h2 className="page-heading-title">Scan the web</h2>
        <p className="page-heading-sub">Search YouTube, Dailymotion, Twitter/X, Facebook and the web for your content</p>
      </div>

      {/* Waveform viz */}
      <WaveformViz active={loading} />

      {/* Platform chips */}
      <div className="platform-chips mb-16">
        {PLATFORMS.map(p => (
          <div key={p.id} className={`platform-chip ${activePlat === p.id ? 'active' : ''}`}>
            <span>{p.icon}</span> {p.label}
          </div>
        ))}
      </div>

      {/* Form */}
      <div className="card">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, display: 'block' }}>Video ID</label>
            <input className="input input-mono" placeholder="From Step 1" value={videoId} onChange={e => setVideoId(e.target.value)} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, display: 'block' }}>Sport</label>
            <input className="input" placeholder="e.g. cricket" value={sport} onChange={e => setSport(e.target.value)} />
          </div>
        </div>

        <div style={{ marginBottom: 12 }}>
          <label style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, display: 'block' }}>Keywords</label>
          <input className="input" placeholder="e.g. IPL 2024 final highlights" value={keywords} onChange={e => setKeywords(e.target.value)} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, display: 'block' }}>Max results per source</label>
            <input className="input" type="number" min={1} max={20} value={maxResults} onChange={e => setMaxResults(Number(e.target.value))} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, display: 'block' }}>Suspicious channels (optional)</label>
            <input className="input" placeholder="YouTube channel URLs, one per line" value={channels} onChange={e => setChannels(e.target.value)} />
          </div>
        </div>

        <button className="btn btn-primary btn-full" onClick={run} disabled={!videoId.trim() || !sport.trim() || !keywords.trim() || loading}>
          {loading ? <><div className="processing-spinner" /> Scanning platforms...</> : '🌐 Start web scan'}
        </button>

        {error && <div className="alert alert-danger mt-16">{error}</div>}

        {result && (
          <div className="success-burst mt-16">
            <div className="alert alert-success mb-12">✅ Scan complete — {result.total_found} URLs collected</div>
            <div className="stats-grid mb-12">
              <div className="stat-cell"><div className="stat-value">{result.total_found}</div><div className="stat-label">URLs found</div></div>
              <div className="stat-cell"><div className="stat-value">{result.saved_to_mongo}</div><div className="stat-label">Saved</div></div>
              <div className="stat-cell"><div className="stat-value">{result.duplicates_skipped}</div><div className="stat-label">Duplicates</div></div>
            </div>
            {result.by_platform && (
              <div className="platform-chips">
                {Object.entries(result.by_platform).map(([p, count]) => (
                  <div key={p} className="platform-chip active">{p}: <strong>{count}</strong></div>
                ))}
              </div>
            )}
            <div className="alert alert-info mt-12" style={{ fontSize: 12 }}>
              Next: Go to <strong>Step 4 · Match scraped</strong> to fingerprint and compare these URLs.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}