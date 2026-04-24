import React, { useState } from 'react'
import axios from 'axios'

export default function WatermarkedPage() {
  const [videoId,  setVideoId]  = useState('')
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)
  const [error,    setError]    = useState(null)

  const fetch = async () => {
    if (!videoId.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const res = await axios.get(`/api/watermarked/${videoId.trim()}`)
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Not found')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    try {
        const res = await axios.get(`/api/download/${videoId.trim()}`, {
            responseType: "blob"
        })
        console.log(res)
        const blobUrl = window.URL.createObjectURL(new Blob([res.data], { type: "video/mp4" }))
        // const blobUrl = window.URL.createObjectURL(new Blob([res.data]))
        const a = document.createElement("a")
        a.href = blobUrl
        a.download = `watermarked_${videoId.trim()}.mp4`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(blobUrl)
    } catch (e) {
        setError(e.response?.data?.detail || e.message || "Download failed")
    }
  }

  return (
    <div className="animate-fade-up">
      <div className="page-heading">
        <div className="page-heading-badge">
          <span className="badge badge-success">Watermarked</span>
        </div>
        <h2 className="page-heading-title">Watermarked video</h2>
        <p className="page-heading-sub">
          View and download the watermarked version of your video
        </p>
      </div>

      {/* Shield icon */}
      <div className="card mb-16" style={{ textAlign: 'center', padding: '24px' }}>
        <div style={{ fontSize: 48, marginBottom: 8 }}>🛡️</div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Your video has an invisible watermark embedded in every frame.
          The watermark carries your organisation ID and video ID —
          provable ownership even after re-encoding or re-uploading.
        </p>
      </div>

      {/* Input */}
      <div className="card">
        <label style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, display: 'block' }}>
          Video ID (from Step 1)
        </label>
        <div className="flex" style={{ gap: 10, marginBottom: 16 }}>
          <input
            className="input input-mono"
            placeholder="e.g. 9b332136-734d-4002-b6dc-a25c7a2cff4c"
            value={videoId}
            onChange={e => setVideoId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && fetch()}
          />
          <button
            className="btn btn-primary"
            onClick={fetch}
            disabled={!videoId.trim() || loading}
          >
            {loading
              ? <><div className="processing-spinner" /> Loading</>
              : 'Load video'
            }
          </button>
        </div>

        {error && (
          <div className="alert alert-danger">
            {error}
            {error.includes('Step 2') && (
              <p style={{ marginTop: 8, fontSize: 11 }}>
                Run <strong>Step 2 · Fingerprint</strong> first to generate the watermarked video.
              </p>
            )}
          </div>
        )}

        {/* Video player + download */}
        {result && (
          <div className="success-burst">
            {/* Info row */}
            <div className="flex-between mb-16" style={{ flexWrap: 'wrap', gap: 8 }}>
              <div>
                <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                  {result.filename}
                </p>
                {result.n_frames && (
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                    {result.n_frames} sampled frames · Watermark embedded
                  </p>
                )}
              </div>
              <span className="badge badge-success">✅ Watermarked</span>
            </div>

            {/* Video player */}
            <div style={{
              borderRadius: 'var(--radius-lg)',
              overflow: 'hidden',
              background: '#000',
              border: '1px solid var(--border)',
              marginBottom: 16,
              position: 'relative',
            }}>
              <video
                key={result.watermarked_video_url}
                controls
                style={{ width: '100%', display: 'block', maxHeight: 400 }}
                preload="metadata"
              >
                <source src={result.watermarked_video_url} type="video/mp4" />
                Your browser does not support the video tag.
              </video>

              {/* Watermark overlay badge */}
              <div style={{
                position: 'absolute',
                top: 10, right: 10,
                background: 'rgba(0,0,0,0.7)',
                border: '1px solid rgba(85,99,255,0.5)',
                borderRadius: 'var(--radius-sm)',
                padding: '3px 10px',
                fontSize: 11,
                color: '#7b8fff',
                backdropFilter: 'blur(4px)',
              }}>
                🛡️ Watermarked
              </div>
            </div>

            {/* Download button */}
            <button
                onClick={() => handleDownload()}
                className="btn btn-primary btn-full"
                style={{ textDecoration: 'none', display: 'flex', justifyContent: 'center' }}
            >
                ⬇️ Download watermarked video
            </button>

            {/* Info alert */}
            <div className="alert alert-info mt-16" style={{ fontSize: 12 }}>
              <strong>What is the watermark?</strong><br />
              Every frame of this video contains an invisible mark embedded using
              DCT spread-spectrum encoding. It is undetectable to the human eye
              but can be extracted algorithmically to prove ownership.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}