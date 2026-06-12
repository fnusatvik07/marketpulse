function median(nums) {
  const s = [...nums].sort((a, b) => a - b)
  const mid = Math.floor(s.length / 2)
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2
}

function fmt(n) {
  return n != null ? n.toLocaleString('en-IN') : '–'
}

function ratingClass(r) {
  if (r == null) return 'cold'
  if (r >= 4.2) return 'hot'
  if (r >= 3.8) return 'warm'
  return 'cold'
}

export function computePicks(products) {
  const priced = products.filter((p) => p.price != null)
  if (priced.length < 2) return []
  const picks = []

  const trusted = [...priced].sort((a, b) => (b.reviews_count || 0) - (a.reviews_count || 0))[0]
  const rated = [...priced]
    .filter((p) => (p.reviews_count || 0) > 50)
    .sort((a, b) => (b.rating || 0) - (a.rating || 0))[0]
  const value = [...priced]
    .filter((p) => (p.rating || 0) >= 3.9)
    .sort((a, b) => a.price - b.price)[0]

  if (value) picks.push({ tag: 'BEST VALUE', why: `rating ${value.rating} at the lowest price`, p: value })
  if (rated && !picks.some((x) => x.p.asin === rated.asin))
    picks.push({ tag: 'TOP RATED', why: `${rated.rating} stars across ${fmt(rated.reviews_count)} reviews`, p: rated })
  if (trusted && !picks.some((x) => x.p.asin === trusted.asin))
    picks.push({ tag: 'MOST TRUSTED', why: `${fmt(trusted.reviews_count)} reviews, the crowd favourite`, p: trusted })

  return picks.slice(0, 3)
}

export default function Analytics({ products }) {
  const priced = products.filter((p) => p.price != null)
  if (priced.length < 2) return null

  const prices = priced.map((p) => p.price)
  const ratings = priced.filter((p) => p.rating != null).map((p) => p.rating)
  const lo = Math.min(...prices)
  const hi = Math.max(...prices)
  const med = median(prices)
  const avgRating = ratings.length ? (ratings.reduce((a, b) => a + b, 0) / ratings.length).toFixed(1) : '–'
  const currency = priced[0].currency || ''
  const picks = computePicks(products)

  return (
    <div className="snapshot">
      <div className="snap-head">
        <span className="snap-title">Market snapshot</span>
        <span className="snap-n">{priced.length} products scanned</span>
      </div>

      <div className="stats">
        <div className="stat">
          <div className="s-label">Price floor</div>
          <div className="s-value dim-cur"><em>{currency}</em>{fmt(lo)}</div>
        </div>
        <div className="stat">
          <div className="s-label">Median</div>
          <div className="s-value dim-cur"><em>{currency}</em>{fmt(med)}</div>
        </div>
        <div className="stat">
          <div className="s-label">Ceiling</div>
          <div className="s-value dim-cur"><em>{currency}</em>{fmt(hi)}</div>
        </div>
        <div className="stat">
          <div className="s-label">Avg rating</div>
          <div className="s-value">★ {avgRating}</div>
        </div>
      </div>

      <div className="ladder">
        <div className="s-label" style={{ marginBottom: 8 }}>Price ladder · colored by rating</div>
        {priced
          .slice()
          .sort((a, b) => a.price - b.price)
          .map((p, i) => (
            <div className="rung" key={p.asin} style={{ animationDelay: `${i * 60}ms` }}>
              <span className="rung-name" title={p.title}>{p.title?.slice(0, 34)}</span>
              <span className="rung-track">
                <span
                  className={`rung-bar ${ratingClass(p.rating)}`}
                  style={{ width: `${Math.max(6, Math.round((p.price / hi) * 100))}%` }}
                />
                {p.best_seller && <span className="rung-flag">BS</span>}
              </span>
              <span className="rung-price">{fmt(p.price)}</span>
              <span className="rung-rating">{p.rating != null ? `★${p.rating}` : ''}</span>
            </div>
          ))}
      </div>

      {picks.length > 0 && (
        <div className="picks">
          <div className="s-label" style={{ marginBottom: 8 }}>MarketPulse picks</div>
          <div className="picks-row">
            {picks.map(({ tag, why, p }) => (
              <div className="pick" key={tag}>
                <div className="pick-tag">{tag}</div>
                <div className="pick-name" title={p.title}>{p.title?.slice(0, 44)}</div>
                <div className="pick-meta">
                  <span className="pick-price">{p.currency} {fmt(p.price)}</span>
                  <span className="pick-asin">{p.asin}</span>
                </div>
                <div className="pick-why">{why}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
