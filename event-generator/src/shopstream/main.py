import argparse
import json

from .generator import generate_event


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ShopStream e-commerce events."
    )

    parser.add_argument(
        "--events",
        type=int,
        default=10,
        help="Number of events to generate.",
    )

    args = parser.parse_args()

    for _ in range(args.events):
        event = generate_event()

        print(
            json.dumps(
                event.model_dump(mode="json"),
                separators=(",", ":"),
            )
        )

if __name__ == "__main__":
    main()