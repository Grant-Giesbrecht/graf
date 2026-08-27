"""Fidelity tests for the reconstruction path (Graf.to_fig / *.apply_to).

The rest of the suite verifies the *capture* path: that a matplotlib figure is
correctly turned into a Graf object. These tests verify the other half -- that a
Graf object is correctly turned back into a matplotlib figure -- by asserting on
the reconstructed figure itself rather than on the intermediate Graf.

This half was previously untested: `roundtrip_fig` was called throughout the
suite but the only assertion made on the result was `assert fig2 is not None`.
That is how legend loss went unnoticed.
"""
import matplotlib.pyplot as plt
from matplotlib.legend import Legend
import numpy as np
import pytest

from graf.base import Graf
from .conftest import roundtrip_fig


def rebuilt(fig, tmp_path, name="recon.graf"):
    """Round-trip a figure and return the reconstructed figure's first axes."""
    _, fig2 = roundtrip_fig(fig, tmp_path, name)
    return fig2.axes[0]


# ---------------------------------------------------------------------------
# Data survives to the rebuilt artists
# ---------------------------------------------------------------------------

class TestReconstructedData:

    def test_line_count(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.plot(x, y * 2)
        ax.plot(x, y * 3)
        assert len(rebuilt(fig, tmp_path).lines) == 3

    def test_xdata_matches(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        assert np.allclose(rebuilt(fig, tmp_path).lines[0].get_xdata(), x)

    def test_ydata_matches(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        assert np.allclose(rebuilt(fig, tmp_path).lines[0].get_ydata(), y)

    def test_multiple_traces_keep_their_own_data(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.plot(x, x ** 2)
        ax2 = rebuilt(fig, tmp_path)
        assert np.allclose(ax2.lines[0].get_ydata(), y)
        assert np.allclose(ax2.lines[1].get_ydata(), x ** 2)

    def test_trace_order_is_preserved(self, tmp_path):
        fig, ax = plt.subplots()
        for i in range(4):
            ax.plot([0, 1], [i, i])
        ax2 = rebuilt(fig, tmp_path)
        firsts = [ln.get_ydata()[0] for ln in ax2.lines]
        assert firsts == [0, 1, 2, 3]


# ---------------------------------------------------------------------------
# Styling survives
# ---------------------------------------------------------------------------

class TestReconstructedStyling:

    @pytest.mark.parametrize("style", ['-', '--', ':', '-.'])
    def test_line_style(self, xy, style, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, linestyle=style)
        assert rebuilt(fig, tmp_path).lines[0].get_linestyle() == style

    def test_line_width(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, linewidth=3.5)
        assert rebuilt(fig, tmp_path).lines[0].get_linewidth() == pytest.approx(3.5)

    def test_line_color(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, color='#FF00AA')
        got = rebuilt(fig, tmp_path).lines[0].get_color()
        assert np.allclose(got[:3], (1.0, 0.0, 2 / 3), atol=0.01)

    @pytest.mark.parametrize("marker", ['o', '^', 'v', 'x', '+', '*', '.'])
    def test_marker_type(self, xy, marker, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, marker=marker)
        assert rebuilt(fig, tmp_path).lines[0].get_marker() == marker

    def test_marker_size(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, marker='o', markersize=11)
        assert rebuilt(fig, tmp_path).lines[0].get_markersize() == pytest.approx(11)

    def test_alpha(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, alpha=0.35)
        assert rebuilt(fig, tmp_path).lines[0].get_alpha() == pytest.approx(0.35)

    def test_distinct_colors_stay_distinct(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, color='red')
        ax.plot(x, y * 2, color='blue')
        ax2 = rebuilt(fig, tmp_path)
        c0 = ax2.lines[0].get_color()
        c1 = ax2.lines[1].get_color()
        assert np.allclose(c0[:3], (1, 0, 0), atol=0.01)
        assert np.allclose(c1[:3], (0, 0, 1), atol=0.01)


# ---------------------------------------------------------------------------
# Labels, titles and axis configuration
# ---------------------------------------------------------------------------

class TestReconstructedLabels:

    def test_axis_labels(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_xlabel('Frequency (GHz)')
        ax.set_ylabel('Power (dBm)')
        ax2 = rebuilt(fig, tmp_path)
        assert ax2.get_xlabel() == 'Frequency (GHz)'
        assert ax2.get_ylabel() == 'Power (dBm)'

    def test_title(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_title('Measured response')
        assert rebuilt(fig, tmp_path).get_title() == 'Measured response'

    def test_unicode_labels(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_xlabel('λ (μm)')
        ax.set_title('Δ vs θ — 温度')
        ax2 = rebuilt(fig, tmp_path)
        assert ax2.get_xlabel() == 'λ (μm)'
        assert ax2.get_title() == 'Δ vs θ — 温度'

    def test_trace_labels(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, label='measured')
        ax.plot(x, y * 2, label='modelled')
        ax2 = rebuilt(fig, tmp_path)
        assert [ln.get_label() for ln in ax2.lines] == ['measured', 'modelled']

    def test_suptitle(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        fig.suptitle('Figure 4')
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2._suptitle is not None
        assert fig2._suptitle.get_text() == 'Figure 4'


class TestReconstructedAxes:

    def test_x_limits(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_xlim(-2, 9)
        assert rebuilt(fig, tmp_path).get_xlim() == pytest.approx((-2, 9))

    def test_y_limits(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_ylim(-5, 5)
        assert rebuilt(fig, tmp_path).get_ylim() == pytest.approx((-5, 5))

    def test_log_x_scale(self, tmp_path):
        fig, ax = plt.subplots()
        ax.plot([1, 10, 100], [1, 2, 3])
        ax.set_xscale('log')
        assert rebuilt(fig, tmp_path).get_xscale() == 'log'

    def test_log_y_scale(self, tmp_path):
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 10, 100])
        ax.set_yscale('log')
        assert rebuilt(fig, tmp_path).get_yscale() == 'log'

    def test_loglog(self, tmp_path):
        fig, ax = plt.subplots()
        ax.loglog([1, 10, 100], [1, 10, 100])
        ax2 = rebuilt(fig, tmp_path)
        assert ax2.get_xscale() == 'log'
        assert ax2.get_yscale() == 'log'

    @pytest.mark.parametrize("on", [True, False])
    def test_grid_state(self, xy, on, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.grid(on)
        ax2 = rebuilt(fig, tmp_path)
        gridlines = ax2.xaxis.get_gridlines()
        assert bool(gridlines) and gridlines[0].get_visible() == on


# ---------------------------------------------------------------------------
# Legends -- regression coverage
# ---------------------------------------------------------------------------

class TestReconstructedLegend:
    """`include_in_legend` was stored and manifested, but to_fig() never called
    ax.legend(), so every legend was silently lost on reload."""

    def test_legend_is_restored(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, label='measured')
        ax.legend()
        assert rebuilt(fig, tmp_path).get_legend() is not None

    def test_legend_entries_match(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, label='alpha')
        ax.plot(x, y * 2, label='beta')
        ax.legend()
        legend = rebuilt(fig, tmp_path).get_legend()
        assert [t.get_text() for t in legend.get_texts()] == ['alpha', 'beta']

    def test_absent_legend_stays_absent(self, xy, tmp_path):
        """A labelled trace without ax.legend() must not gain a legend."""
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, label='labelled but no legend call')
        assert rebuilt(fig, tmp_path).get_legend() is None

    @pytest.mark.parametrize("loc", ['upper right', 'upper left',
                                     'lower left', 'lower right', 'center'])
    def test_legend_location_preserved(self, xy, loc, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, label='a')
        ax.legend(loc=loc)
        legend = rebuilt(fig, tmp_path).get_legend()
        assert legend is not None
        assert legend._get_loc() == Legend.codes[loc]

    def test_twin_axes_get_one_combined_legend(self, xy, tmp_path):
        """Two overlapping legends is never what the author saw."""
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, label='left')
        ax2 = ax.twinx()
        ax2.plot(x, y * 10, label='right')
        ax.legend()
        _, fig2 = roundtrip_fig(fig, tmp_path)
        legends = [a.get_legend() for a in fig2.axes if a.get_legend() is not None]
        assert len(legends) == 1
        assert [t.get_text() for t in legends[0].get_texts()] == ['left', 'right']


# ---------------------------------------------------------------------------
# Subplots and figure-level structure
# ---------------------------------------------------------------------------

class TestReconstructedSubplots:

    def test_subplot_count(self, tmp_path):
        fig, axs = plt.subplots(2, 2)
        for i, a in enumerate(axs.flat):
            a.plot([0, 1], [i, i])
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert len(fig2.axes) == 4

    def test_each_subplot_keeps_its_own_data(self, tmp_path):
        fig, axs = plt.subplots(1, 3)
        for i, a in enumerate(axs.flat):
            a.plot([0, 1], [i * 10, i * 10])
        _, fig2 = roundtrip_fig(fig, tmp_path)
        firsts = sorted(a.lines[0].get_ydata()[0] for a in fig2.axes)
        assert firsts == [0, 10, 20]

    def test_each_subplot_keeps_its_own_title(self, tmp_path):
        fig, axs = plt.subplots(1, 2)
        axs[0].plot([0, 1], [0, 1])
        axs[0].set_title('left')
        axs[1].plot([0, 1], [1, 0])
        axs[1].set_title('right')
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert sorted(a.get_title() for a in fig2.axes) == ['left', 'right']

    def test_twin_axes_produce_two_axes(self, xy, tmp_path):
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.twinx().plot(x, y * 3)
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert len(fig2.axes) == 2


# ---------------------------------------------------------------------------
# Idempotence -- a reload must be stable
# ---------------------------------------------------------------------------

class TestRoundTripStability:

    def test_second_roundtrip_is_identical(self, xy, tmp_path):
        """Save -> load -> save -> load must not drift.

        Any accumulating loss shows up here as a mismatch on the second pass.
        """
        x, y = xy
        fig, ax = plt.subplots()
        ax.plot(x, y, 'r--o', label='trace')
        ax.set_xlabel('X')
        ax.set_title('T')
        ax.legend()
        ax.grid(True)

        g1, fig1 = roundtrip_fig(fig, tmp_path, "pass1.graf")

        p2 = str(tmp_path / "pass2.graf")
        g1.write_graf(p2)
        g2 = Graf()
        g2.read_graf(p2)
        fig2 = g2.to_fig()

        a1, a2 = fig1.axes[0], fig2.axes[0]
        assert np.allclose(a1.lines[0].get_ydata(), a2.lines[0].get_ydata())
        assert a1.get_xlabel() == a2.get_xlabel()
        assert a1.get_title() == a2.get_title()
        assert a1.lines[0].get_linestyle() == a2.lines[0].get_linestyle()
        assert a1.lines[0].get_marker() == a2.lines[0].get_marker()
        assert (a1.get_legend() is None) == (a2.get_legend() is None)
        plt.close(fig2)
