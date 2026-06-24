// Horizontal bar chart of live poll results.
export default function ResultBars({ results }) {
  const total = results.reduce((s, r) => s + r.count, 0) || 1
  const max = Math.max(...results.map((r) => r.count))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {results.map((r) => {
        const pct = Math.round((r.count / total) * 100)
        const lead = r.count === max
        return (
          <div className="result-row" key={r.id}>
            <div className="result-row__head">
              <span className="label">{r.label}</span>
              <span className="pct">{pct}%</span>
            </div>
            <div className="result-track">
              <div className={`result-fill ${lead ? 'lead' : ''}`} style={{ width: `${pct}%` }} />
            </div>
            <span className="result-count">{r.count} responses</span>
          </div>
        )
      })}
    </div>
  )
}
