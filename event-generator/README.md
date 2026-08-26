# ShopStream Event Generator

A configurable synthetic e-commerce event generator for the **ShopStream Data Platform** project.

The generator simulates realistic customer activity and produces structured events that can be streamed through Google Cloud Pub/Sub, processed with Dataflow, and stored in BigQuery.

The goal of this component is not simply to generate random data. It is designed to simulate the kinds of conditions that a real streaming data platform needs to handle:

- normal e-commerce traffic
- realistic customer journeys
- duplicate events
- invalid events
- late-arriving events
- out-of-order events
- configurable event rates
- configurable anomaly rates

## Implemented - Local Event Generator

The local event generator is implemented and tested.

It currently supports:

- Pydantic-based event schema validation
- Six e-commerce event types
- Synthetic customers and products
- Realistic customer journeys
- Shared customer/product context across related events
- Shared order context between order and payment/cancellation events
- Configurable event generation rate
- Duration-based event generation
- Event and ingestion timestamps
- Duplicate-event simulation
- Invalid-event simulation
- Late-event simulation
- Out-of-order event simulation
- Configurable anomaly rates
- CLI validation
- Automated tests with pytest

## Technologies and Libraries

### Python

Python is the primary programming language used to implement:

- event generation
- customer journey simulation
- anomaly simulation
- command-line interface
- test automation

### Pydantic

Pydantic defines and validates the ShopStream event schema.

It ensures that generated events conform to the expected structure before they enter the streaming pipeline.

This is particularly useful for simulating data-quality failures because the generator can intentionally create invalid events and verify that schema validation catches them.

### UUID

Python's uuid library generates unique identifiers for:

- events
- orders

This allows individual events and business transactions to be tracked throughout the future streaming pipeline.

### datetime

UTC timestamps are generated for each event.

ShopStream maintains both:

- event_timestamp — when the business event occurred
- ingestion_timestamp — when the event entered the simulated ingestion layer

This distinction will later support event-time processing and late-arriving event handling in Dataflow.

### random

Python's `random` module introduces controlled variability into:

- customer behavior
- product selection
- order creation
- payment outcomes
- cancellation outcomes
- anomaly generation

### argparse

`argparse` provides the command-line interface used to configure the generator without modifying the source code.

### time

Python's `time.monotonic()` is used to schedule events at a target generation rate.

This avoids relying on repeated fixed sleeps and provides more accurate scheduling for simulated streaming workloads.

### Pytest

Pytest provides automated testing for:

- Pydantic models
- event generators
- customer journeys
- CLI behavior
- anomaly simulation
- duplicate events
- invalid events
- late events
- out-of-order events

### Google Cloud Pub/Sub

Google Cloud Pub/Sub provides the messaging layer between the ShopStream event generator and the future stream-processing pipeline.

The Python Pub/Sub client is used to:

- publish serialized ShopStream events
- attach event metadata as message attributes
- receive Pub/Sub message IDs
- handle publishing errors
- gracefully close the publisher client

## Event Model

The generator currently produces six event types:

- customer_created
- product_viewed
- cart_added
- order_created
- payment_completed
- order_cancelled

A simplified event structure is:
```
ShopStreamEvent
│
├── event_id
├── event_type
├── event_version
├── event_timestamp
├── ingestion_timestamp
├── source
│
├── customer
│   └── customer_id
│
├── product
│   └── product_id
│
└── order
    ├── order_id
    ├── currency
    └── total_amount
```

Not every event contains every entity.

For example:
```
product_viewed
    ├── customer
    └── product
```
while:
```
payment_completed
    ├── customer
    └── order
```
### Customer Journey Simulation

The generator can simulate a realistic customer journey instead of producing completely independent events.

A typical journey can follow:
```
product_viewed
       │
       ▼
cart_added
       │
       ▼
order_created
       │
       ├──────────────┐
       ▼              ▼
payment_completed   order_cancelled
```
Not every customer completes every step.

For example:

product_viewed may represent a visitor who leaves without adding anything to the cart.

Another customer might generate:

- product_viewed
- cart_added
- order_created
- payment_completed

This provides more realistic relationships between events than independently generating random event types.

### Anomaly Simulation

The generator contains a separate anomaly simulation layer.

This allows normal event generation to remain separate from intentionally generated data-quality and streaming anomalies.

#### Duplicate Events

Duplicate events preserve the original event_id.

This simulates scenarios such as:

- producer retries
- at-least-once delivery
- message redelivery

