"""Tests for GrAF's font model: roles, stacks, resolution, and licensing.

The design under test has three separated concepts -- generic roles, an ordered
font stack, and local resolution. Most of these tests exist to keep them
separated, because collapsing them is exactly what the previous model did.
"""
import json
import os
import warnings

import matplotlib.pyplot as plt
import pytest

from graf import fonts
from graf.base import Font, GraphStyle, Graf, mod_path
from graf.fonts import (
    ALLOWED_FONT_LICENSES,
    GENERIC_ROLES,
    MONOSPACE,
    SANS_SERIF,
    SERIF,
    FontResolver,
    ensure_role,
    is_generic_role,
    load_manifest,
    normalize_role,
    normalize_stack,
    normalize_style,
    normalize_weight,
    stack_role,
)
from .conftest import roundtrip


FAMILIES, ROLE_DEFAULTS = load_manifest(mod_path)


def family_ids():
    return [f['family'] for f in FAMILIES]


@pytest.fixture
def isolated_resolver(tmp_path):
    """A resolver with a private config file, so tests never touch ~/.config."""
    return FontResolver(mod_path, config_path=str(tmp_path / "fonts.json"))


# ---------------------------------------------------------------------------
# Roles are not family names
# ---------------------------------------------------------------------------

class TestGenericRoles:
    """The previous model made 'serif' an alias of MFB Oldstyle, so a file could
    not distinguish "this exact font" from "any serif". These tests keep the two
    namespaces apart."""

    def test_roles_are_a_closed_set(self):
        assert GENERIC_ROLES == (SERIF, SANS_SERIF, MONOSPACE)

    @pytest.mark.parametrize("role", GENERIC_ROLES)
    def test_roles_are_recognised(self, role):
        assert is_generic_role(role)

    @pytest.mark.parametrize("name", ["SUSE", "MFB Oldstyle", "Helvetica", "spline"])
    def test_family_names_are_not_roles(self, name):
        assert not is_generic_role(name)

    @pytest.mark.parametrize("spelling,expected", [
        ("sanserif", SANS_SERIF), ("sans", SANS_SERIF), ("Sans-Serif", SANS_SERIF),
        ("mono", MONOSPACE), ("monospaced", MONOSPACE), ("SERIF", SERIF),
    ])
    def test_alternate_spellings_normalise(self, spelling, expected):
        assert normalize_role(spelling) == expected

    @pytest.mark.parametrize("ff", FAMILIES, ids=family_ids())
    def test_no_family_claims_a_role_as_alias(self, ff):
        """A family claiming 'serif' as an alias would reintroduce the conflation."""
        for alias in ff['aliases']:
            assert not is_generic_role(alias), (
                f"{ff['family']} claims generic role '{alias}' as an alias"
            )

    @pytest.mark.parametrize("role", GENERIC_ROLES)
    def test_every_role_has_a_default_family(self, role):
        assert ROLE_DEFAULTS.get(role), f"no bundled family serves '{role}'"

    def test_role_defaults_name_real_families(self):
        known = {f['family'] for f in FAMILIES}
        for role, family in ROLE_DEFAULTS.items():
            assert family in known, f"role_defaults['{role}'] names unknown {family}"


# ---------------------------------------------------------------------------
# Font stacks
# ---------------------------------------------------------------------------

