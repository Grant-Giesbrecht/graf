"""Round-trip tests for 3-D line traces."""
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pytest

from graf.base import Graf, Axis
from .conftest import roundtrip, roundtrip_fig


def _make_3d_fig(x, y, z, **plot_kwargs):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(x, y, z, **plot_kwargs)
    return fig


class TestData3D:

    def test_xyz_data_preserved(self, tmp_path):
        t = np.linspace(0, 4 * np.pi, 60)
        x, y, z = np.cos(t), np.sin(t), t / (4 * np.pi)
        g = roundtrip(_make_3d_fig(x, y, z), tmp_path)
        tr = list(g.axes['Ax0'].traces.values())[0]
        assert np.allclose(tr.x_data, x)
        assert np.allclose(tr.y_data, y)
        assert np.allclose(tr.z_data, z)

    def test_trace_type_is_line3d(self, tmp_path):
        t = np.linspace(0, 2 * np.pi, 20)
        fig = _make_3d_fig(np.cos(t), np.sin(t), t)
        g = roundtrip(fig, tmp_path)
        assert list(g.axes['Ax0'].traces.values())[0].trace_type == 'TRACE_LINE3D'

    def test_z_axis_is_valid(self, tmp_path):
        t = np.linspace(0, 2 * np.pi, 20)
        fig = _make_3d_fig(np.cos(t), np.sin(t), t)
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].z_axis.is_valid == True


class TestStyling3D:

    def test_line_color_preserved(self, tmp_path):
        t = np.linspace(0, 2 * np.pi, 30)
        fig = _make_3d_fig(np.cos(t), np.sin(t), t, color='magenta')
        g = roundtrip(fig, tmp_path)
        expected = mcolors.to_rgb('magenta')
        assert list(g.axes['Ax0'].traces.values())[0].line_color == pytest.approx(expected, abs=0.01)

    def test_line_width_preserved(self, tmp_path):
        t = np.linspace(0, 2 * np.pi, 30)
        fig = _make_3d_fig(np.cos(t), np.sin(t), t, linewidth=2.5)
        g = roundtrip(fig, tmp_path)
        assert list(g.axes['Ax0'].traces.values())[0].line_width == pytest.approx(2.5, abs=0.1)


class TestLabels3D:

    def test_axis_labels_preserved(self, tmp_path):
        t = np.linspace(0, 2 * np.pi, 20)
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(np.cos(t), np.sin(t), t)
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        ax.set_zlabel('Z axis')
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].x_axis.label == 'X axis'
        assert g.axes['Ax0'].y_axis_L.label == 'Y axis'
        assert g.axes['Ax0'].z_axis.label == 'Z axis'

    def test_title_preserved(self, tmp_path):
        t = np.linspace(0, 2 * np.pi, 20)
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(np.cos(t), np.sin(t), t)
        ax.set_title('3D Helix')
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].title == '3D Helix'


class TestReconstruct3D:

    def test_to_fig_does_not_raise(self, tmp_path):
        t = np.linspace(0, 4 * np.pi, 60)
        fig = _make_3d_fig(np.cos(t), np.sin(t), t / (4 * np.pi),
                           color='royalblue', linewidth=1.5)
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2 is not None
