check:
	black --check .
	flake8
	isort --check-only --recursive

dev:
	pip install -q -U pip~=20.0.1 pip-tools~=4.5.0
	pip-sync requirements.txt

fix:
	black .
	flake8
	isort --recursive

pip:
	pip install -q -U pip~=20.0.1 pip-tools~=4.5.0
	pip-compile $(p) requirements.ini > requirements.txt
