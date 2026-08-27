"""Tests for provenance and history stamping.

GrAF is meant to be a self-describing archive: the plot AND its data, openable
later on any machine. Provenance is what makes that promise real rather than
aspirational, so its two invariants are worth pinning down explicitly:

  * creation provenance is written ONCE and is thereafter immutable
  * history is append-only -- one record per save that changed the data
"""
import matplotlib.pyplot as plt
import numpy as np
import pytest

from graf.base import (
    GRAF_FORMAT_VERSION,
    PROVENANCE_SCHEMA,
    Graf,
    MetaInfo,
    _library_version,
    save_graf,
)


@pytest.fixture
def fig():
    f, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    yield f
    plt.close(f)


def reload(path):
    g = Graf()
    g.read_graf(path)
    return g


# ---------------------------------------------------------------------------
# Creation record
# ---------------------------------------------------------------------------

class TestCreationProvenance:

    def test_written_on_first_save(self, fig, tmp_path):
        p = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p)
        assert reload(p).info.provenance

    def test_records_schema_and_versions(self, fig, tmp_path):
        p = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p)
        prov = reload(p).info.provenance
        assert prov["provenance_schema"] == PROVENANCE_SCHEMA
        assert prov["graf_format_version"] == GRAF_FORMAT_VERSION
        assert prov["graf_library_version"] == _library_version()

    def test_records_creation_time_as_utc_iso(self, fig, tmp_path):
        import datetime
        p = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p)
        stamp = reload(p).info.provenance["created_utc"]
        parsed = datetime.datetime.fromisoformat(stamp)
        assert parsed.tzinfo is not None

    def test_is_immutable_across_resaves(self, fig, tmp_path):
        """Re-saving must never rewrite the creation record."""
        p1 = str(tmp_path / "a.graf")
        g = Graf(fig=fig)
        g.write_graf(p1)
        original = dict(reload(p1).info.provenance)

        g2 = reload(p1)
        p2 = str(tmp_path / "b.graf")
        g2.write_graf(p2)
        assert reload(p2).info.provenance == original

    def test_system_info_included_by_default(self, fig, tmp_path):
        p = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p)
        prov = reload(p).info.provenance
        for key in ("hostname", "os_platform", "machine_arch"):
            assert key in prov

    def test_system_info_can_be_omitted(self, fig, tmp_path):
        """Privacy switch: no hostname or machine identity in the file."""
        p = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p, include_system_info=False)
        prov = reload(p).info.provenance
        for key in ("hostname", "os_platform", "machine_arch", "cpu_model"):
            assert key not in prov

    def test_source_app_recorded(self, fig, tmp_path):
        p = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p, source_app="test_harness 9.9")
        assert reload(p).info.provenance.get("created_by_app") == "test_harness 9.9"

    def test_source_format_recorded_by_save_graf(self, fig, tmp_path):
        p = str(tmp_path / "a.graf")
        save_graf(fig, p)
        assert reload(p).info.provenance.get("source_format") == "matplotlib_figure"

    def test_no_absolute_paths_leak(self, fig, tmp_path):
        """Full paths leak directory structure and are meaningless elsewhere."""
        p = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p, source_file=str(tmp_path / "origin.csv"),
                                 source_format="csv")
        prov = reload(p).info.provenance
        for value in prov.values():
            assert str(tmp_path) not in str(value)


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

class TestHistory:

    def test_first_save_creates_one_entry(self, fig, tmp_path):
        p = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p)
        hist = reload(p).info.history
        assert len(hist) == 1
        assert hist[0]["action"] == "created"

    def test_entries_carry_required_fields(self, fig, tmp_path):
        p = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p)
        entry = reload(p).info.history[0]
        for key in ("utc", "action", "by", "content_sha256"):
            assert key in entry

    def test_unchanged_resave_does_not_append(self, fig, tmp_path):
        """History records changes, not saves. Identical data adds nothing."""
        p1 = str(tmp_path / "a.graf")
        g = Graf(fig=fig)
        g.write_graf(p1)
        g2 = reload(p1)
        p2 = str(tmp_path / "b.graf")
        g2.write_graf(p2)
        assert len(reload(p2).info.history) == 1

    def test_changed_data_appends_an_entry(self, fig, tmp_path):
        p1 = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p1)

        g = reload(p1)
        trace = g.axes['Ax0'].traces['Tr0']
        trace.y_data = [float(v) * 2 for v in trace.y_data]

        p2 = str(tmp_path / "b.graf")
        g.write_graf(p2)
        assert len(reload(p2).info.history) == 2

    def test_history_is_append_only(self, fig, tmp_path):
        """Earlier entries must survive verbatim."""
        p1 = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p1)
        first = dict(reload(p1).info.history[0])

        g = reload(p1)
        g.axes['Ax0'].traces['Tr0'].y_data = [9.0, 9.0, 9.0]
        p2 = str(tmp_path / "b.graf")
        g.write_graf(p2)

        assert reload(p2).info.history[0] == first

    def test_explicit_action_is_recorded(self, fig, tmp_path):
        p = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p, action="edited trace data")
        assert reload(p).info.history[-1]["action"] == "edited trace data"

    def test_content_hash_tracks_the_data(self, fig, tmp_path):
        """Same data -> same hash; different data -> different hash."""
        p1 = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p1)
        h1 = reload(p1).info.history[0]["content_sha256"]

        g = reload(p1)
        g.axes['Ax0'].traces['Tr0'].y_data = [1.0, 1.0, 1.0]
        p2 = str(tmp_path / "b.graf")
        g.write_graf(p2)
        assert reload(p2).info.history[-1]["content_sha256"] != h1

    def test_values_stay_flat_for_portability(self, fig, tmp_path):
        """Flat str/number values survive the TOME round-trip and stay readable
        in a structure browser -- nested objects would not."""
        p = str(tmp_path / "a.graf")
        Graf(fig=fig).write_graf(p, source_app="app 1.0")
        g = reload(p)
        for value in g.info.provenance.values():
            assert isinstance(value, (str, int, float, bool))
        for entry in g.info.history:
            for value in entry.values():
                assert isinstance(value, (str, int, float, bool))


# ---------------------------------------------------------------------------
# Mutable default arguments
# ---------------------------------------------------------------------------

class TestConditionsIsolation:
    """`conditions:dict={}` was a shared mutable default: conditions written
    into one figure would silently appear in the next one created."""

    def test_default_conditions_not_shared_between_instances(self):
        a = MetaInfo()
        b = MetaInfo()
        a.conditions['temperature_K'] = 4.2
        assert b.conditions == {}

    def test_default_conditions_not_shared_between_grafs(self):
        a = Graf()
        b = Graf()
        a.info.conditions['bias_V'] = 1.5
        assert b.info.conditions == {}

    def test_supplied_conditions_are_copied(self):
        supplied = {'temperature_K': 300}
        info = MetaInfo(conditions=supplied)
        info.conditions['temperature_K'] = 4
        assert supplied['temperature_K'] == 300

    def test_conditions_round_trip(self, fig, tmp_path):
        p = str(tmp_path / "a.graf")
        Graf(fig=fig, conditions={'temperature_K': 4.2}).write_graf(p)
        assert reload(p).info.conditions['temperature_K'] == pytest.approx(4.2)

    def test_description_round_trip(self, fig, tmp_path):
        p = str(tmp_path / "a.graf")
        Graf(fig=fig, description="Sample A, cooldown 3").write_graf(p)
        assert reload(p).info.description == "Sample A, cooldown 3"
