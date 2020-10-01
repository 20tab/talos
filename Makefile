check:
	black --check .
	isort --check-only .
	flake8

dev:
	pip install -q -U pip~=20.2.0 pip-tools~=5.3.0
	pip-sync requirements.txt

fix:
	black .
	isort .
	flake8

pip:
	pip install -q -U pip~=20.2.0 pip-tools~=5.3.0
	pip-compile $(p) -U -q -o requirements.txt requirements.ini
