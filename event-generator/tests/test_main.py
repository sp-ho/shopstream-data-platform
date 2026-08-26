# CLI test
import pytest

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