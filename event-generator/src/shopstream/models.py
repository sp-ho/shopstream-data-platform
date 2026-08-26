from datetime import datetime, timezone
from typing import Literal

# Use pydantic to define and validate events
from pydantic import BaseModel, Field

EventType = Literal[
    "customer_created",
    "product_viewed",
    "cart_added",
    "order_created",
    "payment_completed",
    "order_cancelled",
]

class Customer(BaseModel):
    customer_id: str

class Order(BaseModel):
    order_id: str
    currency: str = "CAD"
    total_amount: float = Field(ge=0)

class Product(BaseModel):
    product_id: str

class ShopStreamEvent(BaseModel):
    event_id: str
    event_type: EventType
    event_version: int = 1
    event_timestamp: datetime
    ingestion_timestamp: datetime
    source: str
    customer: Customer
    order: Order | None = None
    product: Product | None = None