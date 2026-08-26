# CLI test
import pytest
from unittest.mock import MagicMock, patch
from src.shopstream.main import main

def test_main_generates_requested_number_of_events(capsys, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
            "--events",
            "3",
            "--events-per-second",
            "1000",
        ],
    )

    main()

    captured = capsys.readouterr()

    lines = captured.out.strip().splitlines()

    assert len(lines) == 3

def test_main_requires_events_or_duration(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
        ],
    )

    with pytest.raises(SystemExit):
        main()

def test_main_rejects_both_events_and_duration(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
            "--events",
            "10",
            "--duration",
            "5",
        ],
    )

    with pytest.raises(SystemExit):
        main()

def test_main_rejects_invalid_event_rate(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
            "--events",
            "10",
            "--events-per-second",
            "0",
        ],
    )

    with pytest.raises(SystemExit):
        main()

def test_main_rejects_invalid_duration(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
            "--duration",
            "0",
        ],
    )

    with pytest.raises(SystemExit):
        main()

def test_main_generates_events_for_duration(capsys, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
            "--duration",
            "0.01",
            "--events-per-second",
            "1000",
        ],
    )

    main()

    captured = capsys.readouterr()

    lines = captured.out.strip().splitlines()

    assert len(lines) > 0

def test_main_rejects_invalid_invalid_rate(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
            "--events",
            "10",
            "--invalid-rate",
            "1.5",
        ],
    )

    with pytest.raises(SystemExit):
        main()

def test_main_accepts_invalid_rate(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
            "--events",
            "3",
            "--events-per-second",
            "1000",
            "--invalid-rate",
            "0.5",
        ],
    )

    main()

    captured = capsys.readouterr()

    lines = captured.out.strip().splitlines()

    assert len(lines) >= 3

def test_main_rejects_invalid_late_rate(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
            "--events",
            "10",
            "--late-rate",
            "1.5",
        ],
    )

    with pytest.raises(SystemExit):
        main()

def test_main_rejects_invalid_late_delay(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
            "--events",
            "10",
            "--late-delay-seconds",
            "0",
        ],
    )

    with pytest.raises(SystemExit):
        main()

def test_main_accepts_late_event_configuration(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
            "--events",
            "3",
            "--events-per-second",
            "1000",
            "--late-rate",
            "0.5",
            "--late-delay-seconds",
            "60",
        ],
    )

    main()

    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()

    assert len(lines) == 3

def test_main_generates_requested_number_of_journeys(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
            "--journeys",
            "2",
        ],
    )

    main()

    captured = capsys.readouterr()

    lines = captured.out.strip().splitlines()

    assert len(lines) >= 2

def test_main_accepts_out_of_order_rate(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "shopstream",
            "--journeys",
            "5",
            "--out-of-order-rate",
            "1.0",
        ],
    )

    main()

    captured = capsys.readouterr()

    assert captured.out.strip()

@patch("src.shopstream.main.PubSubPublisher")
@patch("src.shopstream.main.generate_event")
def test_main_publish_sends_events_to_pubsub(
    mock_generate_event,
    mock_publisher_class,
    monkeypatch,
):
    event = MagicMock()
    event.model_dump.return_value = {
        "event_id": "test-event",
        "event_type": "product_viewed",
    }
    event.event_type = "product_viewed"

    mock_generate_event.return_value = event

    publisher = mock_publisher_class.return_value

    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--events",
            "3",
            "--publish",
            "--project-id",
            "shopstream-data-platform",
            "--topic-id",
            "shopstream-events",
        ],
    )

    from src.shopstream.main import main

    main()

    mock_publisher_class.assert_called_once_with(
        project_id="shopstream-data-platform",
        topic_id="shopstream-events",
    )

    assert publisher.publish.call_count == 3

@patch("src.shopstream.main.PubSubPublisher")
def test_main_publish_requires_project_id(
    mock_publisher_class,
    monkeypatch,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--events",
            "1",
            "--publish",
        ],
    )

    from src.shopstream.main import main

    with pytest.raises(SystemExit):
        main()

    mock_publisher_class.assert_not_called()

@patch("src.shopstream.main.PubSubPublisher")
def test_main_without_publish_does_not_create_publisher(
    mock_publisher_class,
    monkeypatch,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--events",
            "2",
        ],
    )

    from src.shopstream.main import main

    main()

    mock_publisher_class.assert_not_called()

@patch("src.shopstream.main.PubSubPublisher")
def test_project_id_can_come_from_environment(
    mock_publisher_class,
    monkeypatch,
):
    monkeypatch.setenv(
        "SHOPSTREAM_PROJECT_ID",
        "env-project",
    )

    monkeypatch.delenv(
        "SHOPSTREAM_TOPIC_ID",
        raising=False,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--events",
            "1",
            "--publish",
        ],
    )

    from src.shopstream.main import main

    main()

    mock_publisher_class.assert_called_once_with(
        project_id="env-project",
        topic_id="shopstream-events",
    )

@patch("src.shopstream.main.PubSubPublisher")
def test_topic_id_can_come_from_environment(
    mock_publisher_class,
    monkeypatch,
):
    monkeypatch.setenv(
        "SHOPSTREAM_PROJECT_ID",
        "env-project",
    )

    monkeypatch.setenv(
        "SHOPSTREAM_TOPIC_ID",
        "env-topic",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--events",
            "1",
            "--publish",
        ],
    )

    from src.shopstream.main import main

    main()

    mock_publisher_class.assert_called_once_with(
        project_id="env-project",
        topic_id="env-topic",
    )

@patch("src.shopstream.main.PubSubPublisher")
def test_main_closes_publisher(
    mock_publisher_class,
    monkeypatch,
):
    monkeypatch.setenv(
        "SHOPSTREAM_PROJECT_ID",
        "test-project",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--events",
            "1",
            "--publish",
        ],
    )

    from src.shopstream.main import main

    main()

    publisher = mock_publisher_class.return_value

    publisher.close.assert_called_once()