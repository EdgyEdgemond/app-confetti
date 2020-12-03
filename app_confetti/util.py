import ast
import os

import boto3
import environ
from botocore.exceptions import ClientError
from ec2_metadata import ec2_metadata


def find_env_file(env_file_name, start_path):
    """Searches for an env file recursively up the tree until the cwd.

    The env var should contain standard VARIABLE="VALUE" lines. Lines prefixed
    with a # are ignored as comments. White space is ignored.

    :param env_file_name: Name of the env file to search for.
    :param start_path: Path to start the search from.
    :returns: A dict with the parsed env vars from the file.
    """
    if os.path.isfile(start_path):
        start_path = os.path.dirname(start_path)

    if start_path == os.path.dirname(os.getcwd()):
        return {}
    elif env_file_name in os.listdir(start_path):
        with open(os.path.join(start_path, env_file_name)) as fd:
            file_vars = {}
            for line in fd:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    file_vars[key] = value.replace('"', "")
        return file_vars
    else:
        return find_env_file(env_file_name, os.path.dirname(start_path))


def str_to_literal(val):
    """
    Construct an object literal from a str, but leave other types untouched
    """
    if isinstance(val, str):
        try:
            return ast.literal_eval(val)
        except ValueError:
            pass
    return val


def get_secret(secret_name="settings"):
    """
    If you need more information about configurations or implementing the sample code, visit the AWS docs:
    https://aws.amazon.com/developers/getting-started/python/
    """

    region_name = ec2_metadata.region
    instance_id = ec2_metadata.instance_id

    session = boto3.session.Session()

    # Create an EC2 client
    client = session.client(
        service_name="ec2",
        region_name=region_name,
    )

    response = client.describe_instances(InstanceIds=[instance_id])
    tags = response["Reservations"][0]["Instances"][0]["Tags"]
    tag_data = {
        tag["Key"]: tag["Value"]
        for tag in tags
        if tag["Key"].startswith("MT4")
    }

    # Create a Secrets Manager client
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name,
    )

    # In this sample we only handle the specific exceptions for the "GetSecretValue" API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    secrets = {}
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name,
        )
    except ClientError as e:
        """
        e.response["Error"]["Code"] == "DecryptionFailureException":
            # Secrets Manager can"t decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
        e.response["Error"]["Code"] == "InternalServiceErrorException":
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
        e.response["Error"]["Code"] == "InvalidParameterException":
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
        e.response["Error"]["Code"] == "InvalidRequestException":
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
        e.response["Error"]["Code"] == "ResourceNotFoundException":
            # We can"t find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
        """
        raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        secret = get_secret_value_response["SecretString"]
        secrets = str_to_literal(secret)

    secrets.update(tag_data)
    return secrets


def get_settings(config_cls, start_path, secret_key="settings"):
    """
    A wrapper around aws.SecresManager which acts as a factory for creating instances
    of settings classes (config_cls). It is assumed config_cls is wrapped with @environ.config. If the MT4_ENV
    environment variable is set, settings defined in a local .env file are used instead. The typical usage is to
    export MT4_ENV=dev in your .bashrc or .bash_profile, and override with pytest-env in setup.cfg for testing
    environments, and to create corresponding dev.env and test.env files.

    :param config_cls: a class decorated with @environ.config
    :param start_path: Path to start the search from if loading from an .env file. Typically __file__ of calling context
    :return: instance of config_class
    """
    env = os.getenv("MT4_ENV")

    if env:
        _settings_dict = find_env_file(env_file_name="{0}.env".format(env), start_path=start_path)
    else:
        _settings_dict = get_secret(secret_key)

    _settings_dict.update(os.environ)  # include any OS env vars
    settings = environ.to_config(config_cls, _settings_dict)

    return settings
