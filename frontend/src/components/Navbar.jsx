import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const location = useLocation()
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => setMenuOpen(false), [location.pathname])

  const links = [
    { to: '/', label: 'Home' },
    { to: '/swiftclaim', label: 'SwiftClaim', color: '#6366f1' },
  ]

  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
      height: '72px', display: 'flex', alignItems: 'center',
      padding: '0 32px',
      background: scrolled ? 'rgba(6,9,18,0.88)' : 'rgba(6,9,18,0.4)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderBottom: scrolled ? '1px solid rgba(255,255,255,0.07)' : '1px solid transparent',
      transition: 'all 0.3s ease',
    }}>
      {/* Logo */}
      <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 10, marginRight: 'auto' }}>
        <div style={{
          width: 36, height: 36,
          background: 'linear-gradient(135deg, #6366f1, #10b981)',
          borderRadius: 10,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 18, fontWeight: 800, color: '#fff',
          fontFamily: 'Space Grotesk, sans-serif',
          boxShadow: '0 4px 14px rgba(99,102,241,0.4)',
        }}>AI</div>
        <span style={{ fontFamily: 'Space Grotesk, sans-serif', fontWeight: 700, fontSize: 18, color: '#f8fafc', letterSpacing: '-0.3px' }}>
          Insure<span style={{ background: 'linear-gradient(135deg, #6366f1, #10b981)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>AI</span>
        </span>
      </Link>

      {/* Desktop nav links */}
      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        {links.map(({ to, label, color }) => {
          const active = location.pathname === to
          return (
            <Link key={to} to={to} style={{
              textDecoration: 'none',
              padding: '8px 16px',
              borderRadius: 10,
              fontSize: 14, fontWeight: 600,
              color: active ? '#fff' : '#94a3b8',
              background: active ? (color ? `${color}22` : 'rgba(99,102,241,0.15)') : 'transparent',
              border: active ? `1px solid ${color || '#6366f1'}44` : '1px solid transparent',
              transition: 'all 0.2s ease',
              position: 'relative',
            }}
            onMouseEnter={e => { if (!active) { e.target.style.color='#f8fafc'; e.target.style.background='rgba(255,255,255,0.05)' } }}
            onMouseLeave={e => { if (!active) { e.target.style.color='#94a3b8'; e.target.style.background='transparent' } }}
            >
              {label}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
