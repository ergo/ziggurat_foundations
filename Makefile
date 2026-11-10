SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := lint

.PHONY: lint
lint:
	python -m pip install ".[dev]"
	pre-commit run --all-files
	tox -e lint
	rst_files=($$(find . -name '*.rst' -print)); \
	rstcheck "$${rst_files[@]}" --report 2
	flake8 ./ziggurat_foundations/

.PHONY: test
test:
	@test -n "$(TOX_ENV)" || { echo "Usage: make test TOX_ENV=py311" >&2; exit 2; }
	python -m pip install ".[test]"
	tox -e "$(TOX_ENV)"

.PHONY: build
build:
	python -m pip install ".[build]"
	@if [[ -n "$${GITHUB_REF_NAME:-}" ]]; then \
		package_version=$$(python setup.py --version); \
		if [[ "$$package_version" != "$$GITHUB_REF_NAME" ]]; then \
			echo "Tag $$GITHUB_REF_NAME does not match package version $$package_version" >&2; \
			exit 1; \
		fi; \
	fi
	python -m build
