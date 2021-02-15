import os
from unittest import mock

from app_confetti.fetch import file


class TestFetchToEnv:

    def test_no_update_if_file_not_found(self, monkeypatch, tmpdir):
        monkeypatch.setattr(os, "environ", {})

        tmpdir = str(tmpdir)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=tmpdir))

        file.fetch_to_env()

        assert os.environ == {}

    def test_searches_from_cwd_for_env_file(self, monkeypatch, tmpdir):
        monkeypatch.setattr(os, "environ", {})

        tmpdir = str(tmpdir)
        start_path = os.path.join(str(tmpdir), "start", "path")
        os.makedirs(start_path, exist_ok=True)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=start_path))
        file_path = os.path.join(tmpdir, ".env")
        with open(file_path, "w") as fd:
            fd.write(
                "VARIABLE=testing\n"
                "\n"  # blank line
                "# Comment\n"
                'ANOTHER="variable"\n'
                "                   \n",  # whitespace
            )

        file.fetch_to_env()

        assert os.environ == {
            "VARIABLE": "testing",
            "ANOTHER": "variable",
        }

    def test_searches_ignores_comments(self, monkeypatch, tmpdir):
        monkeypatch.setattr(os, "environ", {})

        tmpdir = str(tmpdir)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=tmpdir))
        file_path = os.path.join(tmpdir, ".env")
        with open(file_path, "w") as fd:
            fd.write("# This is a comment\n")

        file.fetch_to_env()

        assert os.environ == {}

    def test_searches_strips_whitespace_from_line(self, monkeypatch, tmpdir):
        monkeypatch.setattr(os, "environ", {})

        tmpdir = str(tmpdir)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=tmpdir))
        file_path = os.path.join(tmpdir, ".env")
        with open(file_path, "w") as fd:
            fd.write("   VARIABLE\t=\ttesting   \n")

        file.fetch_to_env()
        assert os.environ == {"VARIABLE": "testing"}

    def test_searches_splits_on_equals_one_time(self, monkeypatch, tmpdir):
        monkeypatch.setattr(os, "environ", {})

        tmpdir = str(tmpdir)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=tmpdir))
        file_path = os.path.join(tmpdir, ".env")
        with open(file_path, "w") as fd:
            fd.write("VARIABLE=testing is = to something\n")

        file.fetch_to_env()

        assert os.environ == {"VARIABLE": "testing is = to something"}
