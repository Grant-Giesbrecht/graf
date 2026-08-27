"""A LOCK ON THE ON-DISK FORMAT. Read this before changing it.

Every name below is a field written into a .graf file. Changing this file means
changing the GrAF file format -- which is a promise to every file already
written and to every non-Python implementation.

If a test here fails, that is the point. It means you altered the format. Do not
simply update the expected values to make it pass. Work through this instead:

  1. Is the change necessary? A field added is a field every reader must
     tolerate forever.
  2. Bump GRAF_FORMAT_VERSION in graf/base.py:
       - additive change (new optional field)  -> bump MINOR (1.0 -> 1.1)
       - removal, rename, or type change       -> bump MAJOR (1.0 -> 2.0),
         which makes every existing file unreadable by this library
  3. Update FORMAT.md, including its version history table.
  4. Add a CHANGELOG entry under a "File format" heading.
  5. Only then update the expected schema below.

The point is that changing the format should be a deliberate act, announced in
three places, rather than a side effect of an ordinary refactor.
"""
import matplotlib.pyplot as plt
import pytest

from graf.base import (
    GRAF_FORMAT_VERSION,
    Axis,
    Font,
    Graf,
    GraphStyle,
    MetaInfo,
    Scale,
    Surface,
    Trace,
)

# The format version these expectations describe. Changing the schema below
# without changing this is almost certainly a mistake.
EXPECTED_FORMAT_VERSION = "1.0"

EXPECTED_SCHEMA = {
    "Graf": {
        "manifest": ["supertitle", "fig_width_cm", "fig_height_cm"],
        "obj_manifest": ["style", "info"],
        "dict_manifest": ["axes"],
    },
    "MetaInfo": {
        "manifest": ["version", "source_language", "source_library",
                     "source_version", "description", "conditions",
                     "provenance", "history"],
        "obj_manifest": [],
        "dict_manifest": [],
    },
    "GraphStyle": {
        "manifest": [],
        "obj_manifest": ["supertitle_font", "title_font", "graph_font",
                         "label_font", "legend_font"],
        "dict_manifest": [],
    },
    "Font": {
        # NOTE: 'family' is a font STACK (a list), not a single name.
        # 'weight' is 100-900; 'style' is normal/italic/oblique.
        # The .bold/.italic properties are computed views, deliberately NOT
        # stored -- do not add them here.
        "manifest": ["use_native", "size", "family", "weight", "style",
                     "resolved_family"],
        "obj_manifest": [],
        "dict_manifest": [],
    },
    "Axis": {
        "manifest": ["axis_type", "position", "span", "relative_size",
                     "grid_on", "legend_on", "legend_location", "title"],
        "obj_manifest": ["x_axis", "y_axis_L", "y_axis_R", "z_axis"],
        "dict_manifest": ["surfaces", "traces"],
    },
    "Scale": {
        "manifest": ["is_valid", "val_min", "val_max", "tick_list",
                     "minor_tick_list", "tick_label_list", "label",
                     "scale_type"],
        "obj_manifest": [],
        "dict_manifest": [],
    },
    "Trace": {
        "manifest": ["trace_type", "use_yaxis_R", "x_data", "y_data", "z_data",
                     "line_type", "marker_type", "marker_size", "line_width",
                     "display_name", "include_in_legend", "line_color", "alpha",
                     "marker_color", "has_error_bars", "x_err_neg", "x_err_pos",
                     "y_err_neg", "y_err_pos", "err_line_color",
                     "err_line_width", "err_cap_size", "err_cap_color",
                     "err_cap_width", "err_cap_visible"],
        "obj_manifest": [],
        "dict_manifest": [],
    },
    "Surface": {
        "manifest": ["surf_type", "cmap", "uniform_grid", "x_grid", "y_grid",
                     "z_grid", "line_type", "line_width", "display_name",
                     "include_in_legend", "line_color", "alpha", "antialias",
                     "has_colorbar", "colorbar_label", "colorbar_orientation",
                     "colorbar_ticks", "colorbar_tick_labels", "colorbar_vmin",
                     "colorbar_vmax"],
        "obj_manifest": [],
        "dict_manifest": [],
    },
}

CLASSES = {
    "Graf": Graf, "MetaInfo": MetaInfo, "GraphStyle": GraphStyle, "Font": Font,
    "Axis": Axis, "Scale": Scale, "Trace": Trace, "Surface": Surface,
}


def instantiate(name):
    cls = CLASSES[name]
    if name in ("Axis", "Scale"):
        return cls(GraphStyle())
    return cls()


def actual_schema(name):
    obj = instantiate(name)
    return {
        "manifest": list(obj.manifest),
        "obj_manifest": list(obj.obj_manifest),
        "dict_manifest": sorted(obj.dict_manifest.keys()),
    }


FAILURE_HINT = (
    "\n\nThe GrAF FILE FORMAT has changed.\n"
    "This is not a lint failure -- files already on disk are affected, as is "
    "every non-Python implementation.\n"
    "Before updating the expected values in tests/test_format_schema.py:\n"
    "  1. bump GRAF_FORMAT_VERSION (MINOR if additive, MAJOR if not)\n"
    "  2. update FORMAT.md and its version history\n"
    "  3. add a CHANGELOG entry under 'File format'\n"
)


@pytest.mark.parametrize("name", sorted(EXPECTED_SCHEMA))
class TestOnDiskSchema:

    def test_fields_unchanged(self, name):
        expected = EXPECTED_SCHEMA[name]["manifest"]
        actual = actual_schema(name)["manifest"]

        added = [f for f in actual if f not in expected]
        removed = [f for f in expected if f not in actual]
        assert actual == expected, (
            f"{name} fields changed. added={added} removed={removed}"
            + FAILURE_HINT
        )

    def test_nested_objects_unchanged(self, name):
        expected = EXPECTED_SCHEMA[name]["obj_manifest"]
        actual = actual_schema(name)["obj_manifest"]
        assert actual == expected, (
            f"{name} nested objects changed." + FAILURE_HINT
        )

    def test_nested_dicts_unchanged(self, name):
        expected = EXPECTED_SCHEMA[name]["dict_manifest"]
        actual = actual_schema(name)["dict_manifest"]
        assert actual == expected, (
            f"{name} nested collections changed." + FAILURE_HINT
        )


class TestFormatVersionDiscipline:

    def test_version_matches_the_documented_schema(self):
        assert GRAF_FORMAT_VERSION == EXPECTED_FORMAT_VERSION, (
            "GRAF_FORMAT_VERSION was changed without updating the schema this "
            "file documents (or vice versa)." + FAILURE_HINT
        )

    def test_written_files_declare_that_version(self, tmp_path):
        fig, ax = plt.subplots()
        ax.plot([1, 2], [3, 4])
        path = str(tmp_path / "v.graf")
        Graf(fig=fig).write_graf(path)
        plt.close(fig)

        g = Graf()
        g.read_graf(path)
        assert g.info.version == EXPECTED_FORMAT_VERSION

    def test_font_stores_weight_and_style_not_bools(self):
        """Regression guard on a change that was easy to make quietly.

        bold/italic are computed properties over weight/style. If they ever
        appear in the manifest, the format has silently regained two fields.
        """
        f = Font()
        assert "weight" in f.manifest and "style" in f.manifest
        assert "bold" not in f.manifest
        assert "italic" not in f.manifest
        assert f.bold is False and f.italic is False   # still usable as views

    def test_font_family_is_a_stack_not_a_string(self):
        assert isinstance(Font().family, list)
