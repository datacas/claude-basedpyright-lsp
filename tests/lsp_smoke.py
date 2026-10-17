"""End-to-end smoke test for the basedpyright-lsp plugin.

Starts the language server exactly as Claude Code does (command + args from
the plugin's .lsp.json), then exercises the LSP operations Claude relies on:
documentSymbol, hover, definition, references and published diagnostics.

Standard library only. Exits non-zero on the first failed check.
"""

from __future__ import annotations

import json
import queue
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import unquote

REPO_ROOT = Path(__file__).resolve().parent.parent
LSP_CONFIG = REPO_ROOT / "plugins" / "basedpyright-lsp" / ".lsp.json"
FIXTURES = REPO_ROOT / "tests" / "fixtures"
SAMPLE = FIXTURES / "sample.py"
TIMEOUT = 60.0


class LspClient:
    def __init__(self, argv: list[str]) -> None:
        self.proc = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self.next_id = 0
        self.responses: dict[int, queue.Queue[dict[str, Any]]] = {}
        self.notifications: queue.Queue[dict[str, Any]] = queue.Queue()
        self.lock = threading.Lock()
        threading.Thread(target=self._reader, daemon=True).start()

    def _send(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        assert self.proc.stdin is not None
        self.proc.stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
        self.proc.stdin.flush()

    def _reader(self) -> None:
        stream = self.proc.stdout
        assert stream is not None
        while True:
            headers: dict[str, str] = {}
            while True:
                line = stream.readline()
                if not line:
                    return
                line = line.decode("ascii").strip()
                if not line:
                    break
                key, _, value = line.partition(":")
                headers[key.lower()] = value.strip()
            message = json.loads(stream.read(int(headers["content-length"])))
            self._dispatch(message)

    def _dispatch(self, message: dict[str, Any]) -> None:
        if "method" in message and "id" in message:
            # Server-to-client request: answer so the server never blocks.
            result: Any = None
            if message["method"] == "workspace/configuration":
                result = [None] * len(message["params"]["items"])
            self._send({"jsonrpc": "2.0", "id": message["id"], "result": result})
        elif "method" in message:
            self.notifications.put(message)
        else:
            with self.lock:
                slot = self.responses.get(message["id"])
            if slot is not None:
                slot.put(message)

    def request(self, method: str, params: Any) -> Any:
        with self.lock:
            self.next_id += 1
            request_id = self.next_id
            slot: queue.Queue[dict[str, Any]] = queue.Queue()
            self.responses[request_id] = slot
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        response = slot.get(timeout=TIMEOUT)
        if "error" in response:
            raise RuntimeError(f"{method} failed: {response['error']}")
        return response.get("result")

    def notify(self, method: str, params: Any) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def wait_notification(self, method: str, predicate=lambda _: True) -> dict[str, Any]:
        deadline = time.monotonic() + TIMEOUT
        while (remaining := deadline - time.monotonic()) > 0:
            try:
                message = self.notifications.get(timeout=remaining)
            except queue.Empty:
                break
            if message["method"] == method and predicate(message["params"]):
                return message["params"]
        raise TimeoutError(f"no {method} notification received")

    def close(self) -> None:
        try:
            self.request("shutdown", None)
            self.notify("exit", None)
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def position_of(text: str, needle: str, occurrence: int = 0) -> dict[str, int]:
    index = -1
    for _ in range(occurrence + 1):
        index = text.index(needle, index + 1)
    line = text.count("\n", 0, index)
    character = index - (text.rfind("\n", 0, index) + 1)
    return {"line": line, "character": character}


def same_uri(a: str, b: str) -> bool:
    # Servers may percent-encode the Windows drive colon (file:///d%3A/...).
    return unquote(a).lower() == unquote(b).lower()


def symbol_names(symbols: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for symbol in symbols:
        names.add(symbol["name"])
        names |= symbol_names(symbol.get("children", []))
    return names


def check(condition: bool, label: str) -> None:
    print(f"{'PASS' if condition else 'FAIL'}  {label}")
    if not condition:
        raise SystemExit(1)


def main() -> None:
    config = json.loads(LSP_CONFIG.read_text(encoding="utf-8"))["basedpyright"]
    executable = shutil.which(config["command"])
    check(executable is not None, f"{config['command']} found on PATH")
    assert executable is not None

    client = LspClient([executable, *config["args"]])
    text = SAMPLE.read_text(encoding="utf-8")
    uri = SAMPLE.as_uri()
    doc = {"textDocument": {"uri": uri}}

    try:
        client.request(
            "initialize",
            {
                "processId": None,
                "rootUri": FIXTURES.as_uri(),
                "workspaceFolders": [{"uri": FIXTURES.as_uri(), "name": "fixtures"}],
                "capabilities": {
                    "textDocument": {
                        "documentSymbol": {"hierarchicalDocumentSymbolSupport": True},
                        "hover": {"contentFormat": ["markdown", "plaintext"]},
                        "publishDiagnostics": {},
                    },
                    "workspace": {"configuration": True, "workspaceFolders": True},
                },
            },
        )
        check(True, "initialize")
        client.notify("initialized", {})
        client.notify(
            "textDocument/didOpen",
            {"textDocument": {"uri": uri, "languageId": "python", "version": 1, "text": text}},
        )

        diagnostics = client.wait_notification(
            "textDocument/publishDiagnostics",
            lambda params: same_uri(params["uri"], uri) and params["diagnostics"],
        )["diagnostics"]
        check(
            any("int" in d["message"] for d in diagnostics),
            "diagnostics report the type error",
        )

        symbols = client.request("textDocument/documentSymbol", doc) or []
        check(
            {"Greeter", "greet", "build_greeter"} <= symbol_names(symbols),
            "documentSymbol lists Greeter, greet, build_greeter",
        )

        call_site = position_of(text, "build_greeter", occurrence=1)
        hover = client.request("textDocument/hover", {**doc, "position": call_site})
        hover_text = json.dumps(hover)
        check("Greeter" in hover_text, "hover shows the return type")

        definition = client.request("textDocument/definition", {**doc, "position": call_site})
        definitions = definition if isinstance(definition, list) else [definition]
        expected_line = position_of(text, "def build_greeter")["line"]
        check(
            any(
                (d.get("range") or d.get("targetSelectionRange"))["start"]["line"] == expected_line
                for d in definitions
                if d
            ),
            "definition jumps to build_greeter",
        )

        references = client.request(
            "textDocument/references",
            {**doc, "position": call_site, "context": {"includeDeclaration": True}},
        )
        check(len(references or []) == 2, "references finds declaration and call")
    finally:
        client.close()


if __name__ == "__main__":
    main()
