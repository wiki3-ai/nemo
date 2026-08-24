# syntax=docker/dockerfile:1
# =============================================================================
# Dev-container image for the Nemo repository.
#
# Provides:
#   • Rust nightly (pinned by rust-toolchain.toml)
#   • Python 3 + maturin (to build nmo_python)
#   • JupyterLab + the Nemo kernel (nemo-jupyter/)
#   • The default IPykernel so Python notebooks also work
# =============================================================================

FROM rust:1-bookworm

# ---------------------------------------------------------------------------
# System dependencies
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv python3-dev \
        curl git pkg-config build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Rust: install the nightly toolchain requested by the repo
# ---------------------------------------------------------------------------
COPY rust-toolchain.toml /opt/nemo-build/rust-toolchain.toml
WORKDIR /opt/nemo-build
RUN rustup show active-toolchain

# ---------------------------------------------------------------------------
# Python: create a system-wide virtual-env used by JupyterLab
# ---------------------------------------------------------------------------
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir \
        maturin \
        jupyterlab \
        ipykernel

# ---------------------------------------------------------------------------
# Build nmo_python (Rust → Python wheel) and install into the venv.
# We copy only the crates needed to build the nemo-python extension module.
# ---------------------------------------------------------------------------
COPY Cargo.toml Cargo.lock rust-toolchain.toml rustfmt.toml /opt/nemo-build/
COPY nemo/Cargo.toml                      /opt/nemo-build/nemo/Cargo.toml
COPY nemo/src                             /opt/nemo-build/nemo/src
COPY nemo-cli/Cargo.toml                  /opt/nemo-build/nemo-cli/Cargo.toml
COPY nemo-cli/src                         /opt/nemo-build/nemo-cli/src
COPY nemo-physical/Cargo.toml             /opt/nemo-build/nemo-physical/Cargo.toml
COPY nemo-physical/src                    /opt/nemo-build/nemo-physical/src
COPY nemo-python/Cargo.toml               /opt/nemo-build/nemo-python/Cargo.toml
COPY nemo-python/src                      /opt/nemo-build/nemo-python/src
COPY nemo-python/pyproject.toml           /opt/nemo-build/nemo-python/pyproject.toml
COPY nemo-python/setup.cfg                /opt/nemo-build/nemo-python/setup.cfg
COPY nemo-language-server/Cargo.toml      /opt/nemo-build/nemo-language-server/Cargo.toml
COPY nemo-language-server/src             /opt/nemo-build/nemo-language-server/src
COPY nemo-wasm/Cargo.toml                 /opt/nemo-build/nemo-wasm/Cargo.toml
COPY nemo-wasm/src                        /opt/nemo-build/nemo-wasm/src
COPY xtask/Cargo.toml                     /opt/nemo-build/xtask/Cargo.toml
COPY xtask/src                            /opt/nemo-build/xtask/src

WORKDIR /opt/nemo-build/nemo-python
RUN maturin develop --release

# ---------------------------------------------------------------------------
# Install the Nemo JupyterLab kernel
# ---------------------------------------------------------------------------
COPY nemo-jupyter /opt/nemo-build/nemo-jupyter
WORKDIR /opt/nemo-build/nemo-jupyter

RUN pip install --no-cache-dir -e . && \
    python -m nemo_kernel.install --sys-prefix

# ---------------------------------------------------------------------------
# Register the default Python (ipykernel) so Python notebooks also work
# ---------------------------------------------------------------------------
RUN python -m ipykernel install --sys-prefix --name python3 --display-name "Python 3"

# ---------------------------------------------------------------------------
# Runtime: start JupyterLab, listening on all interfaces, no browser
# ---------------------------------------------------------------------------
WORKDIR /workspace
EXPOSE 8888

CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--NotebookApp.token=''", \
     "--NotebookApp.password=''", \
     "--notebook-dir=/workspace"]
