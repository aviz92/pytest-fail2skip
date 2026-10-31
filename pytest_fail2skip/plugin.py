"""Report failures of tests marked with ``@pytest.mark.fail2skip`` as skipped when ``--fail2skip`` is set.

The plugin only changes pytest's own test report. It has no knowledge of any reporting plugin:
the skip reason is exposed through ``report.user_properties`` so any consumer (JUnit XML, custom
reporters) can pick it up.
"""

from collections.abc import Generator

import pytest

FLAG = "--fail2skip"
MARKER_NAME = "fail2skip"
USER_PROPERTY_REASON = "fail2skip_reason"
DEFAULT_REASON = "no reason given"

_MARKER_HELP = (
    f"{MARKER_NAME}(reason=None, raises=None): when {FLAG} is set, report a failure of this test as skipped. "
    "Use raises=ExceptionType (or a tuple of types) to convert only that failure."
)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        FLAG,
        action="store_true",
        default=False,
        help=f"Report failures of tests marked with @pytest.mark.{MARKER_NAME} as skipped.",
    )


def pytest_configure(config: pytest.Config) -> None:
    # Registered unconditionally, so runs without the flag still work under --strict-markers.
    config.addinivalue_line("markers", _MARKER_HELP)


def _get_reason(marker: pytest.Mark) -> str:
    reason = marker.kwargs.get("reason") or (marker.args[0] if marker.args else None)
    return str(reason) if reason else DEFAULT_REASON


def _should_convert(item: pytest.Item, call: pytest.CallInfo[None], report: pytest.TestReport) -> bool:
    if not item.config.getoption(FLAG) or call.when != "call" or not report.failed:
        return False

    if (marker := item.get_closest_marker(MARKER_NAME)) is None:
        return False

    if (expected := marker.kwargs.get("raises")) is None:
        return True
    return call.excinfo is not None and call.excinfo.errisinstance(expected)


# Not tryfirst: as an inner wrapper this runs before outer (tryfirst) wrappers such as reporting
# plugins read the report, so they observe the final "skipped" outcome regardless of load order.
@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    report = yield

    if not _should_convert(item=item, call=call, report=report):
        return report

    reason = _get_reason(marker=item.get_closest_marker(MARKER_NAME))
    path, lineno, _ = item.reportinfo()
    report.outcome = "skipped"
    report.longrepr = (str(path), (lineno or 0) + 1, f"{MARKER_NAME}: {reason}")
    # The item carries it into later reports (JUnit XML reads it at teardown); the call report gets it directly.
    item.user_properties.append((USER_PROPERTY_REASON, reason))
    report.user_properties.append((USER_PROPERTY_REASON, reason))
    return report
