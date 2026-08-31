"""The GUI dependencies are optional and must stay that way.

PyQt6 is 235 MB installed — more than the rest of GrAF combined — and nothing in
the save/load path needs it. These tests keep the boundary from eroding: it is
very easy for a convenience import in base.py to quietly make a GUI toolkit
mandatory for everyone who only wants to read a file.
"""
import os
import subprocess
import sys
from pathlib import Path

try:
    import tomllib                      # Python 3.11+
except ModuleNotFoundError:             # 3.10
    tomllib = None

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def pyproject():
    if tomllib is None:
        pytest.skip("tomllib requires Python 3.11+; GrAF supports 3.10")
    with open(ROOT / "pyproject.toml", "rb") as fh:
        return tomllib.load(fh)


class TestDependencyDeclaration:

    def test_gui_deps_are_not_required(self, pyproject):
        required = " ".join(pyproject["project"]["dependencies"]).lower()
        assert "pyqt6" not in required
        assert "mplcursors" not in required

    def test_gui_extra_exists(self, pyproject):
        extras = pyproject["project"]["optional-dependencies"]
        gui = " ".join(extras["gui"]).lower()
        assert "pyqt6" in gui
        assert "mplcursors" in gui

    def test_core_deps_still_declared(self, pyproject):
        """Whatever base.py imports at module scope must be a hard dependency."""
        required = " ".join(pyproject["project"]["dependencies"]).lower()
        for name in ("matplotlib", "numpy", "stardust-tools", "pylogfile", "colorama"):
            assert name in required


class TestImportIsolation:
    """Run in a subprocess so an earlier test importing graf.widgets cannot
    mask the result."""

    def run(self, code):
        # Inherit the real environment and override only what matters. Replacing
        # it wholesale breaks Python startup on Windows, which needs SYSTEMROOT,
        # and discards the virtualenv context on every platform.
        env = dict(os.environ, MPLBACKEND="Agg")
        return subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, cwd=str(ROOT), env=env,
        )

    def test_importing_graf_does_not_import_pyqt(self):
        result = self.run(
            "import sys, matplotlib; matplotlib.use('Agg');"
            "import graf;"
            "print(any(m.startswith('PyQt6') for m in sys.modules))"
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "False", (
            "importing graf pulled in PyQt6 — the GUI dependency has leaked "
            "into the core import path"
        )

    def test_importing_graf_base_does_not_import_pyqt(self):
        result = self.run(
            "import sys, matplotlib; matplotlib.use('Agg');"
            "import graf.base;"
            "print(any(m.startswith('PyQt6') for m in sys.modules))"
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "False"

    def test_save_and_load_need_no_gui(self, tmp_path):
        """The core promise must hold on a base install."""
        result = self.run(
            "import matplotlib; matplotlib.use('Agg');"
            "import graf, tempfile, os;"
            "import matplotlib.pyplot as plt;"
            "p = os.path.join(tempfile.mkdtemp(), 'x.graf');"
            "fig, ax = plt.subplots();"
            "ax.plot([1,2,3],[4,5,6]);"
            "graf.save_graf(fig, p);"
            "f2 = graf.load_graf(p);"
            "print(len(f2.axes[0].lines))"
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "1"


class TestHelpfulErrorWhenMissing:
    """A bare ModuleNotFoundError names a package the user never asked for."""

    def test_widgets_error_names_the_extra(self, monkeypatch):
        pytest.importorskip("PyQt6", reason="only meaningful when PyQt6 IS present")

        # Simulate the dependency being absent.
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name.startswith("PyQt6") or name == "mplcursors":
                raise ImportError(f"No module named {name!r}", name=name)
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        for mod in [m for m in list(sys.modules) if m.startswith("graf.widgets")]:
            monkeypatch.delitem(sys.modules, mod, raising=False)

        with pytest.raises(ImportError) as excinfo:
            import graf.widgets  # noqa: F401

        message = str(excinfo.value)
        assert "graf-format[gui]" in message, "error must name the install command"
        assert "pip install" in message


class TestViewerRefusesHeadless:
    """plt.show() on a headless matplotlib returns silently and displays
    nothing, which reads as a broken viewer rather than a missing extra."""

    def test_exits_nonzero_with_a_clear_message(self, capsys):
        from graf.scripts.grafviewer import main

        fixture = str(ROOT / "tests" / "data" / "legacy_format_0_0_0.graf")
        assert main([fixture]) == 1

        err = capsys.readouterr().err
        assert "graf-format[gui]" in err
        assert "headless" in err.lower()
