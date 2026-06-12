import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import ProductCard from './ProductCard.jsx'
import Gallery from './Gallery.jsx'
import Analytics, { computePicks } from './Analytics.jsx'

export default function Turn({ turn }) {
  if (turn.role === 'user') {
    return (
      <div className="turn user">
        <div className="bubble">{turn.content}</div>
      </div>
    )
  }

  const picks = turn.products?.length ? computePicks(turn.products) : []
  const pickFor = (asin) => picks.find((x) => x.p.asin === asin)?.tag

  return (
    <div className="turn agent">
      <div className="who">MarketPulse</div>

      {turn.toolCalls?.length > 0 && (
        <div className="trace">
          {turn.toolCalls.map((c, i) => (
            <div className="trace-line" key={i}>
              <span className="fn">{c.name}</span>
              <span className="args">({JSON.stringify(c.args)})</span>
            </div>
          ))}
        </div>
      )}

      <div className={`bubble ${turn.error ? 'error' : ''}`}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{turn.content}</ReactMarkdown>
      </div>

      {turn.products?.length >= 2 && <Analytics products={turn.products} />}

      {turn.products?.length > 0 && (
        <div className="cards">
          {turn.products.map((p, i) => (
            <ProductCard key={p.asin} product={p} pickTag={pickFor(p.asin)} index={i} />
          ))}
        </div>
      )}

      {turn.images?.map((group) => (
        <Gallery key={group.asin} group={group} />
      ))}
    </div>
  )
}