Example:

event_id = abc123
event_id = abc123

Both messages represent the same event.

Configure the probability with: `--duplicate-rate`

Example:
```powershell
python -m shopstream.main --events 100 --duplicate-rate 0.05
```

#### Invalid Events

The generator can intentionally produce invalid data.

Current examples include:

- negative order amounts
- missing/empty required customer identifiers

Configure the probability with: `--invalid-rate`

Example:
```powershell
python -m shopstream.main --events 100 --invalid-rate 0.02
```

These events will be useful later when implementing data-quality validation and dead-letter handling in the streaming pipeline.

#### Late Events

A late event has an `event_timestamp` that is earlier than its `ingestion_timestamp`.

This simulates an event that occurred earlier but arrived at the streaming system later.

Configure the probability with: `--late-rate`

and the amount of delay with: `--late-delay-seconds`

Example:
```powershell
python -m shopstream.main --events 100 --late-rate 0.10 --late-delay-seconds 60
```

This simulates approximately 10% of events arriving 60 seconds after their event time.

#### Out-of-Order Events

Events within a customer journey can be deliberately reordered.

For example, the original event sequence might be:

- product_viewed
- cart_added
- order_created
- payment_completed

The simulated arrival order could become:

- product_viewed
- order_created
- cart_added
- payment_completed

The event timestamps remain associated with their original events.

This allows the future Dataflow pipeline to be tested against event streams where **arrival order differs from event-time order**.

Configure the probability with: `--out-of-order-rate`

Example:
```powershell
python -m shopstream.main --journeys 20 --out-of-order-rate 1.0
```

Note that journeys containing too few events may not be reordered.

## Pub/Sub Integration

The event generator can publish generated events directly to Google Cloud Pub/Sub.

The Pub/Sub publishing layer is implemented in `publisher.py`.

The publisher:

- serializes `ShopStreamEvent` objects as compact JSON
- publishes events to a configured Pub/Sub topic
- attaches event metadata as Pub/Sub message attributes
- returns the Pub/Sub message ID
- logs successful publications
- logs publishing failures and re-raises the exception
- closes the Pub/Sub publisher client when the application exits

Each published message contains the complete ShopStream event as JSON.

The following Pub/Sub attributes are also attached:

- `event_type`
- `event_version`
- `source`

This allows downstream consumers to inspect basic event metadata without parsing the complete JSON payload.

### Pub/Sub Configuration

The Pub/Sub project and topic can be configured using command-line arguments or environment variables.

Command-line arguments:

- `--project-id`
- `--topic-id`

Environment variables:

- `SHOPSTREAM_PROJECT_ID`
- `SHOPSTREAM_TOPIC_ID`

This allows the same application to be used across different environments without modifying the source code.

### Publish events to Pub/Sub

Generate 10 events and publish them to the `shopstream-events` topic:

```powershell
python -m shopstream.main `
    --events 10 `
    --events-per-second 5 `
    --publish `
    --project-id shopstream-data-platform `
    --topic-id shopstream-events
```

### Verify published messages

Messages can be retrieved from the Pub/Sub subscription using the Google Cloud CLI:

```powershell
gcloud pubsub subscriptions pull shopstream-events-sub --limit=3 --auto-ack
```

The output should contain:
```powershell
DATA: {...}
MESSAGE_ID: ...
ATTRIBUTES: event_type=...
event_version=...
source=...
ACK_STATUS: SUCCESS
```

The --limit option controls how many messages are pulled. For example, --limit=3 requests up to three messages.
The --auto-ack option acknowledges the messages after they are successfully pulled.

### Publish events with anomalies

Generate 100 events and publish them to Pub/Sub while intentionally introducing duplicate, invalid, and late events:

```powershell
python -m shopstream.main `
    --events 100 `
    --events-per-second 10 `
    --publish `
    --project-id shopstream-data-platform `
    --topic-id shopstream-events `
    --duplicate-rate 0.05 `
    --invalid-rate 0.02 `
    --late-rate 0.10 `
    --late-delay-seconds 60
```

These anomalies are intentionally generated so that the downstream streaming pipeline can later demonstrate:

- duplicate detection
- data-quality validation
- late-event handling
- event-time processing

## Command-Line Usage

### Generate a fixed number of events

Generate 10 events at approximately 5 events per second:
```powershell
python -m shopstream.main --events 10 --events-per-second 5
```

### Generate events for a duration

Generate events at approximately 5 events per second for 10 seconds:
```powershell
python -m shopstream.main --duration 10 --events-per-second 5
```

### Generate customer journeys

Generate 10 customer journeys:
```powershell
python -m shopstream.main --journeys 10
```
Each journey may contain a different number of events because customer behavior is randomized.

### Simulate duplicate and invalid events

Generate 100 events with:

- 5% duplicate probability
- 2% invalid-event probability

```powershell
python -m shopstream.main --events 100 --duplicate-rate 0.05 --invalid-rate 0.02
```

### Simulate late events

Generate 100 events with approximately 10% late events and a 60-second delay:
```powershell
python -m shopstream.main --events 100 --late-rate 0.10 --late-delay-seconds 60
```

### Simulate out-of-order events

Generate 20 customer journeys and enable out-of-order simulation:
```powershell
python -m shopstream.main --journeys 20 --out-of-order-rate 1.0
```

### Combine anomalies

Multiple anomaly types can be enabled simultaneously.

For example:
```powershell
python -m shopstream.main `
    --events 100 `
    --events-per-second 10 `
    --duplicate-rate 0.05 `
    --invalid-rate 0.02 `
    --late-rate 0.10 `
    --late-delay-seconds 60
```

Journey-level out-of-order simulation can be combined with journey generation:
```powershell
python -m shopstream.main `
    --journeys 20 `
    --out-of-order-rate 0.5
```

## Testing

Run the complete automated test suite from the event-generator directory:

```powershell
pytest
```

The current test suite covers:

- event schema validation
- event generation
- customer journey generation
- CLI validation
- fixed-count generation
- duration-based generation
- generation rate
- duplicate simulation
- invalid-event simulation
- late-event simulation
- out-of-order simulation
- anomaly configuration
- Pub/Sub publisher initialization
- Pub/Sub topic configuration
- event serialization for Pub/Sub
- Pub/Sub message attributes
- publisher lifecycle and cleanup
- Pub/Sub publishing failure handling
- publisher logging

## Interactive Generator Testing

The generators can also be tested directly from Python.

### Test `generate_event()`

From the `event-generator` directory:

```powershell
python
```

Then:
```
from shopstream.generator import generate_event

for i in range(5):
    event = generate_event()

    print(
        event.event_type,
        "| customer:",
        event.customer.customer_id if event.customer else None,
        "| product:",
        event.product.product_id if event.product else None,
        "| order:",
        event.order.order_id if event.order else None,
    )
```

Exit Python with:

```powershell
exit()
```

### Test generate_journey()

From the event-generator directory:

```powershell
python
```

Then:
```powershell
from shopstream.generator import generate_journey

events = generate_journey()

for event in events:
    print(
        event.event_type,
        "| customer:",
        event.customer.customer_id if event.customer else None,
        "| product:",
        event.product.product_id if event.product else None,
        "| order:",
        event.order.order_id if event.order else None,
    )
```

Exit with:

```powershell
exit()
```

## Project Structure
```
event-generator/
│
├── src/
│   └── shopstream/
│       ├── __init__.py
│       ├── models.py
│       ├── generator.py
│       ├── anomalies.py
│       ├── publisher.py
│       └── main.py
│
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_generator.py
│   ├── test_main.py
│   ├── test_anomalies.py
│   └── test_publisher.py
│
├── requirements.txt
└── README.md
```
## Architecture

The current architecture separates normal event generation from anomaly simulation:
```
                    ┌──────────────────────┐
                    │   Event Generator    │
                    └──────────┬───────────┘
                               │
                  ┌────────────┴────────────┐
                  │                         │
           generate_event()          generate_journey()
                  │                         │
                  ▼                         ▼
           Individual Event          Event Sequence
                  │                         │
                  └────────────┬────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Anomaly Simulator    │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
          Duplicate         Invalid            Late
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                         Out-of-order
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Pub/Sub Publisher  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Google Pub/Sub     │
                    │  shopstream-events   │
                    └──────────┬───────────┘
                               │
                               ▼
                       Future: Dataflow
                               │
                               ▼
                       Future: BigQuery
```
The architecture intentionally separates business-event generation, anomaly simulation, and message publishing.

The generator creates realistic business events, the anomaly simulator introduces controlled streaming and data-quality problems, and the Pub/Sub publisher transports the resulting events into Google Cloud Pub/Sub.

Dataflow and BigQuery are the next stages of the ShopStream Data Platform.

## Installation

From the `event-generator` directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```