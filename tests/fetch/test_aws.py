from unittest import mock

import pytest
from botocore.exceptions import ClientError

from app_confetti.fetch import aws


class TestStrToLiteral:

    @pytest.mark.parametrize("value", [{"a", "b"}, {"a": "b"}, [1, 2, 3], True, None, 5, 6.0, "value"])
    def test_non_string_literals_passed_through(self, value):
        assert aws.str_to_literal(value) == value

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
        assert aws.str_to_literal(value) == expected


class TestFetchToEnv:
    def test_ec2_metadata_region_used(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.return_value = {"SecretString": "{}"}
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": []}]}],
        }

        monkeypatch.setattr(aws.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(aws, "ec2_metadata", mock.Mock(region="us-east-2"))

        aws.fetch_to_env()

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

        monkeypatch.setattr(aws.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(aws, "ec2_metadata", mock.Mock(region="us-east-2"))

        aws.fetch_to_env()

        assert mock_session.client.return_value.get_secret_value.call_args == mock.call(SecretId="settings")

    def test_specified_secret_fetched(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.return_value = {"SecretString": "{}"}
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": []}]}],
        }

        monkeypatch.setattr(aws.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(aws, "ec2_metadata", mock.Mock(region="us-east-2"))

        aws.fetch_to_env("mysecret")

        assert mock_session.client.return_value.get_secret_value.call_args == mock.call(SecretId="mysecret")

    def test_tag_data_fetched(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.return_value = {"SecretString": "{}"}
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": []}]}],
        }

        monkeypatch.setattr(aws.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(aws, "ec2_metadata", mock.Mock(region="us-east-2", instance_id="instance-id"))

        aws.fetch_to_env()

        assert mock_session.client.return_value.describe_instances.call_args == mock.call(InstanceIds=["instance-id"])

    def test_settings_added_to_environ(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.return_value = {
            "SecretString": '{"a": True, "b": 10, "c": "str"}',
        }
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": []}]}],
        }

        monkeypatch.setattr(aws.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(aws, "ec2_metadata", mock.Mock(region="us-east-2"))
        monkeypatch.setattr(aws.os.environ, "update", mock.Mock())

        aws.fetch_to_env()

        assert aws.os.environ.update.call_args == mock.call(
            {"a": "True", "b": "10", "c": "str"},
        )

    def test_tag_data_overrides_secrets(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.return_value = {
            "SecretString": '{"a": True, "b": 10, "c": "str", "HOST": "secret"}',
        }
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": [{"Key": "HOST", "Value": "tag"}]}]}],
        }

        monkeypatch.setattr(aws.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(aws, "ec2_metadata", mock.Mock(region="us-east-2"))
        monkeypatch.setattr(aws.os, "environ", {})

        aws.fetch_to_env()

        assert aws.os.environ == {
            "a": "True", "b": "10", "c": "str", "HOST": "tag",
        }

    def test_client_error_reraised(self, monkeypatch):
        mock_session = mock.Mock()
        mock_session.client.return_value.get_secret_value.side_effect = ClientError({"Error": {}}, "operation")
        mock_session.client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": []}]}],
        }

        monkeypatch.setattr(aws.boto3.session, "Session", mock.Mock(return_value=mock_session))
        monkeypatch.setattr(aws, "ec2_metadata", mock.Mock(region="us-east-2"))

        with pytest.raises(ClientError):
            aws.fetch_to_env()
