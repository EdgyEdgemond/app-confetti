import dataclasses

from app_confetti import util


@dataclasses.dataclass(frozen=True)
class BaseConfig:
    """Configuration class.

    The `env` util function allows for attributes to be retrieved from environment variables.

    Inheriting classes can override:
        logging_level: str
        sentry_dsn: str
        env: str
    """

    logging_level: str = util.env("LOGGING_LEVEL:INFO")
    sentry_dsn: int = util.env("SENTRY_DSN:None", util.str_to_literal)
    env: int = util.env("ENV:None", util.str_to_literal)

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
                    "environment": self.env,
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
