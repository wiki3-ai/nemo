"""Nemo Datalog IPython kernel.

Each cell is treated as a Nemo program fragment.  The kernel accumulates
rules across cells so that later cells can reference predicates defined in
earlier ones.  A cell that begins with ``%%reset`` clears the accumulated
program.

Output predicates (declared with ``@output`` or ``@export``) are reasoned
over and their results printed as plain-text tables after each cell is
executed.
"""

from __future__ import annotations

import io
import traceback
from typing import List

from ipykernel.kernelbase import Kernel

try:
    from nmo_python import load_string, NemoEngine
    _IMPORT_ERROR: str | None = None
except Exception as exc:  # noqa: BLE001
    load_string = None  # type: ignore[assignment]
    NemoEngine = None  # type: ignore[assignment]
    _IMPORT_ERROR = str(exc)


class NemoKernel(Kernel):
    implementation = "nemo"
    implementation_version = "0.1.0"
    language = "nemo"
    language_version = "0.1"
    language_info = {
        "name": "nemo",
        "mimetype": "text/x-nemo",
        "file_extension": ".rls",
        "pygments_lexer": "text",
        "codemirror_mode": "text/plain",
    }
    banner = "Nemo – Datalog Reasoner Kernel"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Accumulated program text from all cells executed so far.
        self._program_parts: List[str] = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _send_text(self, text: str, stream: str = "stdout") -> None:
        self.send_response(
            self.iopub_socket,
            "stream",
            {"name": stream, "text": text},
        )

    def _send_error(self, text: str) -> None:
        self._send_text(text, stream="stderr")

    @staticmethod
    def _format_results(predicate: str, rows) -> str:
        buf = io.StringIO()
        buf.write(f"=== {predicate} ===\n")
        row_list = list(rows)
        if not row_list:
            buf.write("(no results)\n")
        else:
            for row in row_list:
                buf.write("  " + ", ".join(str(v) for v in row) + "\n")
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Kernel protocol
    # ------------------------------------------------------------------

    def do_execute(
        self,
        code: str,
        silent: bool,
        store_history: bool = True,
        user_expressions=None,
        allow_stdin: bool = False,
        *,
        cell_id=None,
    ):
        if _IMPORT_ERROR is not None:
            self._send_error(
                f"nmo_python module could not be imported: {_IMPORT_ERROR}\n"
            )
            return self._error_reply("ImportError", _IMPORT_ERROR, [])

        stripped = code.strip()

        # Magic: %%reset clears the accumulated program.
        if stripped.startswith("%%reset"):
            self._program_parts = []
            if not silent:
                self._send_text("Program reset.\n")
            return self._ok_reply()

        if not stripped:
            return self._ok_reply()

        # Accumulate this cell's code.
        self._program_parts.append(stripped)
        full_program = "\n".join(self._program_parts)

        try:
            program = load_string(full_program)
        except Exception as exc:  # noqa: BLE001
            msg = f"Parse error:\n{exc}\n"
            self._send_error(msg)
            # Roll back the last addition so future cells can still work.
            self._program_parts.pop()
            return self._error_reply("NemoParseError", str(exc), [])

        output_predicates = program.output_predicates()

        if not output_predicates:
            if not silent:
                self._send_text(
                    "Program accepted (no @output predicates to display).\n"
                )
            return self._ok_reply()

        try:
            engine = NemoEngine(program)
            engine.reason()
        except Exception as exc:  # noqa: BLE001
            tb = traceback.format_exc()
            self._send_error(f"Reasoning error:\n{tb}\n")
            return self._error_reply("NemoReasoningError", str(exc), [])

        if not silent:
            for pred in output_predicates:
                try:
                    rows = engine.result(pred)
                    self._send_text(self._format_results(pred, rows))
                except Exception as exc:  # noqa: BLE001
                    self._send_error(f"Could not retrieve results for {pred!r}: {exc}\n")

        return self._ok_reply()

    # ------------------------------------------------------------------
    # Introspection / completion stubs (optional but nice to have)
    # ------------------------------------------------------------------

    def do_complete(self, code: str, cursor_pos: int):
        return {
            "matches": [],
            "cursor_start": cursor_pos,
            "cursor_end": cursor_pos,
            "metadata": {},
            "status": "ok",
        }

    def do_inspect(self, code: str, cursor_pos: int, detail_level: int = 0):
        return {"status": "ok", "found": False, "data": {}, "metadata": {}}

    def do_is_complete(self, code: str):
        # A cell is complete when the last non-blank line ends with '.'
        lines = [ln.rstrip() for ln in code.splitlines() if ln.strip()]
        if not lines:
            return {"status": "complete", "indent": ""}
        last = lines[-1]
        if last.endswith("."):
            return {"status": "complete", "indent": ""}
        return {"status": "incomplete", "indent": "  "}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ok_reply():
        return {
            "status": "ok",
            "execution_count": 0,
            "payload": [],
            "user_expressions": {},
        }

    @staticmethod
    def _error_reply(ename: str, evalue: str, traceback_list: list):
        return {
            "status": "error",
            "ename": ename,
            "evalue": evalue,
            "traceback": traceback_list,
        }
