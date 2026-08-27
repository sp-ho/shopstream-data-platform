import apache_beam as beam
import pytest
from apache_beam.testing.test_pipeline import (
    TestPipeline as BeamTestPipeline,
)
from apache_beam.testing.util import assert_that, equal_to, is_empty

from shopstream_common.models import ShopStreamEvent
from shopstream_pipeline.pipeline import (parse_event, ParseEventDoFn)


def test_parse_event():
    message = b"""
    {
        "event_id": "test-001",
        "event_type": "product_viewed",
        "event_version": 1,
        "event_timestamp": "2026-01-01T12:00:00Z",
        "ingestion_timestamp": "2026-01-01T12:00:01Z",
        "source": "web",
        "customer": {
            "customer_id": "cust_00001"
        },
        "product": {
            "product_id": "prod_00001"
        }
    }
    """

    event = parse_event(message)

    assert event.event_id == "test-001"
    assert event.event_type == "product_viewed"
    assert event.customer.customer_id == "cust_00001"
    assert event.product.product_id == "prod_00001"


def test_parse_event_rejects_invalid_json():
    message = b'{"event_id":"test-001","event_type":'

    with pytest.raises(ValueError):
        parse_event(message)


def test_parse_event_rejects_invalid_event():
    message = b"""
    {
        "event_id": "test-002",
        "event_type": "invalid_event",
        "event_version": 1,
        "event_timestamp": "2026-01-01T12:00:00Z",
        "ingestion_timestamp": "2026-01-01T12:00:01Z",
        "source": "web",
        "customer": {
            "customer_id": "cust_00001"
        }
    }
    """

    with pytest.raises(ValueError):
        parse_event(message)


def test_pipeline_parses_events():
    messages = [
        b"""
        {
            "event_id": "test-001",
            "event_type": "product_viewed",
            "event_version": 1,
            "event_timestamp": "2026-01-01T12:00:00Z",
            "ingestion_timestamp": "2026-01-01T12:00:01Z",
            "source": "web",
            "customer": {
                "customer_id": "cust_00001"
            },
            "product": {
                "product_id": "prod_00001"
            }
        }
        """
    ]

    expected_event = ShopStreamEvent(
        event_id="test-001",
        event_type="product_viewed",
        event_version=1,
        event_timestamp="2026-01-01T12:00:00Z",
        ingestion_timestamp="2026-01-01T12:00:01Z",
        source="web",
        customer={
            "customer_id": "cust_00001"
        },
        product={
            "product_id": "prod_00001"
        },
    )

    with BeamTestPipeline() as pipeline:
        events = (
            pipeline
            | "CreateMessages" >> beam.Create(messages)
            | "ParseEvents" >> beam.Map(parse_event)
        )

        assert_that(
            events,
            equal_to([expected_event]),
        )

def test_parse_event_dofn_separates_valid_event():
    valid_message = b"""
    {
        "event_id": "test-001",
        "event_type": "product_viewed",
        "event_version": 1,
        "event_timestamp": "2026-01-01T12:00:00Z",
        "ingestion_timestamp": "2026-01-01T12:00:01Z",
        "source": "web",
        "customer": {
            "customer_id": "cust_00001"
        },
        "product": {
            "product_id": "prod_00001"
        }
    }
    """

    with BeamTestPipeline() as pipeline:
        parsed = (
            pipeline
            | "CreateValidMessage" >> beam.Create([valid_message])
            | "ParseValidMessage"
            >> beam.ParDo(ParseEventDoFn()).with_outputs(
                ParseEventDoFn.INVALID_TAG,
                main="valid",
            )
        )

        valid_event_ids = (
            parsed.valid
            | "ExtractEventId"
            >> beam.Map(lambda event: event.event_id)
        )

        assert_that(
            valid_event_ids,
            equal_to(["test-001"]),
        )
    
def test_parse_event_dofn_separates_invalid_event():
    invalid_message = b'{"event_id":"test-001","event_type":"invalid_event"}'

    with BeamTestPipeline() as pipeline:
        parsed = (
            pipeline
            | "CreateInvalidMessage" >> beam.Create([invalid_message])
            | "ParseInvalidMessage"
            >> beam.ParDo(ParseEventDoFn()).with_outputs(
                ParseEventDoFn.INVALID_TAG,
                main="valid",
            )
        )

        assert_that(
            parsed.valid,
            is_empty(),
            label="ValidEvents",
        )

        assert_that(
            parsed[ParseEventDoFn.INVALID_TAG],
            equal_to([invalid_message]),
            label="InvalidEvents",
        )