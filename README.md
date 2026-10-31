![PyPI version](https://img.shields.io/pypi/v/pytest-fail2skip)
![Python](https://img.shields.io/badge/python->=3.12-blue)
![Development Status](https://img.shields.io/badge/status-stable-green)
![Maintenance](https://img.shields.io/maintenance/yes/2026)
![PyPI](https://img.shields.io/pypi/dm/pytest-fail2skip)
![License](https://img.shields.io/pypi/l/pytest-fail2skip)

---

# 💡 pytest-fail2skip
A pytest plugin that reports failures of marked tests as **skipped**, so known failures don't block your CI gate.
The failure stays visible by default: conversion only happens when you opt in with `--fail2skip`.

---

## 📦 Installation
```bash
uv add pytest-fail2skip
```

---

## 🚀 Features
  - ✅ **Opt-in conversion** — failures are converted only when `--fail2skip` is passed; locally you still see the real failure
  - ✅ **Targeted with `raises=`** — convert only the expected exception; a new, different failure still fails the run
  - ✅ **Reason in the output** — shown in the `-rs` summary and exposed as the `fail2skip_reason` user property (JUnit XML, custom reporters)
  - ✅ **Strict-markers safe** — the marker is always registered, with or without the flag
  - ✅ **Standalone** — changes only pytest's own report; works with any reporting plugin

---

## 🛠️ How to Use
1. Mark the known-failing test:
   ```python
   import pytest

   @pytest.mark.fail2skip(reason="BUG-123: flaky upstream service", raises=ConnectionError)
   def test_sync_with_upstream():
       ...
   ```
2. Run normally to see the real result: `pytest`
3. In CI, opt in to the conversion: `pytest --fail2skip`

---

## ⚙️ Marker Reference
`@pytest.mark.fail2skip(reason=None, raises=None)`

| Argument | Description |
|---|---|
| `reason` | Shown as `fail2skip: <reason>`. Can also be passed positionally. Defaults to `no reason given`. |
| `raises` | An exception type or tuple of types. When set, only these failures are converted. |

Behavior when `--fail2skip` is set:

| Test result | Reported as |
|---|---|
| Fails in the test body (and matches `raises`, if given) | skipped |
| Fails with an exception not in `raises` | failed |
| Passes | passed |
| Errors in setup/teardown (e.g. a broken fixture) | error — not converted |

The marker can also be applied to a class, or to a whole module with `pytestmark`.

---

## 🤔 fail2skip vs. `xfail`
`@pytest.mark.xfail` is close, but differs in two ways that matter for a release gate:

- **Default direction** — `xfail` hides the failure unless you pass `--runxfail`. `fail2skip` shows it unless you pass `--fail2skip`, so forgetting the flag fails loudly instead of silently.
- **Passing tests** — a passing `xfail` test is reported as XPASS; a passing `fail2skip` test is simply passed.

If neither matters to you, `xfail(raises=..., strict=False)` is the built-in alternative.

---

## ▶️ Usage Examples
### Convert only expected exceptions
Pass a single exception type:
```python
import pytest

@pytest.mark.fail2skip(reason="BUG-123: upstream service is unstable", raises=ConnectionError)
def test_sync_with_upstream():
    ...
```

Or a tuple, to convert any of several known failures:
```python
import pytest

@pytest.mark.fail2skip(
    reason="BUG-456: device sometimes drops the session",
    raises=(ConnectionError, TimeoutError),
)
def test_device_handshake():
    ...
```
Subclasses match too (`ConnectionResetError` is converted by `raises=ConnectionError`).
Any other failure, such as an `AssertionError` from a real regression, still fails the run.

### Enable in `pytest.ini` for CI
```ini
[pytest]
addopts =
    --fail2skip
```

### Read the reason from a custom plugin
```python
def pytest_runtest_logreport(report):
    reason = dict(report.user_properties).get("fail2skip_reason")
    if report.skipped and reason:
        print(f"{report.nodeid} was converted: {reason}")
```

---

## 🔁 Migrating from pytest-plugins
This plugin was previously the `fail2skip` feature of `pytest-plugins`. Both register the `--fail2skip` option,
so don't install them together until you're on a `pytest-plugins` release without `fail2skip`.
Changes when migrating:
- Converted tests are now reported as `skipped` instead of `xfailed`.
- The pytest-plugins report records them as `skipped` (not `failed-skipped`); the reason is available via `user_properties`.

---

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-addition`
3. Make your changes
4. Commit your changes: `git commit -m 'Add my addition'`
5. Push to the branch: `git push origin feature/my-addition`
6. Open a Pull Request

Additions that promote clean, productive, and maintainable development are always welcome.

---

## 📄 License
MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Thanks
Thanks for exploring this repository! <br>
Happy coding!

[![GitHub](https://img.shields.io/badge/GitHub-aviz92-181717?logo=github)](https://github.com/aviz92)
&nbsp; [![PyPI](https://img.shields.io/badge/PyPI-aviz-3775A9?logo=pypi)](https://pypi.org/user/aviz/)
&nbsp; [![Blog](https://img.shields.io/badge/Blog-aviz92.github.io-0066CC?logo=googlechrome)](https://aviz92.github.io/)
&nbsp; [![LinkedIn](https://img.shields.io/badge/LinkedIn-avi--zaguri-0A66C2?logo=linkedin)](https://www.linkedin.com/in/avi-zaguri-41869b11b)
