from __future__ import annotations

from typer.testing import CliRunner

from panoptes.utils.cli.telemetry import app

runner = CliRunner()


class _FakeTelemetryClient:
    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        self.host = host
        self.port = port
        self.current_calls = 0
        self.current_event_calls = 0

    def current(self) -> dict[str, object]:
        self.current_calls += 1
        return {
            "current": {
                "weather": {
                    "type": "weather",
                    "seq": 4,
                    "ts": "2026-03-18T18:00:00.000Z",
                    "data": {"sky": "clear"},
                    "meta": {"source": "sensor", "run_id": "001"},
                }
            }
        }

    def current_event(self, event_type: str) -> dict[str, object]:
        self.current_event_calls += 1
        return {
            "type": event_type,
            "seq": 5,
            "ts": "2026-03-18T18:00:01.000Z",
            "data": {"state": "running"},
            "meta": {"source": "mount"},
        }


class _FollowTelemetryClient:
    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        self.host = host
        self.port = port
        self._payloads = [
            {
                "current": {
                    "status": {
                        "type": "status",
                        "seq": 1,
                        "ts": "2026-03-18T18:00:00.000Z",
                        "data": {"state": "idle"},
                        "meta": {"run_id": "001"},
                    }
                }
            },
            {
                "current": {
                    "status": {
                        "type": "status",
                        "seq": 2,
                        "ts": "2026-03-18T18:00:01.000Z",
                        "data": {"state": "running"},
                        "meta": {"run_id": "001"},
                    }
                }
            },
        ]
        self._index = 0

    def current(self) -> dict[str, object]:
        payload = self._payloads[min(self._index, len(self._payloads) - 1)]
        self._index += 1
        return payload


class _FakeProcess:
    def __init__(self) -> None:
        self.pid = 12345
        self.started = False

    def start(self) -> None:
        self.started = True

    def is_alive(self) -> bool:
        return False

    def terminate(self) -> None:
        return None

    def join(self, _: float) -> None:
        return None


def test_current_command_prints_full_snapshot(monkeypatch):
    monkeypatch.setattr("panoptes.utils.cli.telemetry.TelemetryClient", _FakeTelemetryClient)

    result = runner.invoke(app, ["current"])

    assert result.exit_code == 0
    assert "Current telemetry" in result.stdout
    assert "weather" in result.stdout
    assert "type" in result.stdout
    assert "001" in result.stdout
    assert "sensor" in result.stdout
    assert '"sky": "clear"' in result.stdout


def test_current_command_prints_single_event(monkeypatch):
    monkeypatch.setattr("panoptes.utils.cli.telemetry.TelemetryClient", _FakeTelemetryClient)

    result = runner.invoke(app, ["current", "status"])

    assert result.exit_code == 0
    assert "Current telemetry: status" in result.stdout
    assert "type" in result.stdout
    assert "status" in result.stdout
    assert "mount" in result.stdout
    assert '"state": "running"' in result.stdout


def test_current_command_follow_prints_updates(monkeypatch):
    monkeypatch.setattr("panoptes.utils.cli.telemetry.TelemetryClient", _FollowTelemetryClient)

    sleep_calls = {"count": 0}

    def fake_sleep(_: float) -> None:
        sleep_calls["count"] += 1
        if sleep_calls["count"] >= 2:
            raise KeyboardInterrupt

    monkeypatch.setattr("panoptes.utils.cli.telemetry.time.sleep", fake_sleep)

    result = runner.invoke(app, ["current", "--follow", "--interval", "0.1"])

    assert result.exit_code == 0
    assert "Current telemetry" in result.stdout
    assert '"state": "running"' in result.stdout
    assert "Stopped following telemetry." in result.stdout


def test_run_command_passes_verbose_to_server(monkeypatch):
    fake_process = _FakeProcess()
    captured_kwargs: dict[str, object] = {}

    def fake_telemetry_server(**kwargs: object) -> _FakeProcess:
        captured_kwargs.update(kwargs)
        return fake_process

    monkeypatch.setattr("panoptes.utils.cli.telemetry.telemetry_server", fake_telemetry_server)
    monkeypatch.setattr("panoptes.utils.cli.telemetry._server_is_ready", lambda _host, _port: True)

    result = runner.invoke(app, ["run", "--verbose"])

    assert result.exit_code == 0
    assert fake_process.started is True
    assert captured_kwargs["verbose"] is True
