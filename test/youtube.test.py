import sys
import unittest

sys.path.append('../src')
from youtube import find_added_items
from youtube import find_missing_items
from youtube import find_renamed_items

class TestYoutubeDiff(unittest.TestCase):

    def setUp(self):
        self.old_items = [
            ["", "00000000000", "Item 0"],
            ["", "00000000001", "Item 1"],
            ["", "00000000002", "Item 2"],
            ["", "00000000003", "Item 3"],
            ["!", "00000000004", "Item 4"]
        ]
        self.new_items = {
            "00000000000": "Item 0 (New)",
            "00000000001": "Item 1",
            "00000000002": "Item 2",
            "00000000005": "Item 5"
        }

    def test_added_items(self):
        expected = [
            ("00000000005", "Item 5")
        ]
        actual = find_added_items(self.old_items, self.new_items)

        self.assertEqual(expected, actual)

    def test_added_items_empty(self):
        expected = [
            ("00000000000", "Item 0 (New)"),
            ("00000000001", "Item 1"),
            ("00000000002", "Item 2"),
            ("00000000005", "Item 5")
        ]
        actual = find_added_items([], self.new_items)

        self.assertEqual(expected, actual)

    def test_missing_items(self):
        expected = [
            ("00000000003", "Item 3")
        ]
        actual = find_missing_items(self.old_items, self.new_items)

        self.assertEqual(expected, actual)

    def test_missing_items_empty(self):
        expected = []
        actual = find_missing_items([], self.new_items)

        self.assertEqual(expected, actual)

    def test_renamed_items(self):
        expected = [
            ("00000000000", "Item 0", "Item 0 (New)"),
        ]
        actual = find_renamed_items(self.old_items, self.new_items)

        self.assertEqual(expected, actual)

    def test_renamed_items_empty(self):
        expected = []
        actual = find_renamed_items([], self.new_items)

        self.assertEqual(expected, actual)

if __name__=='__main__':
    unittest.main()
