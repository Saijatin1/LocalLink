from pydantic import BaseModel


class CartItem(BaseModel):
    product_id: int
    name: str
    price: float
    qty: int


class Cart(BaseModel):
    user_id: str
    items: list[CartItem] = []
    total: float = 0.0
