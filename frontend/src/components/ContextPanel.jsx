import { useEffect, useRef, useState } from 'react'

const MAX_MESSAGES = 12
const SEGMENTS = 12

export default function ContextPanel({ state }) {
  const { message_count = 0, summary = '', checkpoints = 0 } = state || {}
  const [flash, setFlash] = useState(false)
  const prevSummary = useRef(summary)

  useEffect(() => {
    if (summary && summary !== prevSummary.current) {
      setFlash(true)
      const t = setTimeout(() => setFlash(false), 1400)
      return () => clearTimeout(t)
    }
    prevSummary.current = summary
  }, [summary])

  const lit = Math.min(SEGMENTS, Math.round((message_count / MAX_MESSAGES) * SEGMENTS))
  const heat = lit >= SEGMENTS * 0.9 ? 'hot' : lit >= SEGMENTS * 0.6 ? 'warm' : ''

  return (
    <section className="memory">
      <h3 className="board-title">
        Agent memory
        {flash && <span className="fired"> · Summarized</span>}
      </h3>

      <div className="mem-row">
        <div className="mem-cell">
          <div className="mem-n">
            {message_count}<span className="mem-of">/{MAX_MESSAGES}</span>
          </div>
          <div className="mem-l">Messages in context</div>
          <div className="led-row">
            {Array.from({ length: SEGMENTS }, (_, i) => (
              <span key={i} className={`led ${i < lit ? `on ${heat}` : ''}`} />
            ))}
          </div>
        </div>
        <div className="mem-cell">
          <div className="mem-n">{checkpoints}</div>
          <div className="mem-l">Checkpoints saved</div>
        </div>
      </div>

      <div className="mem-l" style={{ marginTop: 14, marginBottom: 6 }}>Running summary</div>
      <div className={`summary-box ${summary ? '' : 'empty'} ${flash ? 'summary-flash' : ''}`}>
        {summary || 'Nothing summarized yet. Past the threshold, old messages get folded in here.'}
      </div>
    </section>
  )
}
