"""Reading files written before format 1.0.

The fixture is a genuine artefact: written by the pre-release GrAF at commit
2d8f59a using that version's own code, not synthesised to look old.

There is deliberately no migration code. stardust >= 0.2.0 keeps the default for
any field a file does not contain, so the fields added in format 1.0 simply take
their defaults and everything else loads normally. What remains is the check
AFTER loading: tolerant unpacking is only safe if the caller finds out what was
tolerated, and a load that quietly returns less data than the file contains is
the worst failure an archive format can have.
"""
import os
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pytest

from graf.base import (
    GRAF_FORMAT_VERSION,
    Graf,
    GrafFormatError,
    GrafVersionError,
    check_format_version,
    is_legacy_version,
)
from graf.fonts import SANS_SERIF

LEGACY = os.path.join(os.path.dirname(__file__), "data", "legacy_format_0_0_0.graf")


@pytest.fixture
def legacy():
    g = Graf()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        g.read_graf(LEGACY)
    return g


class TestLegacyFileLoads:

    def test_fixture_is_actually_legacy(self):
        from stardust.tome import tome_to_dict
        assert tome_to_dict(LEGACY)['info']['version'] == "0.0.0"

    def test_legacy_version_is_recognised(self):
        assert is_legacy_version("0.0.0")
        assert not is_legacy_version(GRAF_FORMAT_VERSION)

    def test_it_opens(self, legacy):
        assert legacy is not None

    def test_it_warns_and_names_the_upgrade_tool(self):
        g = Graf()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            g.read_graf(LEGACY)
        messages = " ".join(str(w.message) for w in caught)
        assert "pre-release" in messages
        assert "graf-upgrade" in messages

    def test_reading_does_not_modify_the_file(self):
        """Archives are read-only. Upgrading is an explicit, separate act."""
        before = os.path.getsize(LEGACY)
        mtime = os.path.getmtime(LEGACY)
        g = Graf()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            g.read_graf(LEGACY)
        assert os.path.getsize(LEGACY) == before
        assert os.path.getmtime(LEGACY) == mtime


class TestLegacyDataSurvives:
    """The data is the whole point of the format. None of it may be lost."""

    def test_all_traces_load(self, legacy):
        assert len(legacy.axes['Ax0'].traces) == 2

    def test_trace_data_is_intact(self, legacy):
        t = legacy.axes['Ax0'].traces['Tr0']
        assert len(t.x_data) == 40
        assert np.allclose(t.y_data, np.sin(np.array(t.x_data)), atol=1e-9)

    def test_second_trace_is_intact(self, legacy):
        t = legacy.axes['Ax0'].traces['Tr1']
        assert np.allclose(t.y_data, np.cos(np.array(t.x_data)), atol=1e-9)

    def test_scales_load(self, legacy):
        """Scales live in obj_manifest, which the old abort skipped entirely."""
        assert legacy.axes['Ax0'].x_axis.is_valid
        assert legacy.axes['Ax0'].x_axis.label == 'Frequency (GHz)'
        assert legacy.axes['Ax0'].y_axis_L.label == 'Power (dBm)'

    def test_titles_and_grid_survive(self, legacy):
        assert legacy.axes['Ax0'].title == 'Legacy figure'
        assert legacy.supertitle == 'Pre-release GrAF'
        assert legacy.axes['Ax0'].grid_on is True

    def test_trace_styling_survives(self, legacy):
        t = legacy.axes['Ax0'].traces['Tr0']
        assert t.line_type == '--'
        assert t.marker_type == 'o'
        assert t.display_name == 'measured'

    def test_description_survives(self, legacy):
        assert legacy.info.description == "written by pre-release GrAF"

    def test_provenance_survives(self, legacy):
        assert legacy.info.provenance.get('created_utc')

    def test_it_reconstructs(self, legacy):
        fig = legacy.to_fig()
        assert len(fig.axes[0].lines) == 2
        plt.close(fig)


class TestLegacyCosmeticsFallBackToDefaults:
    """Fonts and legend visibility were stored differently before 1.0. Both are
    cosmetic, so they default rather than being translated."""

    def test_fonts_default(self, legacy):
        assert legacy.style.title_font.family == [SANS_SERIF]
        assert legacy.style.title_font.weight == 400
        assert legacy.style.title_font.style == "normal"

    def test_legend_defaults_to_hidden(self, legacy):
        """Pre-1.0 never recorded legend visibility and never drew one, so
        hidden reproduces how the file actually rendered. Inferring a legend
        from trace labels would fabricate content the file does not contain."""
        assert legacy.axes['Ax0'].legend_on is False

    def test_reconstructed_figure_has_no_legend(self, legacy):
        fig = legacy.to_fig()
        assert fig.axes[0].get_legend() is None
        plt.close(fig)


class TestUnpackReporting:
    """Tolerating absence is only safe if the caller can see what was tolerated."""

    def test_report_lists_the_defaulted_fields(self, legacy):
        report = legacy.unpack_report
        assert not report.ok
        assert any('legend_on' in m for m in report.missing)
        assert any('family' in m for m in report.missing)

    def test_report_paths_are_qualified(self, legacy):
        assert any(m.startswith('style.') for m in legacy.unpack_report.missing)

    def test_no_errors_only_absences(self, legacy):
        """Nothing in the file was unusable; fields were merely absent."""
        assert legacy.unpack_report.errors == []

    def test_current_files_report_clean(self, tmp_path):
        fig, ax = plt.subplots()
        ax.plot([1, 2], [3, 4])
        path = str(tmp_path / "current.graf")
        Graf(fig=fig).write_graf(path)
        plt.close(fig)

        g = Graf()
        g.read_graf(path)
        assert g.unpack_report.ok, f"unexpected gaps: {g.unpack_report}"


class TestSilentDataLossIsStillCaught:
    """Defence in depth. stardust no longer abandons objects, but _verify_load
    stays: it is cheap, and it catches any future path that loses data."""

    def test_dropped_traces_raise(self, monkeypatch):
        from stardust.serializer import Packable
        original = Packable.unpack

        def lossy(self, data, strict=False):
            result = original(self, data, strict=strict)
            if 'traces' in getattr(self, 'dict_manifest', {}):
                self.traces = {}          # simulate a path that loses data
            return result

        monkeypatch.setattr(Packable, "unpack", lossy)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(GrafFormatError, match="silently lost"):
                Graf().read_graf(LEGACY)

    def test_error_names_the_affected_collection(self, monkeypatch):
        from stardust.serializer import Packable
        original = Packable.unpack

        def lossy(self, data, strict=False):
            result = original(self, data, strict=strict)
            if 'traces' in getattr(self, 'dict_manifest', {}):
                self.traces = {}
            return result

        monkeypatch.setattr(Packable, "unpack", lossy)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(GrafFormatError) as excinfo:
                Graf().read_graf(LEGACY)
        assert "traces" in str(excinfo.value)


class TestUnknownVersionsStillRefused:
    """Tolerance must not become a licence to accept anything."""

    def test_future_major_is_refused(self):
        with pytest.raises(GrafVersionError):
            check_format_version("2.0")

    def test_unknown_old_version_is_refused(self):
        """0.0.0 is explicitly supported; 0.5.0 is not, and must not half-load."""
        assert not is_legacy_version("0.5.0")
        with pytest.raises(GrafVersionError):
            check_format_version("0.5.0")
