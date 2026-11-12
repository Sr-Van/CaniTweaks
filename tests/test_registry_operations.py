"""Testes das operações de registro (valor único e por interface de rede)."""
import unittest

from app.adapters.operations.registry_operations import InterfaceValuesOperation, RegistryValueOperation
from tests.fakes import FakeRegistry

PATH = "HKLM\\Test"


class TestRegistryValueOperation(unittest.TestCase):
    def setUp(self):
        self.registry = FakeRegistry()
        self.op = RegistryValueOperation(self.registry, PATH, "Flag", 1, default=7)

    def test_is_applied_reflects_current_value(self):
        self.assertFalse(self.op.is_applied())
        self.registry.seed(PATH, "Flag", 1)
        self.assertTrue(self.op.is_applied())

    def test_restore_returns_original_value(self):
        self.registry.seed(PATH, "Flag", 42)
        snapshot = self.op.snapshot()
        self.op.apply()
        self.op.restore(snapshot)
        self.assertEqual(self.registry.read(PATH, "Flag").value, 42)

    def test_restore_removes_value_that_did_not_exist(self):
        snapshot = self.op.snapshot()
        self.op.apply()
        self.op.restore(snapshot)
        self.assertIsNone(self.registry.read(PATH, "Flag"))

    def test_reset_to_default_uses_default_or_removes(self):
        self.op.apply()
        self.op.reset_to_default()
        self.assertEqual(self.registry.read(PATH, "Flag").value, 7)

        removing = RegistryValueOperation(self.registry, PATH, "Other", 1)
        removing.apply()
        removing.reset_to_default()
        self.assertIsNone(self.registry.read(PATH, "Other"))


class TestInterfaceValuesOperation(unittest.TestCase):
    def setUp(self):
        self.registry = FakeRegistry()
        self.registry.seed(f"{PATH}\\{{A}}", "DhcpIPAddress", "1.1.1.1", reg_type=1)
        self.registry.seed(f"{PATH}\\{{B}}", "DhcpIPAddress", "2.2.2.2", reg_type=1)
        self.op = InterfaceValuesOperation(self.registry, PATH, {"TCPNoDelay": 1})

    def test_applies_to_every_interface_and_restores(self):
        self.registry.seed(f"{PATH}\\{{A}}", "TCPNoDelay", 0)
        snapshot = self.op.snapshot()
        self.op.apply()
        self.assertTrue(self.op.is_applied())

        self.op.restore(snapshot)
        self.assertEqual(self.registry.read(f"{PATH}\\{{A}}", "TCPNoDelay").value, 0)
        self.assertIsNone(self.registry.read(f"{PATH}\\{{B}}", "TCPNoDelay"))

    def test_not_applied_without_interfaces(self):
        empty = InterfaceValuesOperation(FakeRegistry(), PATH, {"TCPNoDelay": 1})
        self.assertFalse(empty.is_applied())


if __name__ == "__main__":
    unittest.main()
