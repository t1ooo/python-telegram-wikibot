import unittest
from unittest.mock import MagicMock, patch
from wikipedia import exceptions
from wiki import (
    WikiException,
    prepare_query,
    get_lang_code,
    search,
    summary,
    suggest,
)


class WikiTestCase(unittest.TestCase):
    def test_validate_query(self):
        self.assertEqual(prepare_query(" 1 "), "1")
        self.assertRaisesRegex(WikiException, "Query is empty", prepare_query, "")
        self.assertRaisesRegex(WikiException, "Query is empty", prepare_query, "   ")

    def test_get_lang_code(self):
        self.assertEqual(get_lang_code("English"), "en")
        self.assertEqual(get_lang_code("en"), "en")
        self.assertEqual(get_lang_code("deutsch"), "de")
        self.assertEqual(get_lang_code("de"), "de")
        self.assertEqual(get_lang_code("bad_lang"), None)
        self.assertEqual(get_lang_code(""), None)

    @patch("wiki.wikipedia.search")
    def test_search(self, mock_search: MagicMock):
        return_value = ["result 1", "result 2"]
        
        mock_search.return_value = return_value
        self.assertEqual(search("query", "en"), return_value)
        
        mock_search.assert_called_once_with("query")

        mock_search.return_value = []
        self.assertRaisesRegex(
            WikiException, "Nothing was found for the query", search, "query", "en"
        )

    @patch("wiki.wikipedia.summary")
    def test_summary(self, mock_summary: MagicMock):
        return_value = "Summary"
        
        mock_summary.return_value = return_value
        self.assertEqual(summary("query", "en"), return_value)

        mock_summary.assert_called_once_with("query", auto_suggest=False)

        mock_summary.side_effect = exceptions.DisambiguationError("options", [])
        self.assertRaisesRegex(WikiException, "Maybe you mean", summary, "query", "en")

        mock_summary.side_effect = exceptions.PageError("title")
        self.assertRaisesRegex(WikiException, "Page with title", summary, "query", "en")

    @patch("wiki.wikipedia.suggest")
    def test_suggest(self, mock_suggest: MagicMock):
        return_value = "suggested query"
        
        mock_suggest.return_value = return_value
        self.assertEqual(suggest("query", "en"), return_value)
        
        mock_suggest.assert_called_once_with("query")

        mock_suggest.return_value = ""
        self.assertRaisesRegex(WikiException, "No suggestion was found", suggest, "query", "en")


if __name__ == "__main__":
    unittest.main()
