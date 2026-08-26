import argparse
import json
import time

from .generator import generate_event, generate_journey
from .anomalies import AnomalyConfig, AnomalySimulator
from .publisher import PubSubPublisher

def wait_until(target_time: float) -> None:
    """
    Sleep until the target monotonic time.
    """
    remaining = target_time - time.monotonic()

    if remaining > 0:
        time.sleep(remaining)

def output_event(
    event,
    publisher: PubSubPublisher | None = None,
) -> None:
    """
    Output an event locally and optionally publish it to Pub/Sub.
    """

    print(
        json.dumps(
            event.model_dump(mode="json"),
            separators=(",", ":"),
        )
    )

    if publisher is not None:
        message_id = publisher.publish(event)
        print(f"Published to Pub/Sub: {message_id}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ShopStream e-commerce events."
    )

    parser.add_argument(
        "--events",
        type=int,
        help="Number of events to generate.",
    )

    parser.add_argument(
        "--events-per-second",
        type=float,
        default=1.0,
        help="Target number of events to generate per second.",
    )

    parser.add_argument(
        "--duration",
        type=float,
        help="Duration in seconds to generate events.",
    )

    parser.add_argument(
        "--duplicate-rate",
        type=float,
        default=0.0,
        help="Probability of duplicating each generated event (0.0 to 1.0).",
    )

    parser.add_argument(
        "--invalid-rate",
        type=float,
        default=0.0,
        help="Probability of generating an invalid event (0.0 to 1.0).",
    )

    parser.add_argument(
        "--late-rate",
        type=float,
        default=0.0,
        help="Probability of generating a late event (0.0 to 1.0).",
    )

    parser.add_argument(
        "--late-delay-seconds",
        type=float,
        default=30.0,
        help="How many seconds a late event should be shifted into the past.",
    )

    parser.add_argument(
        "--journeys",
        type=int,
        default=0,
        help="Number of customer journeys to generate.",
    )

    parser.add_argument(
        "--out-of-order-rate",
        type=float,
        default=0.0,
        help="Probability of reordering events within a journey.",
    )

    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish generated events to Google Cloud Pub/Sub.",
    )

    parser.add_argument(
        "--project-id",
        help="Google Cloud project ID used for Pub/Sub publishing.",
    )

    parser.add_argument(
        "--topic-id",
        default="shopstream-events",
        help="Pub/Sub topic ID.",
    )

    args = parser.parse_args()

    # -----------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------

    if (
        args.events is None
        and args.duration is None
        and args.journeys == 0
    ):
        parser.error("Specify --events, --duration, or --journeys.")

    if args.journeys > 0 and (
        args.events is not None or args.duration is not None
    ):
        parser.error("--journeys cannot be combined with --events or --duration.")

    if args.events is not None and args.duration is not None:
        parser.error("Specify either --events or --duration, not both.")

    if args.events is not None and args.events <= 0:
        parser.error("--events must be greater than 0.")

    if args.duration is not None and args.duration <= 0:
        parser.error("--duration must be greater than 0.")

    if args.journeys < 0:
        parser.error("--journeys must be non-negative.")

    if args.events_per_second <= 0:
        parser.error("--events-per-second must be greater than 0.")

    if not 0.0 <= args.duplicate_rate <= 1.0:
        parser.error("--duplicate-rate must be between 0.0 and 1.0.")

    if not 0.0 <= args.invalid_rate <= 1.0:
        parser.error("--invalid-rate must be between 0.0 and 1.0.")

    if not 0.0 <= args.late_rate <= 1.0:
        parser.error("--late-rate must be between 0.0 and 1.0.")

    if args.late_delay_seconds <= 0:
        parser.error("--late-delay-seconds must be greater than 0.")

    if not 0.0 <= args.out_of_order_rate <= 1.0:
        parser.error("--out-of-order-rate must be between 0.0 and 1.0.")

    if args.publish and not args.project_id:
        parser.error("--project-id is required when using --publish.")

    # -----------------------------------------------------------------------
    # Pub/Sub publisher
    # -----------------------------------------------------------------------

    publisher = None

    if args.publish:
        publisher = PubSubPublisher(
            project_id=args.project_id,
            topic_id=args.topic_id,
        )

    # -----------------------------------------------------------------------
    # Anomaly simulator
    # -----------------------------------------------------------------------

    anomaly_simulator = AnomalySimulator(
        AnomalyConfig(
            duplicate_rate=args.duplicate_rate,
            invalid_rate=args.invalid_rate,
            late_rate=args.late_rate,
            late_delay_seconds=args.late_delay_seconds,
            out_of_order_rate=args.out_of_order_rate,
        )
    )

    # -----------------------------------------------------------------------
    # Journey mode
    # -----------------------------------------------------------------------

    if args.journeys > 0:
        for _ in range(args.journeys):
            journey = generate_journey()

            journey = anomaly_simulator.process_events(journey)

            for event in journey:
                output_event(event, publisher)

    # -----------------------------------------------------------------------
    # Individual event mode
    # -----------------------------------------------------------------------

    interval = 1.0 / args.events_per_second

    if args.events is not None:
        next_event_time = time.monotonic()

        for _ in range(args.events):
            wait_until(next_event_time)

            event = generate_event()

            for output_event_result in anomaly_simulator.process(event):
                output_event(
                    output_event_result,
                    publisher,
                )

            next_event_time += interval

    elif args.duration is not None:
        start_time = time.monotonic()
        end_time = start_time + args.duration
        next_event_time = start_time

        while next_event_time < end_time:
            wait_until(next_event_time)

            event = generate_event()

            for output_event_result in anomaly_simulator.process(event):
                output_event(
                    output_event_result,
                    publisher,
                )

            next_event_time += interval 

if __name__ == "__main__":
    main()