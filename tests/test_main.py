import unittest
from unittest.mock import Mock, call, patch

import requests

from longriver import (
    SOURCE_URLS,
    fetch_all_river_data,
    fetch_river_data,
    merge_river_data,
    parse_river_data,
)


class ParseRiverDataTests(unittest.TestCase):
    def test_parses_sssq_array_with_flexible_whitespace(self) -> None:
        html = """
        <script>
            var  sssq = [
                {
                    "rvnm": "长江干流",
                    "stcd": "60112200",
                    "stnm": "汉口",
                    "tm": 1785139200000
                }
            ];
        </script>
        """

        self.assertEqual(
            parse_river_data(html),
            [
                {
                    "rvnm": "长江干流",
                    "stcd": "60112200",
                    "stnm": "汉口",
                    "tm": 1785139200000,
                }
            ],
        )

    def test_rejects_page_without_sssq_data(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not contain"):
            parse_river_data("404")

    def test_rejects_empty_sssq_array(self) -> None:
        with self.assertRaisesRegex(ValueError, "contains no river data"):
            parse_river_data("<script>var sssq = [];</script>")

    def test_rejects_malformed_station_data(self) -> None:
        with self.assertRaisesRegex(ValueError, "malformed"):
            parse_river_data('<script>var sssq = [{"stcd": "1"}];</script>')


class FetchRiverDataTests(unittest.TestCase):
    @patch("longriver.requests.get")
    def test_fetches_and_parses_source(self, get: Mock) -> None:
        response = Mock()
        response.text = (
            '<script>var sssq = [{"rvnm": "长江干流", "stcd": "1", '
            '"stnm": "甲", "tm": 100}];</script>'
        )
        get.return_value = response

        data = fetch_river_data("http://example.test/source")

        self.assertEqual(data[0]["stcd"], "1")
        response.raise_for_status.assert_called_once_with()

    @patch("longriver.time.sleep")
    @patch(
        "longriver.requests.get",
        side_effect=requests.ConnectionError("unavailable"),
    )
    def test_retries_then_raises_clear_error(
        self,
        get: Mock,
        sleep: Mock,
    ) -> None:
        with self.assertRaisesRegex(RuntimeError, "after 3 attempts"):
            fetch_river_data("http://example.test/source")

        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_args_list, [call(2), call(4)])


class MergeRiverDataTests(unittest.TestCase):
    def test_keeps_distinct_times_and_removes_exact_overlap(self) -> None:
        older = {
            "rvnm": "长江干流",
            "stcd": "60112200",
            "stnm": "汉口",
            "tm": 100,
        }
        newer = {**older, "tm": 200}

        self.assertEqual(
            merge_river_data([[newer], [older, newer.copy()]]),
            [older, newer],
        )

    @patch("longriver.fetch_river_data")
    def test_fetches_both_configured_sources(self, fetch: Mock) -> None:
        fetch.side_effect = [
            [{"rvnm": "长江干流", "stcd": "1", "stnm": "甲", "tm": 200}],
            [{"rvnm": "长江干流", "stcd": "2", "stnm": "乙", "tm": 100}],
        ]

        data = fetch_all_river_data()

        self.assertEqual([station["stcd"] for station in data], ["2", "1"])
        self.assertEqual(fetch.call_args_list, [call(url) for url in SOURCE_URLS])


if __name__ == "__main__":
    unittest.main()
