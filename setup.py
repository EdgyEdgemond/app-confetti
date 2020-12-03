import setuptools

import clt_util


packages = (
    "boto3",
    "ec2-metadata",
    "environ-config",
    "redis",
    "sqlalchemy",
    "slackclient==1.3.0",
)

setuptools.setup(
    name="clt_util",
    version=clt_util.VERSION,
    packages=setuptools.find_packages(include=("clt_util*",)),
    url="",
    license="",
    author="Daniel Edgy Edgecombe",
    author_email="edgy.edgemond@gmail.com",
    description="",
    install_requires=packages,
    extras_require={
        "test": (
            "freezegun",
            "pytest > 3.3.2",
            "pytest-asyncio",
            "pytest-benchmark",
            "pytest-cov",
            "pytest-env",
            "pytest-xdist",
            "pytest-random-order",
        ),
        "dev": (
            "flake8",
            "flake8-commas",
            "flake8-isort",
            "flake8-quotes",
            "isort<5.0.0",
            "bump2version",
        ),
    },
)
