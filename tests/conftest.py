"""Shared fixtures and helpers for graf round-trip tests."""
import matplotlib
matplotlib.use('Agg')  # headless — must happen before any other matplotlib import

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pytest

from graf.base import Graf


# ---------------------------------------------------------------------------
# Core helper
# ---------------------------------------------------------------------------

def roundtrip(fig, tmp_path, name="test.graf"):
    """Save fig to a .graf file then reload and return the new Graf object."""
    path = str(tmp_path / name)
    g = Graf(fig=fig)
    g.save_hdf(path)
    plt.close(fig)

    g2 = Graf()
    g2.load_hdf(path)
    return g2


def roundtrip_fig(fig, tmp_path, name="test.graf"):
    """Round-trip and return the reconstructed matplotlib figure."""
    g2 = roundtrip(fig, tmp_path, name)
    fig2 = g2.to_fig()
    plt.close(fig2)
    return g2, fig2


# ---------------------------------------------------------------------------
# Common data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def xy():
    """Simple 1-D x/y data arrays."""
    x = np.linspace(0, 2 * np.pi, 40)
    return x, np.sin(x)


@pytest.fixture
def xy_err(xy):
    """x/y data plus asymmetric errors."""
    x, y = xy
    y_err = 0.1 + 0.04 * np.abs(np.sin(x))
    x_err = 0.08
    return x, y, x_err, y_err
