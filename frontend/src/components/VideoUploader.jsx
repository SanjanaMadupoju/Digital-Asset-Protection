import React, { useState, useRef, useCallback } from 'react'
import axios from 'axios'

// ─── tiny helper: format bytes into KB / MB ───────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

// ─── allowed video MIME types for front-end check ────────────────────────
const ALLOWED_TYPES = [
  'video/mp4',
  'video/quicktime',        // .mov
  'video/x-msvideo',        // .avi
  'video/x-matroska',       // .mkv
  'video/webm',
]

export default function VideoUploader() {

  // State variables — each controls one piece of the UI
  const [file, setFile]           = useState(null)      // the selected File object
  const [dragging, setDragging]   = useState(false)     // is user dragging over the zone?
  const [uploading, setUploading] = useState(false)     // is upload in progress?
  const [progress, setProgress]   = useState(0)         // 0–100 upload %
  const [result, setResult]       = useState(null)      // success response from backend
  const [error, setError]         = useState(null)      // error message string

  // Ref to the hidden <input type="file"> so we can trigger it on click
  const fileInputRef = useRef()

  // ── called when user picks or drops a file ──────────────────────────────
  const handleFileSelect = useCallback((selectedFile) => {
    if (!selectedFile) return

    // Front-end validation: check MIME type
    const isValidType = ALLOWED_TYPES.includes(selectedFile.type) ||
      /\.(mp4|mov|avi|mkv|webm)$/i.test(selectedFile.name)

    if (!isValidType) {
      setError('Please upload a video file: MP4, MOV, AVI, MKV, or WebM.')
      return
    }

    // Clear any previous state and set the new file
    setFile(selectedFile)
    setError(null)
    setResult(null)
    setProgress(0)
  }, [])

  // ── drag-and-drop handlers ───────────────────────────────────────────────
  const onDragOver  = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = ()  => setDragging(false)
  const onDrop      = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFileSelect(e.dataTransfer.files[0])
  }

  // ── file input change ────────────────────────────────────────────────────
  const onInputChange = (e) => handleFileSelect(e.target.files[0])

  // ── reset everything ────────────────────────────────────────────────────
  const reset = () => {
    setFile(null); setError(null); setResult(null); setProgress(0)
    // Also clear the hidden input so the same file can be re-selected
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // ── main upload function ─────────────────────────────────────────────────
  const handleUpload = async () => {
    if (!file || uploading) return

    setUploading(true)
    setError(null)

    // FormData is how browsers send files to a backend
    const formData = new FormData()
    formData.append('file', file)   // 'file' must match the FastAPI parameter name

    try {
      const response = await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        // onUploadProgress fires repeatedly as chunks are sent
        onUploadProgress: (event) => {
          const percent = Math.round((event.loaded / event.total) * 100)
          setProgress(percent)
        }
      })
      setResult(response.data)

    } catch (err) {
      // Try to get the error detail from FastAPI, fall back to generic message
      const msg = err.response?.data?.detail || err.message || 'Upload failed. Is the backend running?'
      setError(msg)
    } finally {
      setUploading(false)
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div style={{
      width: '100%',
      maxWidth: '560px',
      background: '#161b22',
      border: '1px solid #30363d',
      borderRadius: '14px',
      padding: '32px',
    }}>

      {/* ── Drop Zone ── */}
      <div
        onClick={() => !file && fileInputRef.current.click()}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        style={{
          border: `2px dashed ${dragging ? '#388bfd' : file ? '#2ea043' : '#30363d'}`,
          borderRadius: '10px',
          padding: '36px 20px',
          textAlign: 'center',
          cursor: file ? 'default' : 'pointer',
          background: dragging ? '#0d1f36' : file ? '#0d2217' : 'transparent',
          transition: 'all 0.2s',
        }}
      >
        {/* Hidden real file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".mp4,.mov,.avi,.mkv,.webm,video/*"
          style={{ display: 'none' }}
          onChange={onInputChange}
        />

        {/* Icon */}
        <div style={{ fontSize: '36px', marginBottom: '10px', lineHeight: 1 }}>
          {file ? '✅' : '🎬'}
        </div>

        {!file ? (
          <>
            <p style={{ fontSize: '15px', color: '#8b949e', marginBottom: '6px' }}>
              Drag & drop your video here
            </p>
            <p style={{ fontSize: '13px', color: '#484f58' }}>
              or click to browse files
            </p>
          </>
        ) : (
          <p style={{ fontSize: '14px', color: '#3fb950', fontWeight: 500 }}>
            {file.name}
          </p>
        )}
      </div>

      {/* ── File info row (shows after file is selected) ── */}
      {file && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: '14px',
          padding: '12px 14px',
          background: '#0d1117',
          border: '1px solid #30363d',
          borderRadius: '8px',
        }}>
          <div>
            <p style={{ fontSize: '13px', color: '#e6edf3', fontWeight: 500 }}>
              {file.name}
            </p>
            <p style={{ fontSize: '11px', color: '#484f58', marginTop: '3px' }}>
              {formatBytes(file.size)}
            </p>
          </div>
          {/* Remove file button */}
          <button
            onClick={reset}
            title="Remove file"
            style={{
              background: 'none', border: 'none',
              color: '#484f58', cursor: 'pointer',
              fontSize: '20px', lineHeight: 1, padding: '4px'
            }}
          >×</button>
        </div>
      )}

      {/* ── Progress bar (shows while uploading) ── */}
      {uploading && (
        <div style={{ marginTop: '16px' }}>
          <div style={{
            height: '6px', borderRadius: '3px',
            background: '#21262d', overflow: 'hidden'
          }}>
            <div style={{
              height: '100%',
              width: `${progress}%`,
              background: progress === 100 ? '#2ea043' : '#1f6feb',
              borderRadius: '3px',
              transition: 'width 0.25s ease',
            }}/>
          </div>
          <p style={{
            fontSize: '11px', color: '#484f58',
            textAlign: 'right', marginTop: '4px'
          }}>
            {progress}%
          </p>
        </div>
      )}

      {/* ── Upload button ── */}
      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        style={{
          marginTop: '18px',
          width: '100%',
          padding: '12px',
          borderRadius: '8px',
          border: '1px solid transparent',
          fontSize: '14px',
          fontWeight: 600,
          cursor: (!file || uploading) ? 'not-allowed' : 'pointer',
          background: (!file || uploading) ? '#21262d' : '#238636',
          borderColor: (!file || uploading) ? '#30363d' : '#2ea043',
          color: (!file || uploading) ? '#484f58' : '#ffffff',
          transition: 'all 0.2s',
        }}
      >
        {uploading ? `Uploading... ${progress}%` : 'Upload Video'}
      </button>

      {/* ── Error message ── */}
      {error && (
        <div style={{
          marginTop: '16px',
          padding: '14px',
          background: '#1c0b0b',
          border: '1px solid #f85149',
          borderRadius: '8px',
        }}>
          <p style={{ fontSize: '13px', fontWeight: 600, color: '#f85149', marginBottom: '4px' }}>
            Upload failed
          </p>
          <p style={{ fontSize: '12px', color: '#b22b2b' }}>{error}</p>
          <p style={{ fontSize: '11px', color: '#484f58', marginTop: '8px' }}>
            Make sure the backend is running: <code style={{color:'#8b949e'}}>uvicorn main:app --reload</code>
          </p>
        </div>
      )}

      {/* ── Success result ── */}
      {result && (
        <div style={{
          marginTop: '16px',
          padding: '16px',
          background: '#0d2217',
          border: '1px solid #2ea043',
          borderRadius: '8px',
        }}>
          <p style={{ fontSize: '13px', fontWeight: 600, color: '#3fb950', marginBottom: '12px' }}>
            Upload successful
          </p>

          {/* Key-value rows */}
          {[
            { label: 'Video ID',  value: result.video_id,    mono: true  },
            { label: 'Filename',  value: result.filename,    mono: false },
            { label: 'Saved at',  value: result.saved_path,  mono: true  },
          ].map(({ label, value, mono }) => (
            <div key={label} style={{
              display: 'flex',
              justifyContent: 'space-between',
              gap: '12px',
              padding: '6px 0',
              borderBottom: '1px solid #1b3829',
              fontSize: '12px',
            }}>
              <span style={{ color: '#484f58', flexShrink: 0 }}>{label}</span>
              <span style={{
                color: '#e6edf3',
                fontFamily: mono ? 'monospace' : 'inherit',
                fontSize: mono ? '11px' : '12px',
                textAlign: 'right',
                wordBreak: 'break-all',
              }}>
                {value}
              </span>
            </div>
          ))}

          {/* Next step callout */}
          <div style={{
            marginTop: '14px',
            padding: '10px 12px',
            background: '#0d1f36',
            border: '1px solid #1f6feb',
            borderRadius: '6px',
          }}>
            <p style={{ fontSize: '12px', color: '#58a6ff', fontWeight: 600, marginBottom: '4px' }}>
              What happens next (Step 2)
            </p>
            <p style={{ fontSize: '11px', color: '#8b949e', lineHeight: 1.6 }}>
              Copy the <strong style={{color:'#e6edf3'}}>Video ID</strong> above.
              In Step 2, OpenCV will extract frames from this file and CLIP will
              generate a 512-dimensional fingerprint vector for it.
            </p>
            {/* Copy button */}
            <button
              onClick={() => navigator.clipboard.writeText(result.video_id)}
              style={{
                marginTop: '8px',
                padding: '5px 12px',
                fontSize: '11px',
                fontWeight: 600,
                background: '#1f6feb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer',
              }}
            >
              Copy Video ID
            </button>
          </div>
        </div>
      )}
    </div>
  )
}