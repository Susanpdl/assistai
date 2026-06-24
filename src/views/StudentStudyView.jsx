import { useState } from 'react'
import TopNav from '../components/TopNav.jsx'
import { ChatThread, Composer } from '../components/Chat.jsx'
import {
  courses,
  student,
  studyConversation,
  studySuggestions,
  cannedReplies,
} from '../data/mock.js'

let replyIdx = 0

export default function StudentStudyView() {
  const [activeCourse, setActiveCourse] = useState('cs310')
  const [messages, setMessages] = useState(studyConversation)
  const [typing, setTyping] = useState(false)

  const send = (text) => {
    const userMsg = {
      id: `u-${Date.now()}`,
      role: 'user',
      text,
      time: 'now',
    }
    setMessages((m) => [...m, userMsg])
    setTyping(true)

    // Simulated grounded AI reply (no backend yet).
    setTimeout(() => {
      const canned = cannedReplies[replyIdx % cannedReplies.length]
      replyIdx += 1
      setTyping(false)
      setMessages((m) => [
        ...m,
        { id: `a-${Date.now()}`, role: 'ai', text: canned.text, source: canned.source, time: 'now' },
      ])
    }, 1200)
  }

  const empty = messages.length === 0
  const courseName = courses.find((c) => c.id === activeCourse)?.name

  return (
    <>
      <TopNav variant="study" user={student} />
      <div className="layout">
        <aside className="sidebar">
          <div className="sidebar__heading">My Courses</div>
          {courses.map((c) => (
            <button
              key={c.id}
              className={`nav-item ${activeCourse === c.id ? 'active' : ''}`}
              onClick={() => setActiveCourse(c.id)}
            >
              <span className="ico">📘</span>
              <span style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                <strong style={{ fontSize: 13.5 }}>{c.code}</strong>
                <span style={{ fontSize: 11.5, color: 'var(--muted)' }}>{c.name}</span>
              </span>
            </button>
          ))}

          <div className="sidebar__spacer" />
          <div className="sidebar__divider" />
          <button className="nav-item"><span className="ico">🕘</span> Chat history</button>
          <button className="nav-item"><span className="ico">⚙️</span> Settings</button>
        </aside>

        <main className="main">
          <div className="chat">
            {empty ? (
              <div className="empty-state">
                <div className="empty-state__icon">◆</div>
                <div>
                  <h2>Ask about {courseName}</h2>
                  <p>
                    I'm your AI teaching assistant for this course. Every answer is grounded in the
                    materials your professor uploaded — with a citation so you can check the source.
                  </p>
                </div>
                <div className="chips">
                  {studySuggestions.map((s) => (
                    <button key={s} className="chip" onClick={() => send(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <ChatThread messages={messages} typing={typing} />
            )}
            <Composer
              onSend={send}
              placeholder={`Ask anything about ${courses.find((c) => c.id === activeCourse)?.code}…`}
              hint="Answers are grounded in your course materials and cited. AI can make mistakes."
            />
          </div>
        </main>
      </div>
    </>
  )
}
