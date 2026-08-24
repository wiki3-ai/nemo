"""End-to-end smoke test: boots the real Nemo kernel via jupyter_client.

Run: .venv/bin/python nemo-jupyter/tests/smoke_test.py
Requires the kernelspec to be installed (see nemo-jupyter/install-kernel.py).
"""

from __future__ import annotations

import os
import subprocess
import sys

# pyzmq (used by jupyter_client) needs libstdc++ at runtime; on the Nix
# devcontainer it is only on LD_LIBRARY_PATH inside `nix develop`. If the
# import fails for that reason, find a working libstdc++ and re-exec
# ourselves with the right environment.
try:
    from jupyter_client import KernelManager
except ImportError as exc:
    if "libstdc++" not in str(exc):
        raise
    from pathlib import Path

    candidates = [
        "/usr/lib/aarch64-linux-gnu",
        "/usr/lib/x86_64-linux-gnu",
        "/usr/lib",
        "/usr/lib64",
        *sorted(str(p) for p in Path("/nix/store").glob("*-gcc-*-lib/lib")),
    ]
    for directory in candidates:
        if not Path(directory).joinpath("libstdc++.so.6").exists():
            continue
        env = {**os.environ, "LD_LIBRARY_PATH": directory}
        probe = subprocess.run(
            [sys.executable, "-c", "import zmq"], capture_output=True, env=env
        )
        if probe.returncode == 0:
            os.execve(sys.executable, [sys.executable, os.path.abspath(__file__)], env)
    raise

KERNEL_NAME = "nemo"
TIMEOUT = 60

PROGRAM = """
parent(ada, bob) .
parent(bob, cyd) .

ancestor(?x, ?y) :- parent(?x, ?y) .
ancestor(?x, ?y) :- parent(?x, ?z), ancestor(?z, ?y) .

@export ancestor :- csv {}.
"""


def execute(client, code: str, timeout: int = TIMEOUT) -> list[dict]:
    """Execute code, returning the list of iopub messages until idle."""
    client.execute(code)
    messages = []
    while True:
        msg = client.get_iopub_msg(timeout=timeout)
        messages.append(msg)
        if msg["msg_type"] == "status" and msg["content"]["execution_state"] == "idle":
            return messages


def stream_text(messages: list[dict]) -> str:
    return "".join(
        m["content"]["text"]
        for m in messages
        if m["msg_type"] == "stream"
    )


def main() -> int:
    manager = KernelManager(kernel_name=KERNEL_NAME)
    manager.start_kernel()
    client = manager.client()
    client.start_channels()
    try:
        client.wait_for_ready(timeout=TIMEOUT)
        print(f"[ok] kernel '{KERNEL_NAME}' started")

        # 1. run a Nemo program
        msgs = execute(client, PROGRAM)
        text = stream_text(msgs)
        print("--- cell output ---")
        print(text)
        for expected in ("ancestor(<ada>, <bob>)", "ancestor(<bob>, <cyd>)", "ancestor(<ada>, <cyd>)"):
            assert expected in text, f"missing expected fact: {expected}"
        print("[ok] program cell produced expected facts")

        # 2. run a magic
        msgs = execute(client, "!trace ancestor(ada, cyd)")
        text = stream_text(msgs)
        assert "ancestor(?x, ?y) :- parent(?x, ?z), ancestor(?z, ?y)" in text, text
        assert "parent(ada, bob)" in text, text
        print("[ok] !trace magic produced a derivation")

        # 3. run an invalid program -> error message
        error_msgs = [m for m in execute(client, "this is not nemo(") if m["msg_type"] == "error"]
        assert error_msgs, "expected an error message for invalid program"
        print(f"[ok] invalid program reported error: {error_msgs[0]['content']['evalue'][:60]!r}...")

        # 4. check kernel info (skip any stale replies in the shell channel)
        client.kernel_info()
        info = None
        while True:
            candidate = client.get_shell_msg(timeout=TIMEOUT)
            if candidate["msg_type"] == "kernel_info_reply":
                info = candidate
                break
        lang = info["content"]["language_info"]
        assert lang["name"] == "nemo", lang
        assert lang["file_extension"] == ".rls", lang
        print(f"[ok] kernel_info reports language {lang['name']!r} ({lang['file_extension']})")

        print()
        print("smoke test passed")
        return 0
    finally:
        client.stop_channels()
        manager.shutdown_kernel(now=True)


if __name__ == "__main__":
    sys.exit(main())
