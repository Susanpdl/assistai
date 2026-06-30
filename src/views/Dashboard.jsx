// Phase 8 — real instructor dashboard for a course: stat cards + escalated questions
// with a "send answer to the student" action.
import { useCallback, useEffect, useState } from 'react'
import * as api from '../api/dashboard.js'

export default function CourseDashboard({ courseId }) {
  const [stats, setStats] = useState(null)
  const [escalations, setEscalations] = useState([])

  const load = useCallback(() => {
    api.getDashboard(courseId).then(setStats).catch(() => {})
    api.listEscalations(courseId).then(setEscalations).catch(() => {})
  }, [courseId])

  useEffect(() => {
    load()
  }, [load])

  const open = escalations.filter((e) => e.status === 'needs')

  return (
    <div className="course-card__requests">
      <div className="course-card__requests-label">Dashboard</div>

      <div className="dash-stats">
        <Stat value={stats?.students_enrolled} label="Enrolled" />
        <Stat value={stats?.pending_requests} label="Pending" />
        <Stat value={stats?.questions_today} label="Questions today" />
        <Stat value={stats?.escalated_open} label="Escalated" />
      </div>

      <div className="course-card__requests-label" style={{ marginTop: 12 }}>
        Escalated questions ({open.length})
      </div>
      {open.length === 0 ? (
        <p className="courses__empty">Nothing needs your answer right now.</p>
      ) : (
        open.map((e) => <EscalationItem key={e.id} esc={e} reload={load} />)
      )}
    </div>
  )
}

function Stat({ value, label }) {
  return (
    <div className="stat-inline" style={{ flex: 1 }}>
      <div>
        <div className="big">{value ?? '—'}</div>
        <div className="lbl">{label}</div>
      </div>
    </div>
  )
}

function EscalationItem({ esc, reload }) {
  const [answer, setAnswer] = useState('')
  const [open, setOpen] = useState(false)

  async function send() {
    if (!answer.trim()) return
    await api.answerEscalation(esc.id, answer.trim())
    setAnswer('')
    setOpen(false)
    reload()
  }

  return (
    <div className="card" style={{ marginBottom: 8 }}>
      <p className="esc-item__q">{esc.question}</p>
      <div className="esc-item__meta">
        <span>{esc.student}</span>
        <span className="dot">·</span>
        <span className="status-badge needs">Needs answer</span>
      </div>
      {open ? (
        <div style={{ marginTop: 8 }}>
          <textarea
            placeholder="Type your answer — it's sent to the student's chat…"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={2}
            style={{ width: '100%', marginBottom: 8 }}
          />
          <div className="flex gap-sm">
            <button className="btn btn--primary" onClick={send} disabled={!answer.trim()}>Send answer</button>
            <button className="btn btn--ghost" onClick={() => setOpen(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <div className="esc-actions">
          <button className="btn btn--primary" onClick={() => setOpen(true)}>Answer</button>
        </div>
      )}
    </div>
  )
}
