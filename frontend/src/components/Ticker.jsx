export default function Ticker({ items }) {
  if (!items.length) {
    return (
      <div className="ticker">
        <span className="ticker-idle">Run a search to populate the market tape</span>
      </div>
    )
  }

  // duplicate the list so the marquee loops seamlessly
  const tape = [...items, ...items]

  return (
    <div className="ticker">
      <div className="tape" style={{ animationDuration: `${Math.max(20, items.length * 6)}s` }}>
        {tape.map((p, i) => (
          <span className="tick-item" key={`${p.asin}-${i}`}>
            <span className="tick-sym">{(p.title || p.asin || '').slice(0, 22).toUpperCase()}</span>
            <span className="tick-price">{p.currency} {p.price?.toLocaleString('en-IN')}</span>
            {p.rating != null && (
              <span className={`tick-delta ${p.rating >= 4 ? 'up' : 'down'}`}>
                {p.rating >= 4 ? '▲' : '▼'} {p.rating}
              </span>
            )}
          </span>
        ))}
      </div>
    </div>
  )
}
