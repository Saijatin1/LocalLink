from pydantic import BaseModel


class Product(BaseModel):
    id: int
    vendor_id: int
    name: str
    price: float
    stock_qty: int
    category: str
    area_tag: str  # "alwal" | "secunderabad" | "kompally"
    fabric_gsm: int | None = None   # for clothing thickness
    material: str | None = None
    rating: float | None = None
