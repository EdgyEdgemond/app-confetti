install:
	poetry install --no-dev --extras=aws

install-dev:
	poetry install --extras=aws

check-style:
	ruff .

tests:
	pytest

tests-coverage:
	pytest --cov=app_confetti

release:
	changelog-gen
