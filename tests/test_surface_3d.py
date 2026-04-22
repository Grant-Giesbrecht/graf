"""Round-trip tests for 3-D surface plots (plot_surface / Poly3DCollection)."""
import matplotlib.pyplot as plt
import numpy as np
import pytest

from graf.base import Graf, Axis, Surface
from .conftest import roundtrip, roundtrip_fig


# ---------------------------------------------------------------------------
# Shared data builders
# ---------------------------------------------------------------------------

def _sinc_grid(step=0.5, extent=5):
    X_flat = np.arange(-extent, extent, step)
    Y_flat = np.arange(-extent, extent, step)
    X, Y = np.meshgrid(X_flat, Y_flat)
    R = np.sqrt(X ** 2 + Y ** 2) + 1e-9
    Z = np.sin(R) / R
    return X, Y, Z


def _make_surf_fig(X, Y, Z, **kwargs):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(X, Y, Z, **kwargs)
    return fig


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

class TestClassification:

    def test_axis_type_is_surface(self, tmp_path):
        X, Y, Z = _sinc_grid()
        g = roundtrip(_make_surf_fig(X, Y, Z), tmp_path)
        assert g.axes['Ax0'].axis_type == Axis.AXIS_SURFACE

    def test_surf_type_is_surface(self, tmp_path):
        X, Y, Z = _sinc_grid()
        g = roundtrip(_make_surf_fig(X, Y, Z), tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.surf_type == Surface.SURF_SURFACE

    def test_z_axis_is_valid(self, tmp_path):
        X, Y, Z = _sinc_grid()
        g = roundtrip(_make_surf_fig(X, Y, Z), tmp_path)
        assert g.axes['Ax0'].z_axis.is_valid == True


# ---------------------------------------------------------------------------
# Grid reconstruction
# ---------------------------------------------------------------------------

class TestGridReconstruction:

    def test_x_grid_shape(self, tmp_path):
        X, Y, Z = _sinc_grid()
        g = roundtrip(_make_surf_fig(X, Y, Z), tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert np.array(sf.x_grid).shape == X.shape

    def test_y_grid_shape(self, tmp_path):
        X, Y, Z = _sinc_grid()
        g = roundtrip(_make_surf_fig(X, Y, Z), tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert np.array(sf.y_grid).shape == Y.shape

    def test_z_grid_shape(self, tmp_path):
        X, Y, Z = _sinc_grid()
        g = roundtrip(_make_surf_fig(X, Y, Z), tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert np.array(sf.z_grid).shape == Z.shape

    def test_z_values_preserved(self, tmp_path):
        X, Y, Z = _sinc_grid()
        g = roundtrip(_make_surf_fig(X, Y, Z), tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert np.allclose(np.array(sf.z_grid), Z, atol=1e-6)

    def test_x_range_preserved(self, tmp_path):
        X, Y, Z = _sinc_grid(extent=3)
        g = roundtrip(_make_surf_fig(X, Y, Z), tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        x = np.array(sf.x_grid)
        assert x.min() == pytest.approx(X.min(), abs=1e-6)
        assert x.max() == pytest.approx(X.max(), abs=1e-6)

    def test_uniform_grid_flag(self, tmp_path):
        X, Y, Z = _sinc_grid()
        g = roundtrip(_make_surf_fig(X, Y, Z), tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.uniform_grid == True


# ---------------------------------------------------------------------------
# Labels and metadata
# ---------------------------------------------------------------------------

class TestLabels:

    def test_axis_labels_preserved(self, tmp_path):
        X, Y, Z = _sinc_grid()
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(X, Y, Z)
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        ax.set_zlabel('Z axis')
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].x_axis.label == 'X axis'
        assert g.axes['Ax0'].y_axis_L.label == 'Y axis'
        assert g.axes['Ax0'].z_axis.label == 'Z axis'

    def test_title_preserved(self, tmp_path):
        X, Y, Z = _sinc_grid()
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(X, Y, Z)
        ax.set_title('sinc surface')
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].title == 'sinc surface'


# ---------------------------------------------------------------------------
# Colorbar on 3-D surface
# ---------------------------------------------------------------------------

class TestColorbar:

    def test_has_colorbar_flag(self, tmp_path):
        X, Y, Z = _sinc_grid()
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(X, Y, Z, cmap='coolwarm')
        fig.colorbar(surf, ax=ax, label='sinc(r)')
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.has_colorbar == True

    def test_colorbar_label_preserved(self, tmp_path):
        X, Y, Z = _sinc_grid()
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(X, Y, Z, cmap='viridis')
        fig.colorbar(surf, ax=ax, label='amplitude')
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.colorbar_label == 'amplitude'

    def test_colorbar_to_fig_does_not_raise(self, tmp_path):
        X, Y, Z = _sinc_grid()
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(X, Y, Z, cmap='coolwarm')
        fig.colorbar(surf, ax=ax, label='sinc(r)')
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2 is not None


# ---------------------------------------------------------------------------
# Reconstruct (to_fig) without error
# ---------------------------------------------------------------------------

class TestReconstruct:

    def test_to_fig_does_not_raise(self, tmp_path):
        X, Y, Z = _sinc_grid()
        _, fig2 = roundtrip_fig(_make_surf_fig(X, Y, Z, cmap='viridis'), tmp_path)
        assert fig2 is not None

    @pytest.mark.parametrize("cmap", ['viridis', 'plasma', 'coolwarm', 'RdBu'])
    def test_colormaps_do_not_raise(self, tmp_path, cmap):
        X, Y, Z = _sinc_grid()
        _, fig2 = roundtrip_fig(_make_surf_fig(X, Y, Z, cmap=cmap), tmp_path)
        assert fig2 is not None
