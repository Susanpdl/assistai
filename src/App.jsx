import { useState } from 'react'
import ViewSwitcher from './components/ViewSwitcher.jsx'
import StudentStudyView from './views/StudentStudyView.jsx'
import StudentLiveView from './views/StudentLiveView.jsx'
import InstructorConsoleView from './views/InstructorConsoleView.jsx'
import LoginView from './views/LoginView.jsx'
import { useAuth } from './auth/AuthContext.jsx'

export default function App() {
  const { user, loading, logout } = useAuth()
  const [view, setView] = useState('study')

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
      <div className="account-bar">
        <span className="account-bar__id">
          {user.email} · <span className="account-bar__role">{user.role}</span>
        </span>
        <button className="btn btn--ghost account-bar__logout" onClick={logout}>
          Log out
        </button>
      </div>
      <div className="view-area">
        {view === 'study' && <StudentStudyView />}
        {view === 'live' && <StudentLiveView />}
        {view === 'instructor' && <InstructorConsoleView />}
      </div>
      <ViewSwitcher view={view} setView={setView} />
    </div>
  )
}
