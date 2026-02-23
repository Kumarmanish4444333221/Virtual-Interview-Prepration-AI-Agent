"""Tests for the interview history module."""
import os
import tempfile
import unittest
from unittest import mock

import modules.history as hist_mod


class TestHistory(unittest.TestCase):
    """Unit tests for modules.history."""

    def setUp(self):
        self.db_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.db_dir, "interviews.db")
        self._dir_patch = mock.patch.object(hist_mod, "DB_DIR", self.db_dir)
        self._path_patch = mock.patch.object(hist_mod, "DB_PATH", self.db_path)
        self._dir_patch.start()
        self._path_patch.start()
        hist_mod.init_db()

    def tearDown(self):
        self._dir_patch.stop()
        self._path_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_retrieve(self):
        iid = hist_mod.save_interview(
            username="alice",
            company="Google",
            role="SWE",
            experience_level="Senior",
            fit_score=85,
            num_questions=7,
            summary="Good",
            transcript=[("Interviewer", "Q1"), ("Candidate", "A1")],
        )
        self.assertGreater(iid, 0)
        history = hist_mod.get_user_interviews("alice")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["company"], "Google")

    def test_user_isolation(self):
        hist_mod.save_interview("alice", "Google", "SWE", "Senior", 80, 5, "ok")
        hist_mod.save_interview("bob", "Amazon", "DE", "Junior", 70, 5, "ok")
        self.assertEqual(len(hist_mod.get_user_interviews("alice")), 1)
        self.assertEqual(len(hist_mod.get_user_interviews("bob")), 1)

    def test_get_interview_detail(self):
        iid = hist_mod.save_interview(
            "alice", "Meta", "ML", "Mid", 90, 10, "Great",
            transcript=[("I", "Q"), ("C", "A")],
        )
        detail = hist_mod.get_interview_detail(iid, "alice")
        self.assertIsNotNone(detail)
        self.assertEqual(detail["transcript"], [["I", "Q"], ["C", "A"]])

    def test_get_interview_detail_wrong_user(self):
        iid = hist_mod.save_interview("alice", "Meta", "ML", "Mid", 90, 10, "ok")
        self.assertIsNone(hist_mod.get_interview_detail(iid, "bob"))

    def test_stats_empty(self):
        stats = hist_mod.get_user_stats("nobody")
        self.assertEqual(stats["total_interviews"], 0)
        self.assertEqual(stats["avg_score"], 0)

    def test_stats_aggregate(self):
        hist_mod.save_interview("alice", "Google", "SWE", "Sr", 80, 5, "ok")
        hist_mod.save_interview("alice", "Amazon", "SWE", "Sr", 90, 5, "ok")
        stats = hist_mod.get_user_stats("alice")
        self.assertEqual(stats["total_interviews"], 2)
        self.assertEqual(stats["avg_score"], 85.0)
        self.assertEqual(stats["best_score"], 90)
        self.assertEqual(stats["companies_practiced"], 2)

    def test_ordering(self):
        hist_mod.save_interview("alice", "Google", "SWE", "Sr", 80, 5, "first")
        hist_mod.save_interview("alice", "Amazon", "SWE", "Sr", 90, 5, "second")
        history = hist_mod.get_user_interviews("alice")
        # Most recent first
        self.assertEqual(history[0]["company"], "Amazon")

    def test_limit(self):
        for i in range(5):
            hist_mod.save_interview("alice", f"Co{i}", "SWE", "Sr", 80, 5, "ok")
        self.assertEqual(len(hist_mod.get_user_interviews("alice", limit=3)), 3)


if __name__ == "__main__":
    unittest.main()
