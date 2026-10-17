# BasedPyright LSP for Claude Code

[![CI](https://github.com/datacas/claude-basedpyright-lsp/actions/workflows/ci.yml/badge.svg)](https://github.com/datacas/claude-basedpyright-lsp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A [Claude Code](https://code.claude.com) plugin that connects Claude to
[BasedPyright](https://docs.basedpyright.com), giving it real Python code intelligence:
go to definition, find references, hover types, document symbols and type-checking
diagnostics after every edit.

It is a drop-in alternative to the official `pyright-lsp` plugin for people who
prefer BasedPyright's stricter checks and extra features.

## Requirements

- Claude Code
- `basedpyright-langserver` available on the `PATH` of the process that runs Claude Code

The plugin does **not** bundle or install BasedPyright. You install and update it
yourself, so the plugin never changes anything on your machine.

## 1. Install BasedPyright

Pick one:

```bash
uv tool install basedpyright     # recommended
pipx install basedpyright
pip install basedpyright         # into the active environment
npm install -g basedpyright
```

Check it is on your `PATH`:

```bash
basedpyright --version
# macOS / Linux
command -v basedpyright-langserver
# Windows (PowerShell)
Get-Command basedpyright-langserver
```

## 2. Install the plugin

```bash
claude plugin marketplace add datacas/claude-basedpyright-lsp
claude plugin install basedpyright-lsp@basedpyright-marketplace
```

Or from inside Claude Code:

```
/plugin marketplace add datacas/claude-basedpyright-lsp
/plugin install basedpyright-lsp@basedpyright-marketplace
```

Restart Claude Code after installing.

> [!IMPORTANT]
> Do not enable this plugin and the official `pyright-lsp` plugin at the same time.
> Both handle `.py` and `.pyi` files, so you would run two servers on the same code.
>
> ```bash
> claude plugin uninstall pyright-lsp@claude-plugins-official
> ```

## Configuration

The plugin sends no settings of its own. BasedPyright reads your project's
configuration as usual, from `pyproject.toml`:

```toml
[tool.basedpyright]
typeCheckingMode = "standard"   # off | basic | standard | strict | recommended | all
venvPath = "."
venv = ".venv"
```

or from `pyrightconfig.json`. See the
[BasedPyright configuration docs](https://docs.basedpyright.com/latest/configuration/config-files/).

If your project uses a virtual environment, point `venvPath`/`venv` at it so imports
resolve.

## Verify that Claude is using it

Open Claude Code in a Python project and ask:

> Use the LSP tool to list the document symbols of `path/to/file.py`, then find all
> references to `<some function>`.

Claude should call the `LSP` tool (`documentSymbol`, `findReferences`, ...) rather
than grepping. You can also run `/plugin` and check that `basedpyright-lsp` is
enabled without errors.

## Troubleshooting

**`Executable not found in $PATH` / the server never starts.**
Claude Code inherits `PATH` from wherever it was launched.

- `uv tool` and `pipx` install into `~/.local/bin`. Run `uv tool update-shell` or
  `pipx ensurepath`, open a new terminal, and start Claude Code from it.
- macOS: apps started from the Dock or Spotlight do not read your shell profile.
  Start Claude Code from a terminal.
- Windows: make sure the scripts folder (e.g. `%USERPROFILE%\.local\bin` or your
  Python `Scripts` folder) is in your user `PATH`, then restart the terminal.
- WSL: install BasedPyright inside the WSL distribution, not on Windows.

**Imports are reported as unresolved.**
BasedPyright cannot find your environment. Configure `venvPath`/`venv` (see above),
or start Claude Code with the virtual environment activated.

**Too many (or too few) diagnostics.**
Adjust `typeCheckingMode` or individual rules in your project config. The plugin
itself does not change the checking level.

**Slow startup on large projects.**
The plugin allows 30 seconds for the server to start. Exclude generated or vendored
folders with `exclude` in your config to speed up analysis.

## Development

```bash
git clone https://github.com/datacas/claude-basedpyright-lsp
cd claude-basedpyright-lsp

claude plugin validate --strict .                         # marketplace manifest
claude plugin validate --strict plugins/basedpyright-lsp  # plugin manifest
python tests/lsp_smoke.py                                 # end-to-end LSP check

# Try your local checkout in Claude Code
claude --plugin-dir ./plugins/basedpyright-lsp
```

`tests/lsp_smoke.py` starts the server with the exact command from `.lsp.json` and
checks diagnostics, `documentSymbol`, `hover`, `definition` and `references`. CI runs
it on Linux, macOS and Windows, plus a weekly run against the latest BasedPyright.

## Repository layout

```
.claude-plugin/marketplace.json            # marketplace catalog
plugins/basedpyright-lsp/
  .claude-plugin/plugin.json               # plugin manifest
  .lsp.json                                # language server definition
tests/                                     # LSP smoke test and fixtures
```

## License

[MIT](LICENSE). BasedPyright is a separate project with its own
[license](https://github.com/DetachHead/basedpyright/blob/main/LICENSE.txt).
This project is not affiliated with Anthropic or the BasedPyright maintainers.
