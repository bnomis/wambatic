# Installation

How to install wambatic from a clone of its repository and check that it runs.

## Prerequisites

- Python 3.14.7 or a later 3.14 release. [uv](https://docs.astral.sh/uv/) can install it for you.
- [uv](https://docs.astral.sh/uv/getting-started/installation/), which creates the environment and
  installs the dependencies.
- [git](https://git-scm.com/downloads) 2.40 or later, to clone the repository and, at run time, to read
  commits from bare clones of the repositories you report on.

## Install

```shell
git clone https://github.com/bnomis/wambatic
cd wambatic
uv sync
source bin/activate.sh
wambatic --help
```

`uv sync` creates `.venv` in the clone and installs wambatic and its dependencies there.
`source bin/activate.sh` activates that environment and puts `src` on the Python path; run it in each new
shell before you use `wambatic`.

## Check the install

`wambatic --help` lists the `report`, `serve` and `cache` commands. `python -m wambatic` runs the same
program.

```shell
wambatic cache info
```

This describes the cache without changing it, and makes no request, so it needs no token.

## Shell completion

wambatic can print the completion source for your shell:

```shell
wambatic --completion generate
```

See [the command line reference](reference/cli.md) for the `--completion` option.

## Updating

```shell
git pull
git submodule update --init
uv sync
```

A cache written by an earlier wambatic may be refused after an upgrade. The cache is derived data, so run
`wambatic cache clear` and the next report fetches it again; see [The cache](guide/cache.md).

## Next

[The GitHub token](token.md) says how to give wambatic access to GitHub.
