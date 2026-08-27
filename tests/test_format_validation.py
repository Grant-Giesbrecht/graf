"""Tests for GrAF file validation, versioning, and the public API surface.

GrAF's promise is that a figure opens years later on another machine. A file
this library cannot correctly interpret must therefore fail loudly rather than
half-load and quietly lose data -- these tests pin that behaviour down.
"""
import os
import warnings

import matplotlib.pyplot as plt
import pytest

import graf
from graf.base import (
    GRAF_FORMAT_VERSION,
    GrafError,
    GrafFormatError,
    GrafVersionError,
    Graf,
    _library_version,
    _parse_format_version,
    check_format_version,
)
from .conftest import roundtrip


def simple_fig():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    return fig


def written_file(tmp_path, name="v.graf"):
    path = str(tmp_path / name)
    fig = simple_fig()
    Graf(fig=fig).write_graf(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Version identity
# ---------------------------------------------------------------------------

class TestVersionIdentity:

    def test_format_and_library_versions_are_distinct_concepts(self):
        """The on-disk layout version must not be tied to the package version."""
        assert GRAF_FORMAT_VERSION == "1.0"
        assert graf.__version__ != "0.0.0"

    def test_library_version_matches_installed_distribution(self):
        from importlib.metadata import version
        assert _library_version() == version("graf-format")

    def test_package_exposes_version(self):
        assert graf.__version__ == _library_version()

    def test_file_records_format_version(self, tmp_path):
        g = roundtrip(simple_fig(), tmp_path)
        assert g.info.version == GRAF_FORMAT_VERSION

    def test_file_records_library_version(self, tmp_path):
        g = roundtrip(simple_fig(), tmp_path)
        assert g.info.source_version == _library_version()


class TestVersionParsing:

    @pytest.mark.parametrize("value,expected", [
        ("1.0", (1, 0)), ("1.7", (1, 7)), ("2.0", (2, 0)),
        ("10.3", (10, 3)), ("3", (3, 0)),
    ])
    def test_parses_valid(self, value, expected):
        assert _parse_format_version(value) == expected

    @pytest.mark.parametrize("value", ["", "abc", "1.x", None, "v1.0"])
    def test_rejects_invalid(self, value):
        with pytest.raises(GrafVersionError):
            _parse_format_version(value)


class TestVersionCompatibility:

    def test_same_version_is_silent(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            check_format_version(GRAF_FORMAT_VERSION)

    def test_older_minor_is_silent(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            check_format_version("1.0")

    def test_newer_minor_warns_but_passes(self):
        """Minor bumps are additive: read the data, warn about missed fields."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            check_format_version("1.99")
        assert len(caught) == 1
        assert "newer" in str(caught[0].message)

    @pytest.mark.parametrize("bad", ["2.0", "3.1", "0.9"])
    def test_different_major_is_refused(self, bad):
        with pytest.raises(GrafVersionError):
            check_format_version(bad)

    def test_version_error_is_a_format_error(self):
        """Callers catching GrafFormatError should also catch version failures."""
        assert issubclass(GrafVersionError, GrafFormatError)
        assert issubclass(GrafFormatError, GrafError)


# ---------------------------------------------------------------------------
# Reader validation
# ---------------------------------------------------------------------------

class TestReadValidation:

    def test_missing_file_raises_filenotfound(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            Graf().read_graf(str(tmp_path / "does_not_exist.graf"))

    def test_directory_raises_format_error(self, tmp_path):
        d = tmp_path / "adir.graf"
        d.mkdir()
        with pytest.raises(GrafFormatError):
            Graf().read_graf(str(d))

    def test_garbage_file_raises_format_error(self, tmp_path):
        p = tmp_path / "junk.graf"
        p.write_text("this is definitely not a GrAF document")
        with pytest.raises(GrafFormatError):
            Graf().read_graf(str(p))

    def test_empty_file_raises_format_error(self, tmp_path):
        p = tmp_path / "empty.graf"
        p.write_bytes(b"")
        with pytest.raises(GrafFormatError):
            Graf().read_graf(str(p))

    def test_unexpected_extension_warns(self, tmp_path):
        """Readable content with the wrong extension warns but still loads."""
        src = written_file(tmp_path)
        dst = str(tmp_path / "renamed.dat")
        os.rename(src, dst)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            g = Graf()
            g.read_graf(dst)
        assert any("extension" in str(w.message) for w in caught)
        assert g.info.version == GRAF_FORMAT_VERSION

    def test_valid_file_reads_without_warning(self, tmp_path):
        path = written_file(tmp_path)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Graf().read_graf(path)
        assert not caught

    def test_error_message_names_the_file(self, tmp_path):
        p = tmp_path / "named.graf"
        p.write_text("nonsense")
        with pytest.raises(GrafFormatError, match="named.graf"):
            Graf().read_graf(str(p))


# ---------------------------------------------------------------------------
# Public API surface -- these names are a compatibility promise after v0.1.0
# ---------------------------------------------------------------------------

class TestPublicAPI:

    @pytest.mark.parametrize("name", [
        "Graf", "GraphStyle", "Font", "Axis", "Trace", "Surface", "Scale",
        "MetaInfo", "save_graf", "load_graf", "available_font_families",
        "GrafFormatError", "GrafVersionError", "GRAF_FORMAT_VERSION",
        "__version__",
    ])
    def test_exported_from_package_root(self, name):
        assert hasattr(graf, name), f"graf.{name} is missing from the public API"
        assert name in graf.__all__

    def test_save_and_load_from_package_root(self, tmp_path):
        """The documented one-liner must work without importing graf.base."""
        path = str(tmp_path / "api.graf")
        fig = simple_fig()
        graf.save_graf(fig, path)
        plt.close(fig)
        assert os.path.isfile(path)
        fig2 = graf.load_graf(path)
        assert fig2 is not None
        plt.close(fig2)

    def test_save_graf_records_source_format(self, tmp_path):
        path = str(tmp_path / "sf.graf")
        fig = simple_fig()
        graf.save_graf(fig, path)
        plt.close(fig)
        g = Graf()
        g.read_graf(path)
        assert g.info.provenance.get("source_format") == "matplotlib_figure"


# ---------------------------------------------------------------------------
# The library must not print
# ---------------------------------------------------------------------------

class TestQuiet:

    def test_write_is_silent_by_default(self, tmp_path, capsys):
        fig = simple_fig()
        Graf(fig=fig).write_graf(str(tmp_path / "quiet.graf"))
        plt.close(fig)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_debug_print_opt_in_produces_output(self, tmp_path, capsys):
        fig = simple_fig()
        Graf(fig=fig).write_graf(str(tmp_path / "loud.graf"), debug_print=True)
        plt.close(fig)
        assert len(capsys.readouterr().out) > 0

    def test_roundtrip_is_silent(self, tmp_path, capsys):
        fig = simple_fig()
        g = Graf(fig=fig)
        path = str(tmp_path / "rt.graf")
        g.write_graf(path)
        plt.close(fig)
        g2 = Graf()
        g2.read_graf(path)
        fig2 = g2.to_fig()
        plt.close(fig2)
        captured = capsys.readouterr()
        assert captured.out == "", f"library printed to stdout: {captured.out[:200]!r}"
