const BASE =
  new URLSearchParams(window.location.search).get('api') ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8010'

export const apiBase = BASE

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} on ${path}`)
  return res.json()
}

export const api = {
  health: () => get('/health'),
  threads: () => get('/threads'),
  history: (threadId) => get(`/threads/${encodeURIComponent(threadId)}/history`),
  state: (threadId) => get(`/threads/${encodeURIComponent(threadId)}/state`),
  marketplaces: () => get('/marketplaces'),
  chat: async (threadId, message, domain) => {
    const res = await fetch(`${BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: threadId, message, domain }),
    })
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}))
      throw new Error(detail.detail || `chat failed with ${res.status}`)
    }
    return res.json()
  },
}
