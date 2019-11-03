import sys
import unittest

sys.path.append('../src')
from youtube import find_added_items
from youtube import find_missing_items
from youtube import find_renamed_items

class TestYoutubeDiff(unittest.TestCase):

    def setUp(self):
        print("setup")

    def test_added_items(self):
        print("add test")

    def test_missing_items(self):
        print("missing test")

    def test_renamed_items(self):
        print("renamed test")

if __name__=='__main__':
    unittest.main()
