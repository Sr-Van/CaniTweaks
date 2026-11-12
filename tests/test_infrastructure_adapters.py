"""Testes dos adapters de infraestrutura (disco, backup, powercfg, serviços, restauração, registro)."""
import json
import os
import tempfile
import unittest
import winreg
from pathlib import Path

from app.adapters.disk_clean_adapter import DiskCleanAdapter
from app.adapters.errors import SystemOperationError
from app.adapters.powercfg_adapter import PowerCfgAdapter
from app.adapters.registry_adapter import WindowsRegistryAdapter
from app.adapters.restore_adapter import SystemRestoreAdapter
from app.adapters.services_adapter import WindowsServiceAdapter
from app.adapters.state_backup import JsonStateBackup
from app.domain.formatting import format_bytes
from tests.fakes import FakeRegistry, FakeRunner


class TestDiskCleanAdapter(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "cache"
        (self.root / "sub" / "deep").mkdir(parents=True)
        (self.root / "a.bin").write_bytes(b"x" * 100)
        (self.root / "sub" / "b.bin").write_bytes(b"y" * 50)
        (self.root / "sub" / "deep" / "c.bin").write_bytes(b"z" * 25)

    def test_empties_directory_and_counts_freed_bytes(self):
        summary = DiskCleanAdapter().clean([str(self.root)])

        self.assertEqual(summary.freed_bytes, 175)
        self.assertEqual(summary.failed_files, 0)
        self.assertTrue(self.root.is_dir())  # A pasta raiz é preservada.
        self.assertEqual(list(self.root.iterdir()), [])

    def test_read_only_files_are_removed(self):
        target = self.root / "a.bin"
        os.chmod(target, 0o444)
        DiskCleanAdapter().clean([str(self.root)])
        self.assertFalse(target.exists())

    def test_locked_file_is_counted_as_failure_not_exception(self):
        locked = self.root / "a.bin"
        with open(locked, "rb"):  # No Windows, arquivo aberto não pode ser removido.
            summary = DiskCleanAdapter().clean([str(self.root)])
        self.assertEqual(summary.failed_files, 1)
        self.assertEqual(summary.freed_bytes, 75)

    def test_refuses_drive_roots_and_unexpanded_variables(self):
        summary = DiskCleanAdapter().clean(["C:\\", "C:\\Windows", "%VARIAVEL_INEXISTENTE%\\Temp"])
        self.assertEqual((summary.freed_bytes, summary.failed_files), (0, 0))

    def test_missing_directory_is_ignored(self):
        summary = DiskCleanAdapter().clean([str(self.root / "nao_existe")])
        self.assertEqual(summary.freed_bytes, 0)


class TestJsonStateBackup(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "state.json"
        self.backup = JsonStateBackup(self.path)

    def test_save_get_delete_roundtrip(self):
        self.backup.save("t", {"k": {"exists": True, "value": 1}})
        self.assertEqual(self.backup.get("t"), {"k": {"exists": True, "value": 1}})
        self.backup.delete("t")
        self.assertIsNone(self.backup.get("t"))

    def test_corrupt_file_is_treated_as_empty(self):
        self.path.write_text("{ não é json", encoding="utf-8")
        self.assertIsNone(self.backup.get("t"))
        self.backup.save("t", {"ok": 1})
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), {"t": {"ok": 1}})


class TestPowerCfgAdapter(unittest.TestCase):
    ACTIVE_PT = "GUID do Esquema de Energia: 381B4222-F694-41F0-9685-FF5BB260DF2E  (Equilibrado)"

    def test_active_scheme_is_parsed_regardless_of_language(self):
        adapter = PowerCfgAdapter(FakeRunner(stdout=self.ACTIVE_PT))
        self.assertEqual(adapter.get_active_scheme(), "381b4222-f694-41f0-9685-ff5bb260df2e")

    def test_ac_value_uses_second_to_last_hex_value(self):
        output = (
            "  Índice de Configuração de Energia CA Atual: 0x00000002\n"
            "  Índice de Configuração de Energia CC Atual: 0x00000001\n"
        )
        self.assertEqual(PowerCfgAdapter(FakeRunner(stdout=output)).get_ac_value("s", "t"), 2)

    def test_failed_command_raises_system_operation_error(self):
        adapter = PowerCfgAdapter(FakeRunner(returncode=1, stderr="não existe"))
        with self.assertRaises(SystemOperationError):
            adapter.get_ac_value("s", "t")

    def test_set_ac_value_applies_and_reactivates_scheme(self):
        runner = FakeRunner()
        PowerCfgAdapter(runner).set_ac_value("sub", "set", 0)
        self.assertEqual(runner.commands[0][:2], ["powercfg", "/setacvalueindex"])
        self.assertEqual(runner.commands[1], ["powercfg", "/setactive", "SCHEME_CURRENT"])


