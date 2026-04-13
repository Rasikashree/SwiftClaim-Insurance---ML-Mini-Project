import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const API = 'http://localhost:5001'

const SEV_COLOR = { Minor: '#10b981', Moderate: '#f59e0b', Severe: '#ef4444' }
const BADGE_MAP  = { Minor: 'badge-minor', Moderate: 'badge-moderate', Severe: 'badge-severe' }

const REC_STYLES = {
  LOW_VALUE_CLAIM:          { bg: 'rgba(99,102,241,0.1)',  border: '#6366f1', label: '📋 Low Value', color: '#818cf8' },
  APPROVE:                  { bg: 'rgba(16,185,129,0.1)',  border: '#10b981', label: '✅ Auto Approved', color: '#34d399' },
  APPROVE_WITH_INSPECTION:  { bg: 'rgba(245,158,11,0.1)',  border: '#f59e0b', label: '🔍 Approved + Inspection', color: '#fbbf24' },
  ESCALATE:                 { bg: 'rgba(239,68,68,0.1)',   border: '#ef4444', label: '⚠️ Escalate to Adjuster', color: '#f87171' },
}

function fmt(n) { return '₹' + Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 }) }

export default function SwiftClaimPage() {
  const [file, setFile]           = useState(null)
  const [preview, setPreview]     = useState(null)
  const [loading, setLoading]     = useState(false)
  const [result, setResult]       = useState(null)
  const [error, setError]         = useState(null)
  const [vehicleAge, setVehicleAge] = useState(3)
  const [useOem, setUseOem]       = useState(false)
  const [deductible, setDeductible] = useState(5000)

  const onDrop = useCallback(accepted => {
    if (!accepted.length) return
    const f = accepted[0]
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
    setError(null)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'image/*': [] }, maxFiles: 1
  })

  async function submitClaim() {
    if (!file) return
    setLoading(true); setError(null); setResult(null)
    const fd = new FormData()
    fd.append('image', file)
    fd.append('vehicle_age', vehicleAge)
    fd.append('use_oem', useOem)
    fd.append('deductible', deductible)
    try {
      const res = await fetch(`${API}/api/upload-claim`, { method: 'POST', body: fd })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Server error')
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const chartData = result?.detected_parts?.map(p => ({
    name: p.part_name.replace(/ /g, '\n'),
    confidence: (p.confidence * 100).toFixed(1),
    fill: SEV_COLOR[p.severity] || '#6366f1',
  })) || []

  const rec = result ? REC_STYLES[result.payout_estimation.recommendation] : null

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 24px 80px' }}>

      {/* Page header */}
      <div style={{ marginBottom: 40 }}>
        <div className="section-eyebrow">Computer Vision</div>
        <h1 style={{ fontSize: 'clamp(28px,5vw,52px)', fontWeight: 900, letterSpacing: '-1px' }}>
          <span className="gradient-text-swift">SwiftClaim</span> Engine
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: 10, fontSize: 16, maxWidth: 560 }}>
          Upload a photo of a damaged vehicle — AI detects parts, scores severity, and calculates your payout instantly.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: result ? '1fr 1fr' : '1fr', gap: 28, alignItems: 'start' }}>

        {/* ── LEFT: Upload + Config ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Dropzone */}
          <div {...getRootProps()} style={{
            border: `2px dashed ${isDragActive ? '#6366f1' : 'rgba(255,255,255,0.12)'}`,
            borderRadius: 16,
            padding: preview ? 0 : '48px 28px',
            textAlign: 'center', cursor: 'pointer',
            background: isDragActive ? 'rgba(99,102,241,0.08)' : 'rgba(255,255,255,0.02)',
            transition: 'all 0.25s ease',
            overflow: 'hidden',
            minHeight: 220,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <input {...getInputProps()} />
            {preview ? (
              <img src={preview} alt="preview" style={{ width: '100%', maxHeight: 340, objectFit: 'cover', borderRadius: 14 }} />
            ) : (
              <div>
                <div style={{ fontSize: 52, marginBottom: 14 }}>📸</div>
                <p style={{ fontWeight: 600, fontSize: 16, color: 'var(--text-primary)', marginBottom: 6 }}>
                  {isDragActive ? 'Drop it here…' : 'Drag & drop a damage photo'}
                </p>
                <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>or click to browse • JPG, PNG, WEBP</p>
              </div>
            )}
          </div>

          {/* Config panel */}
          <div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 18, color: 'var(--text-primary)' }}>⚙️ Claim Parameters</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div className="form-group">
                <label>Vehicle Age (years)</label>
                <input type="number" className="form-input" min={0} max={30} value={vehicleAge}
                  onChange={e => setVehicleAge(+e.target.value)} />
              </div>
              <div className="form-group">
                <label>Deductible (₹)</label>
                <input type="number" className="form-input" min={0} step={500} value={deductible}
                  onChange={e => setDeductible(+e.target.value)} />
              </div>
              <div className="form-group" style={{ gridColumn: '1/-1' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
                  <input type="checkbox" checked={useOem} onChange={e => setUseOem(e.target.checked)}
                    style={{ width: 16, height: 16, accentColor: '#6366f1' }} />
                  <span>Use OEM Parts (higher cost, better quality)</span>
                </label>
              </div>
            </div>
          </div>

          <button className="btn btn-primary" onClick={submitClaim} disabled={!file || loading}
            style={{ width: '100%', justifyContent: 'center', fontSize: 16, padding: '14px' }}>
            {loading ? <><div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} /> Processing…</> : '🔍 Analyse Damage & Estimate Payout'}
          </button>

          {error && (
            <div className="alert alert-error">
              <span>⚠️</span>
              <div>
                <strong>Error:</strong> {error}
                <br /><small style={{ opacity: 0.8 }}>Make sure the SwiftClaim backend is running on port 5001.</small>
              </div>
            </div>
          )}
        </div>

        {/* ── RIGHT: Results ── */}
        {result && (
          <div className="animate-scaleIn" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Claim ID + timing */}
            <div className="glass-card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Claim ID</div>
                  <div style={{ fontFamily: 'Space Grotesk', fontWeight: 700, fontSize: 22, color: '#818cf8' }}>{result.claim_id}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Processed In</div>
                  <div style={{ fontWeight: 700, fontSize: 20, color: '#34d399' }}>{result.processing_time_ms} ms</div>
                </div>
              </div>
            </div>

            {/* Recommendation banner */}
            {rec && (
              <div style={{ padding: '18px 22px', borderRadius: 14, background: rec.bg, border: `1px solid ${rec.border}44` }}>
                <div style={{ fontWeight: 700, fontSize: 17, color: rec.color }}>{rec.label}</div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
                  {result.payout_estimation.recommendation_note}
                </div>
              </div>
            )}

            {/* Payout summary */}
            <div className="glass-card" style={{ padding: 24 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>💰 Payout Summary</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                {[
                  ['Parts Cost', fmt(result.payout_estimation.subtotal_parts)],
                  ['Labour Cost', fmt(result.payout_estimation.subtotal_labor)],
                  ['GST (18%)', fmt(result.payout_estimation.subtotal_gst)],
                  ['Gross Total', fmt(result.payout_estimation.gross_total)],
                  ['Deductible', `−${fmt(result.payout_estimation.deductible)}`],
                  ['Depreciation', result.payout_estimation.depreciation_rate],
                ].map(([k, v]) => (
                  <div key={k} className="stat-tile">
                    <div className="stat-label">{k}</div>
                    <div className="stat-value" style={{ fontSize: 18, color: k === 'Deductible' ? '#f87171' : 'var(--text-primary)' }}>{v}</div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 18, padding: '16px 20px', borderRadius: 12, background: 'linear-gradient(135deg, rgba(99,102,241,0.18), rgba(139,92,246,0.12))', border: '1px solid rgba(99,102,241,0.3)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 700, fontSize: 16 }}>Net Payout (Est.)</span>
                <span style={{ fontWeight: 900, fontSize: 26, fontFamily: 'Space Grotesk', color: '#818cf8' }}>{fmt(result.payout_estimation.net_payout)}</span>
              </div>
            </div>

            {/* Detected parts */}
            <div className="glass-card" style={{ padding: 24 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>🔍 Detected Damaged Parts</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {result.detected_parts.map(p => (
                  <div key={p.part_id} style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 600 }}>{p.part_name}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{p.severity_description}</div>
                    </div>
                    <span className={`badge ${BADGE_MAP[p.severity]}`}>{p.severity}</span>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', minWidth: 44, textAlign: 'right' }}>
                      {(p.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Confidence Chart */}
            {chartData.length > 0 && (
              <div className="glass-card" style={{ padding: 24 }}>
                <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>📊 Damage Confidence</h3>
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} unit="%" domain={[0, 100]} />
                    <Tooltip formatter={v => [`${v}%`, 'Confidence']}
                      contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 13 }} />
                    <Bar dataKey="confidence" radius={[6,6,0,0]}>
                      {chartData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Line items table */}
            <div className="glass-card" style={{ padding: 24 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>📋 Itemised Estimate</h3>
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Part</th><th>Action</th><th>Parts</th><th>Labour</th><th>GST</th><th>Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.payout_estimation.line_items.map(item => (
                      <tr key={item.part_id}>
                        <td style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{item.part_name}</td>
                        <td><span className={`badge ${BADGE_MAP[item.severity]}`}>{item.action}</span></td>
                        <td>{fmt(item.depreciated_cost)}</td>
                        <td>{fmt(item.labor_cost)}</td>
                        <td>{fmt(item.gst)}</td>
                        <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{fmt(item.line_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  )
}
