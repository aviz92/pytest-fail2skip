# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-31

First standalone release. Extracted from the `fail2skip` feature of [pytest-plugins](https://github.com/aviz92/pytest-plugins).

### Added
- `raises=` marker argument: convert only the given exception type(s); any other failure still fails the run.
- Positional reason: `@pytest.mark.fail2skip("reason")`.
- The skip reason is exposed as the `fail2skip_reason` user property (shows up in JUnit XML and any reporter that reads `user_properties`).

### Changed
- Converted tests are reported as **skipped** (previously shown as xfailed).
- No dependency on the pytest-plugins report: the plugin only changes pytest's own test report, and runs before outer report wrappers regardless of plugin load order.

### Fixed
- The `fail2skip` marker is registered even without `--fail2skip`, so runs under `--strict-markers` no longer error at collection.

---
