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

# ---------------------------------------------------------------------------
# Reference data - 1000 customers, 500 products, 2 sources
# ---------------------------------------------------------------------------
  
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

# ---------------------------------------------------------------------------
# Event context
# ---------------------------------------------------------------------------

class EventContext:
    """
    Maintains state shared by events belonging to the same simulated customer journey.
    """

    def __init__(self):
        self.customer_id = random.choice(CUSTOMER_IDS)
        self.product_id = random.choice(PRODUCT_IDS)
        self.order_id: str | None = None
        self.order_amount: float | None = None

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

# generate relationship between order and payment events. see generate_order_created_event()
def generate_order_details() -> tuple[str, float]:
    """
    Generate an order ID and order amount.
    """
    order_id = f"ord_{uuid.uuid4().hex[:12]}"
    quantity = random.randint(1, 5)
    unit_price = round(random.uniform(10, 500), 2)
    total_amount = round(quantity * unit_price, 2)

    return order_id, total_amount

# ---------------------------------------------------------------------------
# Independent event generators
# ---------------------------------------------------------------------------

def generate_customer_created_event() -> ShopStreamEvent:
    """
    Generate a customer_created event.
    """
    now = datetime.now(timezone.utc)

    return ShopStreamEvent(
        event_id=str(uuid.uuid4()),
        event_type="customer_created",
        event_version=1,
        event_timestamp=now,
        ingestion_timestamp=now,
        source=random.choice(SOURCES),
        customer=Customer(
            customer_id=random.choice(CUSTOMER_IDS)
        ),
    )

def generate_product_viewed_event(context: EventContext | None = None) -> ShopStreamEvent:
    """
    Generate a product_viewed event.

    If a context is provided, the event uses the customer's
    existing customer_id and product_id.
    """
    if context is None:
        context = EventContext()

    now = datetime.now(timezone.utc)

    return ShopStreamEvent(
        event_id=str(uuid.uuid4()),
        event_type="product_viewed",
        event_version=1,
        event_timestamp=now,
        ingestion_timestamp=now,
        source=random.choice(SOURCES),
        customer=Customer(
            customer_id=context.customer_id
        ),
        product=Product(
            product_id=context.product_id
        ),
    )

def generate_cart_added_event(context: EventContext | None = None) -> ShopStreamEvent:
    """
    Generate a cart_added event.

    If a context is provided, the event uses the customer's
    existing customer_id and product_id.
    """
    if context is None:
        context = EventContext()

    now = datetime.now(timezone.utc)

    return ShopStreamEvent(
        event_id=str(uuid.uuid4()),
        event_type="cart_added",
        event_version=1,
        event_timestamp=now,
        ingestion_timestamp=now,
        source=random.choice(SOURCES),
        customer=Customer(
            customer_id=context.customer_id
        ),
        product=Product(
            product_id=context.product_id
        ),
    )

def generate_order_created_event(context: EventContext | None = None) -> ShopStreamEvent:
    """
    Generate an order_created event.

    The generated order ID and amount are stored in the context
    so subsequent payment/cancellation events can reference
    the same order.
    """

    if context is None:
        context = EventContext()

    now = datetime.now(timezone.utc)

    order_id, total_amount = generate_order_details()

    context.order_id = order_id
    context.order_amount = total_amount

    return ShopStreamEvent(
        event_id=str(uuid.uuid4()),
        event_type="order_created",
        event_version=1,
        event_timestamp=now,
        ingestion_timestamp=now,
        source=random.choice(SOURCES),
        customer=Customer(
            customer_id=context.customer_id
        ),
        order=Order(
            order_id=order_id,
            currency="CAD",
            total_amount=total_amount,
        ),
        product=Product(
            product_id=context.product_id,
        ),
    )

# ---------------------------------------------------------------------------
# Order-dependent event generators
# ---------------------------------------------------------------------------

def generate_payment_completed_event(context: EventContext) -> ShopStreamEvent:
    """
    Generate a payment_completed event for an existing order.
    """

    if context.order_id is None:
        raise ValueError(
            "Cannot generate payment_completed without an existing order."
        )

    now = datetime.now(timezone.utc)

    return ShopStreamEvent(
        event_id=str(uuid.uuid4()),
        event_type="payment_completed",
        event_version=1,
        event_timestamp=now,
        ingestion_timestamp=now,
        source=random.choice(SOURCES),
        customer=Customer(
            customer_id=context.customer_id
        ),
        order=Order(
            order_id=context.order_id,
            currency="CAD",
            total_amount=context.order_amount,
        ),
    )

def generate_order_cancelled_event(context: EventContext) -> ShopStreamEvent:
    """
    Generate an order_cancelled event for an existing order.
    """

    if context.order_id is None:
        raise ValueError(
            "Cannot generate order_cancelled without an existing order."
        )

    now = datetime.now(timezone.utc)
    
    return ShopStreamEvent(
        event_id=str(uuid.uuid4()),
        event_type="order_cancelled",
        event_version=1,
        event_timestamp=now,
        ingestion_timestamp=now,
        source=random.choice(SOURCES),
        customer=Customer(
            customer_id=context.customer_id
        ),
        order=Order(
            order_id=context.order_id,
            currency="CAD",
            total_amount=context.order_amount,
        ),
    )

# ---------------------------------------------------------------------------
# Independent event generator registry
# ---------------------------------------------------------------------------

# map each event type to its generator function
EVENT_GENERATORS = [
    generate_customer_created_event,
    generate_product_viewed_event,
    generate_cart_added_event,
    generate_order_created_event,
]

# ---------------------------------------------------------------------------
# Single-event generation
# ---------------------------------------------------------------------------

def generate_event() -> ShopStreamEvent:
    """
    Generate one independent e-commerce event.

    This function is intentionally limited to events that do not
    require an existing order context.
    """
    generator = random.choice(EVENT_GENERATORS)
    return generator()

# ---------------------------------------------------------------------------
# Customer journey generation
# ---------------------------------------------------------------------------

# # Generate a realistic customer journey with optional cart,
# order, payment, and cancellation events. 
def generate_journey() -> list[ShopStreamEvent]:
    """
    Generate a realistic customer journey.

    Possible flow:

        product_viewed
              |
              v
        cart_added
              |
              v
        order_created
              |
        +-----+------+
        |            |
        v            v
    payment      cancellation
    completed
    """

    context = EventContext()

    events: list[ShopStreamEvent] = []

    # Customer views a product.
    events.append(
        generate_product_viewed_event(context)
    )

    # Not every visitor adds something to their cart.
    if random.random() < 0.6:
        events.append(
            generate_cart_added_event(context)
        )

        # Not every cart becomes an order.
        if random.random() < 0.5:
            events.append(
                generate_order_created_event(context)
            )

            outcome = random.random()

            # Most orders are successfully paid.
            if outcome < 0.9:
                events.append(
                    generate_payment_completed_event(context)
                )

            # A small percentage of orders are cancelled.
            elif outcome < 0.95:
                events.append(
                    generate_order_cancelled_event(context)
                )

    return events
