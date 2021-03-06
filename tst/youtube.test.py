import os
import sys
import unittest

tst_dir = os.path.dirname(__file__)
src_dir = os.path.join(tst_dir, '../src')
sys.path.append(src_dir)

from youtube import find_added_items
from youtube import find_recovered_items
from youtube import find_missing_items
from youtube import find_renamed_items

class TestYoutubeDiff(unittest.TestCase):

    #
    # Setup
    #

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

    #
    # find_added_items
    #

    def test_added_items(self):
        expected = [
            ("00000000005", "Item 5")
        ]
        actual = find_added_items(self.old_items, self.new_items)

        self.assertEqual(expected, actual)

    def test_added_items_master(self):
        expected = [
            ["", "00000000005", "Item 5"],
            ["", "00000000000", "Item 0"],
            ["", "00000000001", "Item 1"],
            ["", "00000000002", "Item 2"],
            ["", "00000000003", "Item 3"],
            ["!", "00000000004", "Item 4"]
        ]
        actual = find_added_items(self.old_items, self.new_items)

        self.assertEqual(expected, self.old_items)

    def test_added_items_empty(self):
        expected = [
            ("00000000000", "Item 0 (New)"),
            ("00000000001", "Item 1"),
            ("00000000002", "Item 2"),
            ("00000000005", "Item 5")
        ]
        self.old_items = []
        actual = find_added_items(self.old_items, self.new_items)

        self.assertEqual(expected, actual)

    def test_added_items_empty_master(self):
        expected = [
            ["", "00000000000", "Item 0 (New)"],
            ["", "00000000001", "Item 1"],
            ["", "00000000002", "Item 2"],
            ["", "00000000005", "Item 5"]
        ]
        self.old_items = []
        actual = find_added_items(self.old_items, self.new_items)

        self.assertEqual(expected, self.old_items)

    #
    # find_recovered_items
    #

    def test_recovered_items(self):
        expected = [
            ("00000000001", "Item 1")
        ]
        self.old_items[1][0] = "!"
        actual = find_recovered_items(self.old_items, self.new_items)

        self.assertEqual(expected, actual)

    #
    # find_missing_items
    #

    def test_missing_items(self):
        expected = [
            ("00000000003", "Item 3")
        ]
        actual = find_missing_items(self.old_items, self.new_items)

        self.assertEqual(expected, actual)

    def test_missing_items_master(self):
        expected = [
            ["", "00000000000", "Item 0"],
            ["", "00000000001", "Item 1"],
            ["", "00000000002", "Item 2"],
            ["!", "00000000003", "Item 3"],
            ["!", "00000000004", "Item 4"]
        ]
        actual = find_missing_items(self.old_items, self.new_items)

        self.assertEqual(expected, self.old_items)

    def test_missing_items_empty(self):
        expected = []
        self.old_items = []
        actual = find_missing_items(self.old_items, self.new_items)

        self.assertEqual(expected, self.old_items)

    def test_missing_items_empty_master(self):
        expected = []
        self.old_items = []
        actual = find_missing_items(self.old_items, self.new_items)

        self.assertEqual(expected, actual)

    #
    # find_renamed_items
    #

    def test_renamed_items(self):
        expected = [
            ("00000000000", "Item 0", "Item 0 (New)"),
        ]
        actual = find_renamed_items(self.old_items, self.new_items)

        self.assertEqual(expected, actual)

    def test_renamed_items_master(self):
        expected = [
            ["", "00000000000", "Item 0"],
            ["", "00000000001", "Item 1"],
            ["", "00000000002", "Item 2"],
            ["", "00000000003", "Item 3"],
            ["!", "00000000004", "Item 4"]
        ]
        actual = find_renamed_items(self.old_items, self.new_items)

        self.assertEqual(expected, self.old_items)

    def test_renamed_items_empty(self):
        expected = []
        self.old_items = []
        actual = find_renamed_items(self.old_items, self.new_items)

        self.assertEqual(expected, actual)

    def test_renamed_items_empty_master(self):
        expected = []
        self.old_items = []
        actual = find_renamed_items(self.old_items, self.new_items)

        self.assertEqual(expected, self.old_items)

if __name__=='__main__':
    unittest.main()
