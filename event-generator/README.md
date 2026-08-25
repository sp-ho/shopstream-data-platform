# ShopStream Event Generator

A configurable synthetic e-commerce event generator for the **ShopStream Data Platform** project.

The generator simulates realistic customer activity and produces structured events that will eventually be streamed through Google Cloud Pub/Sub, processed with Dataflow, and stored in BigQuery.

## Implemented

- **Python** — Used as the primary programming language for implementing the
  event generator, customer journey simulation, and supporting logic.

- **Pydantic** — Used to define and validate the structure of e-commerce
  events. Pydantic ensures that generated events conform to the expected
  schema before they enter the data pipeline.

- **UUID** — Used to generate unique identifiers for events and orders,
  allowing individual events and business transactions to be tracked.

- **`datetime`** — Used to generate UTC event timestamps. These timestamps
  will later be important for event-time processing, windowing, and handling
  late-arriving events in the streaming pipeline.

- **`random`** — Used to simulate realistic variability in customer
  behavior, including product views, cart additions, order creation,
  payment completion, and order cancellation.

- **Pytest** — Used to create automated tests for the Pydantic models and
  event-generation logic. The tests help ensure that changes to the
  generator do not break existing functionality.

- **Configurable event generation rate** — The generator can control the
  approximate number of events produced per second using
  `--events-per-second`.

- **Duration-based generation** — Events can be generated for a specified
  duration using `--duration`, allowing the generator to simulate a
  continuous streaming workload.

- **CLI validation** — The generator validates event counts, generation
  rates, and duration values before starting.

- **Accurate event scheduling** — `time.monotonic()` is used to schedule
  events against a target timeline rather than simply sleeping after each
  event.

- **CLI automated tests** — Pytest tests validate command-line arguments,
  event-count generation, duration mode, and invalid input handling.

- **Duplicate event simulation** — Intentionally produces duplicate messages while preserving the original event_id, simulating at-least-once delivery or producer retries.

- **Configurable duplicate rate** — Controls the probability of generating duplicate events using --duplicate-rate.

- **Invalid event simulation** — Introduces controlled data-quality problems into otherwise valid events.

- **Business-rule violations** — Can generate orders with negative total_amount values.

- **Required-field violations** — Can generate events with an empty customer_id.

- **Configurable invalid-event rate** — Controls the probability of generating invalid events using --invalid-rate.

- **Anomaly simulation layer** — Separates normal event generation from intentional data-quality problems.

- **Automated anomaly tests** — Tests duplicate behavior, invalid events, anomaly configuration, and CLI validation.

- **Combined anomaly simulation** — Duplicate and invalid-event rates can be enabled independently or together.

### Event Generation

The generator produces six event types:

```text
customer_created
product_viewed
cart_added
order_created
payment_completed
order_cancelled
```
---

## Project Structure

```text
event-generator/
│
├── src/
│   └── shopstream/
│       ├── __init__.py
│       ├── models.py
│       ├── generator.py
│       └── main.py
│
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   └── test_generator.py
│
├── requirements.txt
└── README.md
```

---

## Testing the Generators

In addition to the automated pytest suite, the event generator can be tested interactively from Python.

### Test `generate_event()`

From the `event-generator` directory, set the Python path:

```powershell
$env:PYTHONPATH="src"
python
```

Inside python:
```powershell
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

### Test `generate_journey()`

From the `event-generator` directory, set the Python path:

```powershell
$env:PYTHONPATH="src"
python
```

Inside python:
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

Exit the Python interpreter when finished:
```powershell
exit
```

### Test a fixed number of events

Generate 10 events at approximately 5 events per second:

```powershell
$env:PYTHONPATH="src"
python -m shopstream.main --events 10 --events-per-second 5
```

### Test duration-based generation
Generate events at approximately 5 events per second for 10 seconds:

```powershell
$env:PYTHONPATH="src"
python -m shopstream.main --duration 10 --events-per-second 5
```

### Test anomalies generation
Simulates a stream where approximately 5% of generated events may be duplicated and approximately 2% may contain intentional data-quality problems:

```powershell
$env:PYTHONPATH="src"
python -m shopstream.main ` --events 100 ` --events-per-second 10 ` --duplicate-rate 0.05 ` --invalid-rate 0.02
```

