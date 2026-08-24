# nemo-jupyter — Jupyter kernel for the Nemo rule engine

A [Jupyter](https://jupyter.org/) kernel that lets you write and run
[Nemo](https://github.com/knowsys/nemo) rule programs directly in
notebooks. Each cell is a complete Nemo program (facts, rules,
directives); running the cell reasons over the program and prints the
contents of every `@export`-ed predicate.

The kernel is built on `ipykernel` and the Python bindings in
[`nemo-python`](../nemo-python) (the `nmo_python` module).

## Installation

Prerequisites (already set up by the devcontainer):

* a virtualenv at `<repo>/.venv` with `ipykernel` and the `nmo_python`
  bindings installed (`maturin develop` in `nemo-python`), and
* Python 3.9+.

Register the kernel with Jupyter:

```bash
.venv/bin/python nemo-jupyter/install-kernel.py
```

This writes a kernelspec to `~/.local/share/jupyter/kernels/nemo/` that
launches the kernel with the repository's `.venv` Python. The kernel then
appears as **Nemo** in the VS Code Jupyter extension and in JupyterLab.
If it does not show up, reload the VS Code window (or restart the Jupyter
server).

## Usage

Create a notebook and select the **Nemo** kernel. Write a program in a
cell, for example:

```nemo
parent(ada, bob) .
parent(bob, cyd) .

ancestor(?x, ?y) :- parent(?x, ?y) .
ancestor(?x, ?y) :- parent(?x, ?z), ancestor(?z, ?y) .

@export ancestor :- csv {}.
```

Running the cell prints the derived facts:

```
ancestor(<ada>, <bob>)
ancestor(<bob>, <cyd>)
ancestor(<ada>, <cyd>)
[ancestor: 3, total: 3, reasoning: 1.1 ms]
```

(Bare names like `ada` are relative IRIs, so they print in canonical
`<...>` form.)

### Kernel commands

Commands start with `!` (Nemo itself uses `%` for comments, so `%` is not
available for magics):

| Command                 | Effect                                              |
| ----------------------- | --------------------------------------------------- |
| `!help`                 | Show usage help                                     |
| `!version`              | Show kernel, bindings and engine versions           |
| `!pwd`                  | Print the kernel's working directory                |
| `!load <file>`          | Print the contents of a Nemo (`.rls`) file          |
| `!predicates`           | List exported/imported predicates of the last run   |
| `!trace <fact>`         | Show the derivation of a fact of the last run       |

Example:

```
!trace ancestor(ada, cyd)
```

### Nix devcontainer: libstdc++

On this Nix-based devcontainer, `libstdc++.so.6` is only on
`LD_LIBRARY_PATH` inside `nix develop`. pyzmq needs it, so Jupyter
commands fail outside the dev shell with
`libstdc++.so.6: cannot open shared object file`. The setup patches the
venv once so everything works:

```bash
bash nemo-jupyter/fix-venv-libstdcxx.sh
```

(The devcontainer's `postCreateCommand.sh` runs this automatically.)
Re-run it after a container rebuild or after reinstalling/upgrading
pyzmq. The kernel's `run-kernel.sh` also probes for a working libstdc++
as a fallback.

### Notes and limitations

* **Each cell is standalone.** Facts and rules do not accumulate across
  cells; run the whole program in one cell (or concatenate sources).
* **Results come from `@export` directives**, exactly like the `nmo` CLI.
  Without `@export`, a cell runs but shows no results.
* `@import` and `@export` file resources resolve relative to the kernel's
  working directory — run `!pwd` to see it (VS Code usually starts the
  kernel in the workspace folder).
* The Python bindings are experimental; the kernel inherits their
  behavior and limitations.
* The kernel currently reports output predicates by parsing the cell
  source, because `NemoProgram.output_predicates()` in the bindings does
  not return them reliably.

## Development

Run everything (this handles the libstdc++/LD_LIBRARY_PATH quirk of the
Nix devcontainer automatically):

```bash
bash nemo-jupyter/run-tests.sh
```

Or individually:

```bash
.venv/bin/python -m pytest nemo-jupyter/tests/test_kernel_logic.py   # unit tests
.venv/bin/python nemo-jupyter/tests/smoke_test.py                   # end-to-end
```

The smoke test starts a real kernel via `jupyter_client` and needs the
kernelspec installed.

Layout:

```
nemo-jupyter/
  nemo_jupyter/kernel.py     the kernel (ipykernel Kernel subclass)
  nemo_jupyter/__main__.py   entry point (python -m nemo_jupyter)
  run-kernel.py              Python launcher used by the kernelspec
  run-kernel.sh              shell wrapper (finds libstdc++ for pyzmq)
  install-kernel.py          registers the kernelspec with Jupyter
  run-tests.sh               runs unit + smoke tests
  fix-venv-libstdcxx.sh      patches pyzmq for the Nix libstdc++ quirk
  tests/                     unit + end-to-end tests
  examples/                  example notebook
```
