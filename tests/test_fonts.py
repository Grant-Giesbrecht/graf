"""Tests for the bundled font manifest, its licence metadata, and fallback.

The licence assertions here are not busywork: GrAF redistributes third-party
font binaries, and the original packaging shipped them with no licence text at
all. These tests make the add-a-font checklist in assets/fonts/LICENSES/README.md
mechanically enforced rather than merely remembered.
"""
import os
import warnings

import pytest

from graf.base import (
    ALLOWED_FONT_LICENSES,
    FALLBACK_FONT,
    FONT_TYPES,
    Font,
    GraphStyle,
    available_font_families,
    font_data,
    mod_path,
    _find_font_family,
)


def families():
    return font_data['font-list']


def family_ids():
    return [f['names'][0] for f in font_data['font-list']]


# ---------------------------------------------------------------------------
# Licence compliance
# ---------------------------------------------------------------------------

class TestFontLicensing:

    @pytest.mark.parametrize("ff", families(), ids=family_ids())
    def test_declares_license(self, ff):
        assert ff.get('license'), f"{ff['names'][0]} declares no licence"

    @pytest.mark.parametrize("ff", families(), ids=family_ids())
    def test_license_is_allowed(self, ff):
        assert ff['license'] in ALLOWED_FONT_LICENSES, (
            f"{ff['names'][0]} is under {ff['license']}, which is not in the "
            f"redistribution allow-list {ALLOWED_FONT_LICENSES}"
        )

    @pytest.mark.parametrize("ff", families(), ids=family_ids())
    def test_declares_copyright_and_source(self, ff):
        assert ff.get('copyright'), f"{ff['names'][0]} declares no copyright"
        assert ff.get('source_url'), f"{ff['names'][0]} declares no source_url"

    @pytest.mark.parametrize("ff", families(), ids=family_ids())
    def test_license_file_ships(self, ff):
        """The licence text must actually exist on disk, not just be named.

        OFL 1.1 requires the licence travel with the font files.
        """
        rel = ff.get('license_file')
        assert rel, f"{ff['names'][0]} names no license_file"
        path = os.path.join(mod_path, *rel)
        assert os.path.isfile(path), f"declared licence file missing: {path}"
        assert os.path.getsize(path) > 0, f"declared licence file is empty: {path}"

    @pytest.mark.parametrize("ff", families(), ids=family_ids())
    def test_font_binaries_ship(self, ff):
        """Every font file the manifest points at is actually present."""
        for ft in FONT_TYPES:
            if not ff.get(ft):
                continue
            path = os.path.join(mod_path, *ff[ft])
            assert os.path.isfile(path), f"declared font file missing: {path}"


# ---------------------------------------------------------------------------
# Manifest resolution
# ---------------------------------------------------------------------------

class TestFontResolution:

    def test_all_families_resolve_a_regular_face(self):
        for ff in families():
            assert ff['font-regular'] is not None, \
                f"{ff['names'][0]} has no usable regular face"

    def test_absent_style_resolves_to_none(self):
        """A style declared as [] must resolve to None.

        Regression test: load_fonts used to leave `font_path` set from the
        previous loop iteration, so a family declaring no italic silently
        resolved italic to whichever face was loaded last. SUSE italic
        resolved to SUSE-Bold -- asking for italic rendered bold.
        """
        for ff in families():
            for ft in FONT_TYPES:
                if ff.get(ft) == []:
                    assert ff[f'font-{ft}'] is None, (
                        f"{ff['names'][0]} declares no {ft} face but resolved to "
                        f"{ff[f'font-{ft}']}"
                    )

    def test_resolved_face_matches_declared_file(self):
        """Each resolved FontProperties points at the file the manifest names."""
        for ff in families():
            for ft in FONT_TYPES:
                if not ff.get(ft):
                    continue
                expected = os.path.join(mod_path, *ff[ft])
                assert os.path.samefile(ff[f'font-{ft}'].get_file(), expected)

    def test_fallback_family_exists(self):
        assert _find_font_family(FALLBACK_FONT) is not None

    def test_available_families_includes_generics(self):
        names = available_font_families()
        for generic in ('sanserif', 'serif', 'monospace'):
            assert generic in names


# ---------------------------------------------------------------------------
# Fallback behaviour
# ---------------------------------------------------------------------------

class TestFontFallback:

    def test_unknown_family_falls_back_and_warns(self):
        f = Font()
        f.font = 'no-such-font-family'
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            result = f.to_tuple()
        assert result is not None, "fallback must still yield a usable font"
        assert any('no-such-font-family' in str(w.message) for w in caught)

    def test_unknown_family_resolves_to_fallback_face(self):
        f = Font()
        f.font = 'no-such-font-family'
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            got = f.to_tuple()
        expected = Font()
        expected.font = FALLBACK_FONT
        assert os.path.samefile(got[0].get_file(), expected.to_tuple()[0].get_file())

    def test_known_family_does_not_warn(self):
        f = Font()
        f.font = 'serif'
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            f.to_tuple()
        assert not caught

    def test_use_native_returns_none(self):
        f = Font()
        f.use_native = True
        assert f.to_tuple() is None

    def test_size_is_carried_through(self):
        f = Font()
        f.font = 'serif'
        f.size = 17
        assert f.to_tuple()[1] == 17

    def test_bold_selects_bold_face(self):
        f = Font()
        f.font = 'serif'
        f.bold = True
        assert 'Bold' in f.to_tuple()[0].get_file()

    def test_missing_bold_face_falls_back_to_regular(self):
        """SUSE ships no italic; requesting it must yield regular, not bold."""
        f = Font()
        f.font = 'suse'
        f.italic = True
        assert 'Regular' in f.to_tuple()[0].get_file()


# ---------------------------------------------------------------------------
# GraphStyle validation
# ---------------------------------------------------------------------------

class TestGraphStyleValidation:

    def test_unknown_family_warns(self):
        gs = GraphStyle()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            gs.set_all_font_families('not-a-real-family')
        assert any('not-a-real-family' in str(w.message) for w in caught)

    def test_known_family_applies_to_all(self):
        gs = GraphStyle()
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            gs.set_all_font_families('mono')
        assert gs.title_font.font == 'mono'
        assert gs.graph_font.font == 'mono'
        assert gs.label_font.font == 'mono'

    def test_sizes_apply_to_all(self):
        gs = GraphStyle()
        gs.set_all_font_sizes(19)
        assert gs.title_font.size == 19
        assert gs.graph_font.size == 19
        assert gs.label_font.size == 19

    @pytest.mark.parametrize("bad", [0, -3, "large", None])
    def test_invalid_size_rejected(self, bad):
        gs = GraphStyle()
        with pytest.raises(ValueError):
            gs.set_all_font_sizes(bad)
