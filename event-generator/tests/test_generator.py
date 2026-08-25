from src.shopstream.generator import generate_event

def test_event_generation():
    event = generate_event()

    assert event.event_id
    assert event.event_type
    assert event.event_version == 1
    assert event.customer.customer_id