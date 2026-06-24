const VIEWS = [
  { id: 'study', label: 'Student · Study' },
  { id: 'live', label: 'Student · In-Class' },
  { id: 'instructor', label: 'Instructor' },
]

export default function ViewSwitcher({ view, setView }) {
  return (
    <div className="switcher" role="tablist" aria-label="Demo views">
      <span className="switcher__label">Demo</span>
      {VIEWS.map((v) => (
        <button
          key={v.id}
          className={view === v.id ? 'active' : ''}
          onClick={() => setView(v.id)}
          role="tab"
          aria-selected={view === v.id}
        >
          {v.label}
        </button>
      ))}
    </div>
  )
}
