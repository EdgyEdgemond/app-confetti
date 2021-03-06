install:
	poetry install --no-dev

install-dev:
	poetry install

check-style:
	flake8

tests:
	pytest

tests-coverage:
	pytest --cov=app_confetti

isort:
	isort -y

release:
	changelog-gen
