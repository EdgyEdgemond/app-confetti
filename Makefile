install:
	pip install -e .

install-dev:
	pip install -e .[dev,test]

check-style:
	flake8

tests:
	pytest

tests-coverage:
	pytest --cov=app_config

isort:
	isort -y

patch_release:
	bumpversion patch

minor_release:
	bumpversion minor

major_release:
	bumpversion major
