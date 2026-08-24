# nemo-jupyter — Nemo Datalog Kernel for JupyterLab

This directory contains an [IPython](https://ipython.readthedocs.io/) kernel
that lets you use [Nemo](https://github.com/knowsys/nemo) Datalog programs
interactively inside JupyterLab notebooks.

## How it works

Each notebook cell is treated as a fragment of a Nemo program.  The kernel
**accumulates rules across cells**, so predicates defined in earlier cells are
visible in later ones.  After each cell is executed, every predicate declared
with `@output` is reasoned over and its results are printed as a table.

Use the magic line `%%reset` at the top of a cell to clear the accumulated
program and start fresh.

## Prerequisites

The kernel relies on the `nmo_python` wheel, which is the Python binding for
the Nemo Rust library.  Build it with [maturin](https://www.maturin.rs/):

```bash
cd ../nemo-python
maturin develop          # installs into the active virtual-env
```

## Installing the kernel

```bash
pip install -e .                 # install the nemo-kernel package
nemo-kernel-install --sys-prefix # register the kernelspec with Jupyter
```

Or, in one step:

```bash
pip install -e . && python -c "from nemo_kernel.install import main; main(['--sys-prefix'])"
```

## Running JupyterLab

```bash
jupyter lab
```

Then create a new notebook and choose the **Nemo** kernel.

## Example cell

```
data(1, 2) .
data(hi, 42) .
data(hello, world) .

calculated(?x, !v) :- data(?y, ?x) .

@output calculated .
```
