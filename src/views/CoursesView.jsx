// Phase 2 — real course & enrollment screens (separate from the mock demo views).
// Instructors create courses + approve/reject requests; students join by code.
import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import * as api from '../api/courses.js'
import * as content from '../api/content.js'
import * as tutor from '../api/tutor.js'

export default function CoursesView() {
  const { user } = useAuth()
  return user.role === 'instructor' ? <InstructorCourses /> : <StudentCourses />
}

function InstructorCourses() {
  const [courses, setCourses] = useState([])
  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  const load = useCallback(async () => setCourses(await api.listCourses()), [])
  useEffect(() => {
    load()
  }, [load])

  async function onCreate(e) {
    e.preventDefault()
    setError('')
    try {
      await api.createCourse(code.trim(), name.trim())
      setCode('')
      setName('')
      await load()
    } catch {
      setError('Could not create course.')
    }
  }

  return (
    <div className="courses">
      <h1 className="courses__title">My Courses</h1>

      <form className="card courses__panel" onSubmit={onCreate}>
        <h2 className="courses__h2">Create a course</h2>
        <div className="courses__row">
          <input
            placeholder="Code — e.g. CS 310"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            required
          />
          <input
            placeholder="Name — e.g. Algorithms"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <button className="btn btn--primary" type="submit">
            Create
          </button>
        </div>
        {error && <p className="courses__error">{error}</p>}
      </form>

      {courses.length === 0 ? (
        <p className="courses__empty">No courses yet — create one above.</p>
      ) : (
        courses.map((c) => <InstructorCourseCard key={c.id} course={c} />)
      )}
    </div>
  )
}

function InstructorCourseCard({ course }) {
  const [pending, setPending] = useState([])

  const loadPending = useCallback(
    async () => setPending(await api.listEnrollments(course.id, 'pending')),
    [course.id],
  )
  useEffect(() => {
    loadPending()
  }, [loadPending])

  async function decide(enrollmentId, decision) {
    await api.decide(enrollmentId, decision)
    await loadPending()
  }

  return (
    <div className="card course-card">
      <div className="course-card__head">
        <div>
          <div className="course-card__name">{course.name}</div>
          <div className="course-card__code">{course.code}</div>
        </div>
        <div className="course-card__join">
          <span className="course-card__join-label">Join code</span>
          <code className="course-card__join-code">{course.join_code}</code>
        </div>
      </div>

      <div className="course-card__requests">
        <div className="course-card__requests-label">Pending requests ({pending.length})</div>
        {pending.length === 0 ? (
          <p className="courses__empty">No pending requests.</p>
        ) : (
          pending.map((e) => (
            <div key={e.id} className="req-row">
              <span className="req-row__who">
                {e.student?.name} · {e.student?.email}
              </span>
              <div className="req-row__actions">
                <button className="btn btn--primary" onClick={() => decide(e.id, 'approved')}>
                  Approve
                </button>
                <button className="btn btn--ghost" onClick={() => decide(e.id, 'rejected')}>
                  Reject
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <DocumentsPanel courseId={course.id} />
    </div>
  )
}

// Phase 3 — upload course files; the worker chunks + embeds them so the tutor can
// ground answers in them. Statuses (processing/indexed/failed) come from the backend.
function DocumentsPanel({ courseId }) {
  const [docs, setDocs] = useState([])
  const [drag, setDrag] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)

  const load = useCallback(async () => {
    try {
      setDocs(await content.listDocuments(courseId))
    } catch {
      /* ignore transient load errors */
    }
  }, [courseId])

  useEffect(() => {
    load()
  }, [load])

  // While anything is still processing, poll so the UI reflects the worker's progress.
  useEffect(() => {
    if (!docs.some((d) => d.status === 'processing')) return undefined
    const timer = setInterval(load, 2500)
    return () => clearInterval(timer)
  }, [docs, load])

  async function upload(files) {
    setError('')
    for (const file of files) {
      try {
        await content.uploadDocument(courseId, file)
      } catch (e) {
        setError(
          e.status === 413
            ? 'That file is too large.'
            : e.status === 422
              ? 'Unsupported file type.'
              : 'Upload failed.',
        )
      }
    }
    await load()
  }

  function onDrop(e) {
    e.preventDefault()
    setDrag(false)
    if (e.dataTransfer.files?.length) upload([...e.dataTransfer.files])
  }

  return (
    <div className="course-card__requests">
      <div className="course-card__requests-label">Course content ({docs.length})</div>

      <div
        className={`upload-box ${drag ? 'drag' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setDrag(true)
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <div className="upload-box__icon">⬆</div>
        <h4>Drop slides, notes, or readings here</h4>
        <p>The AI reads these to ground its answers in your material.</p>
        <div className="formats">
          <span className="format-tag">PDF</span>
          <span className="format-tag">DOCX</span>
          <span className="format-tag">PPTX</span>
          <span className="format-tag">TXT</span>
        </div>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.pptx,.txt,.md"
          hidden
          onChange={(e) => {
            if (e.target.files?.length) upload([...e.target.files])
            e.target.value = ''
          }}
        />
      </div>

      {error && <p className="courses__error">{error}</p>}

      {docs.map((d) => (
        <DocRow key={d.id} doc={d} onChange={load} />
      ))}
    </div>
  )
}

function DocRow({ doc, onChange }) {
  const ext = (doc.type || '').toLowerCase()

  async function remove() {
    await content.deleteDocument(doc.id)
    onChange()
  }
  async function retry() {
    await content.reindexDocument(doc.id)
    onChange()
  }

  return (
    <div className="file-row">
      <div className={`file-row__icon ${ext}`}>{ext.toUpperCase()}</div>
      <div className="file-row__main">
        <div className="file-row__name">{doc.filename}</div>
        <div className="file-row__sub">
          {doc.status === 'indexed' && `${doc.chunk_count} chunks embedded`}
          {doc.status === 'processing' && 'Queued for indexing'}
          {doc.status === 'failed' && (doc.error || 'Failed to process')}
        </div>
      </div>

      {doc.status === 'indexed' && <span className="file-status indexed">✓ Indexed</span>}
      {doc.status === 'processing' && (
        <span className="file-status processing">
          <span className="mini-spinner" /> Processing…
        </span>
      )}
      {doc.status === 'failed' && (
        <button className="btn btn--ghost" onClick={retry}>
          Retry
        </button>
      )}
      <button className="btn btn--ghost" onClick={remove} aria-label="Delete" title="Delete">
        ✕
      </button>
    </div>
  )
}

function StudentCourses() {
  const [courses, setCourses] = useState([])
  const [joinCode, setJoinCode] = useState('')
  const [status, setStatus] = useState(null) // { type: 'ok' | 'err', msg }

  const load = useCallback(async () => setCourses(await api.listCourses()), [])
  useEffect(() => {
    load()
  }, [load])

  async function onJoin(e) {
    e.preventDefault()
    setStatus(null)
    try {
      const enr = await api.enroll(joinCode.trim())
      setJoinCode('')
      if (enr.status === 'approved') {
        setStatus({ type: 'ok', msg: "You're enrolled!" })
        await load()
      } else {
        setStatus({ type: 'ok', msg: 'Request sent — waiting for instructor approval.' })
      }
    } catch (err) {
      setStatus({
        type: 'err',
        msg: err.status === 404 ? 'No course found for that code.' : 'Something went wrong.',
      })
    }
  }

  return (
    <div className="courses">
      <h1 className="courses__title">My Courses</h1>

      <form className="card courses__panel" onSubmit={onJoin}>
        <h2 className="courses__h2">Join a course</h2>
        <div className="courses__row">
          <input
            placeholder="Enter join code"
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
            required
          />
          <button className="btn btn--primary" type="submit">
            Request to join
          </button>
        </div>
        {status && (
          <p className={status.type === 'err' ? 'courses__error' : 'courses__ok'}>{status.msg}</p>
        )}
      </form>

      {courses.length === 0 ? (
        <p className="courses__empty">You&apos;re not enrolled in any courses yet.</p>
      ) : (
        courses.map((c) => <StudentCourseCard key={c.id} course={c} />)
      )}
    </div>
  )
}

function StudentCourseCard({ course }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="card course-card">
      <div className="course-card__head">
        <div>
          <div className="course-card__name">{course.name}</div>
          <div className="course-card__code">{course.code}</div>
        </div>
        <button className="btn btn--primary" onClick={() => setOpen((o) => !o)}>
          {open ? 'Close' : 'Ask the AI'}
        </button>
      </div>
      {open && <CourseChat courseId={course.id} />}
    </div>
  )
}

// Phase 4 — real grounded chat backed by POST /ask. Answers carry a citation pill;
// when the tutor escalates, we show a "sent to your instructor" note.
function CourseChat({ courseId }) {
  const [messages, setMessages] = useState([])
  const [typing, setTyping] = useState(false)
  const [value, setValue] = useState('')
  const endRef = useRef(null)

  useEffect(() => {
    tutor
      .listMessages(courseId)
      .then((rows) =>
        setMessages(
          rows.map((m) => ({ role: m.role, text: m.text, citation: m.citation })),
        ),
      )
      .catch(() => {})
  }, [courseId])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing])

  async function send() {
    const q = value.trim()
    if (!q) return
    setValue('')
    setMessages((m) => [...m, { role: 'user', text: q }])
    setTyping(true)
    try {
      const reply = await tutor.ask(courseId, q)
      setMessages((m) => [
        ...m,
        { role: 'ai', text: reply.answer, citation: reply.citation, escalated: reply.escalated },
      ])
    } catch {
      setMessages((m) => [
        ...m,
        { role: 'ai', text: 'Something went wrong reaching the tutor.', error: true },
      ])
    } finally {
      setTyping(false)
    }
  }

  return (
    <div className="course-chat">
      <div className="course-chat__scroll">
        {messages.length === 0 && !typing && (
          <p className="courses__empty">
            Ask anything about this course — answers are grounded in your professor&apos;s
            materials and cited.
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role === 'ai' ? 'msg--ai' : 'msg--user'}`}>
            <div className="msg__body">
              <div className="bubble">{m.text}</div>
              {m.citation && (
                <span className="source-pill">{m.citation}</span>
              )}
              {m.escalated && <span className="msg__meta">↪ Sent to your instructor</span>}
            </div>
          </div>
        ))}
        {typing && (
          <div className="msg msg--ai">
            <div className="msg__body">
              <div className="bubble">
                <span className="typing"><span /><span /><span /></span>
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
      <div className="composer">
        <div className="composer__inner">
          <textarea
            rows={1}
            value={value}
            placeholder="Ask anything about this course…"
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                send()
              }
            }}
          />
          <button className="send-btn" onClick={send} disabled={!value.trim()} aria-label="Send">
            ↑
          </button>
        </div>
      </div>
    </div>
  )
}
