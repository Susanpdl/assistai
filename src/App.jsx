import { useState } from 'react'
import ViewSwitcher from './components/ViewSwitcher.jsx'
import StudentStudyView from './views/StudentStudyView.jsx'
import StudentLiveView from './views/StudentLiveView.jsx'
import InstructorConsoleView from './views/InstructorConsoleView.jsx'
import LoginView from './views/LoginView.jsx'
import CoursesView from './views/CoursesView.jsx'
import { useAuth } from './auth/AuthContext.jsx'

export default function App() {
  const { user, loading, logout } = useAuth()
  const [section, setSection] = useState('courses') // 'courses' (live) | 'demo' (mock prototype)
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
        <div className="account-bar__nav" role="tablist" aria-label="Sections">
          <button
            className={section === 'courses' ? 'active' : ''}
            onClick={() => setSection('courses')}
          >
            Courses
          </button>
          <button
            className={section === 'demo' ? 'active' : ''}
            onClick={() => setSection('demo')}
          >
            Demo prototype
          </button>
        </div>
        <div className="account-bar__right">
          <span className="account-bar__id">
            {user.email} · <span className="account-bar__role">{user.role}</span>
          </span>
          <button className="btn btn--ghost account-bar__logout" onClick={logout}>
            Log out
          </button>
        </div>
      </div>

      {section === 'courses' ? (
        <div className="view-area">
          <CoursesView />
        </div>
      ) : (
        <>
          <div className="view-area">
            {view === 'study' && <StudentStudyView />}
            {view === 'live' && <StudentLiveView />}
            {view === 'instructor' && <InstructorConsoleView />}
          </div>
          <ViewSwitcher view={view} setView={setView} />
        </>
      )}
    </div>
  )
}
