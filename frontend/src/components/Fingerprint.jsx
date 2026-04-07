// ── Fingerprint.jsx — replaces old Fingerprint component ──────────────────
import React, { useState } from 'react'
import axios from 'axios'

// ── helpers ───────────────────────────────────────────────────────────────────
function FingerprintPreview({ values, note }) {
  return (
    <div style={{ marginTop: 14 }}>
      <p style={{ fontSize: 10, color: '#484f58', fontFamily: 'monospace', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        {note || 'Fingerprint preview'}
      </p>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {values.map((v, i) => (
          <span key={i} style={{
            padding: '4px 10px', borderRadius: 6, fontSize: 11, fontFamily: 'monospace',
            background: 'rgba(56,139,253,0.08)', border: '1px solid rgba(56,139,253,0.2)',
            color: '#58a6ff',
          }}>{v.toFixed(4)}</span>
        ))}
        <span style={{
          padding: '4px 10px', borderRadius: 6, fontSize: 11, fontFamily: 'monospace',
          background: '#161b22', border: '1px solid #21262d', color: '#484f58',
        }}>… +507 more</span>
      </div>
    </div>
  )
}

function MetaGrid({ items }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${items.length}, 1fr)`, gap: 1, background: '#21262d', borderRadius: 8, overflow: 'hidden', marginTop: 14 }}>
      {items.map(({ label, value, color }) => (
        <div key={label} style={{ padding: '12px 16px', background: '#0d1117' }}>
          <p style={{ fontSize: 18, fontWeight: 700, color: color || '#e6edf3', fontFamily: 'monospace' }}>{value}</p>
          <p style={{ fontSize: 10, color: '#484f58', marginTop: 3, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</p>
        </div>
      ))}
    </div>
  )
}

function Badge({ children, color = '#8b949e', bg = '#161b22', border = '#30363d' }) {
  return (
    <span style={{
      padding: '2px 9px', borderRadius: 20, fontSize: 10, fontWeight: 700,
      fontFamily: 'monospace', letterSpacing: '0.05em', textTransform: 'uppercase',
      background: bg, border: `1px solid ${border}`, color,
    }}>{children}</span>
  )
}

// ── POST result card ──────────────────────────────────────────────────────────
function PostResultCard({ data }) {
  return (
    <div style={{ background: '#0d2217', border: '1px solid #2ea043', borderRadius: 12, overflow: 'hidden', animation: 'fadeIn 0.3s ease' }}>
      <div style={{ padding: '14px 18px', background: '#0d1117', borderBottom: '1px solid #2ea043', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#3fb950', boxShadow: '0 0 8px #3fb950' }} />
          <span style={{ fontSize: 13, fontWeight: 700, color: '#e6edf3' }}>Pipeline complete</span>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {data.watermarked && <Badge color="#3fb950" bg="rgba(46,160,67,0.1)" border="rgba(46,160,67,0.3)">watermarked</Badge>}
          {data.saved_to?.map(s => <Badge key={s} color="#58a6ff" bg="rgba(56,139,253,0.1)" border="rgba(56,139,253,0.25)">{s}</Badge>)}
        </div>
      </div>

      <div style={{ padding: '16px 18px' }}>
        <MetaGrid items={[
          { label: 'Frames processed', value: data.frames_processed },
          { label: 'Vector size',      value: `${data.vector_dimensions}D` },
          { label: 'Stored & indexed', value: '✓', color: '#3fb950' },
        ]} />

        {data.fingerprint_preview?.length > 0 && (
          <FingerprintPreview values={data.fingerprint_preview} note="Fingerprint preview (first 5 / 512 dims)" />
        )}

        <div style={{ marginTop: 14, padding: '10px 14px', background: 'rgba(46,160,67,0.06)', border: '1px solid rgba(46,160,67,0.15)', borderRadius: 8 }}>
          <p style={{ fontSize: 11, color: '#3fb950', fontFamily: 'monospace' }}>→ {data.next_step}</p>
        </div>
      </div>

      <div style={{ padding: '10px 18px', background: '#0d1117', borderTop: '1px solid #21262d' }}>
        <p style={{ fontSize: 11, color: '#484f58', fontFamily: 'monospace' }}>video_id: {data.video_id}</p>
      </div>
    </div>
  )
}

// ── GET result card ───────────────────────────────────────────────────────────
function GetResultCard({ data }) {
  const created = data.created_at ? new Date(data.created_at).toLocaleString() : '—'
  return (
    <div style={{ background: '#0d1f36', border: '1px solid #388bfd', borderRadius: 12, overflow: 'hidden', animation: 'fadeIn 0.3s ease' }}>
      <div style={{ padding: '14px 18px', background: '#0d1117', borderBottom: '1px solid #388bfd', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#58a6ff', boxShadow: '0 0 8px #58a6ff' }} />
          <span style={{ fontSize: 13, fontWeight: 700, color: '#e6edf3' }}>Fingerprint on record</span>
        </div>
        {data.watermarked && <Badge color="#3fb950" bg="rgba(46,160,67,0.1)" border="rgba(46,160,67,0.3)">watermarked</Badge>}
      </div>

      <div style={{ padding: '16px 18px' }}>
        <MetaGrid items={[
          { label: 'Frames',     value: data.n_frames },
          { label: 'Vector dim', value: `${data.vector_dim}D` },
          { label: 'Created',    value: created, color: '#8b949e' },
        ]} />

        {data.fingerprint?.length > 0 && (
          <FingerprintPreview values={data.fingerprint} note={data.note} />
        )}
      </div>

      <div style={{ padding: '10px 18px', background: '#0d1117', borderTop: '1px solid #21262d', display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <p style={{ fontSize: 11, color: '#484f58', fontFamily: 'monospace' }}>{data.video_path}</p>
        <p style={{ fontSize: 11, color: '#484f58', fontFamily: 'monospace' }}>id: {data.video_id}</p>
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export default function Fingerprint() {
  const [videoId, setVideoId]   = useState('')
  const [postResult, setPostResult] = useState(null)
  const [getResult, setGetResult]   = useState(null)
  const [activeTab, setActiveTab]   = useState('post')   // 'post' | 'get'
  const [status, setStatus]     = useState(null)   // { type: 'running'|'success'|'error', msg }
  const [loadingPost, setLoadingPost] = useState(false)
  const [loadingGet, setLoadingGet]   = useState(false)

  const loading = loadingPost || loadingGet

  const runPost = async () => {
    if (!videoId.trim()) return
    setLoadingPost(true)
    setStatus({ type: 'running', msg: `Running fingerprint pipeline for ${videoId} — may take 30–120 s…` })
    try {
      const res = await axios.post(`/api/fingerprint/${videoId}`)
      setPostResult(res.data)
      setStatus({ type: 'success', msg: `Pipeline complete · ${res.data.frames_processed} frames · ${res.data.vector_dimensions}D vector saved` })
      setActiveTab('post')
    } catch (e) {
      setStatus({ type: 'error', msg: e.response?.data?.detail || e.message || 'Pipeline failed' })
    } finally {
      setLoadingPost(false)
    }
  }

  const runGet = async () => {
    if (!videoId.trim()) return
    setLoadingGet(true)
    setStatus({ type: 'running', msg: `Fetching stored fingerprint for ${videoId}…` })
    try {
      const res = await axios.get(`/api/fingerprint/${videoId}`)
      setGetResult(res.data)
      setStatus({ type: 'success', msg: `Fingerprint found · created ${new Date(res.data.created_at).toLocaleString()}` })
      setActiveTab('get')
    } catch (e) {
      setStatus({ type: 'error', msg: e.response?.data?.detail || e.message || 'Not found' })
    } finally {
      setLoadingGet(false)
    }
  }

  // Status bar colors
  const statusStyle = {
    running: { bg: 'rgba(56,139,253,0.07)', border: '#388bfd', color: '#58a6ff' },
    success: { bg: 'rgba(46,160,67,0.07)',  border: '#2ea043', color: '#3fb950' },
    error:   { bg: 'rgba(248,81,73,0.07)',  border: '#f85149', color: '#f85149' },
  }[status?.type] || {}

  const hasResults = postResult || getResult

  return (
    <div style={{ width: '100%', maxWidth: 760 }}>

      {/* Search bar */}
      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 12, padding: 24, marginBottom: 20 }}>
        <p style={{ fontSize: 11, color: '#484f58', fontFamily: 'monospace', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Video ID</p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <input
            value={videoId}
            onChange={e => setVideoId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && runPost()}
            placeholder="e.g. 9b332136-734d-4002-b6dc-a25c7a2cff4c"
            style={{
              flex: 1, minWidth: 200, padding: '10px 14px', background: '#0d1117',
              border: '1px solid #30363d', borderRadius: 8,
              color: '#e6edf3', fontSize: 13, fontFamily: 'monospace', outline: 'none',
            }}
          />
          <button onClick={runGet} disabled={loading || !videoId.trim()} style={{
            padding: '10px 18px', borderRadius: 8, border: '1px solid #30363d',
            background: 'transparent', color: loadingGet ? '#484f58' : '#8b949e',
            fontWeight: 600, fontSize: 13, cursor: loading || !videoId.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !videoId.trim() ? 0.5 : 1,
          }}>
            {loadingGet ? 'Loading…' : 'GET status'}
          </button>
          <button onClick={runPost} disabled={loading || !videoId.trim()} style={{
            padding: '10px 20px', borderRadius: 8, border: 'none',
            background: loading || !videoId.trim() ? '#21262d' : '#238636',
            color: loading || !videoId.trim() ? '#484f58' : '#fff',
            fontWeight: 600, fontSize: 13, cursor: loading || !videoId.trim() ? 'not-allowed' : 'pointer',
          }}>
            {loadingPost ? 'Running…' : '▶ Run fingerprint'}
          </button>
        </div>

        {/* Status bar */}
        {status && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, marginTop: 14,
            padding: '10px 14px', borderRadius: 8,
            background: statusStyle.bg, border: `1px solid ${statusStyle.border}`,
            color: statusStyle.color, fontSize: 12, fontFamily: 'monospace',
          }}>
            {status.type === 'running' && (
              <div style={{ width: 13, height: 13, border: `2px solid ${statusStyle.border}40`, borderTopColor: statusStyle.color, borderRadius: '50%', animation: 'spin 0.7s linear infinite', flexShrink: 0 }} />
            )}
            <span>{status.msg}</span>
          </div>
        )}
      </div>

      {/* Tabs + results */}
      {hasResults && (
        <>
          <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
            {[
              { key: 'post', label: 'Pipeline result', show: !!postResult },
              { key: 'get',  label: 'Stored fingerprint', show: !!getResult },
            ].filter(t => t.show).map(t => (
              <button key={t.key} onClick={() => setActiveTab(t.key)} style={{
                padding: '7px 16px', borderRadius: 8, border: '1px solid',
                borderColor: activeTab === t.key ? '#388bfd' : '#30363d',
                background:  activeTab === t.key ? 'rgba(56,139,253,0.08)' : '#161b22',
                color:       activeTab === t.key ? '#58a6ff' : '#8b949e',
                fontSize: 12, fontWeight: 600, cursor: 'pointer',
              }}>{t.label}</button>
            ))}
          </div>

          {activeTab === 'post' && postResult && <PostResultCard data={postResult} />}
          {activeTab === 'get'  && getResult  && <GetResultCard  data={getResult}  />}
        </>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  )
}