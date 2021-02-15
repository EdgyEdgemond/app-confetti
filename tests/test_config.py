import dataclasses

import pytest

from app_confetti import util
from app_confetti.config import BaseConfig


@dataclasses.dataclass(frozen=True)
class MockConfig(BaseConfig):
    var_1: str = util.env("PREFIX_VAR_1")
    var_2: str = util.env("PREFIX_VAR_2")

    debug: bool = util.env("PREFIX_DEBUG:False", util.str_to_literal)
    env: str = util.env("PREFIX_ENV:dev")


class TestBaseConfig:
    def test_env_not_set(self, monkeypatch):
        with pytest.raises(KeyError):
            MockConfig()

    def test_defaults(self, monkeypatch):
        monkeypatch.setenv("PREFIX_VAR_1", "value_1")
        monkeypatch.setenv("PREFIX_VAR_2", "value_2")
        c = MockConfig()
        assert c.debug is False
        assert c.logging_level == "INFO"
        assert c.sentry_dsn is None

    def test_overrides(self, monkeypatch):
        monkeypatch.setenv("PREFIX_VAR_1", "value_1")
        monkeypatch.setenv("PREFIX_VAR_2", "value_2")
        monkeypatch.setenv("PREFIX_ENV", "env")
        monkeypatch.setenv("DEBUG", "True")
        monkeypatch.setenv("LOGGING_LEVEL", "DEBUG")
        monkeypatch.setenv("SENTRY_DSN", "sentry-dsn")

        settings = MockConfig()

        assert settings.debug is False
        assert settings.logging_level == "DEBUG"
        assert settings.sentry_dsn == "sentry-dsn"
        assert settings.logging_config == {
            "disable_existing_loggers": False,
            "formatters": {"default": {"datefmt": "%Y-%m-%d %H:%M:%S",
                                       "format": "[%(asctime)s][%(name)s][%(levelname)s]: "
                                                 "%(message)s"}},
            "handlers": {"default": {"class": "logging.StreamHandler",
                                     "formatter": "default",
                                     "level": "DEBUG"},
                         "sentry": {"class": "raven.handlers.logging.SentryHandler",
                                    "dsn": "sentry-dsn",
                                    "environment": "env",
                                    "level": "ERROR"}},
            "loggers": {"": {"handlers": ["default",
                                          "sentry"],
                             "level": "DEBUG",
                             "propagate": True},
                        "raven": {"handlers": ["default"],
                                  "level": "WARNING",
                                  "propagate": True}},
            "version": 1,
        }
