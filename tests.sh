#!/bin/bash

ROOT="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"
export PYTHONPATH="${PYTHONPATH}:${ROOT}/src"

coverage run --branch --source=bah -m pytest tests/tests.py
coverage report -m
