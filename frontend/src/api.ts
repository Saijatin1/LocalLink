import type { Product, Cart, ChatResponse } from './types'

// Uses Vite dev server proxy (vite.config.ts maps /api → http://localhost:8000)
// In production, this would be the actual backend URL
const BASE = '/api'

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text()
    let detail = text.slice(0, 200)
    try {
      const parsed = JSON.parse(text)
      if (parsed.detail) detail = parsed.detail
    } catch {}
    throw new Error(detail)
  }
  return res.json()
}

export async function getCatalog(
  query?: string,
  area?: string,
  maxPrice?: number,
): Promise<Product[]> {
  const params = new URLSearchParams()
  if (query) params.set('query', query)
  if (area) params.set('vendor_area', area)
  if (maxPrice !== undefined) params.set('max_price', String(maxPrice))
  const qs = params.toString()
  return fetchJson<Product[]>(`${BASE}/catalog${qs ? `?${qs}` : ''}`)
}

export async function getCart(userId: string): Promise<Cart> {
  return fetchJson<Cart>(`${BASE}/cart/${encodeURIComponent(userId)}`)
}

export async function addToCart(
  userId: string,
  productId: number,
  qty = 1,
): Promise<Cart> {
  return fetchJson<Cart>(
    `${BASE}/cart/add?user_id=${encodeURIComponent(userId)}&product_id=${productId}&qty=${qty}`,
    { method: 'POST' },
  )
}

export async function sendChat(
  userId: string,
  message: string,
): Promise<ChatResponse> {
  return fetchJson<ChatResponse>(`${BASE}/chat`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, message }),
  })
}

export async function resetSession(userId: string): Promise<void> {
  await fetchJson<{ message: string }>(`${BASE}/reset-session`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  })
}
