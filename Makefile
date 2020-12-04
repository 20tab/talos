check:
	black --check .
	isort --check .
	flake8

dev:
	pip install -q -U pip~=20.2.0 pip-tools~=5.4.0
	pip-sync requirements.txt

fix:
	black .
	isort .
	flake8

pip:
	pip install -q -U pip~=20.2.0 pip-tools~=5.4.0
	pip-compile -U -q -o requirements.txt requirements.in
