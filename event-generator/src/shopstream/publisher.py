# test the publisher concept before integrating to main.py
# publisher.py doesn't generate events.
# It receives a ShopStreamEvent from generate_event() or generate_journey(), and publishes it to a Google Cloud Pub/Sub topic.

import json
from google.cloud import pubsub_v1
from .models import ShopStreamEvent

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
        """

        event_json = json.dumps(
            event.model_dump(mode="json"),
            separators=(",", ":"),
        )

        data = event_json.encode("utf-8")

        future = self.publisher.publish(
            self.topic_path,
            data,
            event_type=event.event_type,
            event_version=str(event.event_version),
            source=event.source,
        )

        return future.result()
