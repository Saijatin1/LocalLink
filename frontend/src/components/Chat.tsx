import { useState, useRef, useEffect, useCallback } from 'react'
import { sendChat, addToCart as addToCartApi } from '../api'
import type { Message, Cart } from '../types'

function uid(): string {
  try {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID()
    }
  } catch {}
  return Math.random().toString(36).substring(2, 15)
}

interface ParsedProduct {
  id: number
  name: string
  price: number
}

// Regex to extract [id] Name — ₹price from agent responses
const PRODUCT_PATTERN = /\[\s*(\d+)\s*\]\s*(.+?)\s*[—–-]\s*[₹Rs.]*\s*([\d.]+)/g

/** Parse [id] Name — ₹price patterns from agent responses */
function parseProducts(text: string): ParsedProduct[] {
  const products: ParsedProduct[] = []
  const pattern = new RegExp(PRODUCT_PATTERN.source, 'g')
  let match
  while ((match = pattern.exec(text)) !== null) {
    products.push({
      id: parseInt(match[1]),
      name: match[2].trim(),
      price: parseFloat(match[3]),
    })
  }
  return products
}

function renderMessageContent(
  content: string,
  onAdd: (productId: number) => void,
  addingSet: Set<number>,
) {
  const products = parseProducts(content)
  if (products.length === 0) {
    return <span>{content}</span>
  }

  // Split text around product matches to preserve formatting
  const parts: { type: 'text' | 'product'; content: string; product?: ParsedProduct }[] = []
  const regex = /\[\s*(\d+)\s*\]\s*(.+?)\s*[—–-]\s*[₹Rs.]*\s*([\d.]+)/g
  let lastIndex = 0
  let m
  while ((m = regex.exec(content)) !== null) {
    if (m.index > lastIndex) {
      parts.push({ type: 'text', content: content.slice(lastIndex, m.index) })
    }
    parts.push({
      type: 'product',
      content: m[0],
      product: { id: parseInt(m[1]), name: m[2].trim(), price: parseFloat(m[3]) },
    })
    lastIndex = regex.lastIndex
  }
  if (lastIndex < content.length) {
    parts.push({ type: 'text', content: content.slice(lastIndex) })
  }

  return (
    <div className="space-y-2">
      {parts.map((part, i) =>
        part.type === 'text' ? (
          <span key={i}>{part.content}</span>
        ) : (
          <div key={i} className="flex items-center gap-3 mt-2 p-2.5 bg-gray-50 rounded-xl border border-gray-100">
            <div className="w-9 h-9 rounded-lg bg-white flex items-center justify-center shadow-sm flex-shrink-0">
              <span className="text-xs font-bold text-gray-400">{part.product!.name.charAt(0)}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-900 truncate">{part.product!.name}</p>
              <p className="text-xs text-gray-500">₹{part.product!.price}</p>
            </div>
            <button
              onClick={() => onAdd(part.product!.id)}
              disabled={addingSet.has(part.product!.id)}
              className="px-3 py-1.5 text-xs font-medium bg-brand-500 text-white rounded-lg hover:bg-brand-600 disabled:opacity-40 transition-all active:scale-[0.97] flex-shrink-0"
            >
              {addingSet.has(part.product!.id) ? 'Adding…' : 'Add'}
            </button>
          </div>
        ),
      )}
    </div>
  )
}

interface Props {
  userId: string
  onCartUpdate: (cart: Cart) => void
  onCatalogSearch?: (query: string) => void
}

export default function Chat({ userId, onCartUpdate, onCatalogSearch }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: uid(),
      role: 'assistant',
      content: 'Hi! I can help you find products. Try "I want maggi" or "something sweet under 200".',
    },
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [addingProducts, setAddingProducts] = useState<Set<number>>(new Set())
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleAddProduct = useCallback(async (productId: number) => {
    setAddingProducts((s) => new Set(s).add(productId))
    try {
      const updatedCart = await addToCartApi(userId, productId)
      onCartUpdate(updatedCart)
    } catch {
      console.warn('Failed to add item')
    }
    setAddingProducts((s) => {
      const next = new Set(s)
      next.delete(productId)
      return next
    })
  }, [userId, onCartUpdate])

  const handleSend = async () => {
    const text = input.trim()
    if (!text || sending) return
    setInput('')
    setSending(true)

    const userMsg: Message = { id: uid(), role: 'user', content: text }
    setMessages((m) => [...m, userMsg])

    try {
      const res = await sendChat(userId, text)
      const assistantMsg: Message = {
        id: uid(),
        role: 'assistant',
        content: res.response,
      }
      setMessages((m) => [...m, assistantMsg])
      onCartUpdate(res.cart)

      if (res.flagged_hallucination) {
        console.warn('Hallucination flagged by grounding check')
      }
    } catch {
      const errMsg: Message = {
        id: uid(),
        role: 'assistant',
        content: 'Sorry, something went wrong. Check that the backend server is running.',
      }
      setMessages((m) => [...m, errMsg])
    }
    setSending(false)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-brand-500 text-white rounded-br-md'
                  : 'bg-white border border-gray-100 shadow-sm rounded-bl-md'
              }`}
            >
              {msg.role === 'assistant'
                ? renderMessageContent(msg.content, handleAddProduct, addingProducts)
                : msg.content}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex justify-start animate-fade-in-up">
            <div className="bg-white border border-gray-100 shadow-sm rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex gap-1.5">
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="mt-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask me to find something..."
          className="flex-1 px-4 py-3 rounded-xl border border-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
        />
        <button
          onClick={handleSend}
          disabled={sending || !input.trim()}
          className="px-5 py-3 bg-brand-500 text-white rounded-xl hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" />
          </svg>
        </button>
      </div>
    </div>
  )
}
