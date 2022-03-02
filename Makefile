.DEFAULT_GOAL := help

.PHONY: check
check:  ## Check code formatting and import sorting
	black --check .
	isort --check .
	flake8
	mypy .

.PHONY: local
local: pip_update  ## Install local requirements
	pip-sync requirements/local.txt

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
pip: pip_update  ## Compile requirements
	pip-compile -q -U -o requirements/base.txt requirements/base.in
	pip-compile -q -U -o requirements/common.txt requirements/common.in
	pip-compile -q -U -o requirements/local.txt requirements/local.in
	pip-compile -q -U -o requirements/remote.txt requirements/remote.in
	pip-compile -q -U -o requirements/test.txt requirements/test.in

.PHONY: pip_update
pip_update:  ## Update requirements and dependencies
	python3 -m pip install -q -U pip~=21.2.0 pip-tools~=6.2.0 setuptools~=57.4.0 wheel~=0.36.0

.PHONY: remote
remote: pip_update  ## Install remote requirements and dependencies
	pip-sync requirements/remote.txt

ifeq (simpletest,$(firstword $(MAKECMDGOALS)))
  simpletestargs := $(wordlist 2, $(words $(MAKECMDGOALS)), $(MAKECMDGOALS))
  $(eval $(simpletestargs):;@true)
endif

.PHONY: simpletest # Run debug tests
simpletest:
	python3 -m unittest $(simpletestargs)

help:
	@echo "[Help] Makefile list commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
