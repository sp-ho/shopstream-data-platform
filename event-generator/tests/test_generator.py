from src.shopstream.generator import generate_event, generate_journey

def test_event_generation():
    event = generate_event()

    assert event.event_id
    assert event.event_type
    assert event.event_version == 1
    assert event.customer.customer_id

def test_journey_uses_same_customer():
    events = generate_journey()

    customer_ids = {
        event.customer.customer_id
        for event in events
        if event.customer is not None
    }

    assert len(customer_ids) == 1

def test_journey_uses_same_product():
    events = generate_journey()

    product_ids = {
        event.product.product_id
        for event in events
        if event.product is not None
    }

    assert len(product_ids) == 1

def test_order_and_payment_share_order_id():
    events = generate_journey()

    orders = [
        event
        for event in events
        if event.event_type == "order_created"
    ]

    payments = [
        event
        for event in events
        if event.event_type == "payment_completed"
    ]

    if orders and payments:
        assert (
            orders[0].order.order_id
            == payments[0].order.order_id
        )