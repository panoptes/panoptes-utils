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


def test_migrate_command_converts_file_db_records(tmp_path):
    """migrate converts real PanFileDB json_store records into telemetry NDJSON files."""
    import json
    import random

    from panoptes.utils.database import PanDB

    # Build a PanFileDB with a handful of records across three collections.
    source_root = tmp_path / "json_store"
    db = PanDB(db_type="file", db_name="panoptes", storage_dir=str(source_root))
    collections = ["weather", "mount", "environment"]
    records_per_collection = 4
    for collection in collections:
        for i in range(records_per_collection):
            db.insert_current(collection, {"value": round(random.random(), 4), "index": i})

    source_dir = source_root / "panoptes"
    dest_dir = tmp_path / "telemetry"

    result = runner.invoke(
        app,
        ["migrate", "--source", str(source_dir), "--dest", str(dest_dir)],
    )

    assert result.exit_code == 0, result.stdout
    assert "Done." in result.stdout

    # At least one day-partitioned NDJSON file must be written.
    ndjson_files = sorted(dest_dir.glob("site_*.ndjson"))
    assert ndjson_files, "No NDJSON output files found"

    # Read every record from every output file.
    all_records = []
    for ndjson_file in ndjson_files:
        for line in ndjson_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                all_records.append(json.loads(line))

    # Total records: 3 collections × 4 inserts.
    expected_total = len(collections) * records_per_collection
    assert len(all_records) == expected_total

    # Every record must have the telemetry envelope shape.
    for record in all_records:
        assert "seq" in record
        assert "ts" in record
        assert "type" in record
        assert "data" in record
        assert record["meta"]["migrated_from"] == "PanFileDB"

    # All three collection types must appear in the output.
    assert {r["type"] for r in all_records} == set(collections)

    # Sequence numbers within each file must be contiguous from 1.
    for ndjson_file in ndjson_files:
        file_records = [
            json.loads(line)
            for line in ndjson_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert [r["seq"] for r in file_records] == list(range(1, len(file_records) + 1))

    # current_*.json snapshot files must NOT be converted (they are ephemeral).
    current_types = {r["type"] for r in all_records if r.get("meta", {}).get("original_id", "").startswith("current_")}
    assert not current_types


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
