import { useState } from 'react'

const KEYS = ['A', 'B', 'C', 'D', 'E']

export default function PollCard({ poll, totalAnswered = 24, onAnswer }) {
  const [selected, setSelected] = useState(null)

  const pick = (id) => {
    if (selected) return
    setSelected(id)
    onAnswer?.(id)
  }

  return (
    <div className="poll-card">
      <div className="poll-card__top">
        <span className="live-dot" />
        Live poll · respond now
      </div>
      <div className="poll-card__body">
        <h3 className="poll-card__q">{poll.question}</h3>
        <div className="poll-options">
          {poll.options.map((opt, i) => (
            <button
              key={opt.id}
              className={`poll-opt ${selected === opt.id ? 'selected' : ''}`}
              onClick={() => pick(opt.id)}
              disabled={!!selected && selected !== opt.id}
            >
              <span className="key">{KEYS[i]}</span>
              <span className="txt">{opt.label}</span>
              {selected === opt.id && <span className="check">✓</span>}
            </button>
          ))}
        </div>
        <div className="poll-card__foot">
          {selected ? (
            <span className="done">✓ Answer submitted</span>
          ) : (
            <span>Tap an option to submit your answer</span>
          )}
          <span style={{ marginLeft: 'auto' }}>
            {totalAnswered + (selected ? 1 : 0)} of 38 answered
          </span>
        </div>
      </div>
    </div>
  )
}
