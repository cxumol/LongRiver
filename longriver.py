import json
import re
import time

import requests


SOURCE_URL = "http://www.cjh.com.cn/sqindex.html"
REQUEST_TIMEOUT = 30
MAX_ATTEMPTS = 3


def parse_river_data(html):
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
    return river_data


def fetch_river_data(url=SOURCE_URL):
    last_error = None
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
                print(
                    "Fetch attempt {}/{} failed: {}".format(
                        attempt, MAX_ATTEMPTS, error
                    )
                )
                time.sleep(attempt * 2)

    raise RuntimeError(
        "Failed to fetch river data from {} after {} attempts".format(
            url, MAX_ATTEMPTS
        )
    ) from last_error
