#!/usr/bin/env python3
"""Convert PanFileDB json_store records to telemetry server NDJSON files.

This script reads the flat JSON files produced by ``panoptes.utils.database.file.PanFileDB``
and rewrites them as day-partitioned NDJSON files that match the telemetry server's
storage format.

Usage::

    python scripts/migrate_json_store.py --source json_store/panoptes --dest telemetry/migrated

See ``docs/database-to-telemetry.md`` for full migration guidance.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path


def _parse_date(date_str: str) -> datetime:
    """Parse a PanFileDB date string into a UTC-aware datetime.

    PanFileDB stores dates as ISO-8601 strings produced by ``astropy.time``,
    which may or may not include a timezone designator.  We interpret naive
    timestamps as UTC.

    Args:
        date_str: ISO-8601 date string from a PanFileDB record.

    Returns:
        A timezone-aware UTC datetime.
    """
    # astropy serialises as e.g. "2026-03-18T00:05:48.955398"
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

    Each non-empty line is expected to be a complete JSON object.  Lines that
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
            print(f"  WARNING: skipping malformed line {lineno} in {path.name}: {exc}", file=sys.stderr)
    return records


def migrate(source_dir: Path, dest_dir: Path, *, verbose: bool = False) -> int:
    """Convert PanFileDB records to telemetry NDJSON files.

    Args:
        source_dir: Directory containing ``<collection>.json`` files (the
            ``db_name`` subdirectory inside ``json_store/``).
        dest_dir: Output directory for NDJSON files.  Created if absent.
        verbose: Print one line per converted record.

    Returns:
        Total number of records written.
    """
    collection_files = sorted(f for f in source_dir.glob("*.json") if not f.name.startswith("current_"))

    if not collection_files:
        print(f"No collection files found in {source_dir}", file=sys.stderr)
        return 0

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Group envelopes by day so we can write one NDJSON file per day.
    # day_key -> list of (ts_datetime, envelope_dict)
    by_day: dict[str, list[tuple[datetime, dict]]] = defaultdict(list)

    total_records = 0
    for collection_file in collection_files:
        collection = collection_file.stem  # e.g. "weather"
        print(f"Reading {collection_file.name} …")
        records = _read_collection(collection_file)
        print(f"  {len(records)} records")

        for record in records:
            date_str = record.get("date", "")
            try:
                ts = _parse_date(date_str)
            except (ValueError, TypeError):
                print(
                    f"  WARNING: cannot parse date {date_str!r} for record {record.get('_id')!r}; "
                    "using epoch",
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

    # Write one NDJSON file per day, records sorted chronologically, with seq.
    for day_key in sorted(by_day):
        day_records = sorted(by_day[day_key], key=lambda pair: pair[0])
        out_path = dest_dir / f"site_{day_key}.ndjson"
        print(f"Writing {out_path} ({len(day_records)} records) …")
        with out_path.open("w", encoding="utf-8") as fh:
            for seq, (_, envelope) in enumerate(day_records, start=1):
                envelope["seq"] = seq
                fh.write(json.dumps(envelope, separators=(",", ":")) + "\n")

    return total_records


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("json_store/panoptes"),
        help="PanFileDB source directory (the db_name subdirectory). Default: json_store/panoptes",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path("telemetry/migrated"),
        help="Output directory for NDJSON telemetry files. Default: telemetry/migrated",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print one line per converted record.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    source_dir: Path = args.source.expanduser().resolve()
    dest_dir: Path = args.dest.expanduser().resolve()

    if not source_dir.is_dir():
        print(f"ERROR: source directory does not exist: {source_dir}", file=sys.stderr)
        return 1

    print(f"Source : {source_dir}")
    print(f"Dest   : {dest_dir}")
    print()

    total = migrate(source_dir, dest_dir, verbose=args.verbose)

    print()
    print(f"Done. {total} records written to {dest_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
