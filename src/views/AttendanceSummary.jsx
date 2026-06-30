// Instructor attendance history: per session, the date and who attended, with CSV download.
// Limited to the last ~4 months (server-side). Loaded on demand; data is historical.
import { useEffect, useState } from 'react'
import * as attendance from '../api/attendance.js'

const pad = (n) => String(n).padStart(2, '0')

function mmddyyyy(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${pad(d.getMonth() + 1)}/${pad(d.getDate())}/${d.getFullYear()}`
}

function downloadCsv(session) {
  const date = mmddyyyy(session.date)
  const esc = (v) => `"${String(v).replace(/"/g, '""')}"`
  const header = 'Name,Email,Status,Date\n'
  const lines = session.students
    .map((r) => [esc(r.name), esc(r.email), r.status, date].join(','))
    .join('\n')
  const blob = new Blob([header + lines], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `attendance_${date.replace(/\//g, '-')}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export default function AttendanceSummary({ courseId }) {
  const [open, setOpen] = useState(false)
  const [sessions, setSessions] = useState(null)

  useEffect(() => {
    if (open) attendance.getSummary(courseId).then((d) => setSessions(d.sessions)).catch(() => {})
  }, [open, courseId])

  return (
    <div className="course-card__requests">
      <div className="course-card__requests-label" style={{ display: 'flex', alignItems: 'center' }}>
        Attendance history
        <button className="btn btn--ghost" style={{ marginLeft: 'auto' }} onClick={() => setOpen((o) => !o)}>
          {open ? 'Hide' : 'View'}
        </button>
      </div>

      {open && sessions && (
        sessions.length === 0 ? (
          <p className="courses__empty">No sessions in the last 4 months.</p>
        ) : (
          sessions.map((s) => {
            const present = s.students.filter((r) => r.status === 'present')
            return (
              <div key={s.session_id} className="card" style={{ marginBottom: 8 }}>
                <div className="flex between">
                  <strong style={{ fontSize: 13.5 }}>
                    {mmddyyyy(s.date)}
                    {s.status === 'live' && <span className="live-dot" style={{ marginLeft: 6 }} />}
                  </strong>
                  <span className="muted" style={{ fontSize: 12 }}>{s.present}/{s.total} attended</span>
                </div>
                {present.length === 0 ? (
                  <p className="courses__empty" style={{ margin: '6px 0 0' }}>No one attended.</p>
                ) : (
                  <div style={{ marginTop: 6 }}>
                    {present.map((r) => (
                      <div key={r.email} style={{ fontSize: 13, padding: '2px 0' }}>{r.name}</div>
                    ))}
                  </div>
                )}
                <button className="btn btn--ghost" style={{ marginTop: 8 }} onClick={() => downloadCsv(s)}>
                  Download CSV
                </button>
              </div>
            )
          })
        )
      )}
    </div>
  )
}
