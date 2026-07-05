import { useState, useCallback } from 'react'
import Catalog from './components/Catalog'
import Chat from './components/Chat'
import CartDrawer from './components/CartDrawer'
import type { Cart } from './types'

const USER_ID = 'web-user'

export default function App() {
  const [activeTab, setActiveTab] = useState<'catalog' | 'chat'>('catalog')
  const [cartOpen, setCartOpen] = useState(false)
  const [cart, setCart] = useState<Cart>({ user_id: USER_ID, items: [], total: 0 })
  const [catalogQuery, setCatalogQuery] = useState('')

  const updateCart = useCallback((c: Cart) => setCart(c), [])

  const handleCatalogSearch = useCallback((query: string) => {
    setCatalogQuery(query)
  }, [])

  const itemsCount = cart.items.reduce((s, i) => s + i.qty, 0)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-lg border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" />
              </svg>
            </div>
            <span className="text-lg font-semibold tracking-tight">FreshCart</span>
          </div>

          <div className="flex items-center gap-2">
            {/* Tab Switcher */}
            <div className="flex bg-gray-100 rounded-lg p-0.5">
              <button
                onClick={() => setActiveTab('catalog')}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                  activeTab === 'catalog'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Catalog
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                  activeTab === 'chat'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Chat
              </button>
            </div>

            {/* Cart Button */}
            <button
              onClick={() => setCartOpen(true)}
              className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
              {itemsCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-5 h-5 rounded-full bg-brand-500 text-white text-[10px] font-bold flex items-center justify-center">
                  {itemsCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'catalog' && (
          <Catalog
            onAddToCart={updateCart}
            initialSearch={catalogQuery}
            onSearchChange={setCatalogQuery}
          />
        )}
        {activeTab === 'chat' && (
          <Chat
            userId={USER_ID}
            onCartUpdate={updateCart}
            onCatalogSearch={handleCatalogSearch}
          />
        )}
      </main>

      {/* Cart Drawer */}
      <CartDrawer
        open={cartOpen}
        onClose={() => setCartOpen(false)}
        cart={cart}
        userId={USER_ID}
        onCartUpdate={updateCart}
      />
    </div>
  )
}
