// Phase 2 — real course & enrollment screens (separate from the mock demo views).
// Instructors create courses + approve/reject requests; students join by code.
import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import * as api from '../api/courses.js'

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
        courses.map((c) => (
          <div key={c.id} className="card course-card">
            <div className="course-card__name">{c.name}</div>
            <div className="course-card__code">{c.code}</div>
          </div>
        ))
      )}
    </div>
  )
}
