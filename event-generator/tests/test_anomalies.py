import pytest

from src.shopstream.anomalies import (
    AnomalyConfig,
    AnomalySimulator,
    duplicate_event,
    make_invalid_order_amount,
    make_invalid_customer_id,
    make_invalid_event,
)
from src.shopstream.generator import (
    generate_event,
    generate_order_created_event,
    generate_product_viewed_event,
)

def test_duplicate_event_has_same_event_id():
    event = generate_event()
    duplicate = duplicate_event(event)
    assert duplicate.event_id == event.event_id

def test_duplicate_event_is_a_separate_object():
    event = generate_event()
    duplicate = duplicate_event(event)
    assert duplicate is not event

def test_duplicate_event_has_same_content():
    event = generate_event()
    duplicate = duplicate_event(event)
    assert duplicate.model_dump() == event.model_dump()

def test_anomaly_config_accepts_valid_duplicate_rate():
    config = AnomalyConfig(duplicate_rate=0.05)
    assert config.duplicate_rate == 0.05

def test_anomaly_config_rejects_invalid_duplicate_rate():
    with pytest.raises(ValueError):
        AnomalyConfig(duplicate_rate=1.5)

def test_anomaly_simulator_without_duplicates():
    event = generate_event()
    simulator = AnomalySimulator(
        AnomalyConfig(duplicate_rate=0.0)
    )
    events = simulator.process(event)

    assert len(events) == 1
    assert events[0].event_id == event.event_id

def test_anomaly_simulator_always_duplicates_when_rate_is_one():
    event = generate_event()

    simulator = AnomalySimulator(
        AnomalyConfig(duplicate_rate=1.0)
    )

    events = simulator.process(event)

    assert len(events) == 2
    assert events[0].event_id == events[1].event_id
    assert events[0].model_dump() == events[1].model_dump()

def test_make_invalid_order_amount_creates_negative_amount():
    event = generate_order_created_event()

    invalid_event = make_invalid_order_amount(event)

    assert invalid_event.order is not None
    assert invalid_event.order.total_amount < 0

def test_make_invalid_order_amount_does_not_modify_original():
    event = generate_order_created_event()

    original_amount = event.order.total_amount

    invalid_event = make_invalid_order_amount(event)

    assert event.order.total_amount == original_amount
    assert invalid_event.order.total_amount < 0

def test_make_invalid_order_amount_requires_order():
    event = generate_product_viewed_event()

    with pytest.raises(ValueError):
        make_invalid_order_amount(event)

def test_make_invalid_customer_id_creates_empty_customer_id():
    event = generate_order_created_event()

    invalid_event = make_invalid_customer_id(event)

    assert invalid_event.customer is not None
    assert invalid_event.customer.customer_id == ""

def test_make_invalid_customer_id_does_not_modify_original():
    event = generate_order_created_event()

    original_customer_id = event.customer.customer_id

    invalid_event = make_invalid_customer_id(event)

    assert event.customer.customer_id == original_customer_id
    assert invalid_event.customer.customer_id == ""

def test_make_invalid_customer_id_requires_customer():
    event = generate_product_viewed_event()

    event_without_customer = event.model_copy(
        update={"customer": None}
    )

    with pytest.raises(ValueError):
        make_invalid_customer_id(event_without_customer)

def test_make_invalid_event_invalidates_order_event():
    event = generate_order_created_event()

    invalid_event = make_invalid_event(event)

    assert invalid_event.order is not None
    assert invalid_event.order.total_amount < 0

def test_make_invalid_event_invalidates_customer_event():
    event = generate_product_viewed_event()

    invalid_event = make_invalid_event(event)

    assert invalid_event.customer is not None
    assert invalid_event.customer.customer_id == ""

def test_make_invalid_event_requires_supported_fields():
    event = generate_product_viewed_event()

    event_without_supported_fields = event.model_copy(
        update={
            "customer": None,
            "order": None,
        }
    )

    with pytest.raises(ValueError):
        make_invalid_event(event_without_supported_fields)

def test_anomaly_config_accepts_valid_invalid_rate():
    config = AnomalyConfig(invalid_rate=0.05)

    assert config.invalid_rate == 0.05

def test_anomaly_config_rejects_invalid_invalid_rate():
    with pytest.raises(ValueError):
        AnomalyConfig(invalid_rate=1.5)

def test_anomaly_simulator_always_invalidates_when_rate_is_one():
    event = generate_order_created_event()

    simulator = AnomalySimulator(
        AnomalyConfig(invalid_rate=1.0)
    )

    events = simulator.process(event)

    assert len(events) == 1
    assert events[0].order is not None
    assert events[0].order.total_amount < 0

def test_anomaly_simulator_does_not_invalidate_when_rate_is_zero():
    event = generate_order_created_event()

    simulator = AnomalySimulator(
        AnomalyConfig(invalid_rate=0.0)
    )

    events = simulator.process(event)

    assert len(events) == 1
    assert events[0].order is not None
    assert events[0].order.total_amount >= 0