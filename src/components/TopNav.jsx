export function Brand() {
  return (
    <div className="topnav__brand">
      <span className="brand-mark">◆</span>
      <span>AssistAI</span>
    </div>
  )
}

export function Avatar({ initials, tone = 'blue', size }) {
  const cls = `avatar avatar--${tone}${size ? ` avatar--${size}` : ''}`
  return <div className={cls}>{initials}</div>
}

export default function TopNav({ variant, courseName, professor, connected, user }) {
  return (
    <header className="topnav">
      <Brand />

      {variant === 'live' && (
        <div className="topnav__center">
          <div className="live-indicator">
            <span className="live-dot" />
            {courseName} · Live
          </div>
        </div>
      )}

      {variant === 'instructor' && (
        <div className="topnav__center">
          <span className="pill-tag">Instructor view</span>
        </div>
      )}

      <div className="topnav__right">
        {variant !== 'instructor' && <span className="pill-tag">Student</span>}
        <Avatar
          initials={user.initials}
          tone={variant === 'instructor' ? 'slate' : 'blue'}
        />
      </div>
    </header>
  )
}
