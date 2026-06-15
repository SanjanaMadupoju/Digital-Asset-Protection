import React, { useState } from 'react'
import api from '../../api'

function ScoreBar({ score }) {
  const pct = Math.round((score || 0) * 100)
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

export default function ResultsPage() {
  const [videoId, setVideoId] = useState('')
  const [limit, setLimit] = useState(5)
  const [email, setEmail] = useState('')
  const [filter, setFilter] = useState('all')

  const [loadingMatch, setLoadingMatch] = useState(false)
  const [loadingReport, setLoadingReport] = useState(false)
  const [loadingEmail, setLoadingEmail] = useState(false)

  const [matchResult, setMatchResult] = useState(null)
  const [report, setReport] = useState(null)
  const [emailResult, setEmailResult] = useState(null)
  const [error, setError] = useState(null)

  const runMatching = async () => {
    if (!videoId.trim()) return
    setLoadingMatch(true)
    setError(null)
    setEmailResult(null)
    try {
      const res = await api.post(`/api/fingerprint-scraped/${videoId.trim()}?limit=${limit}`)
      setMatchResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Matching failed')
    } finally {
      setLoadingMatch(false)
    }
  }

  const loadReport = async () => {
    if (!videoId.trim()) return
    setLoadingReport(true)
    setError(null)
    try {
      const res = await api.get(`/api/reports/${videoId.trim()}`)
      setReport(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Report load failed')
    } finally {
      setLoadingReport(false)
    }
  }

  const sendEmail = async () => {
    if (!videoId.trim() || !email.trim()) return
    setLoadingEmail(true)
    setError(null)
    try {
      const res = await api.post(`/api/reports/${videoId.trim()}/send-email`, {
        email: email.trim(),
        violation_filter: filter,
      })
      setEmailResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Email send failed')
    } finally {
      setLoadingEmail(false)
    }
  }

  return (
    <div className="animate-fade-up">
      <div className="page-heading">
        <div className="page-heading-badge"><span className="badge badge-accent">Step 4-6</span></div>
        <h2 className="page-heading-title">Results and action center</h2>
        <p className="page-heading-sub">Match scraped videos, review violations, and send email alerts</p>
      </div>

      <div className="card">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px auto', gap: 10, marginBottom: 12 }}>
          <input className="input input-mono" placeholder="Video ID" value={videoId} onChange={e => setVideoId(e.target.value)} />
          <input className="input" type="number" min={1} max={20} value={limit} onChange={e => setLimit(Number(e.target.value))} />
          <button className="btn btn-primary" onClick={runMatching} disabled={!videoId.trim() || loadingMatch}>
            {loadingMatch ? 'Processing...' : 'Run match'}
          </button>
        </div>

        <div className="flex" style={{ gap: 8, marginBottom: 12 }}>
          <button className="btn btn-secondary btn-sm" onClick={loadReport} disabled={!videoId.trim() || loadingReport}>
            {loadingReport ? 'Loading report...' : 'Load report'}
          </button>
        </div>

        {error && <div className="alert alert-danger mt-12">{error}</div>}

        {matchResult && (
          <div className="mt-16">
            <div className="stats-grid mb-16">
              <div className="stat-cell"><div className="stat-value">{matchResult.processed}</div><div className="stat-label">Processed</div></div>
              <div className="stat-cell"><div className="stat-value" style={{ color: matchResult.flagged_count > 0 ? 'var(--text-danger)' : 'var(--text-success)' }}>{matchResult.flagged_count}</div><div className="stat-label">Flagged</div></div>
              <div className="stat-cell"><div className="stat-value">{matchResult.failed}</div><div className="stat-label">Failed</div></div>
            </div>

            {matchResult.all_results?.slice(0, 8).map((r, i) => (
              <div key={i} className="match-result-item" style={{ marginBottom: 8 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="flex" style={{ gap: 6, marginBottom: 6, flexWrap: 'wrap' }}>
                    <span className="badge badge-muted">{r.platform}</span>
                    {r.flagged && <span className="badge badge-danger">Flagged</span>}
                    {r.watermark_found && <span className="badge badge-warning">Watermark</span>}
                  </div>
                  <a href={r.url} target="_blank" rel="noreferrer" style={{ fontSize: 11, wordBreak: 'break-all', display: 'block', marginBottom: 8 }}>
                    {r.url}
                  </a>
                  {r.match_score !== null && <ScoreBar score={r.match_score} />}
                </div>
              </div>
            ))}
          </div>
        )}

        {report && (
          <div className="alert alert-info mt-16">
            <p className="fw-600 mb-8" style={{ fontSize: 13 }}>Report summary</p>
            <p style={{ fontSize: 12 }}>Total violations: <strong>{report.total_violations}</strong></p>
            <p style={{ fontSize: 12 }}>Critical: <strong>{report.violations_by_risk?.critical || 0}</strong> · High: <strong>{report.violations_by_risk?.high || 0}</strong></p>
          </div>
        )}

        <div className="card mt-16" style={{ border: '1px solid var(--border-accent)' }}>
          <p className="fw-600 mb-10" style={{ fontSize: 13 }}>Send action email</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 180px auto', gap: 8 }}>
            <input className="input" type="email" placeholder="recipient@company.com" value={email} onChange={e => setEmail(e.target.value)} />
            <select className="input" value={filter} onChange={e => setFilter(e.target.value)}>
              <option value="all">All violations</option>
              <option value="high">High and critical</option>
              <option value="critical">Critical only</option>
            </select>
            <button className="btn btn-success" onClick={sendEmail} disabled={!videoId.trim() || !email.trim() || loadingEmail}>
              {loadingEmail ? 'Sending...' : 'Send email'}
            </button>
          </div>

          {emailResult && (
            <div className={`alert ${emailResult.sent ? 'alert-success' : 'alert-warning'} mt-12`}>
              {emailResult.sent ? `Email sent to ${emailResult.recipient_email}` : (emailResult.message || emailResult.error || 'Email not sent')}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
