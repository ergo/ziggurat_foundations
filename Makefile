SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := lint
TOX_ENV ?= py$(shell python -V | cut -d' ' -f2 | cut -d. -f1-2 | tr -d .)

.PHONY: lint
lint:
	python -m pip install ".[dev]"
	pre-commit run --all-files
	tox -e lint
	rst_files=($$(find . \
		-type d \( -name .git -o -name .tox -o -name .venv -o -name build \) -prune \
		-o -name '*.rst' -print)); \
	rstcheck --sphinx-source-dir docs --report-level WARNING "$${rst_files[@]}"
	flake8 ./ziggurat_foundations/

.PHONY: test
test:
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
