import { Link } from 'react-router-dom'

const features = [
  { icon: '🔍', title: 'Computer Vision Detection', desc: 'OpenCV pipeline identifies damaged parts from a single photo — bumper, headlight, door, hood, and more.' },
  { icon: '📊', title: 'Severity Classification', desc: 'Edge density + texture analysis scores damage as Minor, Moderate, or Severe with per-part confidence.' },
  { icon: '💰', title: 'Instant Payout Estimation', desc: 'Cross-references live parts-price DB (SQLite) with depreciation, labour & GST to generate final payout.' },
  { icon: '🔎', title: '16 Part Categories', desc: 'Bumper, headlight, door, hood, windshield and 11 more — every major panel and component covered.' },
  { icon: '📐', title: 'Depreciation Engine', desc: 'Age-based depreciation table + labour costs + GST automatically applied for an actuarial-grade breakdown.' },
  { icon: '⚡', title: 'Results in Under 2s', desc: 'The full detection → severity → payout pipeline completes in under 2 seconds via the Flask REST API.' },
]

const stack = [
  { label: 'Computer Vision', items: ['OpenCV', 'Pillow', 'NumPy'], color: '#6366f1' },
  { label: 'ML / Data Science', items: ['Scikit-learn', 'Pandas', 'SQLite'], color: '#10b981' },
  { label: 'Backend API', items: ['Python Flask', 'Flask-CORS', 'REST'], color: '#06b6d4' },
  { label: 'Frontend', items: ['React 18', 'Recharts', 'React Router'], color: '#f59e0b' },
]

export default function Home() {
  return (
    <div style={{ position: 'relative' }}>

      {/* ── Hero ── */}
      <section style={{
        minHeight: '92vh',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        textAlign: 'center', padding: '80px 24px 60px',
      }}>
        <div className="animate-fadeInUp">
          <div className="badge badge-blue" style={{ marginBottom: 24, fontSize: 13, padding: '6px 16px' }}>
            🏆 &nbsp;InsureAI — Insurance
          </div>
        </div>

        <h1 className="animate-fadeInUp" style={{ fontSize: 'clamp(40px,7vw,80px)', fontWeight: 900, lineHeight: 1.05, letterSpacing: '-2px', maxWidth: 900, animationDelay: '0.1s' }}>
          Vehicle Damage Claims&nbsp;
          <span className="gradient-text-swift">Settled</span>
          <br />by AI — Instantly
        </h1>

        <p className="animate-fadeInUp" style={{ marginTop: 24, fontSize: 18, color: 'var(--text-secondary)', maxWidth: 620, lineHeight: 1.7, animationDelay: '0.2s' }}>
          <strong style={{ color: '#818cf8' }}>SwiftClaim</strong> is a production-grade computer-vision engine that detects damaged vehicle parts,
          scores severity, and generates a fully-itemised insurance payout estimate — all from a single photo.
        </p>

      

        {/* Stats row */}
        <div className="animate-fadeInUp" style={{ display: 'flex', gap: 32, marginTop: 64, flexWrap: 'wrap', justifyContent: 'center', animationDelay: '0.4s' }}>
          {[ ['16', 'Car Parts Detected'], ['3', 'Severity Levels'], ['< 2s', 'Processing Time'], ['100%', 'Automated'] ].map(([val, lab]) => (
            <div key={lab} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 32, fontWeight: 800, fontFamily: 'Space Grotesk, sans-serif', background: 'linear-gradient(135deg,#6366f1,#818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>{val}</div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4, textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 500 }}>{lab}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── SwiftClaim Showcase Card ── */}
      <section style={{ padding: '80px 24px', maxWidth: 800, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 56 }}>
          <div className="section-eyebrow">AI-Powered Claims</div>
          <h2 style={{ fontSize: 'clamp(28px,4vw,44px)', fontWeight: 800 }}>How SwiftClaim Works</h2>
        </div>

        <div className="glass-card" style={{ padding: 48, position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: -60, right: -60, width: 220, height: 220, background: 'radial-gradient(circle, rgba(99,102,241,0.3) 0%, transparent 70%)', borderRadius: '50%', pointerEvents: 'none' }} />
          <div style={{ position: 'absolute', bottom: -40, left: -40, width: 180, height: 180, background: 'radial-gradient(circle, rgba(129,140,248,0.15) 0%, transparent 70%)', borderRadius: '50%', pointerEvents: 'none' }} />

          <div style={{ fontSize: 52, marginBottom: 24 }}>🚗</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <h2 style={{ fontSize: 34, fontWeight: 800, fontFamily: 'Space Grotesk, sans-serif' }} className="gradient-text-swift">SwiftClaim</h2>
            <span className="badge badge-blue">Computer Vision</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 32, fontSize: 16 }}>
            Upload a photo of a damaged vehicle. The AI automatically detects which parts are damaged,
            classifies severity, and instantly generates a fully-itemised insurance payout estimate.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 40 }}>
            {[
              'CV damage detection via OpenCV pipeline',
              'Minor / Moderate / Severe severity scoring',
              'Parts-price DB cross-reference (SQLite)',
              'Depreciation + Labour + GST payout calculation',
              'Results delivered in under 2 seconds',
            ].map(f => (
              <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 15, color: 'var(--text-secondary)' }}>
                <span style={{ color: '#818cf8', fontSize: 18, flexShrink: 0 }}>✓</span> {f}
              </div>
            ))}
          </div>
          <Link to="/swiftclaim" className="btn btn-primary" style={{ padding: '14px 36px', fontSize: 15 }}>
            Launch SwiftClaim →
          </Link>
        </div>
      </section>

      {/* ── Features grid ── */}
      <section style={{ padding: '60px 24px 80px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <div className="section-eyebrow">Capabilities</div>
          <h2 style={{ fontSize: 'clamp(24px,3.5vw,38px)', fontWeight: 800 }}>Everything You Need</h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
          {features.map(({ icon, title, desc }) => (
            <div key={title} className="glass-card" style={{ padding: 28 }}>
              <div style={{ fontSize: 32, marginBottom: 14 }}>{icon}</div>
              <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 8, fontFamily: 'Space Grotesk, sans-serif' }}>{title}</h3>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.65 }}>{desc}</p>
            </div>
          ))}
        </div>
      </section>
      {/* ── Tech Stack ── */}
      <section style={{ padding: '40px 24px 80px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div className="section-eyebrow">Built With</div>
          <h2 style={{ fontSize: 'clamp(22px,3vw,34px)', fontWeight: 800 }}>Technology Stack</h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
          {stack.map(({ label, items, color }) => (
            <div key={label} className="glass-card" style={{ padding: 22, borderTop: `3px solid ${color}` }}>
              <div style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', color, marginBottom: 12 }}>{label}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {items.map(item => (
                  <div key={item} style={{ fontSize: 14, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: color, display: 'inline-block', flexShrink: 0 }} />
                    {item}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
