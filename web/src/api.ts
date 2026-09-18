const BASE = import.meta.env.VITE_API_URL ?? '/api'

export interface Health {
  status: string
}

export interface NewCase {
  question: string
  dataset: string
}

export async function getHealth(): Promise<Health> {
  const res = await fetch(`${BASE}/health`)
  if (!res.ok) throw new Error(`health check failed: ${res.status}`)
  return (await res.json()) as Health
}

// POST /cases lands in P0-DATA-003; the client is ready now so the screen is
// wired against the real contract rather than a placeholder.
export async function createCase(newCase: NewCase): Promise<void> {
  const res = await fetch(`${BASE}/cases`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(newCase),
  })
  if (!res.ok) throw new Error(`create case failed: ${res.status}`)
}
