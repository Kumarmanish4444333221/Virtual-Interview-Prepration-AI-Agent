"""Tests for the authentication module."""
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

import modules.auth as auth_mod


class TestAuth(unittest.TestCase):
    """Unit tests for modules.auth."""

    def setUp(self):
        """Create a fresh database for each test."""
        self.db_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.db_dir, "users.db")
        # Patch the module-level constants
        self._dir_patch = mock.patch.object(auth_mod, "DB_DIR", self.db_dir)
        self._path_patch = mock.patch.object(auth_mod, "DB_PATH", self.db_path)
        self._dir_patch.start()
        self._path_patch.start()
        auth_mod.init_db()

    def tearDown(self):
        self._dir_patch.stop()
        self._path_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_register_and_authenticate(self):
        self.assertTrue(auth_mod.register_user("alice", "secret123"))
        user = auth_mod.authenticate_user("alice", "secret123")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "alice")

    def test_register_duplicate(self):
        self.assertTrue(auth_mod.register_user("bob", "pass"))
        self.assertFalse(auth_mod.register_user("bob", "pass"))

    def test_authenticate_wrong_password(self):
        auth_mod.register_user("carol", "right")
        self.assertIsNone(auth_mod.authenticate_user("carol", "wrong"))

    def test_authenticate_unknown_user(self):
        self.assertIsNone(auth_mod.authenticate_user("nobody", "pass"))

    def test_user_exists(self):
        self.assertFalse(auth_mod.user_exists("dave"))
        auth_mod.register_user("dave", "pw")
        self.assertTrue(auth_mod.user_exists("dave"))

    def test_display_name_default(self):
        auth_mod.register_user("eve", "pw")
        user = auth_mod.authenticate_user("eve", "pw")
        self.assertEqual(user["display_name"], "eve")

    def test_display_name_custom(self):
        auth_mod.register_user("frank", "pw", display_name="Frank Smith")
        user = auth_mod.authenticate_user("frank", "pw")
        self.assertEqual(user["display_name"], "Frank Smith")


if __name__ == "__main__":
    unittest.main()
