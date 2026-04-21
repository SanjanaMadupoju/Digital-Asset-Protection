import React, { useState } from 'react'
import axios from 'axios'

function ParticleViz({ active, results }) {
  const dots = Array.from({ length: 32 }, (_, i) => i)
  return (
    <div className="match-viz">
      <div className="particle-grid">
        {dots.map(i => (
          <div
            key={i}
            className="particle-dot"
            style={{
              background: active
                ? `hsl(${220 + i * 4}, 70%, 60%)`
                : 'var(--border)',
              animationDelay: `${(i * 0.09) % 3}s`,
              animationPlayState: active ? 'running' : 'paused',
            }}
          />
        ))}
      </div>
      <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-muted)' }}>
        {active ? 'Comparing fingerprints via cosine similarity...' : 'Ready to match'}
      </p>
    </div>
  )
}

function ScoreBar({ score }) {
  const pct   = Math.round((score || 0) * 100)
  const color = pct >= 92 ? 'var(--text-danger)' : pct >= 82 ? 'var(--text-warning)' : pct >= 65 ? 'var(--text-accent)' : 'var(--text-success)'
  return (
    <div>
      <div className="flex-between mb-8" style={{ fontSize: 11 }}>
        <span style={{ color: 'var(--text-muted)' }}>Match score</span>
        <span style={{ color, fontWeight: 700 }}>{pct}%</span>
      </div>
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  )
}

export default function MatchPage() {
  const [videoId,  setVideoId]  = useState('')
  const [limit,    setLimit]    = useState(5)
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)
  const [error,    setError]    = useState(null)

  const run = async () => {
    if (!videoId.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const res = await axios.post(`/api/fingerprint-scraped/${videoId.trim()}?limit=${limit}`)
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Match failed')
    } finally {
      setLoading(false)
    }
  }

  const riskColor = level => ({
    critical: 'var(--text-danger)',
    high:     'var(--text-warning)',
    medium:   'var(--text-accent)',
    low:      'var(--text-success)',
  }[level] || 'var(--text-muted)')

  return (
    <div className="animate-fade-up">
      <div className="page-heading">
        <div className="page-heading-badge"><span className="badge badge-accent">Step 4</span></div>
        <h2 className="page-heading-title">Analyse candidate videos</h2>
        <p className="page-heading-sub">Downloads frames, checks watermark, compares AI fingerprints</p>
      </div>

      {/* Particle viz */}
      <ParticleViz active={loading} />

      {/* Form */}
      <div className="card">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 10, marginBottom: 12 }}>
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, display: 'block' }}>Video ID</label>
            <input className="input input-mono" placeholder="From Step 1" value={videoId} onChange={e => setVideoId(e.target.value)} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, display: 'block' }}>Batch size</label>
            <input className="input" type="number" min={1} max={20} value={limit} onChange={e => setLimit(Number(e.target.value))} style={{ width: 80 }} />
          </div>
        </div>

        <button className="btn btn-primary btn-full" onClick={run} disabled={!videoId.trim() || loading}>
          {loading ? <><div className="processing-spinner" /> Matching {limit} URLs...</> : '🔍 Run fingerprint matching'}
        </button>

        {loading && (
          <div className="processing-status mt-16">
            <div className="processing-spinner" />
            This takes 30–120 seconds per URL on CPU. Watch terminal for live logs.
          </div>
        )}

        {error && <div className="alert alert-danger mt-16">{error}</div>}

        {result && (
          <div className="success-burst mt-16">
            <div className="stats-grid mb-16">
              <div className="stat-cell"><div className="stat-value">{result.processed}</div><div className="stat-label">Processed</div></div>
              <div className="stat-cell"><div className="stat-value" style={{ color: result.flagged_count > 0 ? 'var(--text-danger)' : 'var(--text-success)' }}>{result.flagged_count}</div><div className="stat-label">Flagged</div></div>
              <div className="stat-cell"><div className="stat-value">{result.failed}</div><div className="stat-label">Failed</div></div>
            </div>

            {result.all_results?.map((r, i) => (
              <div key={i} className="match-result-item" style={{ animationDelay: `${i * 0.1}s` }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="flex" style={{ gap: 6, marginBottom: 6, flexWrap: 'wrap' }}>
                    <span className="badge badge-muted">{r.platform}</span>
                    {r.flagged && <span className="badge badge-danger">Flagged</span>}
                    {r.watermark_found && <span className="badge badge-warning">Watermark ✓</span>}
                  </div>
                  <a href={r.url} target="_blank" rel="noreferrer" style={{ fontSize: 11, wordBreak: 'break-all', display: 'block', marginBottom: 8 }}>
                    {r.url?.slice(0, 60)}...
                  </a>
                  {r.match_score !== null && <ScoreBar score={r.match_score} />}
                </div>
              </div>
            ))}

            <div className="alert alert-info mt-12" style={{ fontSize: 12 }}>
              Next: Go to <strong>Dashboard</strong> to see all violations and generate reports.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}