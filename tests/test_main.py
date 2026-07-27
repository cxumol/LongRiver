import unittest

from longriver import parse_river_data


class ParseRiverDataTests(unittest.TestCase):
    def test_parses_sssq_array_with_flexible_whitespace(self):
        html = """
        <script>
            var  sssq = [
                {"rvnm": "长江干流", "stnm": "汉口", "tm": 1785139200000}
            ];
        </script>
        """

        self.assertEqual(
            parse_river_data(html),
            [{"rvnm": "长江干流", "stnm": "汉口", "tm": 1785139200000}],
        )

    def test_rejects_page_without_sssq_data(self):
        with self.assertRaisesRegex(ValueError, "does not contain"):
            parse_river_data("404")

    def test_rejects_empty_sssq_array(self):
        with self.assertRaisesRegex(ValueError, "contains no river data"):
            parse_river_data("<script>var sssq = [];</script>")


if __name__ == "__main__":
    unittest.main()
