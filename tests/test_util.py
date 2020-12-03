import os
from decimal import Decimal
from unittest import mock

import environ
import pytest
from botocore.exceptions import ClientError

from clt_util import constants
from clt_util import util
from clt_util.settings.config import BaseConfig


@pytest.fixture
def env_file_factory(monkeypatch, tmpdir):
    def factory(env_name):
        _dir = str(tmpdir)
        start_path = os.path.join(_dir, "start", "path")
        os.makedirs(start_path, exist_ok=True)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=_dir))
        file_path = os.path.join(_dir, "{}.env".format(env_name))
        with open(file_path, "w") as fd:
            fd.write(
                'PREFIX_VAR_1="value_1"\n'
                "\n"  # blank line
                "# Comment\n"
                'PREFIX_VAR_2="value_2"\n'
                "                   \n",  # whitespace
            )
        return start_path
    return factory


@environ.config(prefix="PREFIX")
class MockConfig(BaseConfig):
    VAR_1 = environ.var()
    VAR_2 = environ.var()

    DEBUG = environ.var(False, converter=bool)
    ENV = environ.var("dev")

    SENTRY_DSN = environ.var(None)
    LOGGING_LEVEL = environ.var("INFO")


class TestBaseConfig:
    def test_defaults(self, monkeypatch, env_file_factory):
        start_path = env_file_factory("env")
        monkeypatch.setenv("MT4_ENV", "env")
        settings = util.get_settings(MockConfig, start_path)
        assert settings.DEBUG is False
        assert settings.LOGGING_LEVEL == "INFO"
        assert settings.SENTRY_DSN is None

    def test_overrides(self, monkeypatch, env_file_factory):
        start_path = env_file_factory("env")
        monkeypatch.setenv("MT4_ENV", "env")
        monkeypatch.setenv("PREFIX_DEBUG", "1")
        monkeypatch.setenv("PREFIX_LOGGING_LEVEL", "DEBUG")
        monkeypatch.setenv("PREFIX_SENTRY_DSN", "sentry-dsn")
        settings = util.get_settings(MockConfig, start_path)
        assert settings.DEBUG is True
        assert settings.LOGGING_LEVEL == "DEBUG"
        assert settings.SENTRY_DSN == "sentry-dsn"
        assert settings.LOGGING == {
            "disable_existing_loggers": False,
            "formatters": {"default": {"datefmt": "%Y-%m-%d %H:%M:%S",
                                       "format": "[%(asctime)s][%(name)s][%(levelname)s]: "
                                                 "%(message)s"}},
            "handlers": {"default": {"class": "logging.StreamHandler",
                                     "formatter": "default",
                                     "level": "DEBUG"},
                         "sentry": {"class": "raven.handlers.logging.SentryHandler",
                                    "dsn": "sentry-dsn",
                                    "environment": "dev",
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


class TestGetSettings:

    def test_get_settings_in_local_environment(self, monkeypatch, env_file_factory):
        env_name = "my_environment"
        start_path = env_file_factory(env_name)
        monkeypatch.setenv("MT4_ENV", env_name)
        settings = util.get_settings(MockConfig, start_path)
        assert settings.VAR_1 == "value_1"
        assert settings.VAR_2 == "value_2"

    def test_get_settings_env_vars_override_secrets(self, monkeypatch, env_file_factory):
        env_name = "my_environment"
        start_path = env_file_factory(env_name)
        monkeypatch.setenv("MT4_ENV", env_name)
        monkeypatch.setenv("PREFIX_VAR_1", "value from environment")
        settings = util.get_settings(MockConfig, start_path)
        assert settings.VAR_1 == "value from environment"
        assert settings.VAR_2 == "value_2"

    def test_get_secrets_from_kms(self, monkeypatch):
        monkeypatch.setenv("MT4_ENV", "")
        monkeypatch.setattr(util, "get_secret", mock.Mock(return_value={
            "PREFIX_VAR_1": "var1",
            "PREFIX_VAR_2": "var2",
        }))

        settings = util.get_settings(MockConfig, "")

        assert util.get_secret.call_args == mock.call("settings")

        assert settings.VAR_1 == "var1"
        assert settings.VAR_2 == "var2"

    def test_get_secrets_from_kms_custom_key(self, monkeypatch):
        monkeypatch.setenv("MT4_ENV", "")
        monkeypatch.setattr(util, "get_secret", mock.Mock(return_value={
            "PREFIX_VAR_1": "var1",
            "PREFIX_VAR_2": "var2",
        }))

        settings = util.get_settings(MockConfig, "", "mysettings")

        assert util.get_secret.call_args == mock.call("mysettings")

        assert settings.VAR_1 == "var1"
        assert settings.VAR_2 == "var2"


class TestGetSecret:
    def test_ec2_metadata_region_used(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.return_value = {"SecretString": "{}"}
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": []}]}],
        }

        monkeypatch.setattr(util.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(util, "ec2_metadata", mock.Mock(region="us-east-2"))

        util.get_secret()

        assert mock_session.client.call_args_list == [
            mock.call(
                service_name="ec2",
                region_name="us-east-2",
            ),
            mock.call(
                service_name="secretsmanager",
                region_name="us-east-2",
            ),
        ]

    def test_default_secret_fetched(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.return_value = {"SecretString": "{}"}
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": []}]}],
        }

        monkeypatch.setattr(util.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(util, "ec2_metadata", mock.Mock(region="us-east-2"))

        util.get_secret()

        assert mock_session.client.return_value.get_secret_value.call_args == mock.call(SecretId="settings")

    def test_specified_secret_fetched(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.return_value = {"SecretString": "{}"}
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": []}]}],
        }

        monkeypatch.setattr(util.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(util, "ec2_metadata", mock.Mock(region="us-east-2"))

        util.get_secret("mysecret")

        assert mock_session.client.return_value.get_secret_value.call_args == mock.call(SecretId="mysecret")

    def test_tag_data_fetched(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.return_value = {"SecretString": "{}"}
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": []}]}],
        }

        monkeypatch.setattr(util.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(util, "ec2_metadata", mock.Mock(region="us-east-2", instance_id="instance-id"))

        util.get_secret()

        assert mock_session.client.return_value.describe_instances.call_args == mock.call(InstanceIds=["instance-id"])

    def test_settings_returned(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.return_value = {
            "SecretString": '{"a": True, "b": 10, "c": "str"}',
        }
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": []}]}],
        }

        monkeypatch.setattr(util.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(util, "ec2_metadata", mock.Mock(region="us-east-2"))

        secrets = util.get_secret()

        assert secrets == {"a": True, "b": 10, "c": "str"}

    def test_tag_data_overrides_secrets(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.return_value = {
            "SecretString": '{"a": True, "b": 10, "c": "str", "MT4_HOST": "secret"}',
        }
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": [{"Key": "MT4_HOST", "Value": "tag"}]}]}],
        }

        monkeypatch.setattr(util.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(util, "ec2_metadata", mock.Mock(region="us-east-2"))

        secrets = util.get_secret()

        assert secrets == {"a": True, "b": 10, "c": "str", "MT4_HOST": "tag"}

    def test_non_prefix_tags_ignored(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.return_value = {
            "SecretString": '{"a": True, "b": 10, "c": "str"}',
        }
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": [{"Key": "Name", "Value": "Instance"}]}]}],
        }

        monkeypatch.setattr(util.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(util, "ec2_metadata", mock.Mock(region="us-east-2"))

        secrets = util.get_secret()

        assert secrets == {"a": True, "b": 10, "c": "str"}

    def test_client_error_reraised(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.side_effect = ClientError({"Error": {}}, "operation")
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": []}]}],
        }

        monkeypatch.setattr(util.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(util, "ec2_metadata", mock.Mock(region="us-east-2"))

        with pytest.raises(ClientError):
            util.get_secret()


class TestStrToLiteral:

    @pytest.mark.parametrize("value", [{"a", "b"}, {"a": "b"}, [1, 2, 3], True, None, 5, 6.0, "value"])
    def test_non_string_literals_passed_through(self, value):
        assert util.str_to_literal(value) == value

    @pytest.mark.parametrize("value, expected", [
        ("{'a', 'b'}", {"a", "b"}),
        ("{'a': 'b'}", {"a": "b"}),
        ("[1, 2, 3]", [1, 2, 3]),
        ("True", True),
        ("None", None),
        ("5", 5),
        ("6.0", 6.0),
    ])
    def test_strings_return_literals(self, value, expected):
        assert util.str_to_literal(value) == expected


class TestFindEnvFile:

    def test_return_empty_dict_if_start_path_is_below_cwd(self, monkeypatch, tmpdir):
        tmpdir = str(tmpdir)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=tmpdir))

        assert util.find_env_file("test", os.path.dirname(tmpdir)) == {}

    def test_uses_directory_if_start_path_is_file(self, monkeypatch, tmpdir):
        tmpdir = str(tmpdir)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=tmpdir))
        file_path = os.path.join(tmpdir, "file")
        with open(file_path, "w") as fd:
            fd.write("test")

        assert util.find_env_file("test", file_path) == {}

    def test_searches_from_start_path_to_cwd_for_env_file(self, monkeypatch, tmpdir):
        tmpdir = str(tmpdir)
        start_path = os.path.join(str(tmpdir), "start", "path")
        os.makedirs(start_path, exist_ok=True)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=tmpdir))
        file_path = os.path.join(tmpdir, "test.env")
        with open(file_path, "w") as fd:
            fd.write(
                "VARIABLE=testing\n"
                "\n"  # blank line
                "# Comment\n"
                'ANOTHER="variable"\n'
                "                   \n",  # whitespace
            )

        assert util.find_env_file("test.env", start_path) == dict(VARIABLE="testing", ANOTHER="variable")

    def test_searches_replaces_double_quotes(self, monkeypatch, tmpdir):

        tmpdir = str(tmpdir)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=tmpdir))
        file_path = os.path.join(tmpdir, "test.env")
        with open(file_path, "w") as fd:
            fd.write('VARIABLE=test"ing\n')

        assert util.find_env_file("test.env", file_path) == {"VARIABLE": "testing"}

    def test_searches_ignores_comments(self, monkeypatch, tmpdir):

        tmpdir = str(tmpdir)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=tmpdir))
        file_path = os.path.join(tmpdir, "test.env")
        with open(file_path, "w") as fd:
            fd.write("# This is a comment\n")

        assert util.find_env_file("test.env", file_path) == {}

    def test_searches_strips_whitespace_from_line(self, monkeypatch, tmpdir):

        tmpdir = str(tmpdir)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=tmpdir))
        file_path = os.path.join(tmpdir, "test.env")
        with open(file_path, "w") as fd:
            fd.write("   VARIABLE\t=\ttesting   \n")

        assert util.find_env_file("test.env", file_path) == {"VARIABLE\t": "\ttesting"}

    def test_searches_splits_on_equals_one_time(self, monkeypatch, tmpdir):

        tmpdir = str(tmpdir)
        monkeypatch.setattr(os, "getcwd", mock.Mock(return_value=tmpdir))
        file_path = os.path.join(tmpdir, "test.env")
        with open(file_path, "w") as fd:
            fd.write("VARIABLE=testing is = to something\n")

        assert util.find_env_file("test.env", file_path) == {"VARIABLE": "testing is = to something"}


