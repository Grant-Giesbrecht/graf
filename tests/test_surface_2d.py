"""Round-trip tests for 2-D surface plots (pcolormesh and imshow)."""
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pytest

from graf.base import Graf, Axis, Surface
from .conftest import roundtrip, roundtrip_fig


# ---------------------------------------------------------------------------
# Shared grid builders
# ---------------------------------------------------------------------------

def _uniform_xy(nx=20, ny=15):
    x = np.linspace(-3, 3, nx)
    y = np.linspace(-2, 2, ny)
    return np.meshgrid(x, y)


def _gaussian(X, Y):
    return np.exp(-X ** 2 - Y ** 2)


# ---------------------------------------------------------------------------
# pcolormesh — uniform grid
# ---------------------------------------------------------------------------

class TestPcolormeshUniform:

    def test_axis_type_is_image(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].axis_type == Axis.AXIS_IMAGE

    def test_surf_type_is_image(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.surf_type == Surface.SURF_IMAGE

    def test_uniform_grid_flag(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.uniform_grid == True

    def test_z_data_shape(self, tmp_path):
        X, Y = _uniform_xy(20, 15)
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        z = np.array(sf.z_grid)
        assert z.shape == Z.shape

    def test_z_values_preserved(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert np.allclose(np.array(sf.z_grid), Z, atol=1e-6)

    def test_axis_labels_preserved(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        ax.set_xlabel('X label')
        ax.set_ylabel('Y label')
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].x_axis.label == 'X label'
        assert g.axes['Ax0'].y_axis_L.label == 'Y label'

    def test_title_preserved(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        ax.set_title('Gaussian')
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].title == 'Gaussian'

    def test_to_fig_does_not_raise(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z, cmap='plasma')
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2 is not None


# ---------------------------------------------------------------------------
# pcolormesh — non-uniform (polar-style) grid
# ---------------------------------------------------------------------------

class TestPcolormeshNonUniform:

    def _polar_grid(self):
        theta = np.linspace(0, np.pi / 2, 20)
        r = np.linspace(0.5, 3.0, 15)
        X = np.outer(r, np.cos(theta))
        Y = np.outer(r, np.sin(theta))
        Z = X[:-1, :-1] ** 2 + Y[:-1, :-1] ** 2
        return X, Y, Z

    def test_nonuniform_grid_flag(self, tmp_path):
        X, Y, Z = self._polar_grid()
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.uniform_grid == False

    def test_corner_coords_shape(self, tmp_path):
        X, Y, Z = self._polar_grid()
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        x_corners = np.array(sf.x_grid)
        assert x_corners.shape == X.shape

    def test_corner_coords_values(self, tmp_path):
        X, Y, Z = self._polar_grid()
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert np.allclose(np.array(sf.x_grid), X, atol=1e-6)
        assert np.allclose(np.array(sf.y_grid), Y, atol=1e-6)

    def test_z_values_nonuniform(self, tmp_path):
        X, Y, Z = self._polar_grid()
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert np.allclose(np.array(sf.z_grid), Z, atol=1e-6)

    def test_to_fig_does_not_raise(self, tmp_path):
        X, Y, Z = self._polar_grid()
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z, cmap='viridis')
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2 is not None


# ---------------------------------------------------------------------------
# Colorbar on pcolormesh
# ---------------------------------------------------------------------------

class TestColorbar:

    def test_has_colorbar_flag(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        qm = ax.pcolormesh(X, Y, Z)
        fig.colorbar(qm, ax=ax, label='Intensity')
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.has_colorbar == True

    def test_colorbar_label_preserved(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        qm = ax.pcolormesh(X, Y, Z)
        fig.colorbar(qm, ax=ax, label='Amplitude')
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.colorbar_label == 'Amplitude'

    def test_colorbar_orientation_vertical(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        qm = ax.pcolormesh(X, Y, Z)
        fig.colorbar(qm, ax=ax, orientation='vertical')
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.colorbar_orientation == 'vertical'

    def test_colorbar_orientation_horizontal(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        qm = ax.pcolormesh(X, Y, Z)
        fig.colorbar(qm, ax=ax, orientation='horizontal')
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.colorbar_orientation == 'horizontal'

    def test_no_colorbar_flag(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        ax.pcolormesh(X, Y, Z)
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.has_colorbar == False

    def test_colorbar_to_fig_does_not_raise(self, tmp_path):
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        qm = ax.pcolormesh(X, Y, Z, cmap='viridis')
        fig.colorbar(qm, ax=ax, label='Value')
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2 is not None

    def test_colorbar_axis_not_counted_as_axis(self, tmp_path):
        """Colorbar axes must not become a separate Axis entry in the Graf."""
        X, Y = _uniform_xy()
        Z = _gaussian(X, Y)
        fig, ax = plt.subplots()
        qm = ax.pcolormesh(X, Y, Z)
        fig.colorbar(qm, ax=ax)
        g = roundtrip(fig, tmp_path)
        assert len(g.axes) == 1


# ---------------------------------------------------------------------------
# imshow
# ---------------------------------------------------------------------------

class TestImshow:

    def _z(self, nx=30, ny=25):
        x = np.linspace(-3, 3, nx)
        y = np.linspace(-2, 2, ny)
        X, Y = np.meshgrid(x, y)
        return np.exp(-X ** 2 - Y ** 2)

    def test_axis_type_is_image(self, tmp_path):
        Z = self._z()
        fig, ax = plt.subplots()
        ax.imshow(Z, origin='lower', extent=[-3, 3, -2, 2])
        g = roundtrip(fig, tmp_path)
        assert g.axes['Ax0'].axis_type == Axis.AXIS_IMAGE

    def test_z_data_preserved(self, tmp_path):
        Z = self._z()
        fig, ax = plt.subplots()
        ax.imshow(Z, origin='lower', extent=[-3, 3, -2, 2])
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert np.allclose(np.array(sf.z_grid), Z, atol=1e-6)

    def test_uniform_grid_flag(self, tmp_path):
        Z = self._z()
        fig, ax = plt.subplots()
        ax.imshow(Z, origin='lower', extent=[-3, 3, -2, 2])
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.uniform_grid == True

    def test_colorbar_label_preserved(self, tmp_path):
        Z = self._z()
        fig, ax = plt.subplots()
        im = ax.imshow(Z, origin='lower', extent=[-3, 3, -2, 2], cmap=cm.RdYlGn)
        fig.colorbar(im, ax=ax, orientation='horizontal', label='Heatmap')
        g = roundtrip(fig, tmp_path)
        sf = list(g.axes['Ax0'].surfaces.values())[0]
        assert sf.colorbar_label == 'Heatmap'

    def test_to_fig_does_not_raise(self, tmp_path):
        Z = self._z()
        fig, ax = plt.subplots()
        im = ax.imshow(Z, interpolation='bilinear', origin='lower',
                       extent=[-3, 3, -2, 2], cmap='plasma')
        fig.colorbar(im, ax=ax, label='Value')
        _, fig2 = roundtrip_fig(fig, tmp_path)
        assert fig2 is not None
