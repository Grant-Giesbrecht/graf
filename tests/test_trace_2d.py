"""Round-trip tests for 2-D line traces."""
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pytest

from graf.base import Graf, Axis
from .conftest import roundtrip, roundtrip_fig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_fig(x, y, **plot_kwargs):
    fig, ax = plt.subplots()
    ax.plot(x, y, **plot_kwargs)
    return fig


# ---------------------------------------------------------------------------
# Data fidelity
# ---------------------------------------------------------------------------

class TestDataFidelity:

    def test_x_y_preserved(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(make_fig(x, y), tmp_path)
        t = g.axes['Ax0'].traces['Tr0']
        assert np.allclose(t.x_data, x)
        assert np.allclose(t.y_data, y)

    def test_z_data_empty_for_2d(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(make_fig(x, y), tmp_path)
        assert g.axes['Ax0'].traces['Tr0'].z_data == []

    def test_single_point(self, tmp_path):
        fig, ax = plt.subplots()
        ax.plot([3.14], [2.72], 'o')
        g = roundtrip(fig, tmp_path)
        t = g.axes['Ax0'].traces['Tr0']
        assert np.isclose(t.x_data[0], 3.14)
        assert np.isclose(t.y_data[0], 2.72)

    def test_large_dataset(self, tmp_path):
        x = np.linspace(0, 100, 5000)
        fig, ax = plt.subplots()
        ax.plot(x, np.sin(x))
        g = roundtrip(fig, tmp_path)
        t = g.axes['Ax0'].traces['Tr0']
        assert len(t.x_data) == 5000
        assert np.allclose(t.x_data, x)

    def test_negative_values(self, tmp_path):
        x = np.linspace(-10, 10, 30)
        fig, ax = plt.subplots()
        ax.plot(x, x ** 3)
        g = roundtrip(fig, tmp_path)
        t = g.axes['Ax0'].traces['Tr0']
        assert np.allclose(t.y_data, x ** 3)

    def test_nan_in_data_preserved(self, tmp_path):
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([1.0, np.nan, 3.0, 4.0, 5.0])
        fig, ax = plt.subplots()
        ax.plot(x, y)
        g = roundtrip(fig, tmp_path)
        t = g.axes['Ax0'].traces['Tr0']
        assert np.isnan(t.x_data[2])
        assert np.isnan(t.y_data[1])


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

class TestLineStyle:

    @pytest.mark.parametrize("style", ['-', '--', '-.', ':'])
    def test_line_style_preserved(self, xy, tmp_path, style):
        x, y = xy
        g = roundtrip(make_fig(x, y, linestyle=style), tmp_path)
        assert g.axes['Ax0'].traces['Tr0'].line_type == style

    def test_line_width_preserved(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(make_fig(x, y, linewidth=3.5), tmp_path)
        assert g.axes['Ax0'].traces['Tr0'].line_width == pytest.approx(3.5, abs=0.05)

    def test_no_line(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, linestyle='None', marker='o')
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].traces['Tr0'].line_type == 'None'


class TestMarker:

    @pytest.mark.parametrize("mpl_marker,expected", [
        ('o', 'o'), ('+', '+'), ('^', '^'), ('v', 'v'),
        ('s', '[]'), ('.', '.'), ('x', 'x'), ('*', '*'),
        ('|', '|'), ('_', '_'),
    ])
    def test_marker_type_preserved(self, xy, tmp_path, mpl_marker, expected):
        x, y = xy
        g = roundtrip(make_fig(x, y, marker=mpl_marker), tmp_path)
        assert g.axes['Ax0'].traces['Tr0'].marker_type == expected

    def test_marker_size_preserved(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(make_fig(x, y, marker='o', markersize=9), tmp_path)
        assert g.axes['Ax0'].traces['Tr0'].marker_size == pytest.approx(9, abs=0.1)

    def test_no_marker(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(make_fig(x, y), tmp_path)
        assert g.axes['Ax0'].traces['Tr0'].marker_type == 'None'


class TestColor:

    @pytest.mark.parametrize("color,expected_rgb", [
        ('red',     (1.0, 0.0, 0.0)),
        ('blue',    (0.0, 0.0, 1.0)),
        ('green',   (0.0, 0.5019607843137255, 0.0)),
        ('#ff8800', (1.0, 8/15, 0.0)),
    ])
    def test_line_color_preserved(self, xy, tmp_path, color, expected_rgb):
        x, y = xy
        g = roundtrip(make_fig(x, y, color=color), tmp_path)
        assert g.axes['Ax0'].traces['Tr0'].line_color == pytest.approx(expected_rgb, abs=0.01)

    def test_marker_color_preserved(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, 'o', markerfacecolor='purple')
        g = roundtrip(fig, tmp_path)
        expected = mcolors.to_rgb('purple')
        assert g.axes['Ax0'].traces['Tr0'].marker_color == pytest.approx(expected, abs=0.01)

    def test_alpha_preserved(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(make_fig(x, y, alpha=0.4), tmp_path)
        assert g.axes['Ax0'].traces['Tr0'].alpha == pytest.approx(0.4, abs=0.01)


# ---------------------------------------------------------------------------
# Labels / metadata
# ---------------------------------------------------------------------------

class TestMetadata:

    def test_display_name_preserved(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(make_fig(x, y, label='my trace'), tmp_path)
        assert g.axes['Ax0'].traces['Tr0'].display_name == 'my trace'

    def test_axis_xlabel_preserved(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_xlabel('Time (s)')
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].x_axis.label == 'Time (s)'

    def test_axis_ylabel_preserved(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_ylabel('Amplitude')
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].y_axis_L.label == 'Amplitude'

    def test_title_preserved(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_title('My Plot')
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].title == 'My Plot'

    def test_unicode_title(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_title('α·β = γ²')
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].title == 'α·β = γ²'

    def test_supertitle_preserved(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        fig.suptitle('Super title')
        g = roundtrip(fig, tmp_path)
        assert g.supertitle == 'Super title'

    def test_axis_type_is_line2d(self, xy, tmp_path):
        x, y = xy
        g = roundtrip(make_fig(x, y), tmp_path)
        assert g.axes['Ax0'].axis_type == Axis.AXIS_LINE2D


# ---------------------------------------------------------------------------
# Axis limits
# ---------------------------------------------------------------------------

class TestAxisLimits:

    def test_xlim_preserved(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_xlim(-1, 8)
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].x_axis.val_min == pytest.approx(-1, abs=0.01)
        assert g.axes['Ax0'].x_axis.val_max == pytest.approx(8, abs=0.01)

    def test_ylim_preserved(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_ylim(-2, 2)
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].y_axis_L.val_min == pytest.approx(-2, abs=0.01)
        assert g.axes['Ax0'].y_axis_L.val_max == pytest.approx(2, abs=0.01)


# ---------------------------------------------------------------------------
# Multiple traces
# ---------------------------------------------------------------------------

class TestMultipleTraces:

    def test_two_traces_count(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, label='A')
        ax.plot(x, -y, label='B')
        g = roundtrip(fig, tmp_path)
        assert len(g.axes['Ax0'].traces) == 2

    def test_two_traces_data_independent(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, label='sin')
        ax.plot(x, np.cos(x), label='cos')
        g = roundtrip(fig, tmp_path)
        traces = list(g.axes['Ax0'].traces.values())
        assert np.allclose(traces[0].y_data, y)
        assert np.allclose(traces[1].y_data, np.cos(x))

    def test_two_traces_colors_independent(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, color='red')
        ax.plot(x, -y, color='blue')
        g = roundtrip(fig, tmp_path)
        traces = list(g.axes['Ax0'].traces.values())
        assert traces[0].line_color == pytest.approx((1, 0, 0), abs=0.01)
        assert traces[1].line_color == pytest.approx((0, 0, 1), abs=0.01)


# ---------------------------------------------------------------------------
# Twin axes
# ---------------------------------------------------------------------------

class TestTwinAxes:

    def test_twin_trace_count(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, color='blue', label='left')
        ax2 = ax.twinx()
        ax2.plot(x, y * 10, color='red', label='right')
        g = roundtrip(fig, tmp_path)
        assert len(g.axes['Ax0'].traces) == 2

    def test_twin_trace_use_yaxis_r(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, color='blue')
        ax2 = ax.twinx()
        ax2.plot(x, y * 5, color='red')
        g = roundtrip(fig, tmp_path)
        traces = list(g.axes['Ax0'].traces.values())
        left = [t for t in traces if not t.use_yaxis_R]
        right = [t for t in traces if t.use_yaxis_R]
        assert len(left) == 1
        assert len(right) == 1

    def test_twin_data_fidelity(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax2 = ax.twinx()
        ax2.plot(x, x ** 2)
        g = roundtrip(fig, tmp_path)
        right_trace = next(t for t in g.axes['Ax0'].traces.values() if t.use_yaxis_R)
        assert np.allclose(right_trace.y_data, x ** 2)


# ---------------------------------------------------------------------------
# Reconstruct without error
# ---------------------------------------------------------------------------

class TestReconstruct:

    def test_to_fig_does_not_raise(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, 'r--o', label='test', alpha=0.7)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title('Reconstruct test')
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2 is not None

    def test_grid_state_preserved(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.grid(True)
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].grid_on == True