class TestPipCalculator:
    def test_buy(self):
        assert util.pnl_pip_calculator(
            "EURAUD",
            constants.OrderType.BUY,
            Decimal("10.0"), Decimal("5.0"), Decimal("6.0"), Decimal("4.0"),
        ) == {
            "pnl_pips": -50000.0,
            "sl_pips": 60000.0,
            "tp_pips": -40000.0,
        }

    def test_sell(self):
        assert util.pnl_pip_calculator(
            "EURAUD",
            constants.OrderType.SELL,
            Decimal("10.0"), Decimal("5.0"), Decimal("6.0"), Decimal("4.0"),
        ) == {
            "pnl_pips": 50000.0,
            "sl_pips": -60000.0,
            "tp_pips": 40000.0,
        }

    def test_buy_convert(self):
        assert util.pnl_pip_calculator(
            "AUDJPY",
            constants.OrderType.BUY,
            Decimal("10.0"), Decimal("5.0"), Decimal("6.0"), Decimal("4.0"),
        ) == {
            "pnl_pips": -500.0,
            "sl_pips": 600.0,
            "tp_pips": -400.0,
        }

    def test_sell_convert(self):
        assert util.pnl_pip_calculator(
            "JPYAUD",
            constants.OrderType.SELL,
            Decimal("10.0"), Decimal("5.0"), Decimal("6.0"), Decimal("4.0"),
        ) == {
            "pnl_pips": 500.0,
            "sl_pips": -600.0,
            "tp_pips": 400.0,
        }
