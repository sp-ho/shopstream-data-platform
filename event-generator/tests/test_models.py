from datetime import datetime, timezone

from src.shopstream.models import (
    Customer,
    Order,
    ShopStreamEvent,
)

def test_valid_order_event():
    event = ShopStreamEvent(
        event_id="evt_123",
        event_type="order_created",
        event_version=1,
        event_timestamp=datetime.now(timezone.utc),
        source="web",
        customer=Customer(
            customer_id="cust_123"
        ),
        order=Order(
            order_id="ord_123",
            total_amount=99.99,
        ),
    )
    assert event.event_id == "evt_123"
    assert event.order.total_amount == 99.99