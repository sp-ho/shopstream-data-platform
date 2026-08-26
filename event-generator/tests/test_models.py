from datetime import datetime, timezone

from shopstream_common.models import (
    Customer,
    Order,
    ShopStreamEvent,
)


def test_valid_order_event():

    event_timestamp = datetime.now(timezone.utc) 

    event = ShopStreamEvent(
        event_id="evt_123",
        event_type="order_created",
        event_version=1,
        event_timestamp=event_timestamp,
        ingestion_timestamp=event_timestamp,
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