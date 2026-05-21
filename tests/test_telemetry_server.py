from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from panoptes.utils.telemetry.server import EventRequest, TelemetryService, create_app, get_site_day_key


def _read_ndjson(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_health_and_ready(tmp_path):
    fixed_now = datetime(2026, 3, 17, 13, 30, tzinfo=timezone(timedelta(hours=-7)))
    client = TestClient(create_app(TelemetryService(tmp_path / "site", now_provider=lambda: fixed_now)))

    health_response = client.get("/health")
    ready_response = client.get("/ready")

    assert health_response.status_code == 200
    assert ready_response.status_code == 200
    assert ready_response.json()["ready"] is True
    assert ready_response.json()["run_active"] is False


def test_post_event_defaults_to_site_and_updates_current(tmp_path):
    fixed_now = datetime(2026, 3, 17, 13, 15, tzinfo=timezone(timedelta(hours=-7)))
    site_dir = tmp_path / "site"
    client = TestClient(create_app(TelemetryService(site_dir, now_provider=lambda: fixed_now)))

    response = client.post("/event", json={"type": "weather", "data": {"sky": "clear"}})

    assert response.status_code == 200
    payload = response.json()
    assert payload["seq"] == 1
    assert payload["ts"].endswith("Z")

    current_response = client.get("/current")
    assert current_response.status_code == 200
    assert current_response.json() == {
        "current": {
            "weather": payload,
        },
    }

    output_path = site_dir / "site_20260317.ndjson"
    assert output_path.exists()
    assert _read_ndjson(output_path) == [{**payload, "stream": "site"}]


def test_run_events_use_active_run_context(tmp_path):
    fixed_now = datetime(2026, 3, 17, 13, 45, tzinfo=timezone(timedelta(hours=-7)))
    run_dir = tmp_path / "run-001"
    client = TestClient(create_app(TelemetryService(tmp_path / "site", now_provider=lambda: fixed_now)))

    start_response = client.post("/run/start", json={"run_dir": str(run_dir), "meta": {"run_id": "001"}})
    event_response = client.post("/event", json={"type": "status", "data": {"state": "running"}})

    assert start_response.status_code == 200
    assert event_response.status_code == 200
    assert event_response.json()["meta"]["run_id"] == "001"

    output_path = run_dir / "telemetry.ndjson"
    assert output_path.exists()
    assert _read_ndjson(output_path) == [{**event_response.json(), "stream": "run"}]


def test_relative_run_dir_is_resolved_under_site_dir(tmp_path):
    fixed_now = datetime(2026, 3, 17, 13, 47, tzinfo=timezone(timedelta(hours=-7)))
    site_dir = tmp_path / "site"
    client = TestClient(create_app(TelemetryService(site_dir, now_provider=lambda: fixed_now)))

    start_response = client.post("/run/start", json={"run_dir": "run-003", "run_id": "003"})

    assert start_response.status_code == 200
    assert start_response.json()["run_dir"] == str(site_dir / "run-003")


def test_start_run_defaults_to_next_numeric_run_under_site_dir(tmp_path):
    fixed_now = datetime(2026, 3, 17, 13, 48, tzinfo=timezone(timedelta(hours=-7)))
    site_dir = tmp_path / "site"
    (site_dir / "001").mkdir(parents=True)
    (site_dir / "002").mkdir()
    client = TestClient(create_app(TelemetryService(site_dir, now_provider=lambda: fixed_now)))

    start_response = client.post("/run/start", json={})

    assert start_response.status_code == 200
    assert start_response.json()["run_id"] == "003"
    assert start_response.json()["run_dir"] == str(site_dir / "003")


def test_run_event_meta_uses_active_run_id(tmp_path):
    fixed_now = datetime(2026, 3, 17, 13, 50, tzinfo=timezone(timedelta(hours=-7)))
    run_dir = tmp_path / "run-override"
    client = TestClient(create_app(TelemetryService(tmp_path / "site", now_provider=lambda: fixed_now)))

    start_response = client.post("/run/start", json={"run_dir": str(run_dir), "run_id": "run-123"})
    event_response = client.post(
        "/event",
        json={"type": "status", "data": {"state": "running"}, "meta": {"run_id": "wrong", "source": "test"}},
    )

    assert start_response.status_code == 200
    assert start_response.json()["run_id"] == "run-123"
    assert start_response.json()["meta"]["run_id"] == "run-123"
    assert event_response.status_code == 200
    assert event_response.json()["meta"] == {"run_id": "run-123", "source": "test"}


def test_current_returns_full_snapshot(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 0, tzinfo=UTC)
    client = TestClient(create_app(TelemetryService(tmp_path / "site", now_provider=lambda: fixed_now)))

    first = client.post("/event", json={"type": "weather", "data": {"humidity": 12}}).json()
    second = client.post("/event", json={"type": "power", "data": {"battery": 97}}).json()

    current_response = client.get("/current")
    weather_response = client.get("/current/weather")

    assert current_response.status_code == 200
    assert current_response.json() == {
        "current": {
            "weather": first,
            "power": second,
        },
    }
    assert weather_response.status_code == 200
    assert weather_response.json() == first


def test_current_merges_site_and_run_context(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 5, tzinfo=UTC)
    run_dir = tmp_path / "run-001"
    client = TestClient(create_app(TelemetryService(tmp_path / "site", now_provider=lambda: fixed_now)))

    site_weather = client.post("/event", json={"type": "weather", "data": {"sky": "clear"}}).json()
    client.post("/run/start", json={"run_dir": str(run_dir), "run_id": "001"})
    run_status = client.post("/event", json={"type": "status", "data": {"state": "running"}}).json()

    current_response = client.get("/current")

    assert current_response.status_code == 200
    assert current_response.json() == {
        "current": {
            "weather": site_weather,
            "status": run_status,
        },
    }


def test_append_event_emits_debug_log(tmp_path, monkeypatch):
    fixed_now = datetime(2026, 3, 17, 14, 10, tzinfo=UTC)
    service = TelemetryService(tmp_path / "site", now_provider=lambda: fixed_now)
    debug_calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def fake_debug(message: str, *args: object, **kwargs: object) -> None:
        debug_calls.append((message, args, kwargs))

    monkeypatch.setattr("panoptes.utils.telemetry.server.logger.debug", fake_debug)

    service.append_event(EventRequest(type="weather", data={"sky": "clear"}))

    assert len(debug_calls) == 1
    assert debug_calls[0][0].startswith("Telemetry event received:")
    assert debug_calls[0][2]["event_type"] == "weather"
    assert debug_calls[0][2]["target"] == "site"
    assert debug_calls[0][2]["seq"] == 1


def test_append_event_does_not_advance_sequence_on_write_failure(tmp_path, monkeypatch):
    fixed_now = datetime(2026, 3, 17, 14, 12, tzinfo=UTC)
    service = TelemetryService(tmp_path / "site", now_provider=lambda: fixed_now)
    original_open = Path.open
    write_attempts = {"count": 0}

    def fake_open(
        path: Path,
        *args: object,
        **kwargs: object,
    ):
        if path.name.endswith(".ndjson"):
            write_attempts["count"] += 1
            if write_attempts["count"] == 2:
                raise OSError("disk full")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fake_open)

    first_event = service.append_event(EventRequest(type="weather", data={"sky": "clear"}))

    try:
        service.append_event(EventRequest(type="weather", data={"sky": "cloudy"}))
    except OSError as error:
        assert str(error) == "disk full"
    else:  # pragma: no cover
        raise AssertionError("expected append_event to propagate write failure")

    third_event = service.append_event(EventRequest(type="weather", data={"sky": "windy"}))

    assert first_event["seq"] == 1
    assert third_event["seq"] == 2


