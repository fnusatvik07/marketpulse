import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api'
import Sidebar from './components/Sidebar.jsx'
import Turn from './components/Turn.jsx'
import ContextPanel from './components/ContextPanel.jsx'
import Ticker from './components/Ticker.jsx'
import MarketBoard from './components/MarketBoard.jsx'

const HINTS = [
  'Search for wireless earbuds under 1,500 rupees',
  'Find competitors for ASIN B0FC2YFSN4 and compare prices',
  'Download the images of the top rated one',
  'Which one should I sell against, and at what price?',
]

export default function App() {
  const [threads, setThreads] = useState([])
  const [activeThread, setActiveThread] = useState('demo')
  const [turns, setTurns] = useState([])
  const [memState, setMemState] = useState(null)
  const [busy, setBusy] = useState(false)
  const [input, setInput] = useState('')
  const [mockMode, setMockMode] = useState(false)
  const [lastMs, setLastMs] = useState(null)
  const [markets, setMarkets] = useState([])
  const [domain, setDomain] = useState('in')
  const feedRef = useRef(null)

  const refreshThreads = useCallback(async () => {
    try {
      const data = await api.threads()
      setThreads(data.threads.length ? data.threads : ['demo'])
    } catch {
      setThreads(['demo'])
    }
  }, [])

  const loadThread = useCallback(async (threadId) => {
    setActiveThread(threadId)
    try {
      const [hist, st] = await Promise.all([api.history(threadId), api.state(threadId)])
      setTurns(hist.messages.map((m) => ({ role: m.role === 'user' ? 'user' : 'agent', content: m.content })))
      setMemState(st)
    } catch {
      setTurns([])
      setMemState(null)
    }
  }, [])

  useEffect(() => {
    api.health().then((h) => setMockMode(h.mock_mode)).catch(() => {})
    api.marketplaces().then((m) => {
      setMarkets(m.marketplaces)
      setDomain(m.default)
    }).catch(() => {})
    refreshThreads()
    loadThread('demo')
  }, [refreshThreads, loadThread])

  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight })
  }, [turns, busy])

  const send = async (text) => {
    const message = (text || input).trim()
    if (!message || busy) return
    setInput('')
    setBusy(true)
    setTurns((t) => [...t, { role: 'user', content: message }])
    const t0 = performance.now()

    try {
      const res = await api.chat(activeThread, message, domain)
      setLastMs(Math.round(performance.now() - t0))
      setTurns((t) => [
        ...t,
        {
          role: 'agent',
          content: res.reply,
          toolCalls: res.tool_calls,
          products: res.products,
          images: res.images,
        },
      ])
      const st = await api.state(activeThread)
      setMemState(st)
      refreshThreads()
    } catch (err) {
      setLastMs(null)
      setTurns((t) => [...t, { role: 'agent', content: `error: ${err.message}`, error: true }])
    } finally {
      setBusy(false)
    }
  }

  // every product seen in this thread feeds the ticker tape
  const tickerItems = []
  const seen = new Set()
  for (const t of turns) {
    for (const p of t.products || []) {
      if (p.asin && p.price != null && !seen.has(p.asin)) {
        seen.add(p.asin)
        tickerItems.push(p)
      }
    }
  }

  return (
    <div className="layout">
      <Sidebar
        threads={threads}
        activeThread={activeThread}
        onSelect={loadThread}
        onCreate={(id) => {
          setThreads((t) => (t.includes(id) ? t : [...t, id]))
          loadThread(id)
        }}
        mockMode={mockMode}
      />

      <main className="chat-col">
        <div className="topbar">
          <div className="thread-id-block">
            <span className="thread-label">Thread</span>
            <span className="thread-name">{activeThread}</span>
          </div>
          <label className="market-select">
            <span className="market-label">Marketplace</span>
            <select value={domain} onChange={(e) => setDomain(e.target.value)}>
              {markets.map((m) => (
                <option key={m.code} value={m.code}>
                  {m.flag} · amazon.{m.code} ({m.currency})
                </option>
              ))}
            </select>
          </label>
          <Ticker items={tickerItems} />
        </div>

        <div className="feed" ref={feedRef}>
          {turns.length === 0 && !busy ? (
            <div className="empty-state">
              <div className="masthead">
                <h2>
                  Ask the market <em>anything.</em>
                </h2>
                <p className="mast-sub">
                  Live Amazon data, scraped on demand by an agent that remembers
                  every conversation.
                </p>
              </div>
              <div className="hints">
                {HINTS.map((h) => (
                  <button key={h} className="hint" onClick={() => send(h)}>
                    {h}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            turns.map((turn, i) => <Turn key={i} turn={turn} />)
          )}

          {busy && (
            <div className="turn agent">
              <div className="who">MarketPulse</div>
              <div className="thinking">
                <span className="pulse" /> Scraping live market data…
              </div>
            </div>
          )}
        </div>

        <div className="composer">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              send()
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about products, prices, competitors…"
              disabled={busy}
              autoFocus
            />
            <button type="submit" disabled={busy || !input.trim()}>
              Send
            </button>
          </form>
        </div>

        <div className="statusbar">
          <span className={`sb-mode ${mockMode ? 'mock' : 'live'}`}>
            {mockMode ? 'Mock data' : 'Live'}
          </span>
          <span className="sb-item">Thread {activeThread}</span>
          <span className="sb-item">Messages {memState?.message_count ?? 0} of 12</span>
          <span className="sb-item">Checkpoints {memState?.checkpoints ?? 0}</span>
          <span className="sb-spacer" />
          {lastMs != null && <span className="sb-item">Last turn {(lastMs / 1000).toFixed(1)}s</span>}
          <span className="sb-item">{busy ? 'Working…' : 'Idle'}</span>
        </div>
      </main>

      <aside className="boardcol">
        <MarketBoard products={tickerItems} />
        <ContextPanel state={memState} />
      </aside>
    </div>
  )
}
