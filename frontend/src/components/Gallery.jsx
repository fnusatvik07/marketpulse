import { useState } from 'react'
import { apiBase } from '../api'

export default function Gallery({ group }) {
  const [zoomed, setZoomed] = useState(null)

  return (
    <div className="gallery">
      <div className="g-label">Images saved · {group.title || group.asin}</div>
      <div className="g-grid">
        {group.paths.map((p) => (
          <img key={p} src={`${apiBase}${p}`} alt={group.asin} onClick={() => setZoomed(p)} />
        ))}
      </div>
      {zoomed && (
        <div className="lightbox" onClick={() => setZoomed(null)}>
          <img src={`${apiBase}${zoomed}`} alt="zoomed" />
        </div>
      )}
    </div>
  )
}
