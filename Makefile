install:
	poetry install --no-dev --extras=aws

install-dev:
	poetry install --extras=aws

check-style:
	flake8 app_confetti tests

tests:
	pytest

tests-coverage:
	pytest --cov=app_confetti

isort:
	isort -y

release:
	changelog-gen
