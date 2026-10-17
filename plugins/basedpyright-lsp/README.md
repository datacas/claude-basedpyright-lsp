# basedpyright-lsp

Python language server ([BasedPyright](https://docs.basedpyright.com)) for Claude Code,
providing type checking and code intelligence.

## Supported extensions

`.py`, `.pyi`, `.pyw`

## Installation

Install BasedPyright so that `basedpyright-langserver` is on your `PATH`:

```bash
uv tool install basedpyright   # or: pipx install basedpyright / npm install -g basedpyright
```

Do not enable this plugin together with the official `pyright-lsp` plugin.

See the [project README](https://github.com/datacas/claude-basedpyright-lsp#readme)
for configuration and troubleshooting.