class TestWindowsServiceAdapter(unittest.TestCase):
    SERVICES = "HKLM\\SYSTEM\\CurrentControlSet\\Services"

    def test_start_mode_is_read_from_registry(self):
        registry = FakeRegistry()
        registry.seed(f"{self.SERVICES}\\A", "Start", 4)
        registry.seed(f"{self.SERVICES}\\B", "Start", 2)
        registry.seed(f"{self.SERVICES}\\C", "Start", 2)
        registry.seed(f"{self.SERVICES}\\C", "DelayedAutostart", 1)
        adapter = WindowsServiceAdapter(registry, FakeRunner())

        self.assertEqual(adapter.get_start_mode("A"), "disabled")
        self.assertEqual(adapter.get_start_mode("B"), "auto")
        self.assertEqual(adapter.get_start_mode("C"), "delayed-auto")
        self.assertIsNone(adapter.get_start_mode("Z"))

    def test_is_running_parses_sc_query(self):
        runner = FakeRunner(stdout="        STATE              : 4  RUNNING")
        self.assertTrue(WindowsServiceAdapter(FakeRegistry(), runner).is_running("X"))
        runner = FakeRunner(stdout="        STATE              : 1  STOPPED")
        self.assertFalse(WindowsServiceAdapter(FakeRegistry(), runner).is_running("X"))

    def test_set_start_mode_validates_mode_and_command_result(self):
        adapter = WindowsServiceAdapter(FakeRegistry(), FakeRunner())
        with self.assertRaises(SystemOperationError):
            adapter.set_start_mode("X", "invalido")

        failing = WindowsServiceAdapter(FakeRegistry(), FakeRunner(returncode=5, stderr="Acesso negado"))
        with self.assertRaises(SystemOperationError):
            failing.set_start_mode("X", "disabled")


class TestSystemRestoreAdapter(unittest.TestCase):
    def test_description_is_escaped_for_powershell(self):
        runner = FakeRunner()
        result = SystemRestoreAdapter(runner).create_restore_point("It's a test")
        self.assertTrue(result.ok)
        self.assertIn("'It''s a test'", runner.commands[0][-1])

    def test_failure_is_returned_as_result(self):
        result = SystemRestoreAdapter(FakeRunner(returncode=1, stderr="sem proteção")).create_restore_point("x")
        self.assertFalse(result.ok)
        self.assertIn("sem proteção", result.error)


class TestWindowsRegistryAdapter(unittest.TestCase):
    """Teste de integração com uma chave descartável em HKCU (não exige administrador)."""

    KEY = "HKCU\\Software\\WinTweaksTests"

    def setUp(self):
        self.registry = WindowsRegistryAdapter()
        self.addCleanup(self._remove_test_key)

    @staticmethod
    def _remove_test_key():
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, "Software\\WinTweaksTests")
        except OSError:
            pass

    def test_write_read_delete_and_types(self):
        self.registry.write(self.KEY, "Numero", 0xFFFFFFFF)
        self.registry.write(self.KEY, "Texto", "abc", winreg.REG_SZ)

        self.assertEqual(self.registry.read(self.KEY, "Numero").value, 0xFFFFFFFF)
        self.assertEqual(self.registry.read(self.KEY, "Texto").value, "abc")
        self.registry.delete(self.KEY, "Numero")
        self.registry.delete(self.KEY, "Numero")  # Idempotente.
        self.assertIsNone(self.registry.read(self.KEY, "Numero"))

        self.registry.delete(self.KEY, "Texto")

    def test_list_subkeys_and_missing_key(self):
        self.registry.write(f"{self.KEY}\\Filha", "V", 1)
        self.assertEqual(self.registry.list_subkeys(self.KEY), ["Filha"])
        self.assertEqual(self.registry.list_subkeys("HKCU\\Software\\WinTweaksInexistente"), [])
        self.registry.delete(f"{self.KEY}\\Filha", "V")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, "Software\\WinTweaksTests\\Filha")

    def test_invalid_values_and_hives_are_rejected(self):
        with self.assertRaises(SystemOperationError):
            self.registry.write(self.KEY, "X", "texto", winreg.REG_DWORD)
        with self.assertRaises(SystemOperationError):
            self.registry.write(self.KEY, "X", -1)
        with self.assertRaises(SystemOperationError):
            self.registry.read("HKXX\\Software", "X")


class TestFormatBytes(unittest.TestCase):
    def test_units(self):
        self.assertEqual(format_bytes(0), "0 B")
        self.assertEqual(format_bytes(1536), "1,5 KB")
        self.assertEqual(format_bytes(5 * 1024 * 1024), "5,0 MB")
        self.assertEqual(format_bytes(3 * 1024 ** 3), "3,0 GB")


if __name__ == "__main__":
    unittest.main()
