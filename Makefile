.DEFAULT_GOAL := help

.PHONY: check
check:  ## Check code formatting and import sorting
	black --check .
	isort --check .
	flake8
	mypy .

.PHONY: dev
dev: pip_update  ## Install development requirements
	pip-sync requirements.txt

.PHONY: fix
fix:  ## Fix code formatting and import sorting
	black .
	isort .
	flake8
	mypy .

.PHONY: outdated
outdated:  ## Check outdated requirements and dependencies
	python3 -m pip list --outdated

.PHONY: pip
pip: pip_update ## Compile requirements and dependencies
	pip-compile -q -U -o requirements.txt requirements.in

.PHONY: pip_update
pip_update:  ## Update requirements and dependencies
	python3 -m pip install -q -U pip~=21.1.0 pip-tools~=6.1.0 setuptools~=57.0.0 wheel~=0.36.0

help:
	@echo "[Help] Makefile list commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
