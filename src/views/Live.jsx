// Phase 5 — real live-session UI wired to the WebSocket.
// InstructorLive: start a session, push a poll, watch live tallies, reveal, end.
// StudentLive: see "live", answer the pushed poll, see results once revealed.
import { useCallback, useEffect, useRef, useState } from 'react'
import * as live from '../api/live.js'
import * as attendance from '../api/attendance.js'
import ResultBars from '../components/ResultBars.jsx'

function tallyToBars(activity, results) {
  if (!activity || !results) return []
  return activity.options.map((opt, i) => ({
    id: String(i),
    label: opt,
    count: results.tallies[opt] ?? 0,
  }))
}

export function InstructorLive({ courseId }) {
  const [session, setSession] = useState(null)
  const [connected, setConnected] = useState(0)
  const [activity, setActivity] = useState(null)
  const [results, setResults] = useState(null)
  const [revealed, setRevealed] = useState(false)
  const [question, setQuestion] = useState('')
  const [options, setOptions] = useState(['', '', '', ''])
  const wsRef = useRef(null)

  // Resume an already-running session for this course.
  useEffect(() => {
    live.activeSession(courseId).then((s) => s && setSession(s)).catch(() => {})
  }, [courseId])

  useEffect(() => {
    if (!session) return undefined
    const ws = live.openSessionSocket(session.id, (msg) => {
      if (msg.type === 'connected_count') setConnected(msg.count)
      else if (msg.type === 'results_update') setResults(msg)
      else if (msg.type === 'session_ended') setSession(null)
    })
    wsRef.current = ws
    return () => ws.close()
  }, [session])

  async function start() {
    setSession(await live.startSession(courseId))
  }

  async function push() {
    const opts = options.map((o) => o.trim()).filter(Boolean)
    if (!question.trim() || opts.length < 2) return
    const a = await live.pushPoll(session.id, question.trim(), opts)
    setActivity(a)
    setResults({ tallies: Object.fromEntries(opts.map((o) => [o, 0])), total: 0 })
    setRevealed(false)
    setQuestion('')
    setOptions(['', '', '', ''])
  }

  async function reveal() {
    await live.revealPoll(activity.id)
    setRevealed(true)
  }

  async function end() {
    await live.endSession(session.id)
    wsRef.current?.close()
    setSession(null)
    setActivity(null)
    setResults(null)
  }

  if (!session) {
    return (
      <div className="course-card__requests">
        <div className="course-card__requests-label">Live session</div>
        <button className="btn btn--primary" onClick={start}>Start live session</button>
      </div>
    )
  }

  return (
    <div className="course-card__requests">
      <div className="course-card__requests-label" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className="live-dot" /> Live · {connected} student{connected === 1 ? '' : 's'} connected
        <button className="btn btn--ghost" style={{ marginLeft: 'auto' }} onClick={end}>End</button>
      </div>

      <AttendanceInstructor sessionId={session.id} />

      {!activity && (
        <div className="card" style={{ marginTop: 8 }}>
          <input
            placeholder="Poll question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            style={{ marginBottom: 8 }}
          />
          {options.map((o, i) => (
            <input
              key={i}
              placeholder={`Option ${i + 1}`}
              value={o}
              onChange={(e) => setOptions((os) => os.map((v, j) => (j === i ? e.target.value : v)))}
              style={{ marginBottom: 6 }}
            />
          ))}
          <button className="btn btn--primary" onClick={push}>Push to class</button>
        </div>
      )}

      {activity && (
        <div className="card" style={{ marginTop: 8 }}>
          <div className="poll-card__q" style={{ fontSize: 15 }}>{activity.question}</div>
          <ResultBars results={tallyToBars(activity, results)} />
          <div className="flex between" style={{ marginTop: 12 }}>
            <span className="muted" style={{ fontSize: 12 }}>{results?.total ?? 0} responses</span>
            <div className="flex gap-sm">
              {!revealed && <button className="btn btn--primary" onClick={reveal}>Reveal to class</button>}
              {revealed && <span className="status-badge answered">Revealed</span>}
              <button className="btn btn--ghost" onClick={() => { setActivity(null); setResults(null) }}>
                New poll
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const KEYS = ['A', 'B', 'C', 'D', 'E']

export function StudentLive({ courseId }) {
  const [session, setSession] = useState(null)
  const [connected, setConnected] = useState(0)
  const [activity, setActivity] = useState(null)
  const [selected, setSelected] = useState(null)
  const [results, setResults] = useState(null)
  const [revealed, setRevealed] = useState(false)
  const wsRef = useRef(null)

  // Poll for a live session until one appears (then connect).
  const checkActive = useCallback(() => {
    live.activeSession(courseId).then((s) => s && setSession(s)).catch(() => {})
  }, [courseId])

  useEffect(() => {
    if (session) return undefined
    checkActive()
    const t = setInterval(checkActive, 5000)
    return () => clearInterval(t)
  }, [session, checkActive])

  useEffect(() => {
    if (!session) return undefined
    const ws = live.openSessionSocket(session.id, (msg) => {
      if (msg.type === 'connected_count') setConnected(msg.count)
      else if (msg.type === 'poll_pushed') {
        setActivity(msg.activity)
        setSelected(null)
        setResults(null)
        setRevealed(false)
      } else if (msg.type === 'poll_revealed') setRevealed(true)
      else if (msg.type === 'results_update') setResults(msg)
      else if (msg.type === 'session_ended') {
        setSession(null)
        setActivity(null)
      }
    })
    wsRef.current = ws
    return () => ws.close()
  }, [session])

  function answer(opt) {
    if (selected) return
    setSelected(opt)
    wsRef.current?.send(JSON.stringify({ type: 'submit_answer', activity_id: activity.id, choice: opt }))
  }

  if (!session) return null

  return (
    <div className="course-card__requests">
      <div className="live-banner" style={{ borderRadius: 8, border: '1px solid var(--line)' }}>
        <span className="live-dot" />
        <span><strong>Class is live</strong> — {connected} connected</span>
      </div>

      <AttendanceStudent sessionId={session.id} />

      {!activity && <p className="courses__empty">Waiting for the instructor to push a poll…</p>}

      {activity && (
        <div className="poll-card" style={{ margin: '10px 0 0' }}>
          <div className="poll-card__body">
            <h3 className="poll-card__q">{activity.question}</h3>
            <div className="poll-options">
              {activity.options.map((opt, i) => (
                <button
                  key={opt}
                  className={`poll-opt ${selected === opt ? 'selected' : ''}`}
                  onClick={() => answer(opt)}
                  disabled={!!selected && selected !== opt}
                >
                  <span className="key">{KEYS[i]}</span>
                  <span className="txt">{opt}</span>
                  {selected === opt && <span className="check">✓</span>}
                </button>
              ))}
            </div>
            <div className="poll-card__foot">
              {selected ? <span className="done">✓ Answer submitted</span> : <span>Tap an option to answer</span>}
            </div>
            {revealed && results && (
              <div style={{ marginTop: 14 }}>
                <ResultBars results={tallyToBars(activity, results)} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// Instructor: the rotating check-in code (for the projector) + live attendance roster.
function AttendanceInstructor({ sessionId }) {
  const [code, setCode] = useState(null)
  const [roster, setRoster] = useState(null)

  useEffect(() => {
    let alive = true
    const tick = () => {
      attendance.getCode(sessionId).then((c) => alive && setCode(c)).catch(() => {})
      attendance.getAttendance(sessionId).then((r) => alive && setRoster(r)).catch(() => {})
    }
    tick()
    const t = setInterval(tick, 4000)
    return () => {
      alive = false
      clearInterval(t)
    }
  }, [sessionId])

  return (
    <div className="card" style={{ marginTop: 8 }}>
      <div className="course-card__requests-label">Attendance check-in code</div>
      <div className="attend-code">{code?.code ?? '······'}</div>
      <div className="muted" style={{ fontSize: 12, textAlign: 'center' }}>
        Rotates every 15s · {roster ? `${roster.present}/${roster.total} present` : '…'}
      </div>
      {roster && (
        <div style={{ marginTop: 12 }}>
          {roster.rows.map((r) => (
            <div key={r.student} className="flex between" style={{ padding: '6px 0', fontSize: 13 }}>
              <span>{r.student}</span>
              <span className={`status-badge ${r.status === 'present' ? 'answered' : 'needs'}`}>
                {r.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Student: enter the current code to check in; shows present / needs-poll state.
function AttendanceStudent({ sessionId }) {
  const [code, setCode] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function submit() {
    setError('')
    try {
      const r = await attendance.checkin(sessionId, code.trim(), attendance.deviceId())
      setResult(r)
      setCode('')
    } catch (e) {
      setError(e.detail || 'Check-in failed.')
    }
  }

  if (result?.present) {
    return <p className="courses__ok" style={{ marginTop: 8 }}>✓ Checked in — you&apos;re marked present.</p>
  }

  return (
    <div style={{ marginTop: 8 }}>
      {result && result.needs_poll && (
        <p className="courses__ok">✓ Code accepted — answer the poll to complete your attendance.</p>
      )}
      <div className="courses__row">
        <input
          placeholder="Enter check-in code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          inputMode="numeric"
        />
        <button className="btn btn--primary" onClick={submit} disabled={!code.trim()}>
          Check in
        </button>
      </div>
      {error && <p className="courses__error">{error}</p>}
    </div>
  )
}
