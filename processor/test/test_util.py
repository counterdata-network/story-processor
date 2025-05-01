import unittest

import processor.util as util


class TestUtil(unittest.TestCase):
    def test_chunk(self):
        numbers = range(0, 1001)
        chunks = [c for c in util.chunks(numbers, 10)]
        for chunk in chunks[0:99]:
            assert len(chunk) == 10
        assert len(chunks[100]) == 1
        chunks = [c for c in util.chunks(numbers, 100)]
        assert len(chunks) == 11
        for chunk in chunks[0:9]:
            assert len(chunk) == 100
        assert len(chunks[10]) == 1

    def test_remove_duplicate_by_title_media_id(self):
        stories = [
            {"title": "Story 1", "media_id": "1"},
            {"title": "Story 2", "media_id": "2"},
            {"title": "Story 1", "media_id": "1"},  # Duplicate
            {"title": "Story 3", "media_id": "3"},
            {"title": "Story 2", "media_id": "2"},  # Duplicate
            {"title": "Story 4", "media_id": "couton2.com"},
            {"title": "Story 5", "media_id": "couton2.com"},
            {"title": "Story 4", "media_id": "couton2.com"},  # Duplicate
            {"title": "Story 27", "media_id": "couton2.com"},
            {"title": "Story 100", "media_name": "couton2.com"},
            {"title": "Story 100", "media_name": "couton2.com"},  # Duplicate
            {"title": "Story 102", "media_name": "couton2.com"},
        ]
        unique_stories = util.remove_duplicate_by_title_media_id(stories)
        assert len(unique_stories) == 8
        assert unique_stories[0]["title"] == "Story 1"
        assert unique_stories[1]["title"] == "Story 2"
        assert unique_stories[2]["title"] == "Story 3"
        assert unique_stories[3]["title"] == "Story 4"
        assert unique_stories[4]["title"] == "Story 5"
        assert unique_stories[5]["title"] == "Story 27"
        assert unique_stories[6]["title"] == "Story 100"
        assert unique_stories[7]["title"] == "Story 102"
