import dataclasses

import pytest

from app_confetti import util


def optional_str(v):
    return v if v != "None" else None


def str_to_bool(v):
    return v.lower() in ["true", "t", "1"]


@dataclasses.dataclass(frozen=True)
class MockConfig():
    var_1: str = util.env("PREFIX_VAR_1")
    var_2: str = util.env("PREFIX_VAR_2:")

    logging_level: str = util.env("LOGGING_LEVEL:INFO")
    sentry_dsn: str = util.env("SENTRY_DSN:None", optional_str)
    env: str = util.env("ENV:test")

    debug: bool = util.env("DEBUG:False", str_to_bool)


class TestBaseConfig:
    def test_env_not_set(self, monkeypatch):
        with pytest.raises(KeyError):
            MockConfig()

    def test_defaults(self, monkeypatch):
        monkeypatch.setenv("PREFIX_VAR_1", "value_1")
        c = MockConfig()
        assert c.debug is False
        assert c.logging_level == "INFO"
        assert c.env == "test"
        assert c.sentry_dsn is None
        assert c.var_2 == ""

    def test_overrides(self, monkeypatch):
        monkeypatch.setenv("PREFIX_VAR_1", "value_1")
        monkeypatch.setenv("PREFIX_VAR_2", "value_2")
        monkeypatch.setenv("PREFIX_ENV", "env")
        monkeypatch.setenv("DEBUG", "True")
        monkeypatch.setenv("LOGGING_LEVEL", "DEBUG")
        monkeypatch.setenv("SENTRY_DSN", "sentry-dsn")

        settings = MockConfig()

        assert settings.debug is True
        assert settings.logging_level == "DEBUG"
        assert settings.sentry_dsn == "sentry-dsn"
