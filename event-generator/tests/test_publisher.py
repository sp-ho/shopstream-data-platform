import pytest
from unittest.mock import MagicMock, patch
from src.shopstream.models import Customer, Product, ShopStreamEvent
from src.shopstream.publisher import PubSubPublisher

def create_test_event() -> ShopStreamEvent:
    return ShopStreamEvent(
        event_id="test-event-123",
        event_type="product_viewed",
        event_version=1,
        event_timestamp="2026-01-01T12:00:00Z",
        ingestion_timestamp="2026-01-01T12:00:01Z",
        source="web",
        customer=Customer(
            customer_id="cust_00001",
        ),
        product=Product(
            product_id="prod_00001",
        ),
    )

@patch("shopstream.publisher.pubsub_v1.PublisherClient")
def test_publisher_initializes_topic(mock_publisher_client):
    publisher_client = mock_publisher_client.return_value

    publisher_client.topic_path.return_value = (
        "projects/test-project/topics/shopstream-events"
    )

    publisher = PubSubPublisher(
        project_id="test-project",
        topic_id="shopstream-events",
    )

    publisher_client.topic_path.assert_called_once_with(
        "test-project",
        "shopstream-events",
    )

    assert publisher.topic_path == (
        "projects/test-project/topics/shopstream-events"
    )

@patch("shopstream.publisher.pubsub_v1.PublisherClient")
def test_publish_event(mock_publisher_client):
    publisher_client = mock_publisher_client.return_value

    publisher_client.topic_path.return_value = (
        "projects/test-project/topics/shopstream-events"
    )

    mock_future = MagicMock()
    mock_future.result.return_value = "message-123"

    publisher_client.publish.return_value = mock_future

    publisher = PubSubPublisher(
        project_id="test-project",
        topic_id="shopstream-events",
    )

    event = create_test_event()

    message_id = publisher.publish(event)

    assert message_id == "message-123"

    publisher_client.publish.assert_called_once()

    call_args = publisher_client.publish.call_args

    assert call_args.args[0] == (
        "projects/test-project/topics/shopstream-events"
    )

    assert call_args.kwargs["event_type"] == "product_viewed"
    assert call_args.kwargs["event_version"] == "1"
    assert call_args.kwargs["source"] == "web"

@patch("shopstream.publisher.pubsub_v1.PublisherClient")
def test_publish_serializes_event_as_json(mock_publisher_client):
    publisher_client = mock_publisher_client.return_value

    publisher_client.topic_path.return_value = (
        "projects/test-project/topics/shopstream-events"
    )

    mock_future = MagicMock()
    mock_future.result.return_value = "message-456"

    publisher_client.publish.return_value = mock_future

    publisher = PubSubPublisher(
        project_id="test-project",
        topic_id="shopstream-events",
    )

    event = create_test_event()

    publisher.publish(event)

    call_args = publisher_client.publish.call_args

    published_data = call_args.args[1]

    assert isinstance(published_data, bytes)

    published_json = published_data.decode("utf-8")

    assert '"event_id":"test-event-123"' in published_json
    assert '"event_type":"product_viewed"' in published_json
    assert '"customer":{"customer_id":"cust_00001"}' in published_json
    assert '"product":{"product_id":"prod_00001"}' in published_json

@patch("shopstream.publisher.pubsub_v1.PublisherClient")
def test_publisher_close(mock_publisher_client):
    publisher_client = mock_publisher_client.return_value

    publisher = PubSubPublisher(
        project_id="test-project",
        topic_id="shopstream-events",
    )

    publisher.close()

    publisher_client.stop.assert_called_once()

@patch("shopstream.publisher.pubsub_v1.PublisherClient")
def test_publish_raises_when_pubsub_fails(mock_publisher_client):
    publisher_client = mock_publisher_client.return_value

    publisher_client.topic_path.return_value = (
        "projects/test-project/topics/shopstream-events"
    )

    mock_future = MagicMock()
    mock_future.result.side_effect = RuntimeError(
        "Pub/Sub publish failed"
    )

    publisher_client.publish.return_value = mock_future

    publisher = PubSubPublisher(
        project_id="test-project",
        topic_id="shopstream-events",
    )

    event = create_test_event()

    with pytest.raises(
        RuntimeError,
        match="Pub/Sub publish failed",
    ):
        publisher.publish(event)

@patch("shopstream.publisher.pubsub_v1.PublisherClient")
def test_publish_logs_pubsub_failure(
    mock_publisher_client,
    caplog,
):
    publisher_client = mock_publisher_client.return_value

    publisher_client.topic_path.return_value = (
        "projects/test-project/topics/shopstream-events"
    )

    mock_future = MagicMock()
    mock_future.result.side_effect = RuntimeError(
        "Pub/Sub publish failed"
    )

    publisher_client.publish.return_value = mock_future

    publisher = PubSubPublisher(
        project_id="test-project",
        topic_id="shopstream-events",
    )

    event = create_test_event()

    with caplog.at_level("ERROR"):
        with pytest.raises(RuntimeError):
            publisher.publish(event)

    assert "Failed to publish event to Pub/Sub" in caplog.text
    assert "test-event-123" in caplog.text