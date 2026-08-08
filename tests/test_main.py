import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, call, patch

import requests

from longriver import (
    SOURCE_URLS,
    append_csv_record,
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

    def test_parses_sssq_when_other_script_variables_come_first(self) -> None:
        html = """
        <script>
            var _weekday = ["日", "一"];
            var sssq = [
                {
                    "stcd": "62916275",
                    "stnm": "水口闸",
                    "tm": 1785139200000
                }
            ];
        </script>
        """

        data = parse_river_data(html, default_rvnm="长江下游")

        self.assertEqual(data[0]["rvnm"], "长江下游")

    def test_uses_station_river_name_before_source_default(self) -> None:
        html = """
        <script>
            var sssq = [
                {
                    "stcd": "60115000",
                    "stnm": "大通",
                    "tm": 1785139200000
                }
            ];
        </script>
        """

        data = parse_river_data(html, default_rvnm="长江下游")

        self.assertEqual(data[0]["rvnm"], "长江干流")

    def test_treats_null_string_river_name_as_missing(self) -> None:
        html = """
        <script>
            var sssq = [
                {
                    "rvnm": "(null)",
                    "stcd": "61502800",
                    "stnm": "梅田湖",
                    "tm": 1785139200000
                }
            ];
        </script>
        """

        data = parse_river_data(html, default_rvnm="长江中游")

        self.assertEqual(data[0]["rvnm"], "长江中游")

    def test_normalizes_uppercase_hanjiang_fields(self) -> None:
        html = """
        <script>
            var sssq = [
                {
                    "Q": 1580.0,
                    "TM": 1785139200000,
                    "WPTN": "5",
                    "Z": 179.56,
                    "stcd": "61801700",
                    "stnm": "白河"
                }
            ];
        </script>
        """

        data = parse_river_data(html, default_rvnm="汉江")

        self.assertEqual(data[0]["q"], 1580.0)
        self.assertEqual(data[0]["tm"], 1785139200000)
        self.assertEqual(data[0]["wptn"], "5")
        self.assertEqual(data[0]["z"], 179.56)
        self.assertEqual(data[0]["rvnm"], "汉江")


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
    def test_fetches_all_configured_sources(self, fetch: Mock) -> None:
        fetch.side_effect = [
            [
                {
                    "rvnm": "长江干流",
                    "stcd": str(index),
                    "stnm": "甲",
                    "tm": index,
                }
            ]
            for index, _ in enumerate(SOURCE_URLS)
        ]

        data = fetch_all_river_data()

        self.assertEqual(
            [station["stcd"] for station in data],
            [str(index) for index, _ in enumerate(SOURCE_URLS)],
        )
        self.assertEqual(fetch.call_args_list, [call(url) for url in SOURCE_URLS])

    @patch("longriver.fetch_river_data")
    def test_skips_failed_source_when_other_sources_succeed(self, fetch: Mock) -> None:
        fetch.side_effect = [
            RuntimeError("bad source"),
            [{"rvnm": "长江干流", "stcd": "1", "stnm": "甲", "tm": 100}],
        ]

        data = fetch_all_river_data(["http://bad.test", "http://good.test"])

        self.assertEqual([station["stcd"] for station in data], ["1"])
        self.assertEqual(
            fetch.call_args_list,
            [call("http://bad.test"), call("http://good.test")],
        )

    @patch("longriver.fetch_river_data")
    def test_raises_when_all_sources_fail(self, fetch: Mock) -> None:
        fetch.side_effect = RuntimeError("bad source")

        with self.assertRaisesRegex(RuntimeError, "all configured sources"):
            fetch_all_river_data(["http://bad.test"])


class AppendCsvRecordTests(unittest.TestCase):
    def test_missing_optional_field_does_not_shift_columns(self) -> None:
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "station.csv"
            csv_path.write_text(
                "q,rvnm,stcd,stnm,tm,wptn,z\n",
                encoding="utf-8",
            )
            append_csv_record(
                csv_path,
                {
                    "rvnm": "长江干流",
                    "stcd": "60112200",
                    "stnm": "汉口",
                    "tm": 1781002800000,
                    "wptn": "4",
                    "z": "23.380",
                },
            )

            with csv_path.open(
                "r",
                encoding="utf-8",
                newline="",
            ) as source:
                row = next(csv.DictReader(source))

        self.assertEqual(row["q"], "")
        self.assertEqual(row["stcd"], "60112200")
        self.assertEqual(row["tm"], "1781002800000")


if __name__ == "__main__":
    unittest.main()