class TestFontStacks:

    def test_single_name_becomes_a_stack(self):
        assert normalize_stack("SUSE") == ["SUSE"]

    def test_list_is_preserved_in_order(self):
        assert normalize_stack(["A", "B", "serif"]) == ["A", "B", "serif"]

    def test_duplicates_collapse_preserving_order(self):
        assert normalize_stack(["A", "B", "A"]) == ["A", "B"]

    def test_blanks_and_none_are_dropped(self):
        assert normalize_stack(["A", "  ", ""]) == ["A"]
        assert normalize_stack(None) == []

    def test_roles_normalise_inside_a_stack(self):
        assert normalize_stack(["Georgia", "sanserif"]) == ["Georgia", SANS_SERIF]

    def test_trailing_role_is_detected(self):
        assert stack_role(["MFB Oldstyle", "Georgia", "serif"]) == SERIF

    def test_no_role_returns_none(self):
        assert stack_role(["MFB Oldstyle", "Georgia"]) is None

    def test_ensure_role_appends_when_missing(self):
        assert ensure_role(["Georgia"]) == ["Georgia", SANS_SERIF]

    def test_ensure_role_respects_a_supplied_role(self):
        assert ensure_role(["Georgia"], role=SERIF) == ["Georgia", SERIF]

    def test_ensure_role_leaves_an_existing_role_alone(self):
        stack = ["Georgia", SERIF]
        assert ensure_role(stack) == stack

    def test_degenerate_stack_is_just_a_role(self):
        """Asking for 'any serif' is the same mechanism, not a separate mode."""
        assert ensure_role("serif") == [SERIF]


# ---------------------------------------------------------------------------
# Weight and style
# ---------------------------------------------------------------------------

