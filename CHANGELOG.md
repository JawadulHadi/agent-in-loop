# Changelog

All notable changes to agent-in-loop. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The project has no version tags yet, so
past entries are grouped by merged pull request and date.

Every change adds an entry under **Unreleased** in the same pull request. CI checks this.

## [Unreleased]

### Added
- `CHANGELOG.md` (this file), a pull request template, and a CI job that fails a pull request
  which changes code but not the changelog. Label a PR `skip-changelog` to bypass it.
- README "Changelog and contributing" section.

### Security
- The `changelog` CI workflow now limits its token to read-only repository access.

## PR #2 (2026-10-12)

### Added
- First real `NOTES.md` entries: the CI runs that failed in seconds because of a GitHub billing
  lock, and the README line count that was 30% off.

## PR #1 (2026-10-11)

### Added
- MIT license.

### Changed
- Wider `.gitignore`.

### Fixed
- README said "about 250 lines"; the code is about 330 lines.

## Initial commit (2026-10-11)

### Added
- Tool-calling agent loop in plain Python: JSON protocol with a tolerant parser, sandboxed tools,
  step, error and token caps, human confirmation for risky tools, JSONL trace, and a scripted LLM
  for network-free tests.
