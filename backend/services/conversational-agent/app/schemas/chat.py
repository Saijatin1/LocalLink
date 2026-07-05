from pydantic import BaseModel

from app.schemas.cart import Cart


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    cart: Cart
    flagged_hallucination: bool = False


class ResetSessionRequest(BaseModel):
    user_id: str


class ResetSessionResponse(BaseModel):
    message: str
