class BaseConfig:
    """Configuration class.

    The `environ_config` library allows for its attributes to be retrieved from
    environment variables, the prefix for this class and the attribute name
    defines the variable name to be used, e.g. PREFIX_SENTRY_DSN for SENTRY_DSN.

    This class is generally used in settings.__init__.py to instantiate an object from
    the environment.

    Inheriting classes must implement:
        cls.LOGGING_LEVEL
        cls.SENTRY_DSN
        cls.ENV
    """

    @property
    def LOGGING(self):
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
                    "level": self.LOGGING_LEVEL,
                    "formatter": "default",
                },
                "sentry": {
                    "level": "ERROR",
                    "class": "raven.handlers.logging.SentryHandler",
                    "dsn": self.SENTRY_DSN,
                    "environment": self.ENV,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default", "sentry"],
                    "level": self.LOGGING_LEVEL,
                    "propagate": True,
                },
                "raven": {
                    "handlers": ["default"],
                    "level": "WARNING",
                    "propagate": True,
                },
            },
        }
