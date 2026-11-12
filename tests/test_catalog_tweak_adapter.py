"""Testes do adapter de catálogo: aplicar -> verificar -> reverter, rollback e backup."""
import tempfile
import unittest
from pathlib import Path

from app.adapters.catalog import build_catalog
from app.adapters.catalog_tweak_adapter import CatalogTweakAdapter
from app.adapters.state_backup import JsonStateBackup
from app.domain.enums import TweakKind, TweakStatus
from tests.fakes import FakeCleaner, FakeRegistry, make_context

GAME_DVR = "HKCU\\System\\GameConfigStore"
GAME_DVR_APP = "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR"
POLICY = "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR"
INTERFACES = "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces"


class AdapterTestCase(unittest.TestCase):
    windows_build = 26100

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.backup_path = Path(self._tmp.name) / "backup.json"
        self.registry = FakeRegistry()
        self.cleaner = FakeCleaner(freed_bytes=5 * 1024 * 1024)
        self.context = make_context(registry=self.registry, cleaner=self.cleaner)
        self.adapter = self._build_adapter()

    def _build_adapter(self) -> CatalogTweakAdapter:
        return CatalogTweakAdapter(
            build_catalog(self.context), JsonStateBackup(self.backup_path), self.windows_build
        )


class TestApplyAndRevert(AdapterTestCase):
    def test_apply_marks_active_and_revert_restores_user_values(self):
        self.registry.seed(GAME_DVR, "GameDVR_Enabled", 1)
        self.registry.seed(POLICY, "AllowGameDVR", 1)

        self.assertEqual(self.adapter.check_status("disable_game_dvr"), TweakStatus.INACTIVE)
        self.assertTrue(self.adapter.apply("disable_game_dvr").ok)
        self.assertEqual(self.adapter.check_status("disable_game_dvr"), TweakStatus.ACTIVE)

        self.assertTrue(self.adapter.revert("disable_game_dvr").ok)
        self.assertEqual(self.registry.read(GAME_DVR, "GameDVR_Enabled").value, 1)
        self.assertEqual(self.registry.read(POLICY, "AllowGameDVR").value, 1)
        self.assertEqual(self.adapter.check_status("disable_game_dvr"), TweakStatus.INACTIVE)

    def test_revert_removes_values_that_did_not_exist_before(self):
        self.adapter.apply("hags")
        self.adapter.revert("hags")
        graphics = "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers"
        self.assertIsNone(self.registry.read(graphics, "HwSchMode"))

    def test_second_apply_does_not_overwrite_original_backup(self):
        self.registry.seed(GAME_DVR, "GameDVR_Enabled", 1)
        self.adapter.apply("disable_game_dvr")
        self.adapter.apply("disable_game_dvr")
        self.adapter.revert("disable_game_dvr")
        self.assertEqual(self.registry.read(GAME_DVR, "GameDVR_Enabled").value, 1)

    def test_backup_survives_restart_of_the_app(self):
        self.registry.seed(GAME_DVR, "GameDVR_Enabled", 1)
        self.adapter.apply("disable_game_dvr")

        self._build_adapter().revert("disable_game_dvr")
        self.assertEqual(self.registry.read(GAME_DVR, "GameDVR_Enabled").value, 1)

    def test_revert_without_backup_uses_windows_default(self):
        # Tweak já aplicado fora do app: não há backup, então reverter usa o padrão do Windows.
        self.registry.seed(GAME_DVR, "GameDVR_Enabled", 0)
        self.registry.seed(GAME_DVR_APP, "AppCaptureEnabled", 0)
        self.registry.seed(POLICY, "AllowGameDVR", 0)

        self.assertEqual(self.adapter.check_status("disable_game_dvr"), TweakStatus.ACTIVE)
        self.adapter.apply("disable_game_dvr")
        self.adapter.revert("disable_game_dvr")
        self.assertEqual(self.registry.read(GAME_DVR, "GameDVR_Enabled").value, 1)
        self.assertIsNone(self.registry.read(POLICY, "AllowGameDVR"))

    def test_result_reports_restart_requirement(self):
        self.assertTrue(self.adapter.apply("hags").needs_restart)
        self.assertFalse(self.adapter.apply("game_mode").needs_restart)

    def test_every_toggle_tweak_roundtrips_without_errors(self):
        self.registry.seed(f"{INTERFACES}\\{{X}}", "Dummy", 1)
        self.context.services.services.update({
            "DiagTrack": {"mode": "auto", "running": True},
            "dmwappushservice": {"mode": "demand", "running": False},
        })
        for tweak in self.adapter.get_all_tweaks():
            if tweak.kind != TweakKind.TOGGLE:
                continue
            with self.subTest(tweak=tweak.id):
                self.assertTrue(self.adapter.apply(tweak.id).ok)
                self.assertEqual(self.adapter.check_status(tweak.id), TweakStatus.ACTIVE)
                self.assertTrue(self.adapter.revert(tweak.id).ok)
                self.assertEqual(self.adapter.check_status(tweak.id), TweakStatus.INACTIVE)


class TestFailureHandling(AdapterTestCase):
    def test_partial_failure_rolls_back_and_reports_error(self):
        self.registry.seed(GAME_DVR, "GameDVR_Enabled", 1)
        self.registry.fail_writes_for = {"AllowGameDVR"}  # Falha na última operação.

        result = self.adapter.apply("disable_game_dvr")

        self.assertFalse(result.ok)
        self.assertIn("AllowGameDVR", result.error)
        self.assertEqual(self.registry.read(GAME_DVR, "GameDVR_Enabled").value, 1)
        self.assertIsNone(JsonStateBackup(self.backup_path).get("disable_game_dvr"))

    def test_unknown_tweak_returns_failure_and_unknown_status(self):
        self.assertFalse(self.adapter.apply("nao_existe").ok)
        self.assertFalse(self.adapter.revert("nao_existe").ok)
        self.assertEqual(self.adapter.check_status("nao_existe"), TweakStatus.UNKNOWN)


class TestUnsupportedBuild(AdapterTestCase):
    windows_build = 19045  # Windows 10

    def test_timer_resolution_is_unsupported_on_windows_10(self):
        self.assertEqual(self.adapter.check_status("global_timer_resolution"), TweakStatus.UNSUPPORTED)
        self.assertFalse(self.adapter.apply("global_timer_resolution").ok)
        self.assertEqual(self.adapter.check_status("hags"), TweakStatus.INACTIVE)


class TestActions(AdapterTestCase):
    def test_cleanup_runs_cleaner_and_reports_freed_space(self):
        result = self.adapter.apply("clean_temp_files")
        self.assertTrue(result.ok)
        self.assertIn("5,0 MB", result.message)
        self.assertEqual(len(self.cleaner.calls), 1)

    def test_actions_are_not_revertible_and_stay_inactive(self):
        self.assertFalse(self.adapter.revert("clean_temp_files").ok)
        self.assertEqual(self.adapter.check_status("clean_temp_files"), TweakStatus.INACTIVE)


class TestCatalogIntegrity(AdapterTestCase):
    def test_ids_are_unique_and_entries_are_consistent(self):
        entries = build_catalog(self.context)
        ids = [entry.tweak.id for entry in entries]
        self.assertEqual(len(ids), len(set(ids)))
        for entry in entries:
            if entry.tweak.kind == TweakKind.TOGGLE:
                self.assertTrue(entry.operations, entry.tweak.id)
                self.assertIsNone(entry.action)
            else:
                self.assertIsNotNone(entry.action, entry.tweak.id)


if __name__ == "__main__":
    unittest.main()
