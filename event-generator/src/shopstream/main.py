import argparse
from html import parser
import json
from random import random
import time

from .generator import generate_event
from .anomalies import AnomalyConfig, AnomalySimulator
# from .models import ShopStreamEvent


def wait_until(target_time: float) -> None:
    """
    Sleep until the target monotonic time.
    """
    remaining = target_time - time.monotonic()

    if remaining > 0:
        time.sleep(remaining)

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

    args = parser.parse_args()

    # validation
    if args.events is None and args.duration is None:
        parser.error("Specify either --events or --duration.")

    if args.events is not None and args.duration is not None:
        parser.error("Specify either --events or --duration, not both.")

    if args.events is not None and args.events <= 0:
        parser.error("--events must be greater than 0.")

    if args.duration is not None and args.duration <= 0:
        parser.error("--duration must be greater than 0.")

    if args.events_per_second <= 0:
        parser.error("--events-per-second must be greater than 0.")

    if not 0.0 <= args.duplicate_rate <= 1.0:
        parser.error("--duplicate-rate must be between 0.0 and 1.0.")

    if not 0.0 <= args.invalid_rate <= 1.0:
        parser.error("--invalid-rate must be between 0.0 and 1.0.")

    anomaly_simulator = AnomalySimulator(
    AnomalyConfig(
            duplicate_rate=args.duplicate_rate,
            invalid_rate=args.invalid_rate,
        )
    )

    # calculate the delay
    interval = 1.0 / args.events_per_second

    if args.events is not None:
        next_event_time = time.monotonic()

        for _ in range(args.events):
            wait_until(next_event_time)

            event = generate_event()

            for output_event in anomaly_simulator.process(event):
                print(
                    json.dumps(
                        output_event.model_dump(mode="json"),
                        separators=(",", ":"),
                    )
                )

        next_event_time += interval

    else:
        start_time = time.monotonic()
        end_time = start_time + args.duration
        next_event_time = start_time

        while next_event_time < end_time:
            wait_until(next_event_time)

            event = generate_event()

            for output_event in anomaly_simulator.process(event):
                print(
                    json.dumps(
                        output_event.model_dump(mode="json"),
                        separators=(",", ":"),
                    )
                )

            next_event_time += interval

if __name__ == "__main__":
    main()