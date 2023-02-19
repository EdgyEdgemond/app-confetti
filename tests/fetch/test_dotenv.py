import os
from unittest import mock

from app_confetti.fetch import dotenv


class TestFetchToEnv:
    def test_no_update_if_file_not_found(self, monkeypatch, tmp_path):
        monkeypatch.setattr(os, "environ", {})

        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=str(tmp_path)))

        dotenv.fetch_to_env()

        assert os.environ == {}

    def test_searches_from_cwd_for_env_file(self, monkeypatch, tmp_path):
        monkeypatch.setattr(os, "environ", {})

        start_path = tmp_path / "start" / "path"
        start_path.mkdir(exist_ok=True, parents=True)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=start_path))
        file_path = tmp_path / ".env"
        with file_path.open("w") as fd:
            fd.write(
                "VARIABLE=testing\n"
                "\n"  # blank line
                "# Comment\n"
                'ANOTHER="variable"\n'
                "                   \n",  # whitespace
            )

        dotenv.fetch_to_env()

        assert os.environ == {
            "VARIABLE": "testing",
            "ANOTHER": "variable",
        }

    def test_searches_ignores_comments(self, monkeypatch, tmp_path):
        monkeypatch.setattr(os, "environ", {})

        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=str(tmp_path)))
        file_path = tmp_path / ".env"
        with file_path.open("w") as fd:
            fd.write("# This is a comment\n")

        dotenv.fetch_to_env()

        assert os.environ == {}

    def test_searches_strips_whitespace_from_line(self, monkeypatch, tmp_path):
        monkeypatch.setattr(os, "environ", {})

        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=str(tmp_path)))
        file_path = tmp_path / ".env"
        with file_path.open("w") as fd:
            fd.write("   VARIABLE\t=\ttesting   \n")

        dotenv.fetch_to_env()
        assert os.environ == {"VARIABLE": "testing"}

    def test_searches_splits_on_equals_one_time(self, monkeypatch, tmp_path):
        monkeypatch.setattr(os, "environ", {})

        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=str(tmp_path)))
        file_path = tmp_path / ".env"
        with file_path.open("w") as fd:
            fd.write("VARIABLE=testing is = to something\n")

        dotenv.fetch_to_env()

        assert os.environ == {"VARIABLE": "testing is = to something"}
