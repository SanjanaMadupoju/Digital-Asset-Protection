import React, { useState, useRef, useCallback } from 'react'
import axios from 'axios'

function formatBytes(b) {
  if (b < 1024 * 1024) return `${(b/1024).toFixed(1)} KB`
  return `${(b/(1024*1024)).toFixed(2)} MB`
}

const ALLOWED = ['video/mp4','video/quicktime','video/x-msvideo','video/x-matroska','video/webm']

function ShieldViz({ state }) {
  const icons = { idle: '🛡️', uploading: '⏳', success: '✅', error: '❌' }
  const colors = {
    idle:      'var(--border-accent)',
    uploading: 'var(--accent)',
    success:   'var(--border-success)',
    error:     'var(--border-danger)',
  }
  return (
    <div className="shield-container">
      <div className="shield-rings" style={{ marginBottom: 8 }}>
        {state === 'uploading' && (
          <>
            <div className="shield-ring" style={{ borderColor: colors[state] }} />
            <div className="shield-ring" style={{ borderColor: colors[state], animationDelay: '0.6s' }} />
            <div className="shield-ring" style={{ borderColor: colors[state], animationDelay: '1.2s' }} />
          </>
        )}
        <div
          className={`shield-icon ${state === 'success' ? 'locked' : ''}`}
          style={{ position: 'relative', zIndex: 2 }}
        >
          {icons[state]}
        </div>
      </div>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', textAlign: 'center' }}>
        {state === 'idle'      && 'Drop your video to begin protection'}
        {state === 'uploading' && 'Securing your asset...'}
        {state === 'success'   && 'Asset secured successfully'}
        {state === 'error'     && 'Upload failed — try again'}
      </p>
    </div>
  )
}

export default function UploadPage() {
  const [file, setFile]         = useState(null)
  const [dragging, setDragging] = useState(false)
  const [state, setState]       = useState('idle')
  const [progress, setProgress] = useState(0)
  const [result, setResult]     = useState(null)
  const [error, setError]       = useState(null)
  const inputRef = useRef()

  const handleFile = useCallback((f) => {
    if (!f) return
    const ok = ALLOWED.includes(f.type) || /\.(mp4|mov|avi|mkv|webm)$/i.test(f.name)
    if (!ok) { setError('Unsupported format. Use MP4, MOV, AVI, MKV or WebM.'); return }
    setFile(f); setError(null); setResult(null); setProgress(0); setState('idle')
  }, [])

  const onDragOver  = e => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)
  const onDrop      = e => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }
  const onInput     = e => handleFile(e.target.files[0])

  const reset = () => { setFile(null); setResult(null); setError(null); setProgress(0); setState('idle'); if (inputRef.current) inputRef.current.value = '' }

  const upload = async () => {
    if (!file) return
    setState('uploading'); setError(null)
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res = await axios.post('/api/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: e => setProgress(Math.round(e.loaded / e.total * 100))
      })
      setResult(res.data); setState('success')
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Upload failed')
      setState('error')
    }
  }

  return (
    <div className="upload-zone-wrapper animate-fade-up">

      {/* Page heading */}
      <div className="page-heading">
        <div className="page-heading-badge">
          <span className="badge badge-accent">Step 1</span>
        </div>
        <h2 className="page-heading-title">Upload your sports video</h2>
        <p className="page-heading-sub">Your video will be watermarked and fingerprinted in Step 2</p>
      </div>

      {/* Shield visualization */}
      <div className="card mb-16" style={{ textAlign: 'center' }}>
        <ShieldViz state={state} />
      </div>

      {/* Drop zone */}
      <div
        className={`dropzone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
        onClick={() => !file && inputRef.current.click()}
        onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}
      >
        <input ref={inputRef} type="file" accept=".mp4,.mov,.avi,.mkv,.webm,video/*" style={{ display:'none' }} onChange={onInput} />
        {!file ? (
          <>
            <p style={{ fontSize: 32, marginBottom: 10 }}>🎬</p>
            <p style={{ fontSize: 15, color: 'var(--text-secondary)', marginBottom: 6 }}>Drag & drop your video here</p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>or click to browse · MP4 MOV AVI MKV WebM · max 500MB</p>
          </>
        ) : (
          <>
            <p style={{ fontSize: 32, marginBottom: 10 }}>✅</p>
            <p style={{ fontSize: 14, color: 'var(--text-success)', fontWeight: 600 }}>{file.name}</p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{formatBytes(file.size)}</p>
          </>
        )}
      </div>

      {/* File info + remove */}
      {file && !result && (
        <div className="flex-between mt-12" style={{ padding: '10px 14px', background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{file.name} · {formatBytes(file.size)}</span>
          <button onClick={reset} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 18 }}>×</button>
        </div>
      )}

      {/* Progress */}
      {state === 'uploading' && (
        <div className="mt-12">
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'right', marginTop: 4 }}>{progress}%</p>
        </div>
      )}

      {/* Upload button */}
      {!result && (
        <button
          className={`btn btn-full mt-16 ${file && state !== 'uploading' ? 'btn-success' : 'btn-secondary'}`}
          onClick={upload}
          disabled={!file || state === 'uploading'}
        >
          {state === 'uploading' ? (
            <><div className="processing-spinner" /> Uploading {progress}%</>
          ) : 'Upload Video'}
        </button>
      )}

      {/* Error */}
      {error && (
        <div className="alert alert-danger mt-16">{error}</div>
      )}

      {/* Success */}
      {result && (
        <div className="card mt-16 success-burst" style={{ border: '1px solid var(--border-success)' }}>
          <p className="fw-600 text-success mb-12" style={{ fontSize: 13 }}>✅ Upload successful</p>
          {[
            { k: 'Video ID',  v: result.video_id,   mono: true },
            { k: 'Filename',  v: result.filename,    mono: false },
            { k: 'Saved at',  v: result.saved_path,  mono: true },
          ].map(({ k, v, mono }) => (
            <div className="result-row" key={k}>
              <span className="result-key">{k}</span>
              <span className={`result-val ${mono ? 'text-mono' : ''}`}>{v}</span>
            </div>
          ))}
          <div className="alert alert-info mt-16">
            <p className="fw-600 mb-8" style={{ fontSize: 12 }}>Next: Generate fingerprint</p>
            <p style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              Copy the Video ID and go to <strong>Step 2 · Fingerprint</strong> to watermark and generate your AI fingerprint.
            </p>
            <div className="flex mt-12" style={{ gap: 8 }}>
              <button className="btn btn-primary btn-sm" onClick={() => navigator.clipboard.writeText(result.video_id)}>
                Copy Video ID
              </button>
              <button className="btn btn-secondary btn-sm" onClick={reset}>Upload another</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}