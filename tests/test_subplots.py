"""Round-trip tests for multi-axis subplot layouts."""
import matplotlib.pyplot as plt
import numpy as np
import pytest

from graf.base import Graf
from .conftest import roundtrip, roundtrip_fig


def _xy(n=40):
    x = np.linspace(0, 2 * np.pi, n)
    return x, np.sin(x)


# ---------------------------------------------------------------------------
# Axis count
# ---------------------------------------------------------------------------

class TestAxisCount:

    def test_single_axis(self, tmp_path):
        x, y = _xy()
        fig, ax = plt.subplots()
        ax.plot(x, y)
        g = roundtrip(fig, tmp_path)
        assert len(g.axes) == 1

    def test_two_axes_row(self, tmp_path):
        x, y = _xy()
        fig, axes = plt.subplots(1, 2)
        axes[0].plot(x, y)
        axes[1].plot(x, -y)
        g = roundtrip(fig, tmp_path)
        assert len(g.axes) == 2

    def test_two_axes_col(self, tmp_path):
        x, y = _xy()
        fig, axes = plt.subplots(2, 1)
        axes[0].plot(x, y)
        axes[1].plot(x, -y)
        g = roundtrip(fig, tmp_path)
        assert len(g.axes) == 2

    def test_four_axes_grid(self, tmp_path):
        x, y = _xy()
        fig, axes = plt.subplots(2, 2)
        for ax in axes.flat:
            ax.plot(x, y)
        g = roundtrip(fig, tmp_path)
        assert len(g.axes) == 4

    def test_three_axes_mixed(self, tmp_path):
        x, y = _xy()
        fig, axes = plt.subplots(1, 3)
        for ax in axes:
            ax.plot(x, y)
        g = roundtrip(fig, tmp_path)
        assert len(g.axes) == 3


# ---------------------------------------------------------------------------
# Position tracking
# ---------------------------------------------------------------------------

class TestPositions:

    def test_positions_1x2(self, tmp_path):
        x, y = _xy()
        fig, axes = plt.subplots(1, 2)
        axes[0].plot(x, y, label='left')
        axes[1].plot(x, -y, label='right')
        g = roundtrip(fig, tmp_path)
        positions = sorted([ax.position for ax in g.axes.values()])
        assert [0, 0] in positions
        assert [0, 1] in positions

    def test_positions_2x1(self, tmp_path):
        x, y = _xy()
        fig, axes = plt.subplots(2, 1)
        axes[0].plot(x, y)
        axes[1].plot(x, -y)
        g = roundtrip(fig, tmp_path)
        positions = sorted([ax.position for ax in g.axes.values()])
        assert [0, 0] in positions
        assert [1, 0] in positions

    def test_positions_2x2(self, tmp_path):
        x, y = _xy()
        fig, axes = plt.subplots(2, 2)
        for ax in axes.flat:
            ax.plot(x, y)
        g = roundtrip(fig, tmp_path)
        expected = {(0, 0), (0, 1), (1, 0), (1, 1)}
        actual = {tuple(ax.position) for ax in g.axes.values()}
        assert actual == expected


# ---------------------------------------------------------------------------
# Data independence
# ---------------------------------------------------------------------------

class TestDataIndependence:

    def test_each_axis_has_correct_data(self, tmp_path):
        x = np.linspace(0, 2 * np.pi, 30)
        y_vals = [np.sin(x), np.cos(x), x ** 2]
        fig, axes = plt.subplots(1, 3)
        for ax, y in zip(axes, y_vals):
            ax.plot(x, y)
        g = roundtrip(fig, tmp_path)

        # Build a map: position → y_data
        data_by_pos = {}
        for axobj in g.axes.values():
            col = axobj.position[1]
            t = list(axobj.traces.values())[0]
            data_by_pos[col] = t.y_data

        assert np.allclose(data_by_pos[0], y_vals[0])
        assert np.allclose(data_by_pos[1], y_vals[1])
        assert np.allclose(data_by_pos[2], y_vals[2])

    def test_each_axis_labels_independent(self, tmp_path):
        x, y = _xy()
        fig, axes = plt.subplots(1, 2)
        axes[0].set_xlabel('Time')
        axes[0].set_ylabel('Velocity')
        axes[0].plot(x, y)
        axes[1].set_xlabel('Frequency')
        axes[1].set_ylabel('Power')
        axes[1].plot(x, -y)
        g = roundtrip(fig, tmp_path)

        # Match axes by column position
        ax_left  = next(a for a in g.axes.values() if a.position[1] == 0)
        ax_right = next(a for a in g.axes.values() if a.position[1] == 1)

        assert ax_left.x_axis.label == 'Time'
        assert ax_left.y_axis_L.label == 'Velocity'
        assert ax_right.x_axis.label == 'Frequency'
        assert ax_right.y_axis_L.label == 'Power'

    def test_each_axis_title_independent(self, tmp_path):
        x, y = _xy()
        fig, axes = plt.subplots(1, 2)
        axes[0].plot(x, y)
        axes[0].set_title('Left')
        axes[1].plot(x, -y)
        axes[1].set_title('Right')
        g = roundtrip(fig, tmp_path)

        ax_left  = next(a for a in g.axes.values() if a.position[1] == 0)
        ax_right = next(a for a in g.axes.values() if a.position[1] == 1)
        assert ax_left.title == 'Left'
        assert ax_right.title == 'Right'


# ---------------------------------------------------------------------------
# Reconstruct
# ---------------------------------------------------------------------------

class TestReconstructSubplots:

    def test_1x2_to_fig_does_not_raise(self, tmp_path):
        x, y = _xy()
        fig, axes = plt.subplots(1, 2)
        axes[0].plot(x, y, 'b-')
        axes[1].plot(x, -y, 'r--')
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2 is not None

    def test_2x2_to_fig_does_not_raise(self, tmp_path):
        x, y = _xy()
        fig, axes = plt.subplots(2, 2)
        for i, ax in enumerate(axes.flat):
            ax.plot(x, y * (i + 1))
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2 is not None

    def test_reconstructed_axis_count(self, tmp_path):
        x, y = _xy()
        fig, axes = plt.subplots(1, 3)
        for ax in axes:
            ax.plot(x, y)
        g, fig2 = roundtrip_fig(fig, tmp_path)
        # Each of the 3 data axes should be recreated (colorbars don't apply here)
        assert len(g.axes) == 3
