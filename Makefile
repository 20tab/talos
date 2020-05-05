check:
	black --check .
	isort --check-only --recursive
	flake8

dev:
	pip install -q -U pip~=20.1.0 pip-tools~=5.1.0
	pip-sync requirements.txt

fix:
	black .
	isort --recursive
	flake8

pip:
	pip install -q -U pip~=20.1.0 pip-tools~=5.1.0
	pip-compile $(p) -U -q -o requirements.txt requirements.ini