class TestWeightAndStyle:

    @pytest.mark.parametrize("value,expected", [
        (400, 400), (700, 700), (100, 100), (900, 900),
        ("normal", 400), ("bold", 700), ("light", 300), ("Semibold", 600),
        ("black", 900), ("400", 400), (True, 700), (False, 400),
    ])
    def test_weight_normalisation(self, value, expected):
        assert normalize_weight(value) == expected

    @pytest.mark.parametrize("bad", [0, 1000, -5, "chunky", None])
    def test_invalid_weight_warns_and_defaults(self, bad):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert normalize_weight(bad) == 400
        assert caught

    @pytest.mark.parametrize("value,expected", [
        ("normal", "normal"), ("italic", "italic"), ("oblique", "oblique"),
        ("ITALIC", "italic"), ("roman", "normal"), (True, "italic"), (False, "normal"),
    ])
    def test_style_normalisation(self, value, expected):
        assert normalize_style(value) == expected

    def test_invalid_style_warns_and_defaults(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert normalize_style("slanty") == "normal"
        assert caught

    def test_bold_property_maps_to_weight(self):
        f = Font()
        f.bold = True
        assert f.weight == 700 and f.bold is True
        f.bold = False
        assert f.weight == 400 and f.bold is False

    def test_italic_property_maps_to_style(self):
        f = Font()
        f.italic = True
        assert f.style == "italic" and f.italic is True
        f.italic = False
        assert f.style == "normal" and f.italic is False

    def test_weight_expresses_what_booleans_cannot(self):
        """A semibold face is not expressible as bold=True/False."""
        f = Font(weight="semibold")
        assert f.weight == 600
        assert f.bold is False


# ---------------------------------------------------------------------------
# Licence compliance
# ---------------------------------------------------------------------------

class TestFontLicensing:

    @pytest.mark.parametrize("ff", FAMILIES, ids=family_ids())
    def test_license_is_declared_and_allowed(self, ff):
        assert ff['license'], f"{ff['family']} declares no licence"
        assert ff['license'] in ALLOWED_FONT_LICENSES, (
            f"{ff['family']} is under {ff['license']}, not in the "
            f"redistribution allow-list {ALLOWED_FONT_LICENSES}"
        )

    @pytest.mark.parametrize("ff", FAMILIES, ids=family_ids())
    def test_copyright_and_source_declared(self, ff):
        assert ff['copyright']
        assert ff['source_url']

    @pytest.mark.parametrize("ff", FAMILIES, ids=family_ids())
    def test_license_file_actually_ships(self, ff):
        """OFL 1.1 requires the licence travel with the font files."""
        assert ff['license_file'], f"{ff['family']} names no license_file"
        path = os.path.join(mod_path, *ff['license_file'])
        assert os.path.isfile(path), f"declared licence file missing: {path}"
        assert os.path.getsize(path) > 0

    @pytest.mark.parametrize("ff", FAMILIES, ids=family_ids())
    def test_every_declared_face_loaded(self, ff):
        assert ff['faces'], f"{ff['family']} resolved no usable faces"
        for face in ff['faces']:
            assert os.path.isfile(face['path'])


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

class TestResolution:

    def test_bundled_family_resolves_by_name(self, isolated_resolver):
        props, resolved = isolated_resolver.resolve(["SUSE"])
        assert resolved == "SUSE"
        assert "SUSE" in props.get_file()

    def test_bundled_family_resolves_by_alias(self, isolated_resolver):
        _, resolved = isolated_resolver.resolve(["mfb"])
        assert resolved == "MFB Oldstyle"

    def test_role_resolves_to_its_default_family(self, isolated_resolver):
        _, resolved = isolated_resolver.resolve([SERIF])
        assert resolved == "MFB Oldstyle"

    def test_stack_prefers_the_first_available(self, isolated_resolver):
        _, resolved = isolated_resolver.resolve(["SUSE", "MFB Oldstyle", SANS_SERIF])
        assert resolved == "SUSE"

    def test_stack_skips_unavailable_entries(self, isolated_resolver):
        _, resolved = isolated_resolver.resolve(
            ["Definitely Not Installed", "MFB Oldstyle", SERIF])
        assert resolved == "MFB Oldstyle"

    def test_unavailable_stack_falls_back_within_its_role(self, isolated_resolver):
        """The key fix: a serif request must not degrade to a sans face."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, resolved = isolated_resolver.resolve(["No Such Font", SERIF])
        assert resolved == "MFB Oldstyle"

    def test_monospace_request_stays_monospace(self, isolated_resolver):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, resolved = isolated_resolver.resolve(["No Such Mono", MONOSPACE])
        assert resolved == "Spline Sans Mono"

    def test_substitution_warns(self, isolated_resolver):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            isolated_resolver.resolve(["No Such Font Anywhere", SERIF])
        assert any("No Such Font Anywhere" in str(w.message) for w in caught)

    def test_substitution_warns_only_once(self, isolated_resolver):
        """A per-artist warning storm would make the message useless."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            for _ in range(5):
                isolated_resolver.resolve(["No Such Font Anywhere", SERIF])
        assert len(caught) == 1

    def test_exact_match_does_not_warn(self, isolated_resolver):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            isolated_resolver.resolve(["MFB Oldstyle", SERIF])
        assert not caught

    def test_alias_match_does_not_warn(self, isolated_resolver):
        """'mfb' -> MFB Oldstyle is a correct hit, not a substitution."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            isolated_resolver.resolve(["mfb", SERIF])
        assert not caught

    def test_configured_alias_does_not_warn(self, tmp_path):
        """A redirect the user asked for is the system working, not failing."""
        p = tmp_path / "fonts.json"
        p.write_text(json.dumps({"aliases": {"Helvetica": "SUSE"}}))
        r = FontResolver(mod_path, config_path=str(p))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r.resolve(["Helvetica", SANS_SERIF])
        assert not caught

    def test_role_only_request_does_not_warn(self, isolated_resolver):
        """Asking for 'any serif' and getting one is not a substitution."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            isolated_resolver.resolve([SERIF])
        assert not caught

    def test_bold_selects_the_bold_face(self, isolated_resolver):
        props, _ = isolated_resolver.resolve(["SUSE"], weight=700)
        assert "Bold" in props.get_file()

    def test_italic_selects_the_italic_face(self, isolated_resolver):
        props, _ = isolated_resolver.resolve(["MFB Oldstyle"], style="italic")
        assert "Italic" in props.get_file()

    def test_missing_italic_falls_back_within_the_family(self, isolated_resolver):
        """SUSE ships no italic. It must yield SUSE regular, not another family
        and not SUSE bold."""
        props, resolved = isolated_resolver.resolve(["SUSE"], style="italic")
        assert resolved == "SUSE"
        assert "Regular" in props.get_file()

    def test_nearest_weight_is_chosen(self, isolated_resolver):
        """500 is nearer 400 than 700, so a medium request takes the regular face."""
        props, _ = isolated_resolver.resolve(["SUSE"], weight=500)
        assert "Regular" in props.get_file()
        props, _ = isolated_resolver.resolve(["SUSE"], weight=800)
        assert "Bold" in props.get_file()

    def test_system_fonts_can_be_disabled(self, tmp_path):
        r = FontResolver(mod_path, config_path=str(tmp_path / "f.json"),
                         use_system_fonts=False)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, resolved = r.resolve(["Arial", "Helvetica", SANS_SERIF])
        assert resolved == "SUSE", "system lookup should have been skipped"


# ---------------------------------------------------------------------------
# User configuration
# ---------------------------------------------------------------------------

class TestUserConfig:

    def test_missing_config_is_not_an_error(self, tmp_path):
        cfg = fonts.load_user_config(str(tmp_path / "absent.json"))
        assert cfg == {'defaults': {}, 'font_paths': [], 'aliases': {}}

    def test_broken_config_warns_and_is_ignored(self, tmp_path):
        p = tmp_path / "broken.json"
        p.write_text("{not json")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            cfg = fonts.load_user_config(str(p))
        assert cfg['defaults'] == {}
        assert caught

    def test_config_default_overrides_the_bundled_role(self, tmp_path):
        p = tmp_path / "fonts.json"
        p.write_text(json.dumps({"defaults": {"serif": "Spline Sans Mono"}}))
        r = FontResolver(mod_path, config_path=str(p))
        _, resolved = r.resolve([SERIF])
        assert resolved == "Spline Sans Mono"

    def test_config_alias_redirects_a_family(self, tmp_path):
        p = tmp_path / "fonts.json"
        p.write_text(json.dumps({"aliases": {"Helvetica": "SUSE"}}))
        r = FontResolver(mod_path, config_path=str(p))
        _, resolved = r.resolve(["Helvetica", SANS_SERIF])
        assert resolved == "SUSE"

    def test_unknown_role_in_config_warns(self, tmp_path):
        p = tmp_path / "fonts.json"
        p.write_text(json.dumps({"defaults": {"squiggly": "SUSE"}}))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fonts.load_user_config(str(p))
        assert any("squiggly" in str(w.message) for w in caught)

    def test_set_font_default_persists(self, tmp_path):
        p = str(tmp_path / "fonts.json")
        r = FontResolver(mod_path, config_path=p)
        fonts.resolver, saved = r, fonts.resolver
        try:
            fonts.set_font_default(SERIF, "Spline Sans Mono")
            assert fonts.load_user_config(p)['defaults'][SERIF] == "Spline Sans Mono"
            _, resolved = r.resolve([SERIF])
            assert resolved == "Spline Sans Mono"
        finally:
            fonts.resolver = saved

    def test_set_font_default_rejects_unknown_role(self, tmp_path):
        with pytest.raises(ValueError):
            fonts.set_font_default("wibble", "SUSE", persist=False)

    def test_config_path_is_platform_appropriate(self):
        path = fonts.user_config_path()
        assert path.endswith(os.path.join("graf", "fonts.json"))


# ---------------------------------------------------------------------------
# The Font object and GraphStyle
# ---------------------------------------------------------------------------

class TestFontObject:

    def test_default_font_has_a_role(self):
        assert Font().role in GENERIC_ROLES

    def test_family_always_ends_in_a_role(self):
        assert is_generic_role(Font(family=["Georgia"]).family[-1])

    def test_set_family_keeps_a_role(self):
        f = Font(family=["MFB Oldstyle", SERIF])
        f.set_family(["Baskerville"])
        assert f.family[-1] == SERIF

    def test_prefer_puts_a_family_first(self):
        f = Font(family=["MFB Oldstyle", SERIF])
        f.prefer("Baskerville")
        assert f.family[0] == "Baskerville"
        assert f.family[-1] == SERIF

    def test_use_native_resolves_to_nothing(self):
        f = Font()
        f.use_native = True
        assert f.to_tuple() is None

    def test_resolve_records_the_resolved_family(self):
        f = Font(family=["MFB Oldstyle", SERIF])
        f.resolve()
        assert f.resolved_family == "MFB Oldstyle"

    def test_size_carried_into_the_tuple(self):
        assert Font(family=[SERIF], size=21).to_tuple()[1] == 21


class TestGraphStyle:

    def test_set_all_families_accepts_a_role(self):
        gs = GraphStyle()
        gs.set_all_font_families(SERIF)
        for font in gs.all_fonts():
            assert font.family == [SERIF]

    def test_set_all_families_accepts_a_stack(self):
        gs = GraphStyle()
        gs.set_all_font_families(["Helvetica", "Arial", SANS_SERIF])
        for font in gs.all_fonts():
            assert font.family == ["Helvetica", "Arial", SANS_SERIF]

    def test_set_all_families_appends_a_role(self):
        gs = GraphStyle()
        gs.set_all_font_families(["Helvetica"])
        for font in gs.all_fonts():
            assert is_generic_role(font.family[-1])

    def test_set_all_weights(self):
        gs = GraphStyle()
        gs.set_all_font_weights("bold")
        assert all(f.weight == 700 for f in gs.all_fonts())

    def test_set_all_styles(self):
        gs = GraphStyle()
        gs.set_all_font_styles("italic")
        assert all(f.style == "italic" for f in gs.all_fonts())

    @pytest.mark.parametrize("bad", [0, -3, "large", None, True])
    def test_invalid_size_rejected(self, bad):
        with pytest.raises(ValueError):
            GraphStyle().set_all_font_sizes(bad)


# ---------------------------------------------------------------------------
# Round-tripping through a file
# ---------------------------------------------------------------------------

class TestFontRoundTrip:

    def make(self):
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [4, 5, 6])
        return fig

    def test_stack_survives_a_round_trip(self, tmp_path):
        fig = self.make()
        g = Graf(fig=fig)
        g.style.set_all_font_families(["Baskerville", "Georgia", SERIF])
        path = str(tmp_path / "f.graf")
        g.write_graf(path)
        plt.close(fig)

        g2 = Graf()
        g2.read_graf(path)
        assert g2.style.title_font.family == ["Baskerville", "Georgia", SERIF]

    def test_weight_and_style_survive(self, tmp_path):
        fig = self.make()
        g = Graf(fig=fig)
        g.style.set_all_font_weights(600)
        g.style.set_all_font_styles("italic")
        path = str(tmp_path / "w.graf")
        g.write_graf(path)
        plt.close(fig)

        g2 = Graf()
        g2.read_graf(path)
        assert g2.style.title_font.weight == 600
        assert g2.style.title_font.style == "italic"

    def test_resolved_family_is_recorded(self, tmp_path):
        """Typographic provenance: what was actually on screen when saved."""
        fig = self.make()
        g = Graf(fig=fig)
        g.style.set_all_font_families([SERIF])
        g.style.title_font.resolve()
        path = str(tmp_path / "r.graf")
        g.write_graf(path)
        plt.close(fig)

        g2 = Graf()
        g2.read_graf(path)
        assert g2.style.title_font.resolved_family == "MFB Oldstyle"

    def test_every_category_round_trips(self, tmp_path):
        """Each text category keeps its own family and size through a full cycle.

        Regression: supertitle_font and graph_font were captured but never
        applied (suptitle and tick labels were drawn with no fontproperties at
        all), and the legend had no slot of its own.
        """
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [4, 5, 6], label='series')
        fig.suptitle('SUP', fontfamily='monospace', fontsize=20)
        ax.set_title('TITLE', fontfamily='serif', fontsize=18)
        ax.set_xlabel('XLAB', fontfamily='monospace', fontsize=16)
        for t in ax.get_xticklabels():
            t.set_fontfamily('serif')
            t.set_fontsize(7)
        ax.legend(prop={'family': 'monospace', 'size': 14})

        path = str(tmp_path / "cats.graf")
        Graf(fig=fig).write_graf(path)
        plt.close(fig)

        g2 = Graf()
        g2.read_graf(path)
        fig2 = g2.to_fig()
        ax2 = fig2.axes[0]

        checks = [
            (g2.style.supertitle_font, fig2._suptitle, 20, MONOSPACE),
            (g2.style.title_font, ax2.title, 18, SERIF),
            (g2.style.label_font, ax2.xaxis.label, 16, MONOSPACE),
            (g2.style.graph_font, ax2.get_xticklabels()[0], 7, SERIF),
            (g2.style.legend_font, ax2.get_legend().get_texts()[0], 14, MONOSPACE),
        ]
        for slot, artist, size, role in checks:
            assert stack_role(slot.family) == role
            assert slot.size == pytest.approx(size)
            assert artist.get_fontsize() == pytest.approx(size)
            assert artist.get_fontproperties().get_file(), (
                "artist was drawn with no resolved font file"
            )
        plt.close(fig2)

    def test_legend_size_is_not_dropped(self, tmp_path):
        """matplotlib ignores `fontsize` when `prop` is given; passing both
        silently reverted the legend to the default size."""
        fig, ax = plt.subplots()
        ax.plot([1, 2], [3, 4], label='x')
        ax.legend(prop={'size': 15})
        path = str(tmp_path / "lg.graf")
        Graf(fig=fig).write_graf(path)
        plt.close(fig)

        g2 = Graf()
        g2.read_graf(path)
        fig2 = g2.to_fig()
        text = fig2.axes[0].get_legend().get_texts()[0]
        assert text.get_fontsize() == pytest.approx(15)
        plt.close(fig2)

    def test_legend_font_defaults_to_label_font(self, tmp_path):
        """With no legend to copy, the legend slot inherits the label font so a
        legend added later matches the rest of the figure."""
        fig, ax = plt.subplots()
        ax.plot([1, 2], [3, 4])
        ax.set_xlabel('L', fontfamily='serif', fontsize=13)
        g = roundtrip(fig, tmp_path, "lgd.graf")
        assert stack_role(g.style.legend_font.family) == SERIF
        assert g.style.legend_font.size == pytest.approx(13)

    def test_representative_axes_skips_empty_ones(self, tmp_path):
        """A blindly-taken axes[0] can be empty; the styled axes should win."""
        fig, axs = plt.subplots(1, 2)
        axs[1].plot([1, 2], [3, 4])
        axs[1].set_title('styled', fontfamily='monospace', fontsize=19)
        g = roundtrip(fig, tmp_path, "rep.graf")
        assert stack_role(g.style.title_font.family) == MONOSPACE
        assert g.style.title_font.size == pytest.approx(19)

    def test_set_all_sizes_covers_every_slot(self):
        gs = GraphStyle()
        gs.set_all_font_sizes(23)
        for font in gs.all_fonts():
            assert font.size == 23

    def test_figure_fonts_are_captured(self, tmp_path):
        """GrAF used to never read styling off the source figure at all."""
        fig, ax = plt.subplots()
        ax.plot([1, 2], [3, 4])
        ax.set_title("t", fontfamily="monospace", fontweight="bold")
        g = roundtrip(fig, tmp_path)
        assert g.style.title_font.weight == 700
        assert stack_role(g.style.title_font.family) == MONOSPACE
