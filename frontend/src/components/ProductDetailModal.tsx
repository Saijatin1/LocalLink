import { useState } from 'react'
import type { Product } from '../types'

interface Props {
  product: Product
  onClose: () => void
  onAddToCart: (product: Product, qty?: number) => void
}

const CATEGORY_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  grocery: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500' },
  sweet: { bg: 'bg-pink-50', text: 'text-pink-700', dot: 'bg-pink-500' },
  clothing: { bg: 'bg-violet-50', text: 'text-violet-700', dot: 'bg-violet-500' },
  beverage: { bg: 'bg-cyan-50', text: 'text-cyan-700', dot: 'bg-cyan-500' },
  snacks: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500' },
  dairy: { bg: 'bg-blue-50', text: 'text-blue-700', dot: 'bg-blue-500' },
}

function gsmLabel(gsm: number): string {
  if (gsm >= 400) return 'Heavy'
  if (gsm >= 250) return 'Premium'
  if (gsm >= 180) return 'Regular'
  return 'Lightweight'
}

function gsmDescription(gsm: number): string {
  if (gsm >= 400) return 'Durable, thick fabric — ideal for winters & structured wear'
  if (gsm >= 250) return 'High-quality midweight — great all-season comfort'
  if (gsm >= 180) return 'Everyday essential — breathable & versatile'
  return 'Ultra-light & airy — perfect for summers & layering'
}

