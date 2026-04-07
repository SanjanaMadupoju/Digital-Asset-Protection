import React, { useState } from 'react'
import axios from 'axios'

// ── helpers ───────────────────────────────────────────────────────────────────
function Badge({ children, color, bg, border }) {
  return (
    <span style={{
      padding: '2px 9px', borderRadius: 20, fontSize: 10, fontWeight: 700,
      fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.05em',
      background: bg, border: `1px solid ${border}`, color,
    }}>{children}</span>
  )
}

function platformBadge(p = '') {
  const map = {
    youtube:     { color: '#f85149', bg: '#1c0b0b', border: '#f85149' },
    dailymotion: { color: '#58a6ff', bg: '#0d1f36', border: '#388bfd' },
    twitter:     { color: '#d29922', bg: '#1c1200', border: '#d29922' },
  }
  return map[p.toLowerCase()] || { color: '#8b949e', bg: '#161b22', border: '#30363d' }
}

function ScoreBar({ score, threshold }) {
  const pct = Math.round((score || 0) * 100)
  const over = score >= threshold
  const color = over ? '#f85149' : pct >= 70 ? '#d29922' : '#3fb950'
  return (
    <div style={{ marginTop: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#8b949e', marginBottom: 3 }}>
        <span>match score</span>
        <span style={{ color }}>{pct}% {over ? '▲ flagged' : ''}</span>
      </div>
      <div style={{ height: 4, background: '#21262d', borderRadius: 3, overflow: 'hidden', position: 'relative' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.4s' }} />
        {/* threshold marker */}
        <div style={{ position: 'absolute', top: 0, left: `${Math.round(threshold * 100)}%`, width: 1, height: '100%', background: '#484f58' }} />
      </div>
    </div>
  )
}

function MetricCard({ value, label, color }) {
  return (
    <div style={{ background: '#0d1117', border: '1px solid #21262d', borderRadius: 8, padding: '12px 14px' }}>
      <p style={{ fontSize: 20, fontWeight: 700, color: color || '#e6edf3', fontFamily: 'monospace' }}>{value}</p>
      <p style={{ fontSize: 10, color: '#484f58', marginTop: 3, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</p>
    </div>
  )
}

// ── Result row card ───────────────────────────────────────────────────────────
function ResultRow({ item, threshold }) {
  const ps = platformBadge(item.platform)
  const flagColor = item.flagged ? '#f85149' : '#3fb950'
  const flagBg    = item.flagged ? '#1c0b0b' : '#0d2217'
  const flagBdr   = item.flagged ? '#f85149' : '#2ea043'

  return (
    <div style={{
      padding: '12px 14px',
      background: item.flagged ? 'rgba(248,81,73,0.04)' : '#0d1117',
      border: `1px solid ${item.flagged ? '#3d1a1a' : '#21262d'}`,
      borderRadius: 8,
    }}>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 7 }}>
        <Badge {...ps}>{item.platform}</Badge>
        <Badge color={flagColor} bg={flagBg} border={flagBdr}>{item.flagged ? 'flagged' : 'clean'}</Badge>
        {item.watermark_found && <Badge color="#f85149" bg="#1c0b0b" border="#f85149">watermark detected</Badge>}
        {item.status === 'failed' && <Badge color="#d29922" bg="#1c1200" border="#d29922">failed</Badge>}
      </div>

      <a href={item.url} target="_blank" rel="noreferrer"
        style={{ fontSize: 11, color: '#58a6ff', wordBreak: 'break-all', display: 'block', marginBottom: 6, textDecoration: 'none' }}>
        {item.url}
      </a>

      {item.match_score !== null && item.match_score !== undefined && (
        <ScoreBar score={item.match_score} threshold={threshold} />
      )}

      {item.watermark_found && item.watermark_detail && (
        <div style={{ marginTop: 8, padding: '5px 10px', background: '#1c0b0b', borderRadius: 6, fontSize: 11, fontFamily: 'monospace', color: '#f85149' }}>
          org pattern: {item.watermark_detail.org_match_pct}% &nbsp;|&nbsp; video id: {item.watermark_detail.id_match_pct}%
        </div>
      )}

      {item.error && (
        <p style={{ marginTop: 6, fontSize: 11, color: '#d29922', fontFamily: 'monospace' }}>⚠ {item.error}</p>
      )}
    </div>
  )
}

// ── POST result panel ─────────────────────────────────────────────────────────
function PostResult({ data }) {
  const [filter, setFilter] = useState('all')
  const items = data.all_results || []
  const filtered =
    filter === 'flagged' ? items.filter(r => r.flagged) :
    filter === 'failed'  ? items.filter(r => r.status === 'failed') :
    items

  return (
    <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: 12, overflow: 'hidden' }}>
      {/* header */}
      <div style={{ padding: '12px 18px', background: '#161b22', borderBottom: '1px solid #30363d', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: data.flagged_count > 0 ? '#f85149' : '#3fb950' }} />
          <span style={{ fontSize: 13, fontWeight: 700, color: '#e6edf3' }}>Batch complete</span>
        </div>
        <span style={{ fontSize: 11, color: '#484f58', fontFamily: 'monospace' }}>threshold: {Math.round(data.match_threshold * 100)}%</span>
      </div>

      <div style={{ padding: '16px 18px' }}>
        {/* metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 16 }}>
          <MetricCard value={data.processed}     label="Processed" />
          <MetricCard value={data.failed}         label="Failed" color={data.failed > 0 ? '#d29922' : undefined} />
          <MetricCard value={data.flagged_count}  label="Flagged" color={data.flagged_count > 0 ? '#f85149' : '#3fb950'} />
          <MetricCard value={`${Math.round(data.match_threshold * 100)}%`} label="Threshold" color="#8b949e" />
        </div>

        {/* filter bar */}
        <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
          {[['all', `All (${items.length})`], ['flagged', `Flagged (${data.flagged_count})`], ['failed', `Failed (${data.failed})`]].map(([key, label]) => (
            <button key={key} onClick={() => setFilter(key)} style={{
              padding: '4px 12px', borderRadius: 20, border: '1px solid',
              borderColor: filter === key ? '#388bfd' : '#30363d',
              background: filter === key ? 'rgba(56,139,253,0.1)' : '#161b22',
              color: filter === key ? '#58a6ff' : '#8b949e',
              fontSize: 11, cursor: 'pointer',
            }}>{label}</button>
          ))}
        </div>

        {/* rows */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 400, overflowY: 'auto' }}>
          {filtered.length === 0
            ? <p style={{ fontSize: 13, color: '#484f58', textAlign: 'center', padding: '20px 0' }}>No results for this filter.</p>
            : filtered.map((item, i) => <ResultRow key={i} item={item} threshold={data.match_threshold} />)
          }
        </div>

        {/* next step */}
        <div style={{ marginTop: 14, padding: '10px 14px', background: 'rgba(46,160,67,0.06)', border: '1px solid rgba(46,160,67,0.15)', borderRadius: 8 }}>
          <p style={{ fontSize: 11, color: '#3fb950', fontFamily: 'monospace' }}>→ {data.next_step}</p>
        </div>
      </div>
    </div>
  )
}

// ── GET summary panel ─────────────────────────────────────────────────────────
function SummaryResult({ data }) {
  return (
    <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: 12, overflow: 'hidden' }}>
      <div style={{ padding: '12px 18px', background: '#161b22', borderBottom: '1px solid #30363d', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#58a6ff' }} />
        <span style={{ fontSize: 13, fontWeight: 700, color: '#e6edf3' }}>Summary for {data.video_id}</span>
      </div>

      <div style={{ padding: '16px 18px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10, marginBottom: 16 }}>
          <MetricCard value={data.total_urls} label="Total" />
          <MetricCard value={data.pending}    label="Pending"   color="#d29922" />
          <MetricCard value={data.processed}  label="Processed" color="#3fb950" />
          <MetricCard value={data.failed}     label="Failed"    color={data.failed > 0 ? '#d29922' : undefined} />
          <MetricCard value={data.flagged}    label="Flagged"   color={data.flagged > 0 ? '#f85149' : '#3fb950'} />
        </div>

        {data.flagged_urls?.length > 0 && (
          <>
            <p style={{ fontSize: 10, color: '#484f58', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
              Flagged URLs
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 360, overflowY: 'auto' }}>
              {data.flagged_urls.map((item, i) => (
                <ResultRow key={i} item={item} threshold={0.85} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function FingerprintScraped() {
  const [videoId, setVideoId] = useState('')
  const [limit,   setLimit]   = useState(10)

  const [postResult, setPostResult] = useState(null)
  const [getResult,  setGetResult]  = useState(null)
  const [activeTab,  setActiveTab]  = useState('post')
  const [status,     setStatus]     = useState(null)
  const [loadingPost, setLoadingPost] = useState(false)
  const [loadingGet,  setLoadingGet]  = useState(false)

  const loading = loadingPost || loadingGet

  const showStatus = (type, msg) => setStatus({ type, msg })

  const runPost = async () => {
    if (!videoId.trim()) return showStatus('error', 'Video ID is required')
    setLoadingPost(true)
    showStatus('running', `Fingerprinting scraped URLs for ${videoId} (limit: ${limit})… may take several minutes`)
    try {
      const res = await axios.post(`/api/fingerprint-scraped/${videoId.trim()}`, null, {
        params: { limit: Number(limit) },
        timeout: 600_000,   // 10 min — each URL takes 30-120s on CPU
      })
      setPostResult(res.data)
      showStatus('success', `Done · ${res.data.processed} processed · ${res.data.flagged_count} flagged`)
      setActiveTab('post')
    } catch (e) {
      showStatus('error', e.response?.data?.detail || e.message || 'Failed')
    } finally {
      setLoadingPost(false)
    }
  }

  const runGet = async () => {
    if (!videoId.trim()) return showStatus('error', 'Video ID is required')
    setLoadingGet(true)
    showStatus('running', `Fetching summary for ${videoId}…`)
    try {
      const res = await axios.get(`/api/fingerprint-scraped/${videoId.trim()}/summary`)
      setGetResult(res.data)
      showStatus('success', `${res.data.total_urls} total · ${res.data.flagged} flagged`)
      setActiveTab('get')
    } catch (e) {
      showStatus('error', e.response?.data?.detail || e.message || 'Not found')
    } finally {
      setLoadingGet(false)
    }
  }

  const statusColors = {
    running: { bg: '#0d1f36', border: '#388bfd', color: '#58a6ff' },
    success: { bg: '#0d2217', border: '#2ea043', color: '#3fb950' },
    error:   { bg: '#1c0b0b', border: '#f85149', color: '#f85149' },
  }[status?.type] || {}

  return (
    <div style={{ width: '100%', maxWidth: 760 }}>

      {/* Input panel */}
      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 12, padding: 24, marginBottom: 20 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 12, marginBottom: 16 }}>
          <div>
            <p style={{ fontSize: 11, color: '#484f58', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Video ID</p>
            <input
              value={videoId} onChange={e => setVideoId(e.target.value)}
              placeholder="9b332136-734d-4002-b6dc-a25c7a2cff4c"
              style={{ width: '100%', padding: '10px 14px', background: '#0d1117', border: '1px solid #30363d', borderRadius: 8, color: '#e6edf3', fontSize: 13, fontFamily: 'monospace', outline: 'none' }}
            />
          </div>
          <div>
            <p style={{ fontSize: 11, color: '#484f58', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Batch limit</p>
            <input
              type="number" value={limit} onChange={e => setLimit(e.target.value)} min={1} max={100}
              style={{ width: 90, padding: '10px 14px', background: '#0d1117', border: '1px solid #30363d', borderRadius: 8, color: '#e6edf3', fontSize: 13, outline: 'none' }}
            />
          </div>
        </div>

        <p style={{ fontSize: 11, color: '#484f58', marginBottom: 14, fontFamily: 'monospace' }}>
          ⚡ Each URL takes 30–120 s on CPU. Run multiple times to process all pending URLs in batches.
        </p>

        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={runGet} disabled={loading || !videoId.trim()} style={{
            padding: '10px 18px', borderRadius: 8, border: '1px solid #30363d',
            background: 'transparent', color: '#8b949e', fontWeight: 600, fontSize: 13,
            cursor: loading || !videoId.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !videoId.trim() ? 0.4 : 1,
          }}>
            {loadingGet ? 'Loading…' : 'GET summary'}
          </button>
          <button onClick={runPost} disabled={loading || !videoId.trim()} style={{
            padding: '10px 20px', borderRadius: 8, border: 'none',
            background: loading || !videoId.trim() ? '#21262d' : '#b91c1c',
            color: loading || !videoId.trim() ? '#484f58' : '#fff',
            fontWeight: 600, fontSize: 13,
            cursor: loading || !videoId.trim() ? 'not-allowed' : 'pointer',
          }}>
            {loadingPost ? 'Processing…' : '▶ Run fingerprint batch'}
          </button>
        </div>

        {status && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 14, padding: '10px 14px', borderRadius: 8, background: statusColors.bg, border: `1px solid ${statusColors.border}`, color: statusColors.color, fontSize: 12, fontFamily: 'monospace' }}>
            {status.type === 'running' && (
              <div style={{ width: 13, height: 13, borderRadius: '50%', border: `2px solid ${statusColors.border}40`, borderTopColor: statusColors.color, animation: 'spin 0.7s linear infinite', flexShrink: 0 }} />
            )}
            <span>{status.msg}</span>
          </div>
        )}
      </div>

      {/* Tabs + results */}
      {(postResult || getResult) && (
        <>
          <div style={{ display: 'flex', gap: 4, marginBottom: 14 }}>
            {[['post', 'Batch result', !!postResult], ['get', 'Summary', !!getResult]].filter(t => t[2]).map(([key, label]) => (
              <button key={key} onClick={() => setActiveTab(key)} style={{
                padding: '7px 16px', borderRadius: 8, border: '1px solid',
                borderColor: activeTab === key ? '#388bfd' : '#30363d',
                background: activeTab === key ? 'rgba(56,139,253,0.08)' : '#161b22',
                color: activeTab === key ? '#58a6ff' : '#8b949e',
                fontSize: 12, fontWeight: 600, cursor: 'pointer',
              }}>{label}</button>
            ))}
          </div>
          {activeTab === 'post' && postResult && <PostResult data={postResult} />}
          {activeTab === 'get'  && getResult  && <SummaryResult data={getResult} />}
        </>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}