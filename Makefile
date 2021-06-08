check:
	black --check .
	isort --check .
	flake8
	mypy .

dev: pip_update
	pip-sync requirements.txt

fix:
	black .
	isort .
	flake8
	mypy .

outdated:
	python3 -m pip list --outdated

pip: pip_update
	pip-compile -q -U -o requirements.txt requirements.in

pip_update:
	python3 -m pip install -q -U pip~=21.1.0 pip-tools~=6.1.0 setuptools~=57.0.0 wheel~=0.36.0
