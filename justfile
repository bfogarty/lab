# The Python project lives in iac/, so every recipe runs there.
set working-directory := 'iac'

[private]
default:
    @just --list --unsorted

# Install dependencies and generate imports.
setup: install sync-imports

# Install the Python project's dependencies.
install:
    poetry install

# Generate the cdktn and cdk8s imports. Arguments are passed to `labcli sync-imports`.
sync-imports *args:
    poetry run labcli sync-imports {{ args }}

# Check linting and formatting.
lint:
    poetry run ruff check
    poetry run ruff format --check

# Run the tests. Arguments are passed to pytest.
test *args:
    poetry run pytest {{ args }}
