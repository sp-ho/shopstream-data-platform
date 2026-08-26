# test the publisher concept before integrating to main.py
# publisher.py doesn't generate events.
# It receives a ShopStreamEvent from generate_event() or generate_journey(), and publishes it to a Google Cloud Pub/Sub topic.

import json
import logging
from google.cloud import pubsub_v1
from .models import ShopStreamEvent

logger = logging.getLogger(__name__)

class PubSubPublisher:
    """
    Publishes ShopStream events to a Google Cloud Pub/Sub topic.
    """

    def __init__(self, project_id: str, topic_id: str):
        self.project_id = project_id
        self.topic_id = topic_id

        self.publisher = pubsub_v1.PublisherClient()

        self.topic_path = self.publisher.topic_path(
            project_id,
            topic_id,
        )

    def publish(self, event: ShopStreamEvent) -> str:
        """
        Publish one ShopStream event to Pub/Sub.

        Returns:
            The Pub/Sub message ID.

        Raises:
            Exception: Re-raises any exception from Pub/Sub publishing.
        """

        event_json = json.dumps(
            event.model_dump(mode="json"),
            separators=(",", ":"),
        )

        data = event_json.encode("utf-8")

        try:
            future = self.publisher.publish(
                self.topic_path,
                data,
                event_type=event.event_type,
                event_version=str(event.event_version),
                source=event.source,
            )

            message_id = future.result()

            logger.info(
                "Published event to Pub/Sub: event_id=%s event_type=%s "
                "message_id=%s",
                event.event_id,
                event.event_type,
                message_id,
            )

            return message_id

        except Exception:
            logger.exception(
                "Failed to publish event to Pub/Sub: "
                "event_id=%s event_type=%s",
                event.event_id,
                event.event_type,
            )
            raise

    def close(self) -> None:
        """
        Close the Pub/Sub publisher client and release resources.
        """
        self.publisher.stop()
