import { useState, useEffect, useCallback } from 'react'
import { getCatalog, addToCart as addToCartApi } from '../api'
import type { Product, Cart } from '../types'
import ProductCard from './ProductCard'
import ProductDetailModal from './ProductDetailModal'

const AREAS = ['alwal', 'secunderabad', 'kompally']
const CATEGORIES = ['all', 'grocery', 'sweet', 'clothing', 'beverage', 'snacks', 'dairy']

interface Props {
  onAddToCart: (cart: Cart) => void
  initialSearch?: string
  onSearchChange?: (query: string) => void
}

export default function Catalog({ onAddToCart, initialSearch = '', onSearchChange }: Props) {
  const [products, setProducts] = useState<Product[]>([])
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState(initialSearch)
  const [category, setCategory] = useState('all')
  const [area, setArea] = useState('')

  // Sync when initialSearch changes (e.g. from chat)
  useEffect(() => {
    setSearch(initialSearch)
  }, [initialSearch])

  const fetchProducts = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getCatalog(search || undefined, area || undefined)
      const filtered = category === 'all' ? data : data.filter((p) => p.category === category)
      setProducts(filtered)
    } catch {
      setProducts([])
    }
    setLoading(false)
  }, [search, area, category])

  useEffect(() => {
    fetchProducts()
  }, [fetchProducts])

  const handleSearchChange = (value: string) => {
    setSearch(value)
    onSearchChange?.(value)
  }

  const handleAddToCart = async (product: Product) => {
    try {
      const updatedCart = await addToCartApi('web-user', product.id)
      onAddToCart(updatedCart)
    } catch {
      console.warn('Failed to add item')
    }
  }

  const clearFilter = () => {
    setSearch('')
    setCategory('all')
    setArea('')
    onSearchChange?.('')
  }

  return (
    <div>
      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-8">
        <div className="relative flex-1">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search products..."
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
          />
        </div>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="px-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
          ))}
        </select>
        <select
          value={area}
          onChange={(e) => setArea(e.target.value)}
          className="px-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
        >
          <option value="">All Areas</option>
          {AREAS.map((a) => (
            <option key={a} value={a}>{a.charAt(0).toUpperCase() + a.slice(1)}</option>
          ))}
        </select>
        {(search || category !== 'all' || area) && (
          <button
            onClick={clearFilter}
            className="px-3 py-2.5 text-sm text-gray-500 hover:text-gray-700 bg-gray-100 rounded-xl hover:bg-gray-200 transition-all"
          >
            Clear
          </button>
        )}
      </div>

      {/* Product Grid */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="rounded-2xl bg-white border border-gray-100 p-4 animate-pulse">
              <div className="h-32 bg-gray-100 rounded-xl mb-3" />
              <div className="h-4 bg-gray-100 rounded w-3/4 mb-2" />
              <div className="h-4 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : products.length === 0 ? (
        search ? (
          <div className="text-center py-20">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-amber-50 flex items-center justify-center">
              <svg className="w-8 h-8 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <p className="text-gray-700 text-sm font-medium">No products found for "{search}"</p>
            <p className="text-gray-400 text-xs mt-1">Try a different search term or browse all products</p>
            <button
              onClick={clearFilter}
              className="mt-4 px-5 py-2.5 text-sm font-medium bg-brand-500 text-white rounded-xl hover:bg-brand-600 active:scale-[0.98] transition-all"
            >
              Show all products
            </button>
          </div>
        ) : (
          <div className="text-center py-20">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-100 flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
            </div>
            <p className="text-gray-500 text-sm">No products available</p>
            <p className="text-gray-400 text-xs mt-1">Try changing your filters or check back later</p>
          </div>
        )
      ) : (
        <>
          {search && (
            <p className="text-xs text-gray-400 mb-4">Showing results for "{search}" — {products.length} product{products.length !== 1 ? 's' : ''}</p>
          )}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={handleAddToCart}
                onViewDetail={setSelectedProduct}
              />
            ))}
          </div>
        </>
      )}

      {/* Product Detail Modal */}
      {selectedProduct && (
        <ProductDetailModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onAddToCart={async (product, qty) => {
            const updatedCart = await addToCartApi('web-user', product.id, qty || 1)
            onAddToCart(updatedCart)
          }}
        />
      )}
    </div>
  )
}
