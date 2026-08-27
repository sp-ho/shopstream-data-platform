from unittest.mock import MagicMock, patch

from shopstream_pipeline.pipeline import PublishInvalidEventDoFn

@patch("shopstream_pipeline.pipeline.pubsub_v1.PublisherClient")
def test_publish_invalid_event(mock_publisher_client):
    publisher_client = mock_publisher_client.return_value

    publisher_client.topic_path.return_value = (
        "projects/test-project/topics/shopstream-dlq"
    )

    mock_future = MagicMock()
    mock_future.result.return_value = "message-123"

    publisher_client.publish.return_value = mock_future

    dofn = PublishInvalidEventDoFn(
        project_id="test-project",
        topic_id="shopstream-dlq",
    )

    dofn.setup()

    message = b'{"event_id":"test-003","event_type":"invalid_event"}'

    dofn.process(message)

    publisher_client.topic_path.assert_called_once_with(
        "test-project",
        "shopstream-dlq",
    )

    publisher_client.publish.assert_called_once_with(
        "projects/test-project/topics/shopstream-dlq",
        message,
    )

    mock_future.result.assert_called_once()