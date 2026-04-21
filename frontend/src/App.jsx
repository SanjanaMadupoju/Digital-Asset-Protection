// import React, { useState } from 'react'
// import VideoUploader from './components/VideoUploader.jsx'
// import Dashboard from './components/Dashboard.jsx'
// import Fingerprint from './components/Fingerprint.jsx'
// import Scrape from './components/Scrape.jsx'
// import FingerprintScraped from './components/FingerprintScraped.jsx'
// import { useAuth } from './context/AuthContext'
// import AuthPage from './components/AuthPage'
// import './App.css'

// const NAV_LINKS = ['Features', 'How it works', 'Docs']

// const STATS = [
//   { value: '99.2%', label: 'Detection accuracy' },
//   { value: '<2s',   label: 'Real-time alerts'   },
//   { value: '50+',   label: 'Platforms monitored' },
//   { value: '512D',  label: 'CLIP fingerprint'    },
// ]

// const FEATURES = [
//   { icon: '🛡️', title: 'Invisible watermarking',  desc: 'Spread-spectrum text watermark embeds your org name and video ID invisibly. Survives re-encoding, compression and cropping.' },
//   { icon: '🧠', title: 'AI fingerprinting',        desc: 'CLIP ViT-B/32 generates a 512-dimensional semantic fingerprint. Matches copies even after quality changes or partial edits.' },
//   { icon: '🌐', title: 'Web-wide scraping',        desc: 'Continuously scans YouTube, Dailymotion, Twitter/X, Facebook and the open web using smart sport-specific queries.' },
//   { icon: '⚡', title: 'Near real-time alerts',    desc: 'Cosine similarity matching flags unauthorized copies the moment they are found, with full evidence reports.' },
// ]

// const STEPS = [
//   { key: 'upload',              label: '1 · Upload'              },
//   { key: 'fingerprint',         label: '2 · Fingerprint'         },
//   { key: 'scrape',              label: '3 · Scrape'              },
//   { key: 'fingerprintscraped',  label: '4 · Match scraped'       },
//   { key: 'dashboard',           label: '5–6 · Dashboard'         },
// ]

// function DashboardPreview() {
//   return (
//     <div style={{ background:'rgba(10,12,28,0.95)', border:'1px solid rgba(99,120,255,0.25)', borderRadius:18, overflow:'hidden', boxShadow:'0 40px 120px rgba(60,80,255,0.18), 0 0 0 1px rgba(99,120,255,0.1)', width:'100%', maxWidth:860, margin:'0 auto' }}>
//       <div style={{ background:'rgba(255,255,255,0.03)', borderBottom:'1px solid rgba(255,255,255,0.06)', padding:'12px 20px', display:'flex', alignItems:'center', gap:8 }}>
//         <div style={{ width:11, height:11, borderRadius:'50%', background:'#f85149' }}/>
//         <div style={{ width:11, height:11, borderRadius:'50%', background:'#d29922' }}/>
//         <div style={{ width:11, height:11, borderRadius:'50%', background:'#3fb950' }}/>
//         <div style={{ marginLeft:12, background:'rgba(255,255,255,0.06)', borderRadius:6, padding:'3px 16px', fontSize:11, color:'rgba(255,255,255,0.3)', flex:1, maxWidth:260 }}>
//           sports-fingerprint.ai / dashboard
//         </div>
//       </div>
//       <div style={{ display:'flex', height:420 }}>
//         <div style={{ width:190, background:'rgba(255,255,255,0.02)', borderRight:'1px solid rgba(255,255,255,0.05)', padding:'20px 0', flexShrink:0 }}>
//           <div style={{ padding:'0 16px 20px', display:'flex', alignItems:'center', gap:10 }}>
//             <div style={{ width:30, height:30, borderRadius:8, background:'rgba(85,99,255,0.25)', border:'1px solid rgba(85,99,255,0.4)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:14 }}>🛡️</div>
//             <span style={{ fontWeight:700, fontSize:14, color:'#e8ecf4' }}>SportGuard</span>
//           </div>
//           {['Dashboard','Assets','Detections','Reports','Settings'].map((item,i) => (
//             <div key={item} style={{ padding:'9px 16px', fontSize:13, cursor:'pointer', background:i===0?'rgba(85,99,255,0.12)':'transparent', color:i===0?'#7b8fff':'rgba(255,255,255,0.4)', borderLeft:i===0?'2px solid #5563ff':'2px solid transparent', display:'flex', alignItems:'center', gap:8 }}>
//               <span style={{ fontSize:13 }}>{['⊞','📁','🚨','📋','⚙️'][i]}</span>
//               {item}
//               {item==='Detections' && <span style={{ marginLeft:'auto', background:'#f85149', color:'#fff', fontSize:10, borderRadius:10, padding:'1px 6px' }}>3</span>}
//             </div>
//           ))}
//         </div>
//         <div style={{ flex:1, padding:20, overflow:'hidden' }}>
//           <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:10, marginBottom:16 }}>
//             {[{label:'Protected assets',val:'128',color:'#7b8fff'},{label:'Active scans',val:'24',color:'#3fb950'},{label:'Violations found',val:'7',color:'#f85149'},{label:'Match accuracy',val:'99%',color:'#d29922'}].map(s => (
//               <div key={s.label} style={{ background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.07)', borderRadius:10, padding:'12px 14px' }}>
//                 <div style={{ fontSize:20, fontWeight:700, color:s.color }}>{s.val}</div>
//                 <div style={{ fontSize:10, color:'rgba(255,255,255,0.35)', marginTop:3 }}>{s.label}</div>
//               </div>
//             ))}
//           </div>
//           <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:12 }}>
//             <div style={{ background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.07)', borderRadius:12, padding:14 }}>
//               <div style={{ fontSize:11, color:'rgba(255,255,255,0.4)', marginBottom:6 }}>Scan activity</div>
//               <div style={{ fontSize:18, fontWeight:700, color:'#e8ecf4', marginBottom:10 }}>1,284 <span style={{ fontSize:11, color:'#3fb950', fontWeight:400 }}>+12.4%</span></div>
//               <svg viewBox="0 0 200 50" width="100%" height="50">
//                 <polyline points="0,40 20,35 40,38 60,28 80,32 100,20 120,22 140,15 160,18 180,10 200,12" fill="none" stroke="#5563ff" strokeWidth="1.5" strokeLinejoin="round"/>
//                 <polyline points="0,40 20,35 40,38 60,28 80,32 100,20 120,22 140,15 160,18 180,10 200,12 200,50 0,50" fill="rgba(85,99,255,0.1)" stroke="none"/>
//               </svg>
//             </div>
//             <div style={{ background:'rgba(248,81,73,0.06)', border:'1px solid rgba(248,81,73,0.2)', borderRadius:12, padding:14 }}>
//               <div style={{ fontSize:11, color:'rgba(255,255,255,0.4)', marginBottom:6 }}>Latest violation</div>
//               <div style={{ fontSize:12, color:'#f85149', fontWeight:600, marginBottom:8 }}>🚨 Confirmed copy detected</div>
//               {[{label:'Platform',val:'YouTube'},{label:'Match',val:'94.2%'},{label:'Watermark',val:'Verified'}].map(r => (
//                 <div key={r.label} style={{ display:'flex', justifyContent:'space-between', fontSize:11, padding:'3px 0', borderBottom:'1px solid rgba(255,255,255,0.04)' }}>
//                   <span style={{ color:'rgba(255,255,255,0.35)' }}>{r.label}</span>
//                   <span style={{ color:'#e8ecf4' }}>{r.val}</span>
//                 </div>
//               ))}
//               <div style={{ marginTop:10, background:'#f85149', borderRadius:6, padding:'5px 12px', fontSize:11, color:'#fff', fontWeight:600, display:'inline-block' }}>View evidence →</div>
//             </div>
//           </div>
//           <div style={{ background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.07)', borderRadius:12, padding:14 }}>
//             <div style={{ fontSize:11, color:'rgba(255,255,255,0.4)', marginBottom:10 }}>Recent detections</div>
//             {[{platform:'YouTube',score:'94%',status:'Flagged',color:'#f85149'},{platform:'Dailymotion',score:'87%',status:'Flagged',color:'#d29922'},{platform:'Twitter/X',score:'61%',status:'Review',color:'#7b8fff'},{platform:'Facebook',score:'34%',status:'Clean',color:'#3fb950'}].map(row => (
//               <div key={row.platform} style={{ display:'flex', alignItems:'center', gap:12, padding:'6px 0', borderBottom:'1px solid rgba(255,255,255,0.04)', fontSize:12 }}>
//                 <span style={{ color:'rgba(255,255,255,0.5)', width:90 }}>{row.platform}</span>
//                 <div style={{ flex:1, height:4, background:'rgba(255,255,255,0.06)', borderRadius:2, overflow:'hidden' }}>
//                   <div style={{ width:row.score, height:'100%', background:row.color, borderRadius:2 }}/>
//                 </div>
//                 <span style={{ color:row.color, width:32, textAlign:'right', fontSize:11 }}>{row.score}</span>
//                 <span style={{ background:`${row.color}18`, color:row.color, border:`1px solid ${row.color}40`, borderRadius:10, padding:'1px 8px', fontSize:10, width:52, textAlign:'center' }}>{row.status}</span>
//               </div>
//             ))}
//           </div>
//         </div>
//       </div>
//     </div>
//   )
// }

// export default function App() {
//   const { user, logout } = useAuth()
//   const [tab, setTab]   = useState('upload')

//   // Show auth page if not logged in
//   // if (!user) return <AuthPage />

//   return (
//     <div className="app-root">

//       {/* ── Star field background ── */}
//       <div className="star-field"/>

//       {/* ── Navbar ── */}
//       <nav className="navbar">
//         <div className="navbar-brand">
//           <div className="brand-icon">🛡️</div>
//           <span className="brand-name">SportGuard</span>
//         </div>
//         <div className="navbar-links">
//           {NAV_LINKS.map(l => <span key={l} className="nav-link">{l}</span>)}
//         </div>
//         <div className="navbar-right">
//           <span className="user-chip">👤 {user.username}</span>
//           <button className="btn-logout" onClick={logout}>Logout</button>
//         </div>
//       </nav>

//       {/* ── Hero (shown only when tab === 'hero') ── */}
//       {tab === 'hero' && (
//         <div className="hero-section">

//           <div className="hero-text">
//             <div className="hero-badge">AI-Powered Digital Asset Protection</div>
//             <h1 className="hero-title">Protect Your Sports<br/>Media Instantly</h1>
//             <p className="hero-subtitle">
//               Upload your official sports content. Our AI embeds an invisible watermark,
//               generates a CLIP fingerprint, and continuously scans 50+ platforms to detect
//               unauthorized copies in near real-time.
//             </p>
//             <div className="hero-ctas">
//               <button className="btn-cta-primary" onClick={() => setTab('upload')}>Upload your video →</button>
//               <button className="btn-cta-secondary" onClick={() => setTab('dashboard')}>View dashboard</button>
//             </div>
//           </div>

//           <div className="stats-row">
//             {STATS.map(s => (
//               <div key={s.label} className="stat-hero">
//                 <div className="stat-hero-val">{s.value}</div>
//                 <div className="stat-hero-label">{s.label}</div>
//               </div>
//             ))}
//           </div>

//           <div className="preview-window-wrap">
//             <DashboardPreview />
//           </div>

//           <div className="features-section">
//             <h2 className="features-title">Everything you need to protect your sports IP</h2>
//             <p className="features-sub">Built with state-of-the-art ML — watermarking, CLIP fingerprinting, and web-scale scraping.</p>
//             <div className="features-grid">
//               {FEATURES.map(f => (
//                 <div key={f.title} className="feature-card">
//                   <div className="feature-icon">{f.icon}</div>
//                   <div className="feature-title">{f.title}</div>
//                   <div className="feature-desc">{f.desc}</div>
//                 </div>
//               ))}
//             </div>
//           </div>

//           <div className="cta-banner">
//             <h2 className="cta-banner-title">Ready to protect your content?</h2>
//             <p className="cta-banner-sub">Upload your first video and generate your AI fingerprint in under 2 minutes.</p>
//             <button className="btn-cta-primary" onClick={() => setTab('upload')}>Get started — it's free</button>
//           </div>
//         </div>
//       )}

//       {/* ── App pages (upload / fingerprint / scrape etc.) ── */}
//       {tab !== 'hero' && (
//         <div className="app-content">

//           {/* Step tab switcher */}
//           <div className="step-tabs-wrap">
//             <div className='step-tab-overall'>
//           <div className="step-tabs">
//             {STEPS.map(s => (
//               <button
//                 key={s.key}
//                 className={`step-tab ${tab === s.key ? 'active' : ''}`}
//                 onClick={() => setTab(s.key)}
//               >
//                 {s.label}
//               </button>
//             ))}
//             </div>
//           </div>

//           <div className="page-wrap">
//           {/* Page header */}
//           <div className="page-header">
//             <button className="btn-back" onClick={() => setTab('hero')}>← Home</button>
//             <h1 className="page-title">Sports Video Fingerprint System</h1>
//             <p className="page-sub">Upload · Watermark · Fingerprint · Scrape · Match · Flag</p>
//           </div>

//           {/* Step content */}
//           <div className="step-content">
//             {tab === 'upload'             && <VideoUploader />}
//             {tab === 'fingerprint'        && <Fingerprint />}
//             {tab === 'scrape'             && <Scrape />}
//             {tab === 'fingerprintscraped' && <FingerprintScraped />}
//             {tab === 'dashboard'          && <Dashboard />}
//           </div>
//           </div>
//           </div>
//         </div>
//       )}
//     </div>
//   )
// } 


import React, { useState } from 'react'
import { ThemeProvider } from './context/ThemeContext'
import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import Home from './components/pages/Home'
import VideoUploader from './components/VideoUploader'
import Dashboard from './components/Dashboard'
import Fingerprint from './components/Fingerprint'
import Scrape from './components/Scrape'
import FingerprintScraped from './components/FingerprintScraped'

const STEPS = [
  { key: 'upload',             label: '1 · Upload'         },
  { key: 'fingerprint',        label: '2 · Fingerprint'    },
  { key: 'scrape',             label: '3 · Scrape'         },
  { key: 'fingerprintscraped', label: '4 · Match scraped'  },
  { key: 'dashboard',          label: '5–6 · Dashboard'    },
]

const PAGE_LABELS = {
  upload:             { title: 'Upload your sports video',     sub: 'Step 1 — Upload and secure your media'          },
  fingerprint:        { title: 'Generate AI fingerprint',      sub: 'Step 2 — Watermark + Google Vision AI embedding' },
  scrape:             { title: 'Scan the web',                 sub: 'Step 3 — Search platforms for your content'     },
  fingerprintscraped: { title: 'Analyse candidate videos',     sub: 'Step 4 — Compare scraped videos to your original'},
  dashboard:          { title: 'Detection dashboard',          sub: 'Steps 5–6 — Review matches and generate reports' },
}

function AppInner() {
  const [page, setPage] = useState('home')

  const isHome = page === 'home'

  return (
    <div className="page-wrapper">
      <Navbar
        currentPage={page}
        onNavigate={setPage}
      />

      {isHome ? (
        <Home
          onGetStarted={() => setPage('upload')}
          onDashboard={() => setPage('dashboard')}
        />
      ) : (
        <div className="app-content">
          {/* Page header */}
          <div className="page-header">
            <h1 className="page-title">{PAGE_LABELS[page]?.title}</h1>
            <p className="page-sub">{PAGE_LABELS[page]?.sub}</p>
          </div>

          {/* Step tabs */}
          <div className="step-tabs mb-24">
            {STEPS.map(s => (
              <button
                key={s.key}
                className={`step-tab ${page === s.key ? 'active' : ''}`}
                onClick={() => setPage(s.key)}
              >
                {s.label}
              </button>
            ))}
          </div>

          {/* Step content */}
          <div className="step-content">
            {page === 'upload'             && <VideoUploader />}
            {page === 'fingerprint'        && <Fingerprint />}
            {page === 'scrape'             && <Scrape />}
            {page === 'fingerprintscraped' && <FingerprintScraped />}
            {page === 'dashboard'          && <Dashboard />}
          </div>
        </div>
      )}

      {isHome && <Footer />}
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AppInner />
    </ThemeProvider>
  )
}