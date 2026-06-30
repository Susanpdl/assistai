// Phase 7 — announcements feed. Instructor sees a composer + delete/moderation;
// enrolled students read and comment.
import { useCallback, useState } from 'react'
import * as api from '../api/announcements.js'
import { usePoll } from '../hooks.js'

export default function Announcements({ courseId, isOwner }) {
  const [items, setItems] = useState([])
  const [text, setText] = useState('')

  const load = useCallback(() => {
    api.list(courseId).then(setItems).catch(() => {})
  }, [courseId])

  usePoll(load, 7000) // new announcements/comments appear without a reload

  async function postIt() {
    if (!text.trim()) return
    await api.post(courseId, text.trim())
    setText('')
    load()
  }

  return (
    <div className="course-card__requests">
      <div className="course-card__requests-label">Announcements</div>

      {isOwner && (
        <div className="card" style={{ marginBottom: 8 }}>
          <textarea
            placeholder="Post an announcement — every enrolled student gets an email…"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={2}
            style={{ width: '100%', marginBottom: 8 }}
          />
          <button className="btn btn--primary" onClick={postIt} disabled={!text.trim()}>Post</button>
        </div>
      )}

      {items.length === 0 ? (
        <p className="courses__empty">No announcements yet.</p>
      ) : (
        items.map((a) => (
          <AnnouncementCard key={a.id} a={a} isOwner={isOwner} reload={load} />
        ))
      )}
    </div>
  )
}

function AnnouncementCard({ a, isOwner, reload }) {
  const [comment, setComment] = useState('')

  async function addComment() {
    if (!comment.trim()) return
    await api.comment(a.id, comment.trim())
    setComment('')
    reload()
  }

  return (
    <div className="card" style={{ marginBottom: 8 }}>
      <div className="flex between">
        <strong style={{ fontSize: 13.5 }}>{a.author}</strong>
        {isOwner && (
          <button className="btn btn--ghost" onClick={async () => { await api.remove(a.id); reload() }}>
            Delete
          </button>
        )}
      </div>
      <p style={{ margin: '6px 0 10px', fontSize: 14, whiteSpace: 'pre-wrap' }}>{a.text}</p>

      <div style={{ borderTop: '1px solid var(--line)', paddingTop: 8 }}>
        {a.comments.map((cm) => (
          <div key={cm.id} className="flex between" style={{ fontSize: 13, padding: '3px 0' }}>
            <span>
              <strong>{cm.author}</strong>
              {cm.author_role === 'instructor' && ' · instructor'}: {cm.text}
            </span>
            {isOwner && (
              <button
                className="btn btn--ghost"
                title="Delete comment"
                onClick={async () => { await api.deleteComment(cm.id); reload() }}
              >
                ✕
              </button>
            )}
          </div>
        ))}
        <div className="courses__row" style={{ marginTop: 6 }}>
          <input
            placeholder="Add a comment…"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <button className="btn btn--ghost" onClick={addComment} disabled={!comment.trim()}>
            Comment
          </button>
        </div>
      </div>
    </div>
  )
}
