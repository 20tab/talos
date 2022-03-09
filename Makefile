.DEFAULT_GOAL := help

.PHONY: check
check:  ## Check code formatting and import sorting
	python3 -m black --check .
	python3 -m isort --check .
	python3 -m flake8

.PHONY: fix
fix:  ## Fix code formatting, linting and sorting imports
	python3 -m black .
	python3 -m isort .
	python3 -m flake8

.PHONY: local
local: pip_update  ## Install local requirements and dependencies
	python3 -m piptools sync requirements/local.txt

.PHONY: outdated
outdated:  ## Check outdated requirements and dependencies
	python3 -m pip list --outdated

.PHONY: pip
pip: pip_update  ## Compile requirements
	python3 -m piptools compile --no-header --quiet --upgrade --output-file requirements/common.txt requirements/common.in
	python3 -m piptools compile --no-header --quiet --upgrade --output-file requirements/local.txt requirements/local.in
	python3 -m piptools compile --no-header --quiet --upgrade --output-file requirements/test.txt requirements/test.in

.PHONY: pip_update
pip_update:  ## Update requirements and dependencies
	python3 -m pip install -q -U pip~=22.0.0 pip-tools~=6.5.0 setuptools~=60.9.0 wheel~=0.37.0

.PHONY: precommit
precommit:  ## Fix code formatting, linting and sorting imports
	python3 -m pre_commit run --all-files

.PHONY: precommit_update
precommit_update:  ## Update pre_commit
	python3 -m pre_commit autoupdate

ifeq (simpletest,$(firstword $(MAKECMDGOALS)))
  simpletestargs := $(wordlist 2, $(words $(MAKECMDGOALS)), $(MAKECMDGOALS))
  $(eval $(simpletestargs):;@true)
endif

.PHONY: simpletest # Run debug tests
simpletest:
	python3 -m unittest $(simpletestargs)

.PHONY: update
update: pip precommit_update ## Run update

.PHONY: help
help:
	@echo "[Help] Makefile list commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
