"""Install the Nemo Jupyter kernelspec.

Called by the ``nemo-jupyter-install`` console script::

    nemo-jupyter-install            # user-level (--user)
    nemo-jupyter-install --sys-prefix  # inside the current venv/prefix
    nemo-jupyter-install --system   # system-wide (needs root)

For most automated environments (Binder, Jupyter Docker Stacks) the
``data_files`` in ``pyproject.toml`` already place the kernelspec in
``share/jupyter/kernels/nemo/`` at install time, so this helper is only
needed when that mechanism is insufficient (e.g., user-level installs).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KERNEL_NAME = "nemo"


def install(prefix: str | None = None, user: bool = False, sys_prefix: bool = False) -> int:
    """Install the Nemo kernelspec via ``jupyter_client``.

    At most one of *prefix*, *user*, *sys_prefix* should be truthy.
    """
    try:
        from jupyter_client.kernelspec import KernelSpecManager
    except ImportError:
        print(
            "error: jupyter_client is not installed; cannot register the kernelspec.",
            file=sys.stderr,
        )
        return 1

    import tempfile
    import shutil

    src = Path(__file__).parent / "kernelspec"
    if not (src / "kernel.json").exists():
        print(f"error: bundled kernelspec not found at {src}", file=sys.stderr)
        return 1

    # KernelSpecManager.install_kernel_spec expects a *directory* containing
    # a kernel.json file (and optional logo / support files).
    ksm = KernelSpecManager()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp) / KERNEL_NAME
        shutil.copytree(src, tmp_dir)
        install_kwargs: dict = {"kernel_name": KERNEL_NAME, "overwrite": True}
        if user:
            install_kwargs["user"] = True
        elif sys_prefix:
            import sys as _sys
            install_kwargs["prefix"] = _sys.prefix
        elif prefix:
            install_kwargs["prefix"] = prefix
        dest = ksm.install_kernel_spec(str(tmp_dir), **install_kwargs)

    print(f"Installed Nemo kernelspec in {dest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install the Nemo Jupyter kernelspec."
    )
    loc = parser.add_mutually_exclusive_group()
    loc.add_argument(
        "--user",
        action="store_true",
        default=False,
        help="Install into the per-user kernels directory (default).",
    )
    loc.add_argument(
        "--sys-prefix",
        action="store_true",
        default=False,
        dest="sys_prefix",
        help="Install into sys.prefix (the active virtualenv / conda env).",
    )
    loc.add_argument(
        "--prefix",
        default=None,
        help="Install into <prefix>/share/jupyter/kernels/.",
    )
    loc.add_argument(
        "--system",
        action="store_true",
        default=False,
        help="Install system-wide (requires root/admin).",
    )
    args = parser.parse_args(argv)

    prefix = args.prefix
    if args.system:
        prefix = "/usr/local"

    return install(prefix=prefix, user=args.user, sys_prefix=args.sys_prefix)


if __name__ == "__main__":
    raise SystemExit(main())
