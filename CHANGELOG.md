# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-10-17

### Added

- `.pyw` files are handled by the language server.

### Changed

- CI tests pull requests against pinned Claude Code and BasedPyright versions;
  the weekly run tests the latest releases. Dependabot keeps the pins current.

## [1.0.0] - 2026-10-17

### Added

- `basedpyright-lsp` plugin that registers `basedpyright-langserver --stdio` for
  `.py` and `.pyi` files.
- `basedpyright-marketplace` marketplace for installing the plugin from GitHub.
- End-to-end LSP smoke test and CI on Linux, macOS and Windows.

[1.1.0]: https://github.com/datacas/claude-basedpyright-lsp/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/datacas/claude-basedpyright-lsp/releases/tag/v1.0.0
