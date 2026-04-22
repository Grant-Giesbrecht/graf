"""Edge case and adversarial input tests."""
import matplotlib.pyplot as plt
import numpy as np
import pytest

from graf.base import Graf
from .conftest import roundtrip, roundtrip_fig


# ---------------------------------------------------------------------------
# Data edge cases
# ---------------------------------------------------------------------------

class TestDataEdgeCases:

    def test_single_point_line(self, tmp_path):
        fig, ax = plt.subplots()
        ax.plot([2.5], [7.1], 'o')
        g = roundtrip(fig, tmp_path)
        t = list(g.axes['Ax0'].traces.values())[0]
        assert len(t.x_data) == 1
        assert np.isclose(t.x_data[0], 2.5)
        assert np.isclose(t.y_data[0], 7.1)

    def test_two_point_line(self, tmp_path):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        g = roundtrip(fig, tmp_path)
        t = list(g.axes['Ax0'].traces.values())[0]
        assert len(t.x_data) == 2

    def test_nan_in_middle_preserved(self, tmp_path):
        x = np.array([1.0, 2.0, np.nan, 4.0])
        y = np.array([1.0, 2.0, 3.0,    4.0])
        fig, ax = plt.subplots()
        ax.plot(x, y)
        g = roundtrip(fig, tmp_path)
        t = list(g.axes['Ax0'].traces.values())[0]
        assert np.isnan(t.x_data[2])

    def test_inf_in_data(self, tmp_path):
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([1.0, np.inf, 3.0])
        fig, ax = plt.subplots()
        ax.plot(x, y)
        g = roundtrip(fig, tmp_path)
        t = list(g.axes['Ax0'].traces.values())[0]
        assert np.isinf(t.y_data[1])

    def test_all_zeros(self, tmp_path):
        x = np.zeros(20)
        y = np.zeros(20)
        fig, ax = plt.subplots()
        ax.plot(x, y)
        g = roundtrip(fig, tmp_path)
        t = list(g.axes['Ax0'].traces.values())[0]
        assert np.allclose(t.x_data, 0)
        assert np.allclose(t.y_data, 0)

    def test_integer_data(self, tmp_path):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        fig, ax = plt.subplots()
        ax.plot(x, y)
        g = roundtrip(fig, tmp_path)
        t = list(g.axes['Ax0'].traces.values())[0]
        assert np.allclose(t.x_data, x)

    def test_very_small_values(self, tmp_path):
        x = np.linspace(1e-12, 1e-11, 20)
        y = np.sin(x / 1e-12)
        fig, ax = plt.subplots()
        ax.plot(x, y)
        g = roundtrip(fig, tmp_path)
        t = list(g.axes['Ax0'].traces.values())[0]
        assert np.allclose(t.x_data, x, rtol=1e-6)

    def test_very_large_values(self, tmp_path):
        x = np.linspace(1e8, 1e9, 20)
        y = x ** 2
        fig, ax = plt.subplots()
        ax.plot(x, y)
        g = roundtrip(fig, tmp_path)
        t = list(g.axes['Ax0'].traces.values())[0]
        assert np.allclose(t.x_data, x, rtol=1e-6)


# ---------------------------------------------------------------------------
# Label edge cases
# ---------------------------------------------------------------------------

class TestLabelEdgeCases:

    def test_empty_title(self, tmp_path):
        fig, ax = plt.subplots()
        ax.plot([1, 2], [1, 2])
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].title == ''

    def test_empty_axis_labels(self, tmp_path):
        fig, ax = plt.subplots()
        ax.plot([1, 2], [1, 2])
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].x_axis.label == ''
        assert g.axes['Ax0'].y_axis_L.label == ''

    @pytest.mark.parametrize("title", [
        'Simple title',
        'α·β = γ²',
        'Résumé: ñoño',
        'Title with "quotes" and \'apostrophe\'',
        'Backslash: n=10^{3}',
    ])
    def test_special_characters_in_title(self, tmp_path, title):
        fig, ax = plt.subplots()
        ax.plot([1, 2], [1, 2])
        ax.set_title(title)
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].title == title

    def test_long_label(self, tmp_path):
        long_label = 'A' * 200
        fig, ax = plt.subplots()
        ax.plot([1, 2], [1, 2])
        ax.set_xlabel(long_label)
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].x_axis.label == long_label

    def test_empty_display_name(self, tmp_path):
        fig, ax = plt.subplots()
        ax.plot([1, 2], [1, 2])
        g = roundtrip(fig, tmp_path)
        t = list(g.axes['Ax0'].traces.values())[0]
        # matplotlib auto-assigns '_line0' style labels; just check it round-trips
        assert isinstance(t.display_name, str)

    def test_unicode_supertitle(self, tmp_path):
        fig, ax = plt.subplots()
        ax.plot([1, 2], [1, 2])
        fig.suptitle('∑ μ σ² Δ')
        g = roundtrip(fig, tmp_path)
        assert g.supertitle == '∑ μ σ² Δ'


