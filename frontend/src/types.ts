export interface Product {
  id: number
  vendor_id: number
  name: string
  price: number
  stock_qty: number
  category: string
  area_tag: string
  fabric_gsm: number | null
  material: string | null
  rating: number | null
}

export interface CartItem {
  product_id: number
  name: string
  price: number
  qty: number
}

export interface Cart {
  user_id: string
  items: CartItem[]
  total: number
}

export interface ChatResponse {
  response: string
  cart: Cart
  flagged_hallucination: boolean
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}
