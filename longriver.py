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
    "http://www.cjh.com.cn/sssqw3.html",
    "http://sy.cjh.com.cn/",
    "http://zy.cjh.com.cn/sqall.html",
    "http://xy.cjh.com.cn/index.html",
    "http://hj.cjh.com.cn/hjsssq.html",
    "http://jj.cjh.com.cn/sssqall.html",
)
SOURCE_DEFAULT_RIVER_NAMES = {
    "http://sy.cjh.com.cn/": "长江上游",
    "http://zy.cjh.com.cn/sqall.html": "长江中游",
    "http://xy.cjh.com.cn/index.html": "长江下游",
    "http://hj.cjh.com.cn/hjsssq.html": "汉江",
    "http://jj.cjh.com.cn/sssqall.html": "荆江",
}
STATION_RIVER_NAMES = {
    "60103400": "金沙江",
    "60603300": "岷江",
    "60613950": "沱江",
    "60104800": "长江干流",
    "60703800": "嘉陵江",
    "60105400": "长江干流",
    "60802700": "乌江",
    "60803000": "乌江",
    "60105700": "长江干流",
    "60106000": "长江干流",
    "60112200": "长江干流",
    "60113400": "长江干流",
    "60113500": "长江干流",
    "60113900": "长江干流",
    "60114700": "长江干流",
    "60114900": "长江干流",
    "60115000": "长江干流",
    "60115100": "长江干流",
    "60116000": "长江干流",
    "60116300": "长江干流",
    "60116400": "长江干流",
    "62601600": "鄱阳湖",
}
FIELD_ALIASES = {
    "Q": "q",
    "TM": "tm",
    "WPTN": "wptn",
    "Z": "z",
}
REQUEST_TIMEOUT = 30
MAX_ATTEMPTS = 3


def normalize_river_station(
    station: dict[str, Any],
    default_rvnm: str | None = None,
) -> RiverStation:
    """Normalize source-specific station fields to the LongRiver schema."""
    normalized: dict[str, Any] = {}
    for key, value in station.items():
        normalized_key = FIELD_ALIASES.get(key, key)
        normalized.setdefault(normalized_key, value)

    stcd = str(normalized.get("stcd", ""))
    if str(normalized.get("rvnm", "")).strip() in {"", "(null)", "null"}:
        normalized["rvnm"] = STATION_RIVER_NAMES.get(stcd, default_rvnm)

    required_fields = {"rvnm", "stcd", "stnm", "tm"}
    if any(
        field not in normalized or normalized[field] in (None, "")
        for field in required_fields
    ):
        raise ValueError("source page contains malformed river data")

    return cast(RiverStation, normalized)


def parse_river_data(
    html: str,
    default_rvnm: str | None = None,
) -> list[RiverStation]:
    """Extract and validate river station data embedded in a source page."""
    match = re.search(
        r"\bvar\s+sssq\s*=\s*(\[.*?\])\s*;",
        html,
        flags=re.DOTALL,
    )
    if match is None:
        raise ValueError("source page does not contain the sssq data variable")

    try:
        river_data = json.loads(match.group(1))
    except json.JSONDecodeError as error:
        raise ValueError("source page contains malformed river data") from error

    if not isinstance(river_data, list) or not river_data:
        raise ValueError("source page contains no river data")
    if any(not isinstance(station, dict) for station in river_data):
        raise ValueError("source page contains malformed river data")
    return [
        normalize_river_station(station, default_rvnm)
        for station in cast(list[dict[str, Any]], river_data)
    ]


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
            return parse_river_data(
                response.text,
                SOURCE_DEFAULT_RIVER_NAMES.get(url),
            )
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
    datasets: list[list[RiverStation]] = []
    errors: list[RuntimeError] = []

    for url in urls:
        try:
            datasets.append(fetch_river_data(url))
        except RuntimeError as error:
            errors.append(error)
            print(error)

    if not datasets:
        raise RuntimeError(
            "Failed to fetch river data from all configured sources"
        ) from (errors[-1] if errors else None)

    return merge_river_data(datasets)


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