# ---------------------------------------------------------------------------
# Error bar edge cases
# ---------------------------------------------------------------------------

class TestErrorBarEdgeCases:

    def test_zero_length_errors(self, tmp_path):
        """All error values are zero — should not crash."""
        x = np.linspace(1, 5, 8)
        y = np.sin(x)
        fig, ax = plt.subplots()
        ax.errorbar(x, y, yerr=0.0, fmt='o')
        # Should save and reload without raising
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].traces

    def test_single_point_errorbar(self, tmp_path):
        fig, ax = plt.subplots()
        ax.errorbar([1.0], [2.0], yerr=[0.1], fmt='o', capsize=4)
        g = roundtrip(fig, tmp_path)
        t = list(g.axes['Ax0'].traces.values())[0]
        assert t.has_error_bars
        assert np.isclose(t.x_data[0], 1.0)

    def test_errorbar_no_line(self, tmp_path):
        """fmt='none' yields plotline=None; save/load should not crash."""
        x = np.linspace(1, 5, 6)
        y = np.sin(x)
        fig, ax = plt.subplots()
        ax.errorbar(x, y, yerr=0.1, fmt='none')
        # Just verify it round-trips without an exception
        g = roundtrip(fig, tmp_path)
        t = list(g.axes['Ax0'].traces.values())[0]
        assert t.has_error_bars == True

    def test_errorbar_to_fig_zero_errors(self, tmp_path):
        x = np.linspace(1, 5, 8)
        y = np.sin(x)
        fig, ax = plt.subplots()
        ax.errorbar(x, y, yerr=0.0, fmt='o')
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2 is not None


# ---------------------------------------------------------------------------
# Surface edge cases
# ---------------------------------------------------------------------------

class TestSurfaceEdgeCases:

    def test_small_pcolormesh(self, tmp_path):
        """Minimum viable 2×2 cell grid (3×3 corners)."""
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([0.0, 1.0, 2.0])
        X, Y = np.meshgrid(x, y)
        Z = X + Y
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z[:-1, :-1])
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert np.array(sf.z_grid).shape == (2, 2)

    def test_pcolormesh_negative_z(self, tmp_path):
        x = np.linspace(-2, 2, 15)
        y = np.linspace(-2, 2, 15)
        X, Y = np.meshgrid(x, y)
        Z = -np.exp(-X ** 2 - Y ** 2)
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert np.all(np.array(sf.z_grid) <= 0)

    def test_pcolormesh_with_alpha(self, tmp_path):
        x = np.linspace(0, 1, 10)
        X, Y = np.meshgrid(x, x)
        Z = X * Y
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z, alpha=0.5)
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.alpha == pytest.approx(0.5, abs=0.02)


# ---------------------------------------------------------------------------
# Multi-plot type combinations
# ---------------------------------------------------------------------------

class TestCombinations:

    def test_pcolormesh_plus_line_same_figure(self, tmp_path):
        """Two separate subplots — one pcolormesh, one line."""
        x = np.linspace(-2, 2, 20)
        X, Y = np.meshgrid(x, x)
        Z = np.exp(-X ** 2 - Y ** 2)

        fig, axes = plt.subplots(1, 2)
        axes[0].pcolormesh(X, Y, Z)
        axes[1].plot(x, np.sin(x))
        g = roundtrip(fig, tmp_path)
        assert len(g.axes) == 2

    def test_multiple_errorbars_same_axis(self, tmp_path):
        x = np.linspace(1, 5, 8)
        fig, ax = plt.subplots()
        ax.errorbar(x, np.sin(x), yerr=0.1, fmt='o', label='sin')
        ax.errorbar(x, np.cos(x), yerr=0.15, fmt='s', label='cos')
        g = roundtrip(fig, tmp_path)
        traces = list(g.axes['Ax0'].traces.values())
        assert len(traces) == 2
        assert all(t.has_error_bars for t in traces)

    def test_empty_figure_does_not_crash(self, tmp_path):
        """A Graf with no axes should save and reload cleanly."""
        fig = plt.figure()
        path = str(tmp_path / 'empty.graf')
        g = Graf(fig=fig)
        g.save_hdf(path)
        plt.close(fig)
        g2 = Graf()
        g2.load_hdf(path)
        assert len(g2.axes) == 0

    def test_to_fig_empty_figure(self, tmp_path):
        fig = plt.figure()
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2 is not None
