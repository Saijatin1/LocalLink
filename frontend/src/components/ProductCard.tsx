import type { Product } from '../types'

interface Props {
  product: Product
  onAddToCart: (product: Product) => void
  onViewDetail: (product: Product) => void
}

const CATEGORY_COLORS: Record<string, string> = {
  grocery: 'bg-emerald-50 text-emerald-700',
  sweet: 'bg-pink-50 text-pink-700',
  clothing: 'bg-violet-50 text-violet-700',
  beverage: 'bg-cyan-50 text-cyan-700',
  snacks: 'bg-amber-50 text-amber-700',
  dairy: 'bg-blue-50 text-blue-700',
}

export default function ProductCard({ product, onAddToCart, onViewDetail }: Props) {
  const catColor = CATEGORY_COLORS[product.category] || 'bg-gray-50 text-gray-600'
  const inStock = product.stock_qty > 0

  return (
    <div
      onClick={() => onViewDetail(product)}
      className="group relative rounded-2xl bg-white border border-gray-100 p-4 hover:shadow-lg hover:border-brand-100 transition-all duration-200 cursor-pointer"
    >
      {/* Category Badge */}
      <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider ${catColor}`}>
        {product.category}
      </span>

      {/* Product Image Placeholder */}
      <div className="mt-3 h-28 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl flex items-center justify-center">
        <div className="w-12 h-12 rounded-xl bg-white/80 flex items-center justify-center shadow-sm">
          <span className="text-lg font-semibold text-gray-400">{product.name.charAt(0)}</span>
        </div>
      </div>

      {/* Product Info */}
      <div className="mt-3">
        <h3 className="text-sm font-medium text-gray-900 line-clamp-1">{product.name}</h3>
        <div className="mt-1 flex items-center justify-between">
          <span className="text-lg font-semibold text-gray-900">₹{product.price}</span>
          {product.rating && (
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <svg className="w-3.5 h-3.5 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              {product.rating}
            </span>
          )}
        </div>
      </div>

      {/* Attributes */}
      {(product.fabric_gsm || product.material) && (
        <div className="mt-2 flex flex-wrap gap-1">
          {product.fabric_gsm && (
            <span className="px-2 py-0.5 bg-gray-50 rounded-md text-[10px] text-gray-500">{product.fabric_gsm} GSM</span>
          )}
          {product.material && (
            <span className="px-2 py-0.5 bg-gray-50 rounded-md text-[10px] text-gray-500">{product.material}</span>
          )}
        </div>
      )}

      {/* Quick Add + View Detail */}
      <div className="mt-3 flex gap-2">
        <button
          onClick={(e) => {
            e.stopPropagation()
            onAddToCart(product)
          }}
          disabled={!inStock}
          className={`flex-1 py-2 rounded-xl text-sm font-medium transition-all ${
            inStock
              ? 'bg-brand-500 text-white hover:bg-brand-600 active:scale-[0.98]'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
        >
          {inStock ? 'Add to Cart' : 'Out of Stock'}
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onViewDetail(product)
          }}
          className="px-3 py-2 rounded-xl border border-gray-200 text-gray-500 hover:text-gray-700 hover:bg-gray-50 text-sm transition-all"
          title="View details"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        </button>
      </div>
    </div>
  )
}
