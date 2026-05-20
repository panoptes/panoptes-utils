"""Convert PanFileDB json_store records to telemetry server NDJSON files."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path


def _parse_date(date_str: str) -> datetime:
    """Parse a PanFileDB date string into a UTC-aware datetime.

    PanFileDB stores dates as ISO-8601 strings produced by ``astropy.time``,
    which may or may not include a timezone designator. Naive timestamps are
    interpreted as UTC.

    Args:
        date_str: ISO-8601 date string from a PanFileDB record.

    Returns:
        A timezone-aware UTC datetime.
    """
    dt = datetime.fromisoformat(date_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _day_key(dt: datetime) -> str:
    """Return a ``YYYYMMDD`` key for ``dt`` (UTC)."""
    return dt.strftime("%Y%m%d")


def _to_utc_iso_z(dt: datetime) -> str:
    """Return a UTC ISO-8601 timestamp with a trailing ``Z``."""
    return dt.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _read_collection(path: Path) -> list[dict]:
    """Read all valid JSON records from a PanFileDB collection file.

    Each non-empty line is expected to be a complete JSON object. Lines that
    cannot be parsed are skipped with a warning.

    Args:
        path: Path to a ``<collection>.json`` file.

    Returns:
        List of parsed record dicts.
    """
    records = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            print(
                f"  WARNING: skipping malformed line {lineno} in {path.name}: {exc}",
                file=sys.stderr,
            )
    return records


def migrate(source_dir: Path, dest_dir: Path, *, verbose: bool = False) -> int:
    """Convert PanFileDB records to telemetry NDJSON files.

    Reads ``<collection>.json`` files from ``source_dir`` (skipping
    ``current_*.json`` snapshots), groups records by the date in their
    ``date`` field, and writes day-partitioned ``site_YYYYMMDD.ndjson``
    files under ``dest_dir`` using the telemetry envelope format.

    Args:
        source_dir: Directory containing ``<collection>.json`` files (the
            ``db_name`` subdirectory inside ``json_store/``).
        dest_dir: Output directory for NDJSON files. Created if absent.
        verbose: Print one line per converted record.

    Returns:
        Total number of records written.
    """
    collection_files = sorted(f for f in source_dir.glob("*.json") if not f.name.startswith("current_"))

    if not collection_files:
        return 0

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Group envelopes by day so we write one NDJSON file per day.
    by_day: dict[str, list[tuple[datetime, dict]]] = defaultdict(list)

    total_records = 0
    for collection_file in collection_files:
        collection = collection_file.stem
        records = _read_collection(collection_file)

        for record in records:
            date_str = record.get("date", "")
            try:
                ts = _parse_date(date_str)
            except (ValueError, TypeError):
                print(
                    f"  WARNING: cannot parse date {date_str!r} for record "
                    f"{record.get('_id')!r}; using epoch",
                    file=sys.stderr,
                )
                ts = datetime(1970, 1, 1, tzinfo=UTC)

            envelope = {
                "ts": _to_utc_iso_z(ts),
                "type": record.get("type", collection),
                "data": record.get("data"),
                "meta": {
                    "migrated_from": "PanFileDB",
                    "original_id": record.get("_id", ""),
                },
            }
            by_day[_day_key(ts)].append((ts, envelope))
            total_records += 1
            if verbose:
                print(f"    {envelope['ts']} {envelope['type']}")

    for day_key in sorted(by_day):
        day_records = sorted(by_day[day_key], key=lambda pair: pair[0])
        out_path = dest_dir / f"site_{day_key}.ndjson"
        with out_path.open("w", encoding="utf-8") as fh:
            for seq, (_, envelope) in enumerate(day_records, start=1):
                envelope["seq"] = seq
                fh.write(json.dumps(envelope, separators=(",", ":")) + "\n")

    return total_records
