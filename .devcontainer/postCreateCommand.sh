#!/usr/bin/env bash
# Post-create setup for the nemo devcontainer.
#
# Runs inside the Nix dev shell (see devcontainer.json postCreateCommand),
# which provides python3, maturin, wasm-pack, nodejs, etc.
#
# Steps:
#   1. Create a Python virtualenv (kept out of the Nix store so it's writable
#      and persists across rebuilds via the mounted volume).
#   2. Install the Jupyter tooling (notebook, lab, ipykernel, ...) into the venv.
#   3. Build the nmo_python bindings with maturin and install them into the venv.
set -euo pipefail

VENV_DIR="${WORKSPACE_FOLDER:-/workspaces/nemo}/.venv"
REQ_FILE="${WORKSPACE_FOLDER:-/workspaces/nemo}/.devcontainer/requirements-dev.txt"

echo "==> Creating Python virtualenv at ${VENV_DIR}"
python3 -m venv "${VENV_DIR}"

echo "==> Activating virtualenv"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "==> Installing Jupyter tooling"
pip install --upgrade pip
pip install -r "${REQ_FILE}"

echo "==> Building nmo_python bindings with maturin"
maturin develop --manifest-path "${WORKSPACE_FOLDER:-/workspaces/nemo}/nemo-python/Cargo.toml"

echo "==> Verifying nmo_python import"
python -c "import nmo_python; print('nmo_python OK:', nmo_python.__file__)"

echo "==> Devcontainer setup complete."
