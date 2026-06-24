import { useState } from 'react'
import ViewSwitcher from './components/ViewSwitcher.jsx'
import StudentStudyView from './views/StudentStudyView.jsx'
import StudentLiveView from './views/StudentLiveView.jsx'
import InstructorConsoleView from './views/InstructorConsoleView.jsx'

export default function App() {
  const [view, setView] = useState('study')

  return (
    <div className="app">
      <div className="view-area">
        {view === 'study' && <StudentStudyView />}
        {view === 'live' && <StudentLiveView />}
        {view === 'instructor' && <InstructorConsoleView />}
      </div>
      <ViewSwitcher view={view} setView={setView} />
    </div>
  )
}
