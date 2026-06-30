import LoginView from './views/LoginView.jsx'
import CoursesView from './views/CoursesView.jsx'
import { useAuth } from './auth/AuthContext.jsx'

export default function App() {
  const { user, loading, logout } = useAuth()

  // While we check the session cookie, show a quiet splash (avoids a login flash).
  if (loading) {
    return (
      <div className="app app--center">
        <div className="login__brand">AssistAI</div>
      </div>
    )
  }

  if (!user) return <LoginView />

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar__brand">
          <span className="brand-mark">◆</span> AssistAI
        </div>
        <div className="topbar__right">
          <span className={`role-pill role-pill--${user.role}`}>{user.role}</span>
          <span className="topbar__email">{user.email}</span>
          <button className="btn btn--ghost" onClick={logout}>Log out</button>
        </div>
      </header>

      <div className="view-area">
        <CoursesView />
      </div>
    </div>
  )
}
