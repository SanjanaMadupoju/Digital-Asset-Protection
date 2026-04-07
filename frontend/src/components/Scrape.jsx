import React, { useState, useRef } from 'react'
import axios from 'axios'

// ── Tag chip input ────────────────────────────────────────────────────────────
function ChipInput({ label, placeholder, items, onChange }) {
  console.log(items)
  const [val, setVal] = useState('')
  const add = () => {
    const v = val.trim()
    console.log('val:', v)
    console.log('items:', items)
    console.log('onChange type:', typeof onChange)
    if (!v || items.includes(v)) return
    const newItems = [...items, v]
    console.log('calling onChange with:', newItems)
    onChange(newItems)
    setVal('')
  }
  const remove = (i) => onChange(items.filter((_, idx) => idx !== i))
  return (
    <div>
      <p style={{ fontSize: 11, color: '#484f58', marginBottom: 6 }}>{label}</p>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <input
          value={val}
          onChange={e => setVal(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && add()}
          placeholder={placeholder}
          style={{ flex: 1, padding: '8px 12px', background: '#0d1117', border: '1px solid #30363d', borderRadius: 8, color: '#e6edf3', fontSize: 13, fontFamily: 'monospace', outline: 'none' }}
        />
        <button onClick={add} style={{ padding: '8px 14px', borderRadius: 8, border: '1px solid #30363d', background: '#161b22', color: '#8b949e', fontSize: 12, cursor: 'pointer' }}>
          Add
        </button>
      </div>
      {items.length > 0 && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {items.map((item, i) => (
            <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '3px 10px', borderRadius: 20, background: '#161b22', border: '1px solid #30363d', fontSize: 12, color: '#e6edf3' }}>
              {item}
              <button onClick={() => remove(i)} style={{ border: 'none', background: 'none', color: '#484f58', cursor: 'pointer', fontSize: 14, lineHeight: 1, padding: 0 }}>×</button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function Badge({ children, color = '#8b949e', bg = '#161b22', border = '#30363d' }) {
  return (
    <span style={{ padding: '2px 9px', borderRadius: 20, fontSize: 10, fontWeight: 700, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.05em', background: bg, border: `1px solid ${border}`, color }}>
      {children}
    </span>
  )
}

function platformBadge(p = '') {
  const map = { youtube: { color: '#f85149', bg: '#1c0b0b', border: '#f85149' }, dailymotion: { color: '#58a6ff', bg: '#0d1f36', border: '#388bfd' }, twitter: { color: '#d29922', bg: '#1c1200', border: '#d29922' } }
  return map[p.toLowerCase()] || { color: '#8b949e', bg: '#161b22', border: '#30363d' }
}

function statusStyle(s) {
  if (s === 'flagged')              return { color: '#f85149', bg: '#1c0b0b', border: '#f85149' }
  if (s === 'fingerprinted')        return { color: '#3fb950', bg: '#0d2217', border: '#2ea043' }
  if (s === 'pending_fingerprint')  return { color: '#d29922', bg: '#1c1200', border: '#d29922' }
  return { color: '#8b949e', bg: '#161b22', border: '#30363d' }
}

function MetricCard({ value, label, color }) {
  return (
    <div style={{ background: '#0d1117', border: '1px solid #21262d', borderRadius: 8, padding: '12px 14px' }}>
      <p style={{ fontSize: 20, fontWeight: 700, color: color || '#e6edf3', fontFamily: 'monospace' }}>{value}</p>
      <p style={{ fontSize: 10, color: '#484f58', marginTop: 3, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</p>
    </div>
  )
}

// ── POST result ───────────────────────────────────────────────────────────────
function PostResult({ data }) {
  return (
    <div style={{ background: '#0d2217', border: '1px solid #2ea043', borderRadius: 12, overflow: 'hidden' }}>
      <div style={{ padding: '12px 18px', background: '#0d1117', borderBottom: '1px solid #2ea043', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#3fb950' }} />
        <span style={{ fontSize: 13, fontWeight: 700, color: '#e6edf3' }}>Scraper complete</span>
      </div>
      <div style={{ padding: '16px 18px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 16 }}>
          <MetricCard value={data.total_found}        label="URLs found" />
          <MetricCard value={data.saved_to_mongo}     label="Saved to MongoDB" />
          <MetricCard value={data.duplicates_skipped} label="Duplicates skipped" />
        </div>

        {/* Platform breakdown */}
        {data.by_platform && Object.keys(data.by_platform).length > 0 && (
          <div style={{ marginBottom: 14 }}>
            <p style={{ fontSize: 10, color: '#484f58', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>By platform</p>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {Object.entries(data.by_platform).map(([p, c]) => {
                const s = platformBadge(p)
                return <Badge key={p} color={s.color} bg={s.bg} border={s.border}>{p}: {c}</Badge>
              })}
            </div>
          </div>
        )}

        {/* Sample URLs */}
        {data.sample_urls?.length > 0 && (
          <div style={{ marginBottom: 14 }}>
            <p style={{ fontSize: 10, color: '#484f58', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>Sample URLs (first 5)</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              {data.sample_urls.map((url, i) => (
                <div key={i} style={{ padding: '7px 12px', background: '#0d1117', borderRadius: 6, fontSize: 11, fontFamily: 'monospace' }}>
                  <a href={url} target="_blank" rel="noreferrer" style={{ color: '#58a6ff', textDecoration: 'none', wordBreak: 'break-all' }}>{url}</a>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Errors */}
        {data.errors?.length > 0 && (
          <div style={{ padding: '10px 14px', background: '#1c0b0b', border: '1px solid #f85149', borderRadius: 8, marginBottom: 14 }}>
            {data.errors.map((e, i) => <p key={i} style={{ fontSize: 12, color: '#f85149', fontFamily: 'monospace' }}>⚠ {e}</p>)}
          </div>
        )}

        <div style={{ padding: '10px 14px', background: 'rgba(46,160,67,0.06)', border: '1px solid rgba(46,160,67,0.15)', borderRadius: 8 }}>
          <p style={{ fontSize: 11, color: '#3fb950', fontFamily: 'monospace' }}>→ {data.next_step}</p>
        </div>
      </div>
    </div>
  )
}

// ── GET result ────────────────────────────────────────────────────────────────
function GetResult({ data }) {
  const [filter, setFilter] = useState('all')
  const filtered = filter === 'all' ? data.urls : filter === 'flagged' ? data.urls.filter(u => u.flagged) : filter === 'pending' ? data.urls.filter(u => u.status === 'pending_fingerprint') : data.urls.filter(u => u.status === 'fingerprinted')

  return (
    <div style={{ background: '#0d1f36', border: '1px solid #388bfd', borderRadius: 12, overflow: 'hidden' }}>
      <div style={{ padding: '12px 18px', background: '#0d1117', borderBottom: '1px solid #388bfd', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#58a6ff' }} />
        <span style={{ fontSize: 13, fontWeight: 700, color: '#e6edf3' }}>Scraped URLs for {data.video_id}</span>
      </div>
      <div style={{ padding: '16px 18px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 16 }}>
          <MetricCard value={data.total}        label="Total" />
          <MetricCard value={data.pending}       label="Pending" color="#d29922" />
          <MetricCard value={data.fingerprinted} label="Fingerprinted" color="#3fb950" />
          <MetricCard value={data.flagged}       label="Flagged" color="#f85149" />
        </div>

        {/* Filter bar */}
        <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
          {[['all', `All (${data.total})`], ['flagged', `Flagged (${data.flagged})`], ['pending', 'Pending'], ['fingerprinted', 'Done']].map(([key, label]) => (
            <button key={key} onClick={() => setFilter(key)} style={{
              padding: '4px 12px', borderRadius: 20, border: '1px solid',
              borderColor: filter === key ? '#388bfd' : '#30363d',
              background: filter === key ? 'rgba(56,139,253,0.1)' : '#161b22',
              color: filter === key ? '#58a6ff' : '#8b949e',
              fontSize: 11, cursor: 'pointer',
            }}>{label}</button>
          ))}
        </div>

        {/* URL list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 320, overflowY: 'auto' }}>
          {filtered.length === 0 ? (
            <p style={{ fontSize: 13, color: '#484f58', textAlign: 'center', padding: '20px 0' }}>No results for this filter.</p>
          ) : filtered.map((item, i) => {
            const ps = platformBadge(item.platform)
            const ss = statusStyle(item.status)
            return (
              <div key={i} style={{ padding: '10px 12px', background: '#0d1117', border: '1px solid #21262d', borderRadius: 8 }}>
                <a href={item.url} target="_blank" rel="noreferrer" style={{ fontSize: 11, fontFamily: 'monospace', color: '#58a6ff', wordBreak: 'break-all', display: 'block', marginBottom: 7, textDecoration: 'none' }}>
                  {item.url}
                </a>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <Badge color={ps.color} bg={ps.bg} border={ps.border}>{item.platform}</Badge>
                  <Badge color={ss.color} bg={ss.bg} border={ss.border}>{item.status}</Badge>
                  {item.flagged && <Badge color="#f85149" bg="#1c0b0b" border="#f85149">flagged</Badge>}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function Scrape() {
  const [videoId,  setVideoId]  = useState('')
  const [sport,    setSport]    = useState('')
  const [maxRes,   setMaxRes]   = useState(10)
  const [keywords, setKeywords] = useState([])
  const [channels, setChannels] = useState([])
  console.log('channels state:', channels)

  const [postResult, setPostResult] = useState(null)
  const [getResult,  setGetResult]  = useState(null)
  const [activeTab,  setActiveTab]  = useState('post')
  const [status,     setStatus]     = useState(null)   // { type, msg }
  const [loadingPost, setLoadingPost] = useState(false)
  const [loadingGet,  setLoadingGet]  = useState(false)

  const loading = loadingPost || loadingGet

  const showStatus = (type, msg) => setStatus({ type, msg })

  const runPost = async () => {
    if (!videoId.trim()) return showStatus('error', 'Video ID is required')
    setLoadingPost(true)
    showStatus('running', `Running scraper for video_id: ${videoId}…`)
    try {
      const res = await axios.post('/api/scrape', {
        video_id:            videoId.trim(),
        sport:               sport.trim(),
        keywords:            keywords.join(' '), 
        suspicious_channels: channels,
        max_results:         Number(maxRes),
      })
      setPostResult(res.data)
      showStatus('success', `Done · ${res.data.total_found} URLs found · ${res.data.saved_to_mongo} saved`)
      setActiveTab('post')
    } catch (e) {
      showStatus('error', e.response?.data?.detail || e.message || 'Scraper failed')
    } finally {
      setLoadingPost(false)
    }
  }

  const runGet = async () => {
    if (!videoId.trim()) return showStatus('error', 'Video ID is required')
    setLoadingGet(true)
    showStatus('running', `Fetching scraped URLs for ${videoId}…`)
    try {
      const res = await axios.get(`/api/scrape/${videoId.trim()}`)
      setGetResult(res.data)
      showStatus('success', `Found ${res.data.total} URLs · ${res.data.flagged} flagged`)
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

  const hasResults = postResult || getResult

  return (
    <div style={{ width: '100%', maxWidth: 760 }}>

      {/* Form panel */}
      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 12, padding: 24, marginBottom: 20 }}>

        {/* Video ID */}
        <div style={{ marginBottom: 16 }}>
          <p style={{ fontSize: 11, color: '#484f58', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Video ID</p>
          <input value={videoId} onChange={e => setVideoId(e.target.value)} placeholder="9b332136-734d-4002-b6dc-a25c7a2cff4c"
            style={{ width: '100%', padding: '10px 14px', background: '#0d1117', border: '1px solid #30363d', borderRadius: 8, color: '#e6edf3', fontSize: 13, fontFamily: 'monospace', outline: 'none' }} />
        </div>

        {/* Sport + Max results */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          <div>
            <p style={{ fontSize: 11, color: '#484f58', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Sport / category</p>
            <input value={sport} onChange={e => setSport(e.target.value)} placeholder="e.g. football, cricket"
              style={{ width: '100%', padding: '10px 14px', background: '#0d1117', border: '1px solid #30363d', borderRadius: 8, color: '#e6edf3', fontSize: 13, outline: 'none' }} />
          </div>
          <div>
            <p style={{ fontSize: 11, color: '#484f58', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Max results per source</p>
            <input type="number" value={maxRes} onChange={e => setMaxRes(e.target.value)} min={1} max={100}
              style={{ width: '100%', padding: '10px 14px', background: '#0d1117', border: '1px solid #30363d', borderRadius: 8, color: '#e6edf3', fontSize: 13, outline: 'none' }} />
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <ChipInput label="KEYWORDS" placeholder="Add keyword and press Enter" items={keywords} onChange={setKeywords} />
        </div>
        <div style={{ marginBottom: 20 }}>
          <ChipInput label="SUSPICIOUS CHANNELS" placeholder="e.g. https://youtube.com/@channel" items={channels} onChange={setChannels} />
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={runGet} disabled={loading || !videoId.trim()} style={{
            padding: '10px 18px', borderRadius: 8, border: '1px solid #30363d',
            background: 'transparent', color: '#8b949e', fontWeight: 600, fontSize: 13,
            cursor: loading || !videoId.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !videoId.trim() ? 0.4 : 1,
          }}>
            {loadingGet ? 'Loading…' : 'GET scraped'}
          </button>
          <button onClick={runPost} disabled={loading || !videoId.trim()} style={{
            padding: '10px 20px', borderRadius: 8, border: 'none',
            background: loading || !videoId.trim() ? '#21262d' : '#238636',
            color: loading || !videoId.trim() ? '#484f58' : '#fff',
            fontWeight: 600, fontSize: 13,
            cursor: loading || !videoId.trim() ? 'not-allowed' : 'pointer',
          }}>
            {loadingPost ? 'Running…' : '▶ Run scraper'}
          </button>
        </div>

        {/* Status */}
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
      {hasResults && (
        <>
          <div style={{ display: 'flex', gap: 4, marginBottom: 14 }}>
            {[['post', 'Scraper result', !!postResult], ['get', 'Stored URLs', !!getResult]].filter(t => t[2]).map(([key, label]) => (
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
          {activeTab === 'get'  && getResult  && <GetResult  data={getResult}  />}
        </>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}