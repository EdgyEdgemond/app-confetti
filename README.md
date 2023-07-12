# Configuration Fetcher v0.3.0
[![image](https://img.shields.io/pypi/v/web_error.svg)](https://pypi.org/project/app_confetti/)
[![image](https://img.shields.io/pypi/l/web_error.svg)](https://pypi.org/project/app_confetti/)
[![image](https://img.shields.io/pypi/pyversions/web_error.svg)](https://pypi.org/project/app_confetti/)
![style](https://github.com/EdgyEdgemond/app_confetti/workflows/style/badge.svg)
![tests](https://github.com/EdgyEdgemond/app_confetti/workflows/tests/badge.svg)
[![codecov](https://codecov.io/gh/EdgyEdgemond/app_confetti/branch/master/graph/badge.svg)](https://codecov.io/gh/EdgyEdgemond/app-confetti)

Common code for interacting with dev environs, deployed environs with ENV vars
or for deployed AWS (optional extra) environs.

## Config class

```python
    from app_confetti import util

    @dataclasses.dataclass(frozen=True)
    class Config:
        required_key: str = util.env("REQUIRED_KEY")
        logging_level: str = util.env("LOGGING_LEVEL:INFO")
        sentry_dsn: int = util.env("SENTRY_DSN:__NONE__")
        debug: bool = util.env("DEBUG:__FALSE__")

        @property
        def logging_config(self):
            return {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "[%(asctime)s][%(name)s][%(levelname)s]: %(message)s",
                        "datefmt": "%Y-%m-%d %H:%M:%S",
                    },
                },
                "handlers": {
                    "default": {
                        "class": "logging.StreamHandler",
                        "level": self.logging_level,
                        "formatter": "default",
                    },
                    "sentry": {
                        "level": "ERROR",
                        "class": "raven.handlers.logging.SentryHandler",
                        "dsn": self.sentry_dsn,
                    },
                },
                "loggers": {
                    "": {
                        "handlers": ["default", "sentry"],
                        "level": self.logging_level,
                        "propagate": True,
                    },
                    "raven": {
                        "handlers": ["default"],
                        "level": "WARNING",
                        "propagate": True,
                    },
                },
            }
```
