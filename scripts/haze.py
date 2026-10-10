#!/usr/bin/env python3
"""Fetch Singapore NEA haze readings: 24-hour PSI and 1-hour PM2.5.

Python 3 standard library only. data.gov.sg publishes the readings without an
API key, and rejects requests that omit a User-Agent header (HTTP 403).

Keep scripts/haze.py and skills/singapore-haze/scripts/haze.py identical.
tests/test_haze.py checks both bytes.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

PSI_URL = "https://api-open.data.gov.sg/v2/real-time/api/psi"
PM25_URL = "https://api-open.data.gov.sg/v2/real-time/api/pm25"
USER_AGENT = "singapore-haze-skill/1.0 (+https://www.haze.gov.sg/)"
LICENCE_URL = "https://developers.data.gov.sg/open-data-licence"
REGIONS = ("north", "south", "east", "west", "central")
TIMEOUT_SECONDS = 30
SGT = timezone(timedelta(hours=8))

PSI_READING = "psi_twenty_four_hourly"
PM25_READING = "pm25_one_hourly"
PM25_UNIT = "µg/m³"


class HazeError(Exception):
    """A problem the user should see, with a non-zero exit."""


def psi_descriptor(value: float) -> str:
    """Official 24-hour PSI descriptor from haze.gov.sg.

    Bands are the published integer ranges: 0–50, 51–100, 101–200,
    201–300, and above 300.
    """
    if value <= 50:
        return "Good"
    if value <= 100:
        return "Moderate"
    if value <= 200:
        return "Unhealthy"
    if value <= 300:
        return "Very unhealthy"
    return "Hazardous"


def pm25_descriptor(value: float) -> str:
    """Official 1-hour PM2.5 descriptor from haze.gov.sg.

    Bands are the published integer ranges: 0–55, 56–150, 151–250,
    and 251 and above. A non-integer above 250 is Band 4.
    """
    if value <= 55:
        return "Band 1 (Normal)"
    if value <= 150:
        return "Band 2 (Elevated)"
    if value <= 250:
        return "Band 3 (High)"
    return "Band 4 (Very High)"


def resolve_regions(names: list[str]) -> list[str]:
    """Return canonical region ids, in request order. Empty means all five."""
    if not names:
        return list(REGIONS)
    resolved: list[str] = []
    seen: set[str] = set()
    for name in names:
        key = name.strip().lower()
        if key not in REGIONS:
            expected = ", ".join(REGIONS)
            raise HazeError(f"unknown region {name!r}. Expected one of: {expected}")
        if key not in seen:
            seen.add(key)
            resolved.append(key)
    return resolved


def fetch_json(url: str, timeout: float = TIMEOUT_SECONDS) -> dict:
    """GET JSON. Raises HazeError on network, HTTP, or parse failure."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        reason = exc.reason if isinstance(exc.reason, str) else "request failed"
        exc.close()
        raise HazeError(f"HTTP {exc.code} {reason} from {url}") from exc
    except urllib.error.URLError as exc:
        raise HazeError(f"could not reach {url}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise HazeError(f"timed out waiting for {url}") from exc
    except OSError as exc:
        raise HazeError(f"could not reach {url}: {exc}") from exc

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HazeError(f"response from {url} was not valid JSON") from exc
    if not isinstance(payload, dict):
        raise HazeError(f"response from {url} was not a JSON object")
    code = payload.get("code")
    if code not in (0, None):
        detail = payload.get("errorMsg") or f"API code {code}"
        raise HazeError(f"API error from {url}: {detail}")
    return payload


def latest_item(payload: dict, url: str) -> dict:
    data = payload.get("data")
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list) or not items or not isinstance(items[0], dict):
        raise HazeError(f"response from {url} contained no readings")
    return items[0]


def _reading_value(item: dict, reading: str, region: str, url: str) -> int | float:
    readings = item.get("readings")
    values = readings.get(reading) if isinstance(readings, dict) else None
    if not isinstance(values, dict) or region not in values:
        raise HazeError(f"response from {url} missing {reading} for {region}")
    value = values[region]
    if isinstance(value, bool) or value is None:
        raise HazeError(f"response from {url} missing {reading} for {region}")
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            number = None
        if number is not None:
            return int(number) if number.is_integer() else number
    raise HazeError(f"response from {url} has a non-numeric {reading} for {region}")


