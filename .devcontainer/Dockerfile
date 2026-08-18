# syntax=docker/dockerfile:1

# Base image for the nemo devcontainer.
#
# Nix is installed via the `ghcr.io/devcontainers/features/nix` feature (see
# devcontainer.json), which handles the store permissions, daemon, and non-root
# user setup that are tricky to do by hand inside Docker.
#
# The Rust toolchain, Python, maturin, wasm-pack, etc. are all provided by the
# project's Nix flake (`nix develop`), so we keep this image minimal and let
# Nix be the single source of truth for the toolchain.
FROM mcr.microsoft.com/devcontainers/base:debian

# Keep the image lean; the heavy toolchain comes from the Nix dev shell.
