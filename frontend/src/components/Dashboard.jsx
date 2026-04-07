import React, { useState } from 'react'
import axios from 'axios'

// ── helpers ───────────────────────────────────────────────────────────────────
function riskColor(level) {
  return {
    critical: { bg: '#1c0b0b', border: '#f85149', text: '#f85149', badge: '#3d0b0b' },
    high:     { bg: '#1c1200', border: '#d29922', text: '#d29922', badge: '#3d2400' },
    medium:   { bg: '#0d1f36', border: '#388bfd', text: '#388bfd', badge: '#0d2848' },
    low:      { bg: '#0d1117', border: '#30363d', text: '#8b949e', badge: '#161b22' },
    clean:    { bg: '#0d2217', border: '#2ea043', text: '#3fb950', badge: '#0d2217' },
  }[level] || { bg: '#0d1117', border: '#30363d', text: '#8b949e', badge: '#161b22' }
}

function ScoreBar({ score }) {
  const pct   = Math.round((score || 0) * 100)
  const color = pct >= 92 ? '#f85149' : pct >= 82 ? '#d29922' : pct >= 65 ? '#388bfd' : '#2ea043'
  return (
    <div style={{ marginTop: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#8b949e', marginBottom: 3 }}>
        <span>Match score</span><span style={{ color }}>{pct}%</span>
      </div>
      <div style={{ height: 5, background: '#21262d', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.4s' }} />
      </div>
    </div>
  )
}

function SummaryCard({ summary }) {
  const risk   = riskColor(summary.risk_status)
  const stats  = [
    { label: 'URLs scraped',    value: summary.total_urls_scraped },
    { label: 'Fingerprinted',   value: summary.fingerprinted },
    { label: 'Flagged',         value: summary.flagged },
    { label: 'Watermark hits',  value: summary.watermark_matches },
    { label: 'Avg match score', value: `${Math.round((summary.avg_match_score || 0) * 100)}%` },
    { label: 'Max match score', value: `${Math.round((summary.max_match_score || 0) * 100)}%` },
  ]
  return (
    <div style={{ background: risk.bg, border: `1px solid ${risk.border}`, borderRadius: 12, padding: 20, marginBottom: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <p style={{ fontSize: 11, color: '#8b949e', marginBottom: 4 }}>Overall risk status</p>
          <p style={{ fontSize: 20, fontWeight: 700, color: risk.text, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {summary.risk_status}
          </p>
        </div>
        {summary.flagged > 0 && (
          <div style={{ background: risk.badge, border: `1px solid ${risk.border}`, borderRadius: 8, padding: '8px 14px', textAlign: 'center' }}>
            <p style={{ fontSize: 24, fontWeight: 700, color: risk.text }}>{summary.flagged}</p>
            <p style={{ fontSize: 11, color: '#8b949e' }}>violation{summary.flagged !== 1 ? 's' : ''}</p>
          </div>
        )}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
        {stats.map(s => (
          <div key={s.label} style={{ background: '#0d1117', border: '1px solid #21262d', borderRadius: 8, padding: '10px 12px' }}>
            <p style={{ fontSize: 18, fontWeight: 600, color: '#e6edf3' }}>{s.value}</p>
            <p style={{ fontSize: 11, color: '#484f58', marginTop: 2 }}>{s.label}</p>
          </div>
        ))}
      </div>
      {summary.flagged_by_platform && Object.keys(summary.flagged_by_platform).length > 0 && (
        <div style={{ marginTop: 14 }}>
          <p style={{ fontSize: 11, color: '#484f58', marginBottom: 8 }}>Flagged by platform</p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {Object.entries(summary.flagged_by_platform).map(([p, count]) => (
              <span key={p} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 20, padding: '3px 10px', fontSize: 12, color: '#e6edf3' }}>
                {p}: <strong>{count}</strong>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ViolationCard({ item, index }) {
  const risk  = riskColor(item.risk_level)
  const score = Math.round((item.match_score || 0) * 100)
  return (
    <div style={{ background: risk.bg, border: `1px solid ${risk.border}`, borderRadius: 10, padding: 16, marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Platform + risk badge */}
          <div style={{ display: 'flex', gap: 6, marginBottom: 8, flexWrap: 'wrap' }}>
            <span style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 4, padding: '2px 8px', fontSize: 11, color: '#8b949e', textTransform: 'uppercase' }}>
              {item.platform}
            </span>
            <span style={{ background: risk.badge, border: `1px solid ${risk.border}`, borderRadius: 4, padding: '2px 8px', fontSize: 11, color: risk.text }}>
              {item.risk_level}
            </span>
            {item.watermark_found && (
              <span style={{ background: '#3d0b0b', border: '1px solid #f85149', borderRadius: 4, padding: '2px 8px', fontSize: 11, color: '#f85149' }}>
                watermark detected
              </span>
            )}
          </div>

          {/* URL */}
          <a href={item.url} target="_blank" rel="noreferrer"
            style={{ fontSize: 12, color: '#58a6ff', wordBreak: 'break-all', display: 'block', marginBottom: 8, textDecoration: 'none' }}>
            {item.url}
          </a>

          {/* Score bar */}
          <ScoreBar score={item.match_score} />

          {/* Risk label */}
          <p style={{ fontSize: 11, color: '#484f58', marginTop: 8 }}>{item.risk_label}</p>

          {/* Watermark detail */}
          {item.watermark_found && item.watermark_detail && (
            <div style={{ marginTop: 8, padding: '6px 10px', background: '#1c0b0b', borderRadius: 6, fontSize: 11 }}>
              <span style={{ color: '#f85149' }}>
                Org pattern: {item.watermark_detail.org_match_pct}% &nbsp;|&nbsp;
                Video ID: {item.watermark_detail.id_match_pct}%
              </span>
            </div>
          )}
        </div>

        {/* Score circle */}
        <div style={{ flexShrink: 0, width: 52, height: 52, borderRadius: '50%', border: `2px solid ${risk.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
          <p style={{ fontSize: 14, fontWeight: 700, color: risk.text, lineHeight: 1 }}>{score}%</p>
          <p style={{ fontSize: 9, color: '#484f58' }}>match</p>
        </div>
      </div>
    </div>
  )
}

// ── Main Dashboard component ──────────────────────────────────────────────────
export default function Dashboard() {
  const [videoId, setVideoId]   = useState('')
  const [loading, setLoading]   = useState(false)
  const [summary, setSummary]   = useState(null)
  const [results, setResults]   = useState(null)
  const [filter, setFilter]     = useState('all')   // all | flagged | high
  const [error, setError]       = useState(null)
  const [reporting, setReporting] = useState(false)
  const [report, setReport]     = useState(null)

  const fetchResults = async () => {
    if (!videoId.trim()) return
    setLoading(true); setError(null); setSummary(null); setResults(null); setReport(null)
    try {
      const [sumRes, matchRes] = await Promise.all([
        axios.get(`/api/matches/${videoId}/summary`),
        axios.get(`/api/matches/${videoId}`),
      ])
      setSummary(sumRes.data)
      setResults(matchRes.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Failed to load results')
    } finally {
      setLoading(false)
    }
  }

  const generateReport = async () => {
    setReporting(true)
    try {
      const res = await axios.post(`/api/matches/${videoId}/report`)
      setReport(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Report generation failed')
    } finally {
      setReporting(false)
    }
  }

  const filteredResults = () => {
    if (!results?.results) return []
    if (filter === 'flagged') return results.results.filter(r => r.flagged)
    if (filter === 'high')    return results.results.filter(r => (r.match_score || 0) >= 0.82)
    return results.results
  }

  return (
    <div style={{ width: '100%', maxWidth: 760 }}>

      {/* Search bar */}
      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 12, padding: 24, marginBottom: 24 }}>
        <p style={{ fontSize: 13, color: '#8b949e', marginBottom: 10 }}>Enter your Video ID to see match results</p>
        <div style={{ display: 'flex', gap: 10 }}>
          <input
            value={videoId}
            onChange={e => setVideoId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && fetchResults()}
            placeholder="e.g. 9b332136-734d-4002-b6dc-a25c7a2cff4c"
            style={{
              flex: 1, padding: '10px 14px', background: '#0d1117',
              border: '1px solid #30363d', borderRadius: 8,
              color: '#e6edf3', fontSize: 13, fontFamily: 'monospace',
              outline: 'none',
            }}
          />
          <button onClick={fetchResults} disabled={loading || !videoId.trim()} style={{
            padding: '10px 20px', borderRadius: 8, border: 'none',
            background: loading || !videoId.trim() ? '#21262d' : '#238636',
            color: loading || !videoId.trim() ? '#484f58' : '#fff',
            fontWeight: 600, fontSize: 13, cursor: loading || !videoId.trim() ? 'not-allowed' : 'pointer',
          }}>
            {loading ? 'Loading...' : 'Check'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{ background: '#1c0b0b', border: '1px solid #f85149', borderRadius: 10, padding: 14, marginBottom: 16 }}>
          <p style={{ color: '#f85149', fontSize: 13 }}>{error}</p>
        </div>
      )}

      {/* Summary card */}
      {summary && <SummaryCard summary={summary} />}

      {/* Results */}
      {results && (
        <>
          {/* Filter bar + generate report */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', gap: 6 }}>
              {[
                { key: 'all',     label: `All (${results.total})` },
                { key: 'flagged', label: `Flagged (${results.flagged})` },
                { key: 'high',    label: 'High risk' },
              ].map(f => (
                <button key={f.key} onClick={() => setFilter(f.key)} style={{
                  padding: '5px 14px', borderRadius: 20, border: '1px solid',
                  borderColor: filter === f.key ? '#388bfd' : '#30363d',
                  background:  filter === f.key ? '#0d1f36' : '#161b22',
                  color:       filter === f.key ? '#58a6ff' : '#8b949e',
                  fontSize: 12, cursor: 'pointer',
                }}>
                  {f.label}
                </button>
              ))}
            </div>
            {results.flagged > 0 && (
              <button onClick={generateReport} disabled={reporting} style={{
                padding: '5px 14px', borderRadius: 6, border: '1px solid #f85149',
                background: '#1c0b0b', color: '#f85149',
                fontSize: 12, cursor: 'pointer', fontWeight: 600,
              }}>
                {reporting ? 'Generating...' : 'Generate Evidence Report'}
              </button>
            )}
          </div>

          {/* Violation cards */}
          {filteredResults().length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#484f58', fontSize: 14 }}>
              {filter === 'all' ? 'No results found.' : 'No results for this filter.'}
            </div>
          ) : (
            filteredResults().map((item, i) => (
              <ViolationCard key={item.url} item={item} index={i} />
            ))
          )}
        </>
      )}

      {/* Evidence report */}
      {report && (
        <div style={{ marginTop: 24, background: '#161b22', border: '1px solid #30363d', borderRadius: 12, padding: 20 }}>
          <p style={{ fontSize: 14, fontWeight: 600, color: '#e6edf3', marginBottom: 12 }}>Evidence Report</p>
          <p style={{ fontSize: 12, color: '#484f58', marginBottom: 4 }}>Generated: {report.report_generated_at}</p>
          <p style={{ fontSize: 12, color: '#484f58', marginBottom: 16 }}>Total violations: <strong style={{ color: '#f85149' }}>{report.total_violations}</strong></p>
          <pre style={{
            background: '#0d1117', border: '1px solid #21262d', borderRadius: 8,
            padding: 14, fontSize: 11, color: '#8b949e',
            overflowX: 'auto', maxHeight: 400, overflowY: 'auto',
            whiteSpace: 'pre-wrap', wordBreak: 'break-all',
          }}>
            {JSON.stringify(report.violations, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}