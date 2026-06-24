import { useState } from 'react'
import TopNav from '../components/TopNav.jsx'
import { ChatThread, Composer } from '../components/Chat.jsx'
import PollCard from '../components/PollCard.jsx'
import ResultBars from '../components/ResultBars.jsx'
import {
  student,
  liveSession,
  livePoll,
  liveResults,
  liveSideChat,
  cannedReplies,
} from '../data/mock.js'

let replyIdx = 1

export default function StudentLiveView() {
  const [messages, setMessages] = useState(liveSideChat)
  const [typing, setTyping] = useState(false)
  const [results, setResults] = useState(liveResults)

  const send = (text) => {
    setMessages((m) => [...m, { id: `u-${Date.now()}`, role: 'user', text, time: 'now' }])
    setTyping(true)
    setTimeout(() => {
      const canned = cannedReplies[replyIdx % cannedReplies.length]
      replyIdx += 1
      setTyping(false)
      setMessages((m) => [
        ...m,
        { id: `a-${Date.now()}`, role: 'ai', text: canned.text, source: canned.source, time: 'now' },
      ])
    }, 1100)
  }

  // When the student answers the poll, bump that option's count live.
  const onAnswer = (optId) => {
    setResults((rs) => rs.map((r) => (r.id === optId ? { ...r, count: r.count + 1 } : r)))
  }

  const totalConnected = liveSession.connected
  const totalAnswered = results.reduce((s, r) => s + r.count, 0)

  return (
    <>
      <TopNav variant="live" courseName="CS 310" user={student} />

      <div className="live-banner">
        <span className="live-dot" />
        <span>
          <strong>{liveSession.professor}'s</strong> class is live — {liveSession.course}
        </span>
        <span className="count-badge">
          <span className="live-dot" style={{ animation: 'none' }} />
          {totalConnected} connected
        </span>
      </div>

      <div className="live-split">
        <div className="live-main">
          <div className="chat">
            <PollCard poll={livePoll} totalAnswered={totalAnswered} onAnswer={onAnswer} />
            <ChatThread messages={messages} typing={typing} />
            <Composer
              onSend={send}
              placeholder="Ask the AI quietly during class…"
              hint="Your side questions are private and won't interrupt the class."
            />
          </div>
        </div>

        <aside className="live-aside">
          <div className="aside-header">
            <h3>Class Activity</h3>
            <p>Live poll results · updating in real time</p>
          </div>
          <div className="aside-body">
            <ResultBars results={results} />
            <div style={{ display: 'flex', gap: 10 }}>
              <div className="stat-inline" style={{ flex: 1 }}>
                <div>
                  <div className="big">{totalAnswered}</div>
                  <div className="lbl">Responses</div>
                </div>
              </div>
              <div className="stat-inline" style={{ flex: 1 }}>
                <div>
                  <div className="big">{Math.round((totalAnswered / totalConnected) * 100)}%</div>
                  <div className="lbl">Participation</div>
                </div>
              </div>
            </div>
            <div className="card" style={{ padding: 14 }}>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                Session info
              </div>
              <div style={{ fontSize: 13, color: 'var(--ink-soft)', lineHeight: 1.7 }}>
                <div className="flex between"><span>Started</span><strong>2:05 PM</strong></div>
                <div className="flex between"><span>Polls pushed</span><strong>3</strong></div>
                <div className="flex between"><span>Questions asked</span><strong>27</strong></div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </>
  )
}
