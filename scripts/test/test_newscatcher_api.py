import datetime as dt
import unittest

from scripts.newscatcher_api import search_stories


class TestSearchStories(unittest.TestCase):
    def test_search_stories(self):
        # create a test query
        q = '(("US election" OR "presidential election") AND ("Trump" OR "Republican" OR "Democrat" OR "Harris" OR "Kamala") AND ("vote" OR "voter turnout" OR "ballot" OR "debate" OR "interview"))'
        language = "en"
        countries = "US"
        start_date = dt.datetime(2024, 1, 1)
        end_date = dt.datetime(2024, 10, 1)

        # preform a real-time fetch
        results = search_stories(q, language, countries, start_date, end_date)

        # make sure we get an expected result
        self.assertIn("total_hits", results)
        self.assertIn("articles", results)
        self.assertGreater(
            len(results["articles"]), 0, "No articles found in response."
        )


if __name__ == "__main__":
    unittest.main()
