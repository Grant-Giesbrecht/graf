"""Round-trip tests for error bar traces."""
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pytest

from graf.base import Graf, Axis
from .conftest import roundtrip, roundtrip_fig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _eb_fig(x, y, **kwargs):
    """One-axis figure with a single errorbar trace."""
    fig, ax = plt.subplots()
    ax.errorbar(x, y, **kwargs)
    return fig


def _first_trace(g):
    return list(g.axes['Ax0'].traces.values())[0]


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

class TestClassification:

    def test_axis_type_is_line2d_not_image(self, xy_err, tmp_path):
        """ErrorbarContainer puts LineCollections in ax.collections; must not
        trigger AXIS_IMAGE mis-classification."""
        x, y, x_err, y_err = xy_err
        g = roundtrip(_eb_fig(x, y, yerr=y_err, fmt='o'), tmp_path)
        assert g.axes['Ax0'].axis_type == Axis.AXIS_LINE2D

    def test_has_error_bars_flag(self, xy_err, tmp_path):
        x, y, x_err, y_err = xy_err
        g = roundtrip(_eb_fig(x, y, yerr=y_err, fmt='o'), tmp_path)
        assert _first_trace(g).has_error_bars == True

    def test_plain_line_has_no_error_bars(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        g = roundtrip(fig, tmp_path)
        assert _first_trace(g).has_error_bars == False


# ---------------------------------------------------------------------------
# Data fidelity
# ---------------------------------------------------------------------------

class TestDataFidelity:

    def test_xy_data_preserved(self, xy_err, tmp_path):
        x, y, _, y_err = xy_err
        g = roundtrip(_eb_fig(x, y, yerr=y_err, fmt='o'), tmp_path)
        t = _first_trace(g)
        assert np.allclose(t.x_data, x)
        assert np.allclose(t.y_data, y)

    def test_y_errors_recovered(self, xy_err, tmp_path):
        x, y, _, y_err = xy_err
        g = roundtrip(_eb_fig(x, y, yerr=y_err, fmt='o'), tmp_path)
        t = _first_trace(g)
        assert np.allclose(t.y_err_neg, y_err, atol=1e-6)
        assert np.allclose(t.y_err_pos, y_err, atol=1e-6)

    def test_asymmetric_y_errors_recovered(self, xy, tmp_path):
        x, y = xy
        y_neg = 0.05 * np.ones_like(x)
        y_pos = 0.20 * np.ones_like(x)
        fig, ax = plt.subplots()
        ax.errorbar(x, y, yerr=np.vstack([y_neg, y_pos]), fmt='o')
        g = roundtrip(fig, tmp_path)
        t = _first_trace(g)
        assert np.allclose(t.y_err_neg, y_neg, atol=1e-6)
        assert np.allclose(t.y_err_pos, y_pos, atol=1e-6)

    def test_x_errors_recovered(self, xy_err, tmp_path):
        x, y, x_err, _ = xy_err
        g = roundtrip(_eb_fig(x, y, xerr=x_err, fmt='o'), tmp_path)
        t = _first_trace(g)
        assert np.allclose(t.x_err_neg, x_err, atol=1e-6)
        assert np.allclose(t.x_err_pos, x_err, atol=1e-6)

    def test_xy_errors_both_recovered(self, xy_err, tmp_path):
        x, y, x_err, y_err = xy_err
        g = roundtrip(_eb_fig(x, y, xerr=x_err, yerr=y_err, fmt='o'), tmp_path)
        t = _first_trace(g)
        assert np.allclose(t.y_err_neg, y_err, atol=1e-6)
        assert np.allclose(t.x_err_neg, x_err, atol=1e-6)

    def test_x_errors_zero_when_y_only(self, xy_err, tmp_path):
        x, y, _, y_err = xy_err
        g = roundtrip(_eb_fig(x, y, yerr=y_err, fmt='o'), tmp_path)
        t = _first_trace(g)
        assert all(v == 0.0 for v in t.x_err_neg)
        assert all(v == 0.0 for v in t.x_err_pos)

    def test_y_errors_zero_when_x_only(self, xy_err, tmp_path):
        x, y, x_err, _ = xy_err
        g = roundtrip(_eb_fig(x, y, xerr=x_err, fmt='o'), tmp_path)
        t = _first_trace(g)
        assert all(v == 0.0 for v in t.y_err_neg)
        assert all(v == 0.0 for v in t.y_err_pos)


# ---------------------------------------------------------------------------
# Cap styling
# ---------------------------------------------------------------------------

class TestCapStyling:

    @pytest.mark.parametrize("capsize", [0, 3, 5, 8, 12])
    def test_cap_size_preserved(self, xy, tmp_path, capsize):
        x, y = xy
        g = roundtrip(_eb_fig(x, y, yerr=0.1, fmt='o', capsize=capsize), tmp_path)
        t = _first_trace(g)
        assert t.err_cap_size == pytest.approx(capsize, abs=0.5)

    @pytest.mark.parametrize("capthick", [1.0, 2.0, 3.5])
    def test_cap_width_preserved(self, xy, tmp_path, capthick):
        x, y = xy
        g = roundtrip(_eb_fig(x, y, yerr=0.1, fmt='o', capsize=5, capthick=capthick), tmp_path)
        t = _first_trace(g)
        assert t.err_cap_width == pytest.approx(capthick, abs=0.2)

    def test_cap_visible_when_capsize_nonzero(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(_eb_fig(x, y, yerr=0.1, fmt='o', capsize=5), tmp_path)
        assert _first_trace(g).err_cap_visible == True

    def test_no_caps_when_capsize_zero(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(_eb_fig(x, y, yerr=0.1, fmt='o', capsize=0), tmp_path)
        assert _first_trace(g).err_cap_size == pytest.approx(0, abs=0.1)


# ---------------------------------------------------------------------------
# Stem (bar line) styling
# ---------------------------------------------------------------------------

class TestStemStyling:

    @pytest.mark.parametrize("elinewidth", [1.0, 2.0, 3.5])
    def test_stem_linewidth_preserved(self, xy, tmp_path, elinewidth):
        x, y = xy
        g = roundtrip(_eb_fig(x, y, yerr=0.1, fmt='o', elinewidth=elinewidth), tmp_path)
        t = _first_trace(g)
        assert t.err_line_width == pytest.approx(elinewidth, abs=0.2)

    @pytest.mark.parametrize("ecolor,expected", [
        ('gray',   mcolors.to_rgb('gray')),
        ('red',    (1.0, 0.0, 0.0)),
        ('navy',   mcolors.to_rgb('navy')),
    ])
    def test_stem_color_preserved(self, xy, tmp_path, ecolor, expected):
        x, y = xy
        g = roundtrip(_eb_fig(x, y, yerr=0.1, fmt='o', ecolor=ecolor), tmp_path)
        t = _first_trace(g)
        assert t.err_line_color == pytest.approx(expected, abs=0.01)


# ---------------------------------------------------------------------------
# Main trace styling passed through
# ---------------------------------------------------------------------------

class TestMainTraceStyling:

    def test_fmt_marker_preserved(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(_eb_fig(x, y, yerr=0.1, fmt='s'), tmp_path)
        assert _first_trace(g).marker_type == '[]'  # 's' maps to '[]'

    def test_fmt_circle_preserved(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(_eb_fig(x, y, yerr=0.1, fmt='o'), tmp_path)
        assert _first_trace(g).marker_type == 'o'

    def test_line_color_preserved(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(_eb_fig(x, y, yerr=0.1, fmt='o', color='crimson'), tmp_path)
        expected = mcolors.to_rgb('crimson')
        assert _first_trace(g).line_color == pytest.approx(expected, abs=0.01)

    def test_display_name_preserved(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(_eb_fig(x, y, yerr=0.1, fmt='o', label='measured'), tmp_path)
        assert _first_trace(g).display_name == 'measured'

    def test_alpha_preserved(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(_eb_fig(x, y, yerr=0.1, fmt='o', alpha=0.6), tmp_path)
        assert _first_trace(g).alpha == pytest.approx(0.6, abs=0.02)


# ---------------------------------------------------------------------------
# Mixed plain line + errorbar on same axes
# ---------------------------------------------------------------------------

class TestMixed:

    def test_trace_count(self, xy_err, tmp_path):
        x, y, _, y_err = xy_err
        fig, ax = plt.subplots()
        ax.plot(x, np.cos(x), color='green', label='cos')
        ax.errorbar(x, y, yerr=y_err, fmt='o', color='purple', label='sin ± err')
        g = roundtrip(fig, tmp_path)
        assert len(g.axes['Ax0'].traces) == 2

    def test_errorbar_trace_flagged(self, xy_err, tmp_path):
        x, y, _, y_err = xy_err
        fig, ax = plt.subplots()
        ax.plot(x, np.cos(x))
        ax.errorbar(x, y, yerr=y_err, fmt='o')
        g = roundtrip(fig, tmp_path)
        traces = list(g.axes['Ax0'].traces.values())
        assert any(t.has_error_bars for t in traces)
        assert any(not t.has_error_bars for t in traces)

    def test_plain_trace_data_intact(self, xy_err, tmp_path):
        x, y, _, y_err = xy_err
        cos_y = np.cos(x)
        fig, ax = plt.subplots()
        ax.plot(x, cos_y, color='green')
        ax.errorbar(x, y, yerr=y_err, fmt='o', color='purple')
        g = roundtrip(fig, tmp_path)
        plain = next(t for t in g.axes['Ax0'].traces.values() if not t.has_error_bars)
        assert np.allclose(plain.y_data, cos_y)

    def test_errorbar_trace_data_intact(self, xy_err, tmp_path):
        x, y, _, y_err = xy_err
        fig, ax = plt.subplots()
        ax.plot(x, np.cos(x), color='green')
        ax.errorbar(x, y, yerr=y_err, fmt='o', color='purple')
        g = roundtrip(fig, tmp_path)
        eb = next(t for t in g.axes['Ax0'].traces.values() if t.has_error_bars)
        assert np.allclose(eb.y_data, y)
        assert np.allclose(eb.y_err_neg, y_err, atol=1e-6)


# ---------------------------------------------------------------------------
# Reconstruct (to_fig) without error
# ---------------------------------------------------------------------------

class TestReconstruct:

    def test_y_only_to_fig(self, xy_err, tmp_path):
        x, y, _, y_err = xy_err
        _, fig2 = roundtrip_fig(_eb_fig(x, y, yerr=y_err, fmt='o'), tmp_path)
        assert fig2 is not None

    def test_xy_errors_to_fig(self, xy_err, tmp_path):
        x, y, x_err, y_err = xy_err
        _, fig2 = roundtrip_fig(
            _eb_fig(x, y, xerr=x_err, yerr=y_err, fmt='s',
                    elinewidth=2, capsize=6, capthick=2),
            tmp_path)
        assert fig2 is not None

    def test_mixed_to_fig(self, xy_err, tmp_path):
        x, y, _, y_err = xy_err
        fig, ax = plt.subplots()
        ax.plot(x, np.cos(x), '-^', color='green')
        ax.errorbar(x, y, yerr=y_err, fmt='o', color='purple',
                    ecolor='violet', elinewidth=1, capsize=4, capthick=1.5)
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2 is not None
