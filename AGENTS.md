# AGENTS.md

Homelab infrastructure-as-code.

This repository only defines the infrastructure.
It should not contain any real configuration or credentials.
A Python project in a separate repository can install `iac/` as an editable path dependency, and use `labcli` to manage a deployment.

Stack:

- Python 3.13 with Poetry
- cdk8s with `cdk8s-plus-29` (Kubernetes 1.29 API)
- cdktf 0.21

## Commands

Run all commands from `iac/`, inside the dev shell.

Your harness may already run `.agents/prepare` to set up new checkouts.
If it does not, first enter the dev shell with `nix develop`, then run:

```
poetry install
poetry run labcli sync-imports
```

### Lint and Test

```
poetry run pytest
poetry run ruff check
poetry run ruff format --check
```

### Run

```
poetry run labcli --help
```

## Contributing

Changes take place through pull requests on GitHub.
PRs are squash-merged, and the PR title and description become the commit message.
PR titles use the [Conventional Commits specification](https://www.conventionalcommits.org/en/v1.0.0/).

## Security

The following rules apply unless explicit approval is obtained from the user.
These rules may be automatically enforced by a sandbox.
When they are, a user may provide authorization through an approval prompt.
If you believe you have accessed something you should not have, stop immediately and report the incident to the user.

- Use only fake config values in this repo.
  Do not attempt to find or access config for any real deployments of this infrastructure.
  Assume everything that enters an agent session will leave this machine.
- Do not attempt to read outside your worktree.
- Do not attempt to access live systems.
