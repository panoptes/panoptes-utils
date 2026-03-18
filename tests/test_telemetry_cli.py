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
        return {"current": {"weather": {"type": "weather", "data": {"sky": "clear"}}}}

    def current_event(self, event_type: str) -> dict[str, object]:
        self.current_event_calls += 1
        return {"type": event_type, "data": {"state": "running"}}


class _FollowTelemetryClient:
    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        self.host = host
        self.port = port
        self._payloads = [
            {"current": {"status": {"type": "status", "data": {"state": "idle"}}}},
            {"current": {"status": {"type": "status", "data": {"state": "running"}}}},
        ]
        self._index = 0

    def current(self) -> dict[str, object]:
        payload = self._payloads[min(self._index, len(self._payloads) - 1)]
        self._index += 1
        return payload


def test_current_command_prints_full_snapshot(monkeypatch):
    monkeypatch.setattr("panoptes.utils.cli.telemetry.TelemetryClient", _FakeTelemetryClient)

    result = runner.invoke(app, ["current"])

    assert result.exit_code == 0
    assert '"weather"' in result.stdout
    assert '"sky": "clear"' in result.stdout


def test_current_command_prints_single_event(monkeypatch):
    monkeypatch.setattr("panoptes.utils.cli.telemetry.TelemetryClient", _FakeTelemetryClient)

    result = runner.invoke(app, ["current", "status"])

    assert result.exit_code == 0
    assert '"type": "status"' in result.stdout
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
    assert '"state": "idle"' in result.stdout
    assert '"state": "running"' in result.stdout
    assert "Stopped following telemetry." in result.stdout
