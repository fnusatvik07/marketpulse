import { useState } from 'react'

export default function Sidebar({ threads, activeThread, onSelect, onCreate, mockMode }) {
  const [name, setName] = useState('')

  const nextId = () => {
    let n = threads.length + 1
    let id = `mp-${String(n).padStart(3, '0')}`
    while (threads.includes(id)) {
      n += 1
      id = `mp-${String(n).padStart(3, '0')}`
    }
    return id
  }

  const createCustom = (e) => {
    e.preventDefault()
    const id = name.trim().replace(/\s+/g, '-').toLowerCase()
    if (!id) return
    onCreate(id)
    setName('')
  }

  return (
    <aside className="sidebar">
      <div className="wordmark">
        <h1>
          Market<span className="tick">Pulse</span>
        </h1>
        <div className="sub">Market intelligence</div>
      </div>

      <button className="new-chat-btn" onClick={() => onCreate(nextId())}>
        <span className="plus">+</span> New analysis
      </button>

      <div className="threads">
        <div className="threads-label">Threads</div>
        {threads.map((t) => (
          <button
            key={t}
            className={`thread-item ${t === activeThread ? 'active' : ''}`}
            onClick={() => onSelect(t)}
          >
            {t}
          </button>
        ))}
      </div>

      <form className="new-thread" onSubmit={createCustom}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Name a new thread"
        />
        <button type="submit" title="create named thread">→</button>
      </form>
    </aside>
  )
}
