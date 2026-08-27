import argparse
import json

import apache_beam as beam
from apache_beam import pvalue
from apache_beam.io.gcp.pubsub import ReadFromPubSub
from apache_beam.options.pipeline_options import PipelineOptions
from shopstream_common.models import ShopStreamEvent


def parse_event(message: bytes) -> ShopStreamEvent:
    payload = json.loads(message.decode("utf-8"))
    return ShopStreamEvent.model_validate(payload)

class ParseEventDoFn(beam.DoFn):
    INVALID_TAG = "invalid"

    def process(self, message: bytes):
        try:
            event = parse_event(message)
            yield event
        except (ValueError, TypeError):
            yield pvalue.TaggedOutput(
                self.INVALID_TAG,
                message,
            )

def log_valid_event(event: ShopStreamEvent) -> None:
    print(
        f"VALID: event_id={event.event_id}, "
        f"event_type={event.event_type}"
    )


def log_invalid_event(message: bytes) -> None:
    print(
        f"INVALID: {message.decode('utf-8', errors='replace')}"
    )

def run() -> None:
    parser = argparse.ArgumentParser(
        description="ShopStream streaming pipeline."
    )

    parser.add_argument(
        "--input",
        choices=["test", "pubsub"],
        default="test",
        help="Input source: test data or Pub/Sub.",
    )

    parser.add_argument(
        "--project",
        help="Google Cloud project ID. Required for Pub/Sub input.",
    )

    parser.add_argument(
        "--subscription",
        help="Pub/Sub subscription name. Required for Pub/Sub input.",
    )

    args, pipeline_args = parser.parse_known_args()

    pipeline_options = PipelineOptions(pipeline_args)

    with beam.Pipeline(options=pipeline_options) as pipeline:

        if args.input == "test":
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
                """,
                b"""
                {
                    "event_id": "test-002",
                    "event_type": "cart_added",
                    "event_version": 1,
                    "event_timestamp": "2026-01-01T12:01:00Z",
                    "ingestion_timestamp": "2026-01-01T12:01:01Z",
                    "source": "mobile",
                    "customer": {
                        "customer_id": "cust_00002"
                    },
                    "product": {
                        "product_id": "prod_00002"
                    }
                }
                """,
                b'{"event_id":"test-003","event_type":"invalid_event"}',
            ]

            parsed = (
                pipeline
                | "CreateTestMessages"
                >> beam.Create(messages)
                | "ParseAndValidate"
                >> beam.ParDo(ParseEventDoFn()).with_outputs(
                    ParseEventDoFn.INVALID_TAG,
                    main="valid"
                )
            )

            valid_events = parsed.valid
            invalid_events = parsed[ParseEventDoFn.INVALID_TAG]

            valid_events | "LogValidEvents" >> beam.Map(log_valid_event)
            invalid_events | "LogInvalidEvents" >> beam.Map(log_invalid_event)

        else:
            if not args.project:
                parser.error(
                    "--project is required when --input=pubsub."
                )

            if not args.subscription:
                parser.error(
                    "--subscription is required when --input=pubsub."
                )

            subscription_path = (
                f"projects/{args.project}/subscriptions/"
                f"{args.subscription}"
            )

            parsed = (
                pipeline
                | "ReadFromPubSub"
                >> ReadFromPubSub(subscription=subscription_path)
                | "ParseAndValidate"
                >> beam.ParDo(ParseEventDoFn()).with_outputs(
                    ParseEventDoFn.INVALID_TAG,
                    main="valid",
                )
            )

            valid_events = parsed.valid
            invalid_events = parsed[ParseEventDoFn.INVALID_TAG]

            valid_events | "LogValidEvents" >> beam.Map(log_valid_event)
            invalid_events | "LogInvalidEvents" >> beam.Map(log_invalid_event)


if __name__ == "__main__":
    run()