import { computePicks } from './Analytics.jsx'

function fmt(n) {
  return n != null ? n.toLocaleString('en-IN') : '–'
}

/* hand-rolled SVG scatter: x = price, y = rating */
function Scatter({ products }) {
  const pts = products.filter((p) => p.price != null && p.rating != null)
  if (pts.length < 2) return null

  const W = 312, H = 190, PAD = { l: 30, r: 12, t: 14, b: 26 }
  const prices = pts.map((p) => p.price)
  const lo = Math.min(...prices), hi = Math.max(...prices)
  const span = hi - lo || 1
  const rLo = 3.4, rHi = 5

  const x = (price) => PAD.l + ((price - lo) / span) * (W - PAD.l - PAD.r)
  const y = (rating) => {
    const r = Math.max(rLo, Math.min(rHi, rating))
    return H - PAD.b - ((r - rLo) / (rHi - rLo)) * (H - PAD.t - PAD.b)
  }

  const midPrice = lo + span / 2

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="scatter">
      {/* value zone: cheap + highly rated */}
      <rect x={PAD.l} y={PAD.t} width={(W - PAD.l - PAD.r) / 2} height={(H - PAD.t - PAD.b) / 2}
        className="zone" />
      <text x={PAD.l + 6} y={PAD.t + 13} className="zone-label">Value zone</text>

      {/* axes */}
      <line x1={PAD.l} y1={H - PAD.b} x2={W - PAD.r} y2={H - PAD.b} className="axis" />
      <line x1={PAD.l} y1={PAD.t} x2={PAD.l} y2={H - PAD.b} className="axis" />

      {/* axis labels */}
      <text x={PAD.l} y={H - 8} className="tick-label">{fmt(lo)}</text>
      <text x={W - PAD.r} y={H - 8} className="tick-label" textAnchor="end">{fmt(hi)}</text>
      <text x={PAD.l - 6} y={y(5) + 4} className="tick-label" textAnchor="end">5★</text>
      <text x={PAD.l - 6} y={y(rLo) + 4} className="tick-label" textAnchor="end">{rLo}★</text>
      <text x={(PAD.l + W - PAD.r) / 2} y={H - 8} className="tick-label" textAnchor="middle">Price →</text>

      {pts.map((p) => (
        <g key={p.asin}>
          <circle
            cx={x(p.price)}
            cy={y(p.rating)}
            r={Math.min(9, 3.5 + Math.log10((p.reviews_count || 1) + 1))}
            className={`dot ${p.price <= midPrice && p.rating >= 4.1 ? 'prime' : ''}`}
          >
            <title>{`${p.title?.slice(0, 50)}\n${p.currency} ${fmt(p.price)} · ★${p.rating} · ${fmt(p.reviews_count)} reviews`}</title>
          </circle>
        </g>
      ))}
    </svg>
  )
}

export default function MarketBoard({ products }) {
  const priced = products.filter((p) => p.price != null)

  if (priced.length < 2) {
    return (
      <section className="board">
        <h3 className="board-title">Market overview</h3>
        <div className="board-empty">
          Run a search and this panel fills with live analytics: price range, a rating
          scatter, and the picks.
        </div>
      </section>
    )
  }

  const prices = priced.map((p) => p.price)
  const ratings = priced.filter((p) => p.rating != null).map((p) => p.rating)
  const lo = Math.min(...prices), hi = Math.max(...prices)
  const avgR = ratings.length ? (ratings.reduce((a, b) => a + b, 0) / ratings.length).toFixed(1) : '–'
  const currency = priced[0].currency || ''
  const picks = computePicks(products)

  return (
    <section className="board">
      <h3 className="board-title">Market overview</h3>

      <div className="board-stats">
        <div className="bstat">
          <span className="bstat-n">{priced.length}</span>
          <span className="bstat-l">Tracked</span>
        </div>
        <div className="bstat">
          <span className="bstat-n">{currency} {fmt(lo)}–{fmt(hi)}</span>
          <span className="bstat-l">Price range</span>
        </div>
        <div className="bstat">
          <span className="bstat-n">★ {avgR}</span>
          <span className="bstat-l">Avg rating</span>
        </div>
      </div>

      <div className="board-chart">
        <div className="chart-caption">Price vs rating · dot size = review volume</div>
        <Scatter products={products} />
      </div>

      {picks.length > 0 && (
        <div className="board-picks">
          {picks.map(({ tag, p }) => (
            <div className="bpick" key={tag}>
              <span className="bpick-tag">{tag}</span>
              <span className="bpick-name" title={p.title}>{p.title?.slice(0, 36)}</span>
              <span className="bpick-price">{p.currency} {fmt(p.price)}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