def test_ephemeral_event_skips_file_write(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 15, tzinfo=UTC)
    site_dir = tmp_path / "site"
    client = TestClient(create_app(TelemetryService(site_dir, now_provider=lambda: fixed_now)))

    response = client.post(
        "/event", json={"type": "weather", "data": {"sky": "clear"}, "store_permanently": False}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["seq"] == 1

    current_response = client.get("/current")
    assert "weather" in current_response.json()["current"]

    ndjson_files = list(site_dir.glob("*.ndjson"))
    assert ndjson_files == []


def test_mixed_permanent_and_ephemeral_events(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 20, tzinfo=UTC)
    site_dir = tmp_path / "site"
    client = TestClient(create_app(TelemetryService(site_dir, now_provider=lambda: fixed_now)))

    permanent = client.post("/event", json={"type": "weather", "data": {"sky": "clear"}}).json()
    ephemeral = client.post(
        "/event", json={"type": "weather", "data": {"sky": "cloudy"}, "store_permanently": False}
    ).json()

    assert permanent["seq"] == 1
    assert ephemeral["seq"] == 2

    current_response = client.get("/current")
    assert current_response.json()["current"]["weather"] == ephemeral

    output_path = site_dir / "site_20260317.ndjson"
    assert output_path.exists()
    records = _read_ndjson(output_path)
    assert len(records) == 1
    assert records[0]["seq"] == 1


def test_site_rotation_uses_previous_date_before_noon():
    before_noon = datetime(2026, 3, 17, 11, 59, tzinfo=timezone(timedelta(hours=-7)))

    assert get_site_day_key(before_noon) == "20260316"


def test_site_rotation_uses_current_date_at_or_after_noon():
    at_noon = datetime(2026, 3, 17, 12, 0, tzinfo=timezone(timedelta(hours=-7)))
    after_noon = datetime(2026, 3, 17, 15, 30, tzinfo=timezone(timedelta(hours=-7)))

    assert get_site_day_key(at_noon) == "20260317"
    assert get_site_day_key(after_noon) == "20260317"


# ---------------------------------------------------------------------------
# Post-event hook tests
# ---------------------------------------------------------------------------


def test_post_event_hook_is_called_with_envelope_and_request(tmp_path):
    received = {}
    done = threading.Event()

    def my_hook(envelope, request):
        received["envelope"] = envelope
        received["request"] = request
        done.set()

    service = TelemetryService(tmp_path / "site", post_event_hooks=[my_hook])
    result = service.append_event(EventRequest(type="weather", data={"sky": "clear"}))

    assert done.wait(timeout=1.0), "hook was not called within 1 second"
    assert received["envelope"] == result
    assert received["envelope"]["type"] == "weather"
    assert received["request"].type == "weather"
    assert received["request"].store_permanently is True


def test_post_event_hook_receives_store_permanently_flag(tmp_path):
    received = []
    done = threading.Event()

    def my_hook(envelope, request):
        received.append(request.store_permanently)
        done.set()

    service = TelemetryService(tmp_path / "site", post_event_hooks=[my_hook])
    service.append_event(EventRequest(type="status", data={}, store_permanently=False))

    assert done.wait(timeout=1.0), "hook was not called within 1 second"
    assert received == [False]


def test_post_event_hook_exception_is_non_fatal(tmp_path):
    def bad_hook(envelope, request):
        raise RuntimeError("boom")

    service = TelemetryService(tmp_path / "site", post_event_hooks=[bad_hook])
    result = service.append_event(EventRequest(type="weather", data={"sky": "clear"}))

    time.sleep(0.05)  # give the daemon thread a moment to run
    assert result["seq"] == 1  # server still returned normally


def test_multiple_post_event_hooks_all_fire(tmp_path):
    calls = []
    all_done = threading.Barrier(3)  # main thread + 2 hooks

    def hook_a(envelope, request):
        calls.append("a")
        all_done.wait(timeout=1.0)

    def hook_b(envelope, request):
        calls.append("b")
        all_done.wait(timeout=1.0)

    service = TelemetryService(tmp_path / "site", post_event_hooks=[hook_a, hook_b])
    service.append_event(EventRequest(type="weather", data={}))
    all_done.wait(timeout=1.0)

    assert sorted(calls) == ["a", "b"]


def test_no_hooks_by_default(tmp_path):
    service = TelemetryService(tmp_path / "site")
    assert service._post_event_hooks == []


def test_post_event_hook_does_not_block_server_response(tmp_path):
    slow_hook_started = threading.Event()
    slow_hook_finished = threading.Event()

    def slow_hook(envelope, request):
        slow_hook_started.set()
        time.sleep(0.2)
        slow_hook_finished.set()

    service = TelemetryService(tmp_path / "site", post_event_hooks=[slow_hook])

    start = time.monotonic()
    result = service.append_event(EventRequest(type="weather", data={}))
    elapsed = time.monotonic() - start

    # append_event must return before the slow hook finishes
    assert elapsed < 0.1, f"append_event blocked for {elapsed:.3f}s — hook was not non-blocking"
    assert result["seq"] == 1
    slow_hook_started.wait(timeout=1.0)
    slow_hook_finished.wait(timeout=1.0)
