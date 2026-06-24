import { useState } from 'react'
import TopNav, { Avatar } from '../components/TopNav.jsx'
import ResultBars from '../components/ResultBars.jsx'
import {
  instructor,
  dashboardStats,
  escalatedQuestions,
  courseFiles,
  roster,
  presetPolls,
  liveResults,
} from '../data/mock.js'

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: '▦' },
  { id: 'questions', label: 'Questions', icon: '💬' },
  { id: 'live', label: 'Live session', icon: '🟢' },
  { id: 'upload', label: 'Upload content', icon: '⬆' },
  { id: 'students', label: 'Students', icon: '👥' },
]

export default function InstructorConsoleView() {
  const [tab, setTab] = useState('dashboard')

  return (
    <>
      <TopNav variant="instructor" user={instructor} />
      <div className="layout">
        <aside className="sidebar">
          <div className="sidebar__heading">CS 310 · Operating Systems</div>
          {NAV.map((n) => (
            <button
              key={n.id}
              className={`nav-item ${tab === n.id ? 'active' : ''}`}
              onClick={() => setTab(n.id)}
            >
              <span className="ico">{n.icon}</span>
              {n.label}
              {n.id === 'questions' && <span className="nav-item__sub">4</span>}
            </button>
          ))}
          <div className="sidebar__spacer" />
          <div className="sidebar__divider" />
          <div className="nav-item" style={{ cursor: 'default' }}>
            <Avatar initials={instructor.initials} tone="slate" size="sm" />
            <span style={{ fontSize: 13 }}>{instructor.name}</span>
          </div>
        </aside>

        <main className="main">
          {tab === 'dashboard' && <Dashboard go={setTab} />}
          {tab === 'questions' && <Questions />}
          {tab === 'live' && <LiveControl />}
          {tab === 'upload' && <Upload />}
          {tab === 'students' && <Students />}
        </main>
      </div>
    </>
  )
}

function Dashboard({ go }) {
  return (
    <div className="dash">
      <div className="dash__head">
        <h1>Good afternoon, Dr. Marsh 👋</h1>
        <p>Here's how your classroom is doing today.</p>
      </div>

      <div className="stat-grid">
        {dashboardStats.map((s) => (
          <div className="stat-card" key={s.id}>
            <div className={`stat-card__icon ${s.tone}`}>{s.icon}</div>
            <div className="stat-card__value">{s.value}</div>
            <div className="stat-card__label">{s.label}</div>
            <div className="stat-card__delta up">{s.delta}</div>
          </div>
        ))}
      </div>

      <div className="section-title">
        Escalated questions
        <span className="badge-count">2 need answers</span>
      </div>
      <div className="esc-list">
        {escalatedQuestions.slice(0, 3).map((q) => (
          <EscItem key={q.id} q={q} />
        ))}
      </div>
      <button
        className="btn btn--ghost"
        style={{ marginTop: 12 }}
        onClick={() => go('questions')}
      >
        View all questions →
      </button>

      <div className="section-title">Course content</div>
      <UploadBox compact />
    </div>
  )
}

function EscItem({ q }) {
  return (
    <div className="esc-item">
      <Avatar initials={q.student.split(' ').map((p) => p[0]).join('')} tone="purple" size="sm" />
      <div className="esc-item__main">
        <p className="esc-item__q">{q.question}</p>
        <div className="esc-item__meta">
          <span>{q.student}</span>
          <span className="dot">·</span>
          <span>{q.time}</span>
          <span className="dot">·</span>
          <span>{q.reason}</span>
        </div>
        {q.status === 'needs' && (
          <div className="esc-actions">
            <button className="btn btn--primary">Answer</button>
            <button className="btn btn--ghost">Let AI draft</button>
          </div>
        )}
      </div>
      <span className={`status-badge ${q.status}`}>
        {q.status === 'needs' ? 'Needs answer' : 'Answered'}
      </span>
    </div>
  )
}

function Questions() {
  return (
    <div className="dash">
      <div className="dash__head">
        <h1>Questions</h1>
        <p>Questions the AI escalated to you, plus everything students asked today.</p>
      </div>
      <div className="section-title">
        Escalated to you
        <span className="badge-count">2 need answers</span>
      </div>
      <div className="esc-list">
        {escalatedQuestions.map((q) => (
          <EscItem key={q.id} q={q} />
        ))}
      </div>
    </div>
  )
}

