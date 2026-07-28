import csv
import json
import re
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

import requests

RiverStation = dict[str, Any]

SOURCE_URLS = (
    "http://www.cjh.com.cn/sqindex.html",
    "http://www.cjh.com.cn/sssqcwww.html",
)
REQUEST_TIMEOUT = 30
MAX_ATTEMPTS = 3


def parse_river_data(html: str) -> list[RiverStation]:
    """Extract and validate river station data embedded in a source page."""
    match = re.search(
        r"\bvar\s+sssq\s*=\s*(\[.*?\])\s*;",
        html,
        flags=re.DOTALL,
    )
    if match is None:
        raise ValueError("source page does not contain the sssq data variable")

    river_data = json.loads(match.group(1))
    if not isinstance(river_data, list) or not river_data:
        raise ValueError("source page contains no river data")
    required_fields = {"rvnm", "stcd", "stnm", "tm"}
    if any(
        not isinstance(station, dict) or not required_fields.issubset(station)
        for station in river_data
    ):
        raise ValueError("source page contains malformed river data")
    return cast(list[RiverStation], river_data)


def fetch_river_data(url: str) -> list[RiverStation]:
    """Fetch one river data source with bounded retries."""
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": (
                        "LongRiver/1.0 (+https://github.com/Doradx/LongRiver)"
                    )
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return parse_river_data(response.text)
        except (requests.RequestException, ValueError) as error:
            last_error = error
            if attempt < MAX_ATTEMPTS:
                print(f"Fetch attempt {attempt}/{MAX_ATTEMPTS} failed: {error}")
                time.sleep(attempt * 2)

    raise RuntimeError(
        f"Failed to fetch river data from {url} after {MAX_ATTEMPTS} attempts"
    ) from last_error


def merge_river_data(
    datasets: Iterable[Iterable[RiverStation]],
) -> list[RiverStation]:
    """Merge sources, deduplicating the same station timestamp."""
    stations_by_observation: dict[tuple[str, int], RiverStation] = {}
    for dataset in datasets:
        for station in dataset:
            key = (str(station["stcd"]), int(station["tm"]))
            stations_by_observation.setdefault(key, station)

    return sorted(
        stations_by_observation.values(),
        key=lambda station: (int(station["tm"]), str(station["stcd"])),
    )


def fetch_all_river_data(
    urls: Iterable[str] = SOURCE_URLS,
) -> list[RiverStation]:
    """Fetch and merge all configured river data sources."""
    return merge_river_data(fetch_river_data(url) for url in urls)


def append_csv_record(
    csv_path: str | Path,
    station: RiverStation,
) -> None:
    """Append a station record aligned to the CSV's existing header."""
    path = Path(csv_path)
    with path.open("r", encoding="utf-8", newline="") as source:
        fieldnames = next(csv.reader(source))

    with path.open("a", encoding="utf-8", newline="") as output:
        csv.DictWriter(
            output,
            fieldnames=fieldnames,
            extrasaction="ignore",
        ).writerow(station)
