check:
	black --check .
	isort --check .
	flake8
	mypy .

dev:
	python3 -m pip install -q -U pip~=21.0.0 pip-tools~=5.5.0
	pip-sync requirements.txt

fix:
	black .
	isort .
	flake8
	mypy .

outdated:
	python3 -m pip list --outdated

pip:
	python3 -m pip install -q -U pip~=21.0.0 pip-tools~=5.5.0
	pip-compile -q -U -o requirements.txt requirements.in
