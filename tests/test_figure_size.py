"""Tests for figure size / aspect-ratio preservation and the scale parameter.

Sizes are stored internally in centimetres (fig_width_cm / fig_height_cm).
figsize= arguments to matplotlib use inches, so the helper below works in
inches but the assertions check the cm fields directly.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest

from graf.base import Graf
from .conftest import roundtrip

CM_PER_INCH = 2.54


def _simple_fig(w_in, h_in):
    """Create a minimal figure with the given size in inches."""
    fig, ax = plt.subplots(figsize=(w_in, h_in))
    ax.plot([0, 1], [0, 1])
    return fig


# ---------------------------------------------------------------------------
# Size stored correctly (in cm)
# ---------------------------------------------------------------------------

class TestSizeStorage:

    @pytest.mark.parametrize("w_in,h_in", [
        (6.4, 4.8),   # matplotlib default
        (10.0, 6.0),
        (4.0, 4.0),   # square
        (12.0, 3.0),  # wide
        (3.0, 9.0),   # tall
    ])
    def test_fig_width_cm_stored(self, tmp_path, w_in, h_in):
        g = roundtrip(_simple_fig(w_in, h_in), tmp_path)
        assert g.fig_width_cm == pytest.approx(w_in * CM_PER_INCH, abs=0.01)

    @pytest.mark.parametrize("w_in,h_in", [
        (6.4, 4.8),
        (10.0, 6.0),
        (4.0, 4.0),
        (12.0, 3.0),
        (3.0, 9.0),
    ])
    def test_fig_height_cm_stored(self, tmp_path, w_in, h_in):
        g = roundtrip(_simple_fig(w_in, h_in), tmp_path)
        assert g.fig_height_cm == pytest.approx(h_in * CM_PER_INCH, abs=0.01)

    def test_aspect_ratio_preserved(self, tmp_path):
        w_in, h_in = 10.0, 3.0
        g = roundtrip(_simple_fig(w_in, h_in), tmp_path)
        assert g.fig_width_cm / g.fig_height_cm == pytest.approx(w_in / h_in, rel=1e-4)

    def test_square_aspect_ratio(self, tmp_path):
        g = roundtrip(_simple_fig(5.0, 5.0), tmp_path)
        assert g.fig_width_cm / g.fig_height_cm == pytest.approx(1.0, rel=1e-4)

    def test_subplots_figure_size_stored_in_cm(self, tmp_path):
        w_in, h_in = 15.0, 4.0
        fig, axes = plt.subplots(1, 3, figsize=(w_in, h_in))
        for ax in axes:
            ax.plot([0, 1], [0, 1])
        g = roundtrip(fig, tmp_path)
        assert g.fig_width_cm == pytest.approx(w_in * CM_PER_INCH, abs=0.01)
        assert g.fig_height_cm == pytest.approx(h_in * CM_PER_INCH, abs=0.01)

    def test_no_inch_fields_on_graf(self, tmp_path):
        """Ensure the old inch-based fields no longer exist."""
        g = roundtrip(_simple_fig(6.4, 4.8), tmp_path)
        assert not hasattr(g, 'fig_width'), "fig_width (inches) should not exist"
        assert not hasattr(g, 'fig_height'), "fig_height (inches) should not exist"


# ---------------------------------------------------------------------------
# Reconstructed figure size (to_fig converts cm → inches internally)
# ---------------------------------------------------------------------------

class TestReconstructedSize:

    def test_to_fig_default_scale_matches_original_inches(self, tmp_path):
        w_in, h_in = 9.0, 5.0
        g = roundtrip(_simple_fig(w_in, h_in), tmp_path)
        fig2 = g.to_fig()
        w2, h2 = fig2.get_size_inches()
        plt.close(fig2)
        assert w2 == pytest.approx(w_in, abs=0.01)
        assert h2 == pytest.approx(h_in, abs=0.01)

    def test_to_fig_scale_2x(self, tmp_path):
        w_in, h_in = 6.0, 4.0
        g = roundtrip(_simple_fig(w_in, h_in), tmp_path)
        fig2 = g.to_fig(scale=2.0)
        w2, h2 = fig2.get_size_inches()
        plt.close(fig2)
        assert w2 == pytest.approx(w_in * 2, abs=0.01)
        assert h2 == pytest.approx(h_in * 2, abs=0.01)

    def test_to_fig_scale_half(self, tmp_path):
        w_in, h_in = 8.0, 6.0
        g = roundtrip(_simple_fig(w_in, h_in), tmp_path)
        fig2 = g.to_fig(scale=0.5)
        w2, h2 = fig2.get_size_inches()
        plt.close(fig2)
        assert w2 == pytest.approx(w_in * 0.5, abs=0.01)
        assert h2 == pytest.approx(h_in * 0.5, abs=0.01)

    def test_scale_preserves_aspect_ratio(self, tmp_path):
        w_in, h_in = 10.0, 3.0
        g = roundtrip(_simple_fig(w_in, h_in), tmp_path)
        for scale in [0.5, 1.0, 1.5, 2.0]:
            fig2 = g.to_fig(scale=scale)
            w2, h2 = fig2.get_size_inches()
            plt.close(fig2)
            assert w2 / h2 == pytest.approx(w_in / h_in, rel=1e-4)

    def test_to_fig_default_scale_equals_scale_1(self, tmp_path):
        w_in, h_in = 7.0, 5.0
        g = roundtrip(_simple_fig(w_in, h_in), tmp_path)
        fig_default = g.to_fig()
        fig_scale1  = g.to_fig(scale=1.0)
        w_d, h_d = fig_default.get_size_inches()
        w_1, h_1 = fig_scale1.get_size_inches()
        plt.close('all')
        assert w_d == pytest.approx(w_1, abs=1e-6)
        assert h_d == pytest.approx(h_1, abs=1e-6)
