# lab

## Setup

First, enter the dev shell defined in `flake.nix`:

```
nix develop
```

Then, install dependencies and generate imports:

```
poetry install
poetry run labcli sync-imports
```

## Testing

```
poetry run pytest
```

## Usage

```
poetry run labcli --help
```

## Setting up a deployment project

To facilitate storing configuration and encrypted secrets separately, another
project can add `lab` as an editable path dependency. Run the following steps to
configure:

```
poetry add --editable path/to/lab
poetry run labcli sync-imports
```

Repositories using `labcli` should add the following to `.gitignore`.

```
dist/
cdktf.out/
.terraform/
```
