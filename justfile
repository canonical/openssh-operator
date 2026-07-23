#!/usr/bin/env just --justfile
# Copyright 2026 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

uv := require("uv")

project_dir := justfile_directory()
src_dir := project_dir / "src"
tests_dir := project_dir / "tests"

export PY_COLORS := "1"
export PYTHONPATH := project_dir / "lib" + ":" + src_dir

uv_run := "uv run --frozen --all-groups"

[private]
default:
    @just help

# Show available recipes
help:
    @just --list --unsorted

# Prepare the local environment
setup: env

# Clean project directory
clean:
    {{ uv_run }} coverage erase || true
    rm -rf .mypy_cache .ruff_cache .pytest_cache *.egg-info build/ .charmhub.secret *.charm
    find . -name __pycache__ -type d -exec rm -rf {} + || true

# Apply static checks
check: fmt lint typecheck

# Run tests for specified targets, or all tests if none specified
test *targets:
    #!/usr/bin/env bash
    if [ "{{ targets }}" = "" ]; then
        just test-all
        exit 0
    fi

    for target in {{ targets }}; do
        if just --show $target > /dev/null 2>&1; then
            echo "Running $target tests..."
            just $target
        else
            echo "$target tests not found, skipping."
            exit 1
        fi
    done

# Run all test suites
test-all: unit integration

# Run unit tests
unit *args: lock
    #!/usr/bin/env bash
    set -euxo pipefail

    {{ uv_run }} coverage run \
        -m pytest -v --tb native -s \
        {{ args }} {{ tests_dir / "unit" }} {{ project_dir / "pkg" / "ssh-config" / "tests" / "unit" }}

    {{ uv_run }} coverage report

# Run integration tests
integration *args: lock
    #!/usr/bin/env bash
    set -euxo pipefail

    {{ uv_run }} pytest \
        -v --tb native -s \
        --log-cli-level=INFO \
        {{ args }} \
        {{ tests_dir / "integration" }}

# Build specified artifacts, or all artifacts if none specified
build *args:
    charmcraft -v pack {{ args }}

# Regenerate uv.lock
lock:
    uv lock

# Create a uv development environment
env: lock
    uv sync --all-groups

# Upgrade uv.lock with the latest dependencies
upgrade:
    uv lock --upgrade

# Apply formatting standards
fmt: lock
    {{ uv_run }} ruff format {{ src_dir }} {{ tests_dir }}
    {{ uv_run }} ruff check --fix {{ src_dir }} {{ tests_dir }}

# Check files against style standards
lint: lock
    {{ uv_run }} codespell {{ project_dir }}
    {{ uv_run }} ruff check {{ src_dir }} {{ tests_dir }}
    {{ uv_run }} ruff format --check --diff {{ src_dir }} {{ tests_dir }}

# Perform type checking
typecheck: lock
    {{ uv_run }} pyright

# Generate Charmhub token
generate-charmhub-token:
    charmcraft login \
        --export=.charmhub.secret \
        --permission=package-manage-metadata \
        --permission=package-manage-releases \
        --permission=package-manage-revisions \
        --permission=package-view-metadata \
        --permission=package-view-releases \
        --permission=package-view-revisions \
        --ttl=31536000
