export default function ProductCard({ product, pickTag, index = 0 }) {
  const { title, price, currency, rating, reviews_count, image, asin, best_seller, price_strikethrough, sales_volume } = product

  const discount =
    price_strikethrough && price ? Math.round((1 - price / price_strikethrough) * 100) : null

  return (
    <div className="card" style={{ animationDelay: `${index * 70}ms` }}>
      <i className="corner tl" /><i className="corner tr" /><i className="corner bl" /><i className="corner br" />

      <div className="card-flags">
        {pickTag && <span className="badge pick-badge">{pickTag}</span>}
        {best_seller && <span className="badge">BESTSELLER</span>}
        {discount ? <span className="badge off">-{discount}%</span> : null}
      </div>

      {image && (
        <div className="card-img">
          <img src={image} alt={title} loading="lazy" />
        </div>
      )}

      <div className="title">{title}</div>

      <div className="row">
        <span className="price">
          <span className="cur">{currency || ''}</span>
          {price != null ? price.toLocaleString('en-IN') : '–'}
        </span>
        {price_strikethrough ? (
          <span className="strike">{price_strikethrough.toLocaleString('en-IN')}</span>
        ) : null}
      </div>

      <div className="rating-row">
        {rating != null && (
          <span className="stars" title={`${rating} / 5`}>
            <span className="stars-bg">★★★★★</span>
            <span className="stars-fill" style={{ width: `${(rating / 5) * 100}%` }}>★★★★★</span>
          </span>
        )}
        <span className="reviews">{reviews_count != null ? `${reviews_count.toLocaleString('en-IN')}` : ''}</span>
      </div>

      {sales_volume && <div className="velocity">{sales_volume}</div>}
      <div className="asin">{asin}</div>
    </div>
  )
}