function LiveControl() {
  const [pushed, setPushed] = useState(null)
  return (
    <div className="dash">
      <div className="dash__head">
        <h1>Live session</h1>
        <p>
          <span className="live-dot" style={{ display: 'inline-block', marginRight: 8 }} />
          Class is live · 38 students connected
        </p>
      </div>

      <div className="section-title">Push a poll</div>
      <div className="live-controls">
        {presetPolls.map((p) => (
          <div
            key={p.id}
            className={`preset-poll ${pushed === p.id ? 'pushed' : ''}`}
            onClick={() => setPushed(p.id)}
          >
            <div className="flex between">
              <h4>{p.q}</h4>
              {pushed === p.id ? (
                <span className="status-badge answered">● Pushed live</span>
              ) : (
                <button className="btn btn--primary">Push to class</button>
              )}
            </div>
            <p>{p.opts} options · multiple choice</p>
          </div>
        ))}
      </div>

      {pushed && (
        <>
          <div className="section-title">Live results</div>
          <div className="card" style={{ maxWidth: 640 }}>
            <ResultBars results={liveResults} />
          </div>
        </>
      )}
    </div>
  )
}

function UploadBox({ compact }) {
  const [drag, setDrag] = useState(false)
  return (
    <>
      <div
        className={`upload-box ${drag ? 'drag' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false) }}
      >
        <div className="upload-box__icon">⬆</div>
        <h4>Drop slides, notes, or readings here</h4>
        <p>The AI reads these to stay grounded in your actual course material.</p>
        <div className="formats">
          <span className="format-tag">PDF</span>
          <span className="format-tag">DOCX</span>
          <span className="format-tag">PPTX</span>
        </div>
      </div>

      {!compact && (
        <>
          <div className="section-title">Indexed materials</div>
          {courseFiles.map((f) => (
            <FileRow key={f.id} f={f} />
          ))}
        </>
      )}
      {compact && (
        <div style={{ marginTop: 4 }}>
          {courseFiles.slice(0, 2).map((f) => (
            <FileRow key={f.id} f={f} />
          ))}
        </div>
      )}
    </>
  )
}

function FileRow({ f }) {
  return (
    <div className="file-row">
      <div className={`file-row__icon ${f.type}`}>{f.type.toUpperCase()}</div>
      <div className="file-row__main">
        <div className="file-row__name">{f.name}</div>
        <div className="file-row__sub">
          {f.size}
          {f.status === 'indexed' && ` · ${f.chunks} chunks embedded`}
        </div>
      </div>
      {f.status === 'indexed' ? (
        <span className="file-status indexed">✓ Indexed</span>
      ) : (
        <span className="file-status processing">
          <span className="mini-spinner" /> Processing…
        </span>
      )}
    </div>
  )
}

function Upload() {
  return (
    <div className="dash">
      <div className="dash__head">
        <h1>Upload content</h1>
        <p>Add course material so the AI can answer students with grounded, cited responses.</p>
      </div>
      <UploadBox />
    </div>
  )
}

function Students() {
  return (
    <div className="dash">
      <div className="dash__head">
        <h1>Students</h1>
        <p>42 enrolled · engagement this week</p>
      </div>
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="roster">
          <thead>
            <tr>
              <th>Student</th>
              <th>Questions</th>
              <th>Course progress</th>
              <th>Last active</th>
            </tr>
          </thead>
          <tbody>
            {roster.map((r) => (
              <tr key={r.id}>
                <td>
                  <div className="student-cell">
                    <Avatar initials={r.initials} tone={r.tone} size="sm" />
                    {r.name}
                  </div>
                </td>
                <td>{r.questions}</td>
                <td>
                  <div className="flex gap-sm" style={{ alignItems: 'center' }}>
                    <div className="progress-mini"><div style={{ width: `${r.progress}%` }} /></div>
                    <span className="muted" style={{ fontSize: 12 }}>{r.progress}%</span>
                  </div>
                </td>
                <td className="muted">{r.lastActive}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
