import ast
import os

import boto3
from botocore.exceptions import ClientError
from ec2_metadata import ec2_metadata


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


def get_region():
    return ec2_metadata.region


def fetch_to_env(secret_name="settings"):
    """
    If you need more information about configurations or implementing the sample code, visit the AWS docs:
    https://aws.amazon.com/developers/getting-started/python/
    """

    region_name = get_region()
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
    os.environ.update({k: str(v) for k, v in secrets.items()})
