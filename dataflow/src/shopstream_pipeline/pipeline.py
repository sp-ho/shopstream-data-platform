import argparse

import apache_beam as beam
from apache_beam.io.gcp.pubsub import ReadFromPubSub
from apache_beam.options.pipeline_options import PipelineOptions

def log_message(message: bytes) -> None:
    """Log a Pub/Sub-style message."""
    print(f"Received message: {message.decode('utf-8')}")

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
                b'{"event_id":"test-001","event_type":"product_viewed"}',
                b'{"event_id":"test-002","event_type":"cart_added"}',
            ]

            (
                pipeline
                | "CreateTestMessages"
                >> beam.Create(messages)
                | "LogMessages"
                >> beam.Map(log_message)
            )

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

            (
                pipeline
                | "ReadFromPubSub"
                >> ReadFromPubSub(
                    subscription=subscription_path
                )
                | "LogMessages"
                >> beam.Map(log_message)
            )

if __name__ == "__main__":
    run()