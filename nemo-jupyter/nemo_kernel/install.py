"""Install the Nemo kernel spec into the running Jupyter environment."""

import argparse
import json
import os
import shutil
import sys
import tempfile

import jupyter_client.kernelspec as ks


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Install the Nemo Jupyter kernel spec."
    )
    parser.add_argument(
        "--user",
        action="store_true",
        default=True,
        help="Install into the per-user kernel directory (default).",
    )
    parser.add_argument(
        "--sys-prefix",
        action="store_true",
        dest="sys_prefix",
        help="Install into sys.prefix (useful inside virtual-envs / containers).",
    )
    args = parser.parse_args(argv)

    # Locate the kernel.json bundled with this package.
    here = os.path.dirname(os.path.abspath(__file__))
    kernel_json_src = os.path.join(here, "kernel.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Jupyter expects a directory named after the kernel whose contents
        # will be copied verbatim into the kernelspec directory.
        kernel_dir = os.path.join(tmpdir, "nemo")
        os.makedirs(kernel_dir)
        shutil.copy(kernel_json_src, os.path.join(kernel_dir, "kernel.json"))

        install_dir = ks.install_kernel_spec(
            kernel_dir,
            kernel_name="nemo",
            user=not args.sys_prefix,
            replace=True,
            prefix=sys.prefix if args.sys_prefix else None,
        )

    print(f"Nemo kernel spec installed to: {install_dir}")


if __name__ == "__main__":
    main()