def _timestamp(item: dict, url: str) -> str:
    timestamp = item.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise HazeError(f"response from {url} missing a reading timestamp")
    return timestamp.strip()


def format_sgt(timestamp: str) -> str:
    """Label a reading time in Singapore time, and keep the original text."""
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        return f"{timestamp} (SGT)"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=SGT)
    local = parsed.astimezone(SGT)
    return f"{local.strftime('%Y-%m-%d %H:%M')} SGT ({timestamp})"


def attribution(accessed_on: str | None = None) -> str:
    day = accessed_on or datetime.now(SGT).strftime("%Y-%m-%d")
    return (
        "Contains information from the PSI and PM2.5 real-time datasets "
        f"accessed on {day} from data.gov.sg (National Environment Agency), "
        "made available under the Singapore Open Data Licence version 1.0 "
        f"({LICENCE_URL})."
    )


def build_report(regions: list[str], timeout: float = TIMEOUT_SECONDS) -> dict:
    psi_payload = fetch_json(PSI_URL, timeout=timeout)
    pm_payload = fetch_json(PM25_URL, timeout=timeout)
    return report_from_items(
        latest_item(psi_payload, PSI_URL),
        latest_item(pm_payload, PM25_URL),
        regions,
    )


def report_from_items(psi_item: dict, pm_item: dict, regions: list[str]) -> dict:
    psi_timestamp = _timestamp(psi_item, PSI_URL)
    pm_timestamp = _timestamp(pm_item, PM25_URL)
    rows = []
    for region in regions:
        psi_value = _reading_value(psi_item, PSI_READING, region, PSI_URL)
        pm_value = _reading_value(pm_item, PM25_READING, region, PM25_URL)
        rows.append(
            {
                "region": region,
                "psi_twenty_four_hourly": {
                    "value": psi_value,
                    "descriptor": psi_descriptor(psi_value),
                    "timestamp": psi_timestamp,
                },
                "pm25_one_hourly": {
                    "value": pm_value,
                    "unit": PM25_UNIT,
                    "descriptor": pm25_descriptor(pm_value),
                    "timestamp": pm_timestamp,
                },
            }
        )
    return {
        "source": "NEA via data.gov.sg",
        "attribution": attribution(),
        "psi_timestamp": psi_timestamp,
        "pm25_timestamp": pm_timestamp,
        "regions": rows,
    }


def _format_number(value: int | float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def render_text(report: dict) -> str:
    rows = report["regions"]
    headers = (
        "Region",
        "24-hr PSI",
        "PSI descriptor",
        f"1-hr PM2.5 ({PM25_UNIT})",
        "PM2.5 descriptor",
    )
    body = []
    for row in rows:
        psi = row["psi_twenty_four_hourly"]
        pm = row["pm25_one_hourly"]
        body.append(
            (
                row["region"].title(),
                _format_number(psi["value"]),
                psi["descriptor"],
                _format_number(pm["value"]),
                pm["descriptor"],
            )
        )
    widths = [len(header) for header in headers]
    for cols in body:
        for index, col in enumerate(cols):
            widths[index] = max(widths[index], len(col))

    def line(cols: tuple[str, ...]) -> str:
        padded = [col.ljust(widths[index]) for index, col in enumerate(cols)]
        return "  ".join(padded).rstrip()

    rule = tuple("-" * width for width in widths)
    lines = [
        f"24-hr PSI as of {format_sgt(report['psi_timestamp'])}",
        f"1-hr PM2.5 as of {format_sgt(report['pm25_timestamp'])}",
        "",
        line(headers),
        line(rule),
    ]
    lines.extend(line(cols) for cols in body)
    lines.extend(["", report["attribution"]])
    return "\n".join(lines)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="haze.py",
        description=(
            "Fetch NEA 24-hour PSI and 1-hour PM2.5 for Singapore's five regions."
        ),
        epilog=(
            "examples:\n"
            "  python3 scripts/haze.py\n"
            "  python3 scripts/haze.py central\n"
            "  python3 scripts/haze.py north east --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "regions",
        nargs="*",
        help="North, South, East, West, and/or Central (case-insensitive). Default: all five.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print JSON with values, descriptors, and timestamps.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        regions = resolve_regions(args.regions)
        report = build_report(regions)
    except HazeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.as_json:
        json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
