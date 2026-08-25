import random
# use uuid for unique IDs
import uuid
from datetime import datetime, timezone

from .models import (
    Customer,
    Order,
    Product,
    ShopStreamEvent,
)

#  1000 customers, 500 products, 2 sources
CUSTOMER_IDS = [
    f"cust_{i:05d}"
    for i in range(1, 1001)
]

PRODUCT_IDS = [
    f"prod_{i:05d}"
    for i in range(1, 501)
]

SOURCES = [
    "web",
    "mobile",
]

#  generate semantic menaingful relationships between events, customers, products, and orders
def generate_order_created_event() -> ShopStreamEvent:
    customer_id = random.choice(CUSTOMER_IDS)
    product_id = random.choice(PRODUCT_IDS)

    quantity = random.randint(1, 5)
    unit_price = round(random.uniform(10, 500), 2)
    total_amount = round(quantity * unit_price, 2)

    return ShopStreamEvent(
        event_id=str(uuid.uuid4()),
        event_type="order_created",
        event_version=1,
        event_timestamp=datetime.now(timezone.utc),
        source=random.choice(SOURCES),
        customer=Customer(
            customer_id=customer_id,
        ),
        order=Order(
            order_id=f"ord_{uuid.uuid4().hex[:12]}",
            currency="CAD",
            total_amount=total_amount,
        ),
        product=Product(
            product_id=product_id,
        ),
    )

# generate product_viewed event type
def generate_product_viewed_event() -> ShopStreamEvent:
    return ShopStreamEvent(
        event_id=str(uuid.uuid4()),
        event_type="product_viewed",
        event_version=1,
        event_timestamp=datetime.now(timezone.utc),
        source=random.choice(SOURCES),
        customer=Customer(
            customer_id=random.choice(CUSTOMER_IDS)
        ),
        product=Product(
            product_id=random.choice(PRODUCT_IDS)
        ),
    )

# generate cart_added event type
def generate_cart_added_event() -> ShopStreamEvent:
    return ShopStreamEvent(
        event_id=str(uuid.uuid4()),
        event_type="cart_added",
        event_version=1,
        event_timestamp=datetime.now(timezone.utc),
        source=random.choice(SOURCES),
        customer=Customer(
            customer_id=random.choice(CUSTOMER_IDS)
        ),
        product=Product(
            product_id=random.choice(PRODUCT_IDS)
        ),
    )

# general event generator - map each event type to its generator function
EVENT_GENERATORS = [
    generate_order_created_event,
    generate_product_viewed_event,
    generate_cart_added_event,
]

def generate_event() -> ShopStreamEvent:
    generator = random.choice(EVENT_GENERATORS)
    return generator()