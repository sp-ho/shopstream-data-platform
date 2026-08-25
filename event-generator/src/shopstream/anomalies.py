#  this file is to create invalid events for bad quality events testing
from dataclasses import dataclass
import random

from .models import ShopStreamEvent

@dataclass(frozen=True)
class AnomalyConfig:
    """
    Configuration for intentionally simulated data-quality issues.
    """

    duplicate_rate: float = 0.0
    invalid_rate: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.duplicate_rate <= 1.0:
            raise ValueError(
                "duplicate_rate must be between 0.0 and 1.0."
            )

        if not 0.0 <= self.invalid_rate <= 1.0:
            raise ValueError(
                "invalid_rate must be between 0.0 and 1.0."
            )

def duplicate_event(event: ShopStreamEvent) -> ShopStreamEvent:
    """
    Return an identical copy of an event.

    The duplicate retains the same event_id so downstream systems
    can identify it as the same logical event.
    """
    return event.model_copy(deep=True)

def make_invalid_order_amount(
    event: ShopStreamEvent,
) -> ShopStreamEvent:
    """
    Return a copy of an order event with an invalid negative amount.

    This simulates a business-rule violation that is structurally valid
    but semantically invalid.
    """
    if event.order is None:
        raise ValueError(
            "Cannot create an invalid order amount for an event without an order."
        )

    invalid_event = event.model_copy(deep=True)

    invalid_event.order.total_amount = -abs(
        invalid_event.order.total_amount
    )

    return invalid_event

def make_invalid_customer_id(
    event: ShopStreamEvent,
) -> ShopStreamEvent:
    """
    Return a copy of an event with a missing customer ID.

    This simulates a required-field data-quality violation.
    """
    if event.customer is None:
        raise ValueError(
            "Cannot remove customer ID from an event without a customer."
        )

    invalid_event = event.model_copy(deep=True)

    invalid_event.customer.customer_id = ""

    return invalid_event

def make_invalid_event(event: ShopStreamEvent) -> ShopStreamEvent:
    """
    Create a semantically invalid version of an event.

    The selected anomaly depends on which fields are available
    on the event.
    """
    if event.order is not None:
        return make_invalid_order_amount(event)

    if event.customer is not None:
        return make_invalid_customer_id(event)

    raise ValueError(
        "Cannot create an invalid event because the event "
        "does not contain supported fields."
    )

class AnomalySimulator:
    """
    Applies configured data-quality anomalies to generated events.
    """

    def __init__(self, config: AnomalyConfig):
        self.config = config

    def process(self, event: ShopStreamEvent) -> list[ShopStreamEvent]:
        """
        Apply configured anomalies to an event.

        Returns one or more events because a duplicate may produce
        multiple output events.
        """
        events = [event]

        if random.random() < self.config.invalid_rate:
            events[0] = make_invalid_event(events[0])

        if random.random() < self.config.duplicate_rate:
            events.append(duplicate_event(events[0]))

        return events