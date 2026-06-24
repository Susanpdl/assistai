import { useEffect, useRef, useState } from 'react'
import { Avatar } from './TopNav.jsx'

export function MessageBubble({ msg }) {
  const isAI = msg.role === 'ai'
  return (
    <div className={`msg ${isAI ? 'msg--ai' : 'msg--user'}`}>
      <Avatar initials={isAI ? '◆' : 'SP'} tone={isAI ? 'purple' : 'blue'} size="sm" />
      <div className="msg__body">
        <div className="bubble">
          {msg.text.split('\n\n').map((p, i) => (
            <p key={i} style={{ margin: i === 0 ? '0' : '10px 0 0' }}>
              {p}
            </p>
          ))}
        </div>
        {msg.source && (
          <span className="source-pill">
            <span className="ico">📄</span>
            {msg.source}
          </span>
        )}
        {msg.time && <span className="msg__meta">{msg.time}</span>}
      </div>
    </div>
  )
}

export function TypingBubble() {
  return (
    <div className="msg msg--ai">
      <Avatar initials="◆" tone="purple" size="sm" />
      <div className="msg__body">
        <div className="bubble">
          <span className="typing">
            <span /><span /><span />
          </span>
        </div>
      </div>
    </div>
  )
}

export function Composer({ onSend, placeholder = 'Ask anything about this course…', hint }) {
  const [value, setValue] = useState('')
  const ref = useRef(null)

  const grow = (el) => {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }

  const submit = () => {
    const text = value.trim()
    if (!text) return
    onSend(text)
    setValue('')
    if (ref.current) ref.current.style.height = 'auto'
  }

  return (
    <div className="composer">
      <div className="composer__inner">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          placeholder={placeholder}
          onChange={(e) => {
            setValue(e.target.value)
            grow(e.target)
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              submit()
            }
          }}
        />
        <button className="send-btn" onClick={submit} disabled={!value.trim()} aria-label="Send">
          ↑
        </button>
      </div>
      {hint && <p className="composer__hint">{hint}</p>}
    </div>
  )
}

// Auto-scrolling message list
export function ChatThread({ messages, typing }) {
  const endRef = useRef(null)
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing])

  return (
    <div className="chat__scroll">
      <div className="chat__inner">
        {messages.map((m) => (
          <MessageBubble key={m.id} msg={m} />
        ))}
        {typing && <TypingBubble />}
        <div ref={endRef} />
      </div>
    </div>
  )
}
