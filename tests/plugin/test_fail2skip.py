import pytest

FAILING_MARKED_TEST = """
import pytest

@pytest.mark.fail2skip(reason="known bug")
def test_known_failure():
    assert False
"""


class TestConversion:
    def test_failing_marked_test_becomes_skipped(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(FAILING_MARKED_TEST)
        result = pytester.runpytest_subprocess("--fail2skip")
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"
        result.assert_outcomes(skipped=1)

    def test_passing_marked_test_remains_passed(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.fail2skip
            def test_should_pass():
                assert True
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip")
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"
        result.assert_outcomes(passed=1)

    def test_without_flag_failure_remains_failure(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(FAILING_MARKED_TEST)
        result = pytester.runpytest_subprocess()
        assert result.ret == pytest.ExitCode.TESTS_FAILED, f"Expected TESTS_FAILED, got {result.ret}"
        result.assert_outcomes(failed=1)

    def test_unmarked_failing_test_unaffected_by_flag(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_should_fail():
                assert False
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip")
        assert result.ret == pytest.ExitCode.TESTS_FAILED, f"Expected TESTS_FAILED, got {result.ret}"
        result.assert_outcomes(failed=1)

    def test_multiple_marked_tests_all_become_skipped(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.fail2skip
            def test_fail_1():
                assert False

            @pytest.mark.fail2skip
            def test_fail_2():
                assert False

            def test_pass():
                assert True
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip")
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"
        result.assert_outcomes(skipped=2, passed=1)

    def test_class_level_marker_applies_to_methods(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.fail2skip
            class TestKnownBroken:
                def test_a(self):
                    assert False

                def test_b(self):
                    assert True
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip")
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"
        result.assert_outcomes(skipped=1, passed=1)

    def test_module_level_marker_applies_to_all_tests(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            pytestmark = pytest.mark.fail2skip(reason="module under rework")

            def test_a():
                assert False

            def test_b():
                assert False
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip")
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"
        result.assert_outcomes(skipped=2)

    def test_setup_failure_is_not_converted(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.fixture
            def broken():
                raise RuntimeError("fixture failed")

            @pytest.mark.fail2skip
            def test_uses_broken_fixture(broken):
                assert True
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip")
        assert result.ret == pytest.ExitCode.TESTS_FAILED, f"Expected TESTS_FAILED, got {result.ret}"
        result.assert_outcomes(errors=1)

    def test_converted_failures_do_not_count_toward_exitfirst(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.fail2skip
            def test_fail_1():
                assert False

            @pytest.mark.fail2skip
            def test_fail_2():
                assert False

            def test_pass():
                assert True
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip", "-x")
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"
        result.assert_outcomes(skipped=2, passed=1)


class TestReason:
    def test_keyword_reason_in_skip_summary(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(FAILING_MARKED_TEST)
        result = pytester.runpytest_subprocess("--fail2skip", "-rs")
        result.stdout.fnmatch_lines(["*SKIPPED*fail2skip: known bug*"])

    def test_positional_reason_in_skip_summary(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.fail2skip("tracked in BUG-123")
            def test_known_failure():
                assert False
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip", "-rs")
        result.stdout.fnmatch_lines(["*SKIPPED*fail2skip: tracked in BUG-123*"])

    def test_default_reason_when_none_given(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.fail2skip
            def test_known_failure():
                assert False
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip", "-rs")
        result.stdout.fnmatch_lines(["*SKIPPED*fail2skip: no reason given*"])

    def test_reason_exposed_as_user_property(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(FAILING_MARKED_TEST)
        junit_path = pytester.path / "junit.xml"
        result = pytester.runpytest_subprocess("--fail2skip", f"--junitxml={junit_path}")
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"
        expected_property = '<property name="fail2skip_reason" value="known bug"'
        assert junit_path.read_text().count(expected_property) == 1, "Expected the reason property exactly once"


class TestRaises:
    def test_matching_exception_is_converted(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.fail2skip(raises=ZeroDivisionError)
            def test_known_failure():
                1 / 0
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip")
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"
        result.assert_outcomes(skipped=1)

    def test_other_exception_still_fails(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.fail2skip(raises=ZeroDivisionError)
            def test_new_failure():
                raise KeyError("unexpected")
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip")
        assert result.ret == pytest.ExitCode.TESTS_FAILED, f"Expected TESTS_FAILED, got {result.ret}"
        result.assert_outcomes(failed=1)

    def test_tuple_of_exceptions(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.fail2skip(raises=(KeyError, ZeroDivisionError))
            def test_known_failure():
                raise KeyError("known")
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip")
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"
        result.assert_outcomes(skipped=1)


class TestMarkerRegistration:
    def test_marker_registered_without_flag_under_strict_markers(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(FAILING_MARKED_TEST)
        result = pytester.runpytest_subprocess("--strict-markers")
        assert result.ret == pytest.ExitCode.TESTS_FAILED, f"Expected TESTS_FAILED, got {result.ret}"
        result.assert_outcomes(failed=1)

    def test_marker_listed_in_markers_help(self, pytester: pytest.Pytester) -> None:
        result = pytester.runpytest_subprocess("--markers")
        result.stdout.fnmatch_lines(["*@pytest.mark.fail2skip(reason=None, raises=None)*"])


REPORTER_PROBE = """
from pathlib import Path

import pytest


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        with Path("probe_outcomes.txt").open("a") as probe_file:
            probe_file.write(f"{report.outcome}\\n")
"""


class TestReporterInteraction:
    """A reporting plugin wrapping makereport with tryfirst (like pytest-plugins' report) must see the final outcome."""

    def test_reporter_loaded_after_plugin_sees_skipped(self, pytester: pytest.Pytester) -> None:
        pytester.makeconftest(REPORTER_PROBE)
        pytester.makepyfile(FAILING_MARKED_TEST)
        result = pytester.runpytest_subprocess("--fail2skip")
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"
        assert (pytester.path / "probe_outcomes.txt").read_text().split() == ["skipped"]

    def test_reporter_loaded_before_plugin_sees_skipped(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pytester.makepyfile(reporter_probe=REPORTER_PROBE, test_known=FAILING_MARKED_TEST)
        monkeypatch.setenv("PYTHONPATH", str(pytester.path))
        result = pytester.runpytest_subprocess("--fail2skip", "-p", "reporter_probe")
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"
        assert (pytester.path / "probe_outcomes.txt").read_text().split() == ["skipped"]


class TestRaisesSubclass:
    def test_subclass_of_expected_exception_is_converted(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.fail2skip(raises=ConnectionError)
            def test_known_failure():
                raise ConnectionResetError("peer reset")
        """
        )
        result = pytester.runpytest_subprocess("--fail2skip")
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"
        result.assert_outcomes(skipped=1)
