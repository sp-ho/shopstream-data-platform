import pytest
from datetime import timedelta
import src.shopstream.anomalies as anomalies

from src.shopstream.anomalies import (
    AnomalyConfig,
    AnomalySimulator,
    duplicate_event,
    make_invalid_order_amount,
    make_invalid_customer_id,
    make_invalid_event,
    make_late_event,
    reorder_events
)
from src.shopstream.generator import (
    generate_event,
    generate_journey,
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

def test_make_late_event_shifts_event_timestamp():
    event = generate_event()

    original_event_timestamp = event.event_timestamp
    original_ingestion_timestamp = event.ingestion_timestamp

    late_event = make_late_event(
        event,
        delay_seconds=30,
    )

    assert late_event.event_timestamp == (
        original_event_timestamp - timedelta(seconds=30)
    )

    assert late_event.ingestion_timestamp == (
        original_ingestion_timestamp
    )

def test_make_late_event_does_not_modify_original():
    event = generate_event()

    original_event_timestamp = event.event_timestamp

    late_event = make_late_event(
        event,
        delay_seconds=30,
    )

    assert event.event_timestamp == original_event_timestamp
    assert late_event.event_timestamp < event.event_timestamp

def test_make_late_event_requires_positive_delay():
    event = generate_event()

    with pytest.raises(ValueError):
        make_late_event(event, delay_seconds=0)

    with pytest.raises(ValueError):
        make_late_event(event, delay_seconds=-10)

def test_anomaly_config_accepts_valid_late_settings():
    config = AnomalyConfig(
        late_rate=0.05,
        late_delay_seconds=60,
    )

    assert config.late_rate == 0.05
    assert config.late_delay_seconds == 60

def test_anomaly_config_rejects_invalid_late_rate():
    with pytest.raises(ValueError):
        AnomalyConfig(late_rate=1.5)

def test_anomaly_config_rejects_invalid_late_delay():
    with pytest.raises(ValueError):
        AnomalyConfig(late_delay_seconds=0)

def test_anomaly_simulator_always_makes_event_late_when_rate_is_one():
    event = generate_event()

    simulator = AnomalySimulator(
        AnomalyConfig(
            late_rate=1.0,
            late_delay_seconds=60,
        )
    )

    events = simulator.process(event)

    assert len(events) == 1
    assert events[0].event_timestamp == (
        event.event_timestamp - timedelta(seconds=60)
    )
    assert events[0].ingestion_timestamp == (
        event.ingestion_timestamp
    )

def test_anomaly_simulator_does_not_make_event_late_when_rate_is_zero():
    event = generate_event()

    simulator = AnomalySimulator(
        AnomalyConfig(
            late_rate=0.0,
            late_delay_seconds=60,
        )
    )

    events = simulator.process(event)

    assert len(events) == 1
    assert events[0].event_timestamp == event.event_timestamp

def test_reorder_events_preserves_events():
    events = [
        generate_event(),
        generate_event(),
        generate_event(),
        generate_event(),
    ]

    original_ids = [
        event.event_id
        for event in events
    ]

    reordered = reorder_events(events)

    assert sorted(
        event.event_id for event in reordered
    ) == sorted(original_ids)

def test_reorder_events_preserves_event_data():
    events = [
        generate_event(),
        generate_event(),
        generate_event(),
        generate_event(),
    ]

    original_data = {
        event.event_id: (
            event.event_timestamp,
            event.ingestion_timestamp,
        )
        for event in events
    }

    reordered = reorder_events(events)

    for event in reordered:
        original_event_timestamp, original_ingestion_timestamp = (
            original_data[event.event_id]
        )

        assert event.event_timestamp == original_event_timestamp
        assert event.ingestion_timestamp == original_ingestion_timestamp

def test_reorder_events_does_not_modify_original():
    events = [
        generate_event(),
        generate_event(),
        generate_event(),
        generate_event(),
    ]

    original_ids = [
        event.event_id
        for event in events
    ]

    reorder_events(events)

    assert [
        event.event_id
        for event in events
    ] == original_ids

def test_reorder_events_returns_copy_for_short_sequence():
    events = [generate_event(), generate_event()]

    reordered = reorder_events(events)

    assert reordered == events
    assert reordered is not events

def test_reorder_events_creates_out_of_order_sequence(monkeypatch):
    events = [
        generate_event(),
        generate_event(),
        generate_event(),
        generate_event(),
    ]

    # Force the function to select index 1.
    monkeypatch.setattr(
        anomalies.random,
        "randint",
        lambda _start, _end: 1,
    )

    original_ids = [
        event.event_id
        for event in events
    ]

    reordered = reorder_events(events)

    reordered_ids = [
        event.event_id
        for event in reordered
    ]

    assert reordered_ids == [
        original_ids[0],
        original_ids[2],
        original_ids[1],
        original_ids[3],
    ]

def test_reorder_events_creates_event_time_disorder(monkeypatch):
    events = [
        generate_event(),
        generate_event(),
        generate_event(),
        generate_event(),
    ]

    base_time = events[0].event_timestamp

    for index, event in enumerate(events):
        event.event_timestamp = base_time + timedelta(
            seconds=index
        )

    monkeypatch.setattr(
        anomalies.random,
        "randint",
        lambda _start, _end: 1,
    )

    reordered = reorder_events(events)

    timestamps = [
        event.event_timestamp
        for event in reordered
    ]

    assert timestamps == [
        base_time,
        base_time + timedelta(seconds=2),
        base_time + timedelta(seconds=1),
        base_time + timedelta(seconds=3),
    ]

def test_anomaly_simulator_always_reorders_when_rate_is_one(
    monkeypatch,
):
    events = [
        generate_event(),
        generate_event(),
        generate_event(),
        generate_event(),
    ]

    original_ids = [
        event.event_id
        for event in events
    ]

    monkeypatch.setattr(
        anomalies.random,
        "randint",
        lambda _start, _end: 1,
    )

    simulator = AnomalySimulator(
        AnomalyConfig(
            out_of_order_rate=1.0,
        )
    )

    reordered = simulator.process_events(events)

    reordered_ids = [
        event.event_id
        for event in reordered
    ]

    assert reordered_ids == [
        original_ids[0],
        original_ids[2],
        original_ids[1],
        original_ids[3],
    ]

def test_anomaly_simulator_does_not_reorder_when_rate_is_zero():
    events = [
        generate_event(),
        generate_event(),
        generate_event(),
        generate_event(),
    ]

    original_ids = [
        event.event_id
        for event in events
    ]

    simulator = AnomalySimulator(
        AnomalyConfig(
            out_of_order_rate=0.0,
        )
    )

    result = simulator.process_events(events)

    assert [
        event.event_id
        for event in result
    ] == original_ids

def test_anomaly_config_rejects_invalid_out_of_order_rate():
    with pytest.raises(ValueError):
        AnomalyConfig(out_of_order_rate=1.5)