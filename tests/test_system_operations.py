"""Testes das operações de serviço e energia."""
import unittest

from app.adapters.operations.power_operations import (
    BALANCED_GUID,
    ULTIMATE_PERFORMANCE_GUID,
    WINTWEAKS_ULTIMATE_GUID,
    PowerSettingOperation,
    UltimatePerformancePlanOperation,
)
from app.adapters.operations.service_operations import DisableServiceOperation
from tests.fakes import FakePowerCfg, FakeServices


class TestDisableServiceOperation(unittest.TestCase):
    def setUp(self):
        self.services = FakeServices({"DiagTrack": {"mode": "auto", "running": True}})
        self.op = DisableServiceOperation(self.services, "DiagTrack", default_mode="auto")

    def test_apply_disables_and_stops(self):
        self.op.apply()
        self.assertEqual(self.services.services["DiagTrack"], {"mode": "disabled", "running": False})
        self.assertTrue(self.op.is_applied())

    def test_restore_brings_back_mode_and_running_state(self):
        snapshot = self.op.snapshot()
        self.op.apply()
        self.op.restore(snapshot)
        self.assertEqual(self.services.services["DiagTrack"], {"mode": "auto", "running": True})

    def test_missing_service_counts_as_applied_and_is_noop(self):
        missing = DisableServiceOperation(self.services, "dmwappushservice")
        self.assertTrue(missing.is_applied())
        missing.apply()
        missing.restore(missing.snapshot())
        missing.reset_to_default()


class TestUltimatePerformancePlanOperation(unittest.TestCase):
    def setUp(self):
        self.powercfg = FakePowerCfg()
        self.op = UltimatePerformancePlanOperation(self.powercfg)

    def test_apply_creates_and_activates_plan(self):
        self.op.apply()
        self.assertEqual(self.powercfg.active, WINTWEAKS_ULTIMATE_GUID)
        self.assertTrue(self.op.is_applied())

    def test_apply_is_idempotent(self):
        self.op.apply()
        self.op.apply()
        self.assertEqual(self.powercfg.schemes.count(WINTWEAKS_ULTIMATE_GUID), 1)

    def test_restore_reactivates_previous_and_removes_copy(self):
        snapshot = self.op.snapshot()
        self.op.apply()
        self.op.restore(snapshot)
        self.assertEqual(self.powercfg.active, BALANCED_GUID)
        self.assertNotIn(WINTWEAKS_ULTIMATE_GUID, self.powercfg.schemes)

    def test_original_ultimate_plan_counts_as_applied(self):
        self.powercfg.active = ULTIMATE_PERFORMANCE_GUID
        self.assertTrue(self.op.is_applied())


class TestPowerSettingOperation(unittest.TestCase):
    def test_apply_restore_and_default(self):
        powercfg = FakePowerCfg()
        powercfg.ac_values[("sub", "set")] = 2
        op = PowerSettingOperation(powercfg, "sub", "set", 0, default=1)

        snapshot = op.snapshot()
        op.apply()
        self.assertTrue(op.is_applied())

        op.restore(snapshot)
        self.assertEqual(powercfg.get_ac_value("sub", "set"), 2)

        op.reset_to_default()
        self.assertEqual(powercfg.get_ac_value("sub", "set"), 1)


if __name__ == "__main__":
    unittest.main()
