"""Tests for graf-upgrade.

The tool rewrites archives, so the safety properties matter more than the
conversion itself: never lose the original, never leave a truncated file behind,
never touch a file it could not fully read, and never claim to have done
something it did not do.
"""
import os
import shutil

import matplotlib.pyplot as plt
import pytest

from graf.base import GRAF_FORMAT_VERSION, Graf
from graf.scripts.grafupgrade import file_version, find_files, main, upgrade_file
from stardust.tome import tome_to_dict

LEGACY_SRC = os.path.join(os.path.dirname(__file__), "data",
                          "legacy_format_0_0_0.graf")


@pytest.fixture
def legacy_copy(tmp_path):
    dst = tmp_path / "old.graf"
    shutil.copy2(LEGACY_SRC, dst)
    return str(dst)


@pytest.fixture
def current_file(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    path = str(tmp_path / "new.graf")
    Graf(fig=fig).write_graf(path)
    plt.close(fig)
    return path


class TestVersionDetection:

    def test_reads_legacy_version(self, legacy_copy):
        assert file_version(legacy_copy) == "0.0.0"

    def test_reads_current_version(self, current_file):
        assert file_version(current_file) == GRAF_FORMAT_VERSION

    def test_unreadable_file_returns_none(self, tmp_path):
        bad = tmp_path / "junk.graf"
        bad.write_text("not a graf file")
        assert file_version(str(bad)) is None


class TestUpgrade:

    def test_legacy_file_is_upgraded(self, legacy_copy):
        assert upgrade_file(legacy_copy) == 'upgraded'
        assert file_version(legacy_copy) == GRAF_FORMAT_VERSION

    def test_current_file_is_left_alone(self, current_file):
        before = os.path.getmtime(current_file)
        assert upgrade_file(current_file) == 'current'
        assert os.path.getmtime(current_file) == before

    def test_upgrade_is_idempotent(self, legacy_copy):
        upgrade_file(legacy_copy, backup=False)
        assert upgrade_file(legacy_copy, backup=False) == 'current'

    def test_data_survives_the_upgrade(self, legacy_copy):
        before = Graf()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            before.read_graf(legacy_copy)
        original = list(before.axes['Ax0'].traces['Tr0'].y_data)

        upgrade_file(legacy_copy, backup=False)

        after = Graf()
        after.read_graf(legacy_copy)
        assert list(after.axes['Ax0'].traces['Tr0'].y_data) == original
        assert len(after.axes['Ax0'].traces) == 2

    def test_upgraded_file_reads_without_a_legacy_warning(self, legacy_copy):
        import warnings
        upgrade_file(legacy_copy, backup=False)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Graf().read_graf(legacy_copy)
        assert not any("pre-release" in str(w.message) for w in caught)

    def test_upgraded_file_reports_a_clean_unpack(self, legacy_copy):
        upgrade_file(legacy_copy, backup=False)
        g = Graf()
        g.read_graf(legacy_copy)
        assert g.unpack_report.ok


class TestProvenance:

    def test_upgrade_is_recorded_in_history(self, legacy_copy):
        upgrade_file(legacy_copy, backup=False)
        history = tome_to_dict(legacy_copy)['info']['history']
        assert any('upgraded' in h['action'] for h in history)

    def test_creation_record_is_not_rewritten(self, legacy_copy):
        original = tome_to_dict(legacy_copy)['info']['provenance']['created_utc']
        upgrade_file(legacy_copy, backup=False)
        assert tome_to_dict(legacy_copy)['info']['provenance']['created_utc'] == original

    def test_earlier_history_is_preserved(self, legacy_copy):
        before = len(tome_to_dict(legacy_copy)['info']['history'])
        upgrade_file(legacy_copy, backup=False)
        assert len(tome_to_dict(legacy_copy)['info']['history']) > before


class TestSafety:

    def test_backup_is_written_by_default(self, legacy_copy):
        upgrade_file(legacy_copy)
        assert os.path.isfile(legacy_copy + ".bak")

    def test_backup_still_holds_the_original(self, legacy_copy):
        upgrade_file(legacy_copy)
        assert file_version(legacy_copy + ".bak") == "0.0.0"

    def test_existing_backup_is_never_overwritten(self, legacy_copy):
        """Refuse rather than destroy a backup the user may be relying on."""
        with open(legacy_copy + ".bak", 'w') as fh:
            fh.write("precious")
        assert upgrade_file(legacy_copy) == 'failed'
        with open(legacy_copy + ".bak") as fh:
            assert fh.read() == "precious"

    def test_no_backup_flag_writes_none(self, legacy_copy):
        upgrade_file(legacy_copy, backup=False)
        assert not os.path.exists(legacy_copy + ".bak")

    def test_dry_run_writes_nothing(self, legacy_copy):
        before = os.path.getmtime(legacy_copy)
        assert upgrade_file(legacy_copy, dry_run=True) == 'would-upgrade'
        assert os.path.getmtime(legacy_copy) == before
        assert not os.path.exists(legacy_copy + ".bak")

    def test_unreadable_file_is_left_untouched(self, tmp_path):
        bad = tmp_path / "junk.graf"
        bad.write_text("not a graf file")
        before = bad.read_text()
        assert upgrade_file(str(bad), backup=False) == 'failed'
        assert bad.read_text() == before

    def test_no_temp_file_is_left_behind(self, legacy_copy):
        upgrade_file(legacy_copy, backup=False)
        assert not os.path.exists(legacy_copy + ".upgrading")


class TestFileDiscovery:

    def test_directory_is_expanded(self, tmp_path, legacy_copy):
        assert find_files([str(tmp_path)]) == [legacy_copy]

    def test_non_graf_files_are_ignored(self, tmp_path, legacy_copy):
        (tmp_path / "notes.txt").write_text("hello")
        assert find_files([str(tmp_path)]) == [legacy_copy]

    def test_recursive_finds_nested_files(self, tmp_path):
        sub = tmp_path / "a" / "b"
        sub.mkdir(parents=True)
        shutil.copy2(LEGACY_SRC, sub / "deep.graf")
        assert len(find_files([str(tmp_path)], recursive=True)) == 1

    def test_non_recursive_skips_subdirectories(self, tmp_path):
        sub = tmp_path / "a"
        sub.mkdir()
        shutil.copy2(LEGACY_SRC, sub / "deep.graf")
        assert find_files([str(tmp_path)]) == []


class TestCommandLine:

    def test_exit_zero_on_success(self, legacy_copy):
        assert main([legacy_copy, "--no-backup"]) == 0

    def test_exit_nonzero_when_a_file_fails(self, tmp_path):
        bad = tmp_path / "junk.graf"
        bad.write_text("nope")
        assert main([str(bad), "--no-backup"]) == 1

    def test_exit_nonzero_when_nothing_found(self, tmp_path):
        assert main([str(tmp_path)]) == 1

    def test_missing_file_is_reported_not_crashed(self, tmp_path):
        assert main([str(tmp_path / "nope.graf")]) == 1

    def test_dry_run_via_cli(self, legacy_copy):
        before = os.path.getmtime(legacy_copy)
        assert main(["-n", legacy_copy]) == 0
        assert os.path.getmtime(legacy_copy) == before
