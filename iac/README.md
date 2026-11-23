# lab

## Setup

First, enter the dev shell defined in `flake.nix`:

```
nix develop
```

With [direnv](https://direnv.net/), the dev shell loads automatically on entering this repository.
[nix-direnv](https://github.com/nix-community/nix-direnv) is recommended to cache the shell and protect it from garbage collection.

Then, install dependencies and generate imports:

```
poetry install
poetry run labcli sync-imports
```

### Binary cache

CI pushes the dev shell's builds to the public cache `https://bfogarty.cachix.org`.
Without it, some dev shell packages build from source.
To use the cache, run `cachix use bfogarty`, or add the following to `nix.conf`:

```
extra-substituters = https://bfogarty.cachix.org
extra-trusted-public-keys = bfogarty.cachix.org-1:Q44G+kZZesKfq1fMRcFezSt846t5zgQpiDFHTcvrI80=
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