export default function ProductDetailModal({ product, onClose, onAddToCart }: Props) {
  const [quantity, setQuantity] = useState(1)
  const [adding, setAdding] = useState(false)
  const [added, setAdded] = useState(false)
  const inStock = product.stock_qty > 0
  const colors = CATEGORY_COLORS[product.category] || { bg: 'bg-gray-50', text: 'text-gray-700', dot: 'bg-gray-500' }

  const handleAdd = async () => {
    setAdding(true)
    try {
      await onAddToCart(product, quantity)
      setAdded(true)
      setTimeout(() => {
        setAdded(false)
        onClose()
      }, 800)
    } catch {
      setAdding(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl overflow-hidden animate-modal-in">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 w-8 h-8 rounded-full bg-white/90 flex items-center justify-center shadow-sm hover:bg-white transition-colors"
        >
          <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="flex flex-col sm:flex-row">
          {/* Left — Image */}
          <div className="sm:w-56 h-48 sm:h-auto bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center shrink-0">
            <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-2xl bg-white shadow-md flex items-center justify-center">
              <span className="text-3xl sm:text-4xl font-bold text-gray-300">{product.name.charAt(0)}</span>
            </div>
          </div>

          {/* Right — Details */}
          <div className="flex-1 p-5 sm:p-6">
            {/* Category Badge */}
            <div className="flex items-center gap-2 mb-2">
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider ${colors.bg} ${colors.text}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${colors.dot}`} />
                {product.category}
              </span>
              {product.area_tag && (
                <span className="px-2 py-0.5 rounded-full bg-gray-50 text-[10px] text-gray-500 font-medium">
                  {product.area_tag}
                </span>
              )}
            </div>

            {/* Name */}
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 leading-tight">{product.name}</h2>

            {/* Rating */}
            {product.rating && (
              <div className="flex items-center gap-1.5 mt-1">
                <div className="flex items-center gap-0.5">
                  {[...Array(5)].map((_, i) => (
                    <svg
                      key={i}
                      className={`w-3.5 h-3.5 ${i < Math.round(product.rating!) ? 'text-amber-400' : 'text-gray-200'}`}
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <span className="text-xs text-gray-500">{product.rating}</span>
              </div>
            )}

            {/* Price */}
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-gray-900">₹{product.price}</span>
              {inStock && product.stock_qty <= 10 && (
                <span className="text-[10px] text-amber-600 font-medium bg-amber-50 px-1.5 py-0.5 rounded">
                  Only {product.stock_qty} left
                </span>
              )}
            </div>

            {/* Stock status */}
            {!inStock && (
              <div className="mt-2 flex items-center gap-1.5 text-xs text-red-500">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                Out of Stock
              </div>
            )}
          </div>
        </div>

        {/* Divider */}
        <div className="mx-5 sm:mx-6 border-t border-gray-100" />

        {/* Attributes Section */}
        <div className="px-5 sm:px-6 py-4">
          {/* Clothing-specific: Fabric / GSM Selector */}
          {product.category === 'clothing' && product.material && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Material & Weight</p>
              <div className="flex flex-wrap gap-2">
                <div className="flex-1 min-w-[120px] px-3 py-2 rounded-xl bg-violet-50 border border-violet-100">
                  <p className="text-xs text-violet-600 font-medium">{product.material}</p>
                  <p className="text-[10px] text-violet-400">Material</p>
                </div>
                {product.fabric_gsm && (
                  <div className="flex-1 min-w-[120px] px-3 py-2 rounded-xl bg-violet-50 border border-violet-100">
                    <p className="text-xs text-violet-600 font-medium">{gsmLabel(product.fabric_gsm)}</p>
                    <p className="text-[10px] text-violet-400">{product.fabric_gsm} GSM</p>
                  </div>
                )}
              </div>
              {product.fabric_gsm && (
                <p className="mt-1.5 text-[10px] text-gray-400 leading-relaxed">
                  {gsmDescription(product.fabric_gsm)}
                </p>
              )}
            </div>
          )}

          {/* All products: Attributes Grid */}
          <div className="grid grid-cols-3 gap-2 mb-4">
            <div className="px-3 py-2 rounded-xl bg-gray-50 text-center">
              <p className="text-xs font-semibold text-gray-900">{product.stock_qty}</p>
              <p className="text-[10px] text-gray-400">Stock</p>
            </div>
            <div className="px-3 py-2 rounded-xl bg-gray-50 text-center">
              <p className="text-xs font-semibold text-gray-900">{product.area_tag}</p>
              <p className="text-[10px] text-gray-400">Area</p>
            </div>
            <div className="px-3 py-2 rounded-xl bg-gray-50 text-center">
              <p className="text-xs font-semibold text-gray-900">#{product.id}</p>
              <p className="text-[10px] text-gray-400">Product ID</p>
            </div>
          </div>

          {/* Quantity Selector */}
          {inStock && (
            <div className="mb-3">
              <p className="text-xs font-medium text-gray-500 mb-1.5">Quantity</p>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                  disabled={quantity <= 1}
                  className="w-9 h-9 rounded-xl border border-gray-200 flex items-center justify-center hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                  <svg className="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                  </svg>
                </button>
                <span className="w-8 text-center text-sm font-semibold text-gray-900 tabular-nums">{quantity}</span>
                <button
                  onClick={() => setQuantity((q) => Math.min(product.stock_qty, q + 1))}
                  disabled={quantity >= product.stock_qty}
                  className="w-9 h-9 rounded-xl border border-gray-200 flex items-center justify-center hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                  <svg className="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </button>
              </div>
            </div>
          )}

          {/* Add to Cart Button */}
          <button
            onClick={handleAdd}
            disabled={!inStock || adding}
            className={`w-full py-3 rounded-xl text-sm font-medium transition-all ${
              added
                ? 'bg-emerald-500 text-white'
                : inStock
                  ? 'bg-brand-500 text-white hover:bg-brand-600 active:scale-[0.98]'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            {added ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Added to Cart
              </span>
            ) : adding ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                Adding…
              </span>
            ) : inStock ? (
              `Add to Cart — ₹${(product.price * quantity).toFixed(0)}`
            ) : (
              'Out of Stock'
            )}
          </button>
        </div>
      </div>

      <style>{`
        @keyframes modal-in {
          from {
            opacity: 0;
            transform: scale(0.95) translateY(10px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
        .animate-modal-in {
          animation: modal-in 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
      `}</style>
    </div>
  )
}
