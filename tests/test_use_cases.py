"""Testes dos casos de uso: TweakManager, BatchRunner, PresetsManager e relatório."""
import unittest
from datetime import datetime
from unittest import mock

from app.domain.entities import Preset, SystemInfo, Tweak
from app.domain.enums import OutcomeKind, RiskLevel, TweakCategory, TweakKind, TweakStatus
from app.domain.presets import DEFAULT_PRESETS
from app.domain.result import Result
from app.use_cases.batch_runner import BatchRunner
from app.use_cases.presets_manager import PresetNotFoundError, PresetsManager
from app.use_cases.status_report import build_status_report
from app.use_cases.tweak_manager import TweakManager
from tests.fakes import InMemoryTweakPort, RecordingRestorePort


def make_tweak(tweak_id: str, **kwargs) -> Tweak:
    defaults = dict(name=f"Tweak {tweak_id}", summary="resumo", category=TweakCategory.LATENCY)
    defaults.update(kwargs)
    return Tweak(id=tweak_id, **defaults)


class UseCaseTestCase(unittest.TestCase):
    def setUp(self):
        self.tweaks = [
            make_tweak("a", requires_restart=True),
            make_tweak("b", category=TweakCategory.FPS, name="Latência de rede", risk=RiskLevel.MEDIUM),
            make_tweak("clean", category=TweakCategory.DISK_CLEANUP, kind=TweakKind.ACTION),
        ]
        self.port = InMemoryTweakPort(self.tweaks)
        self.manager = TweakManager(self.port)
        self.restore = RecordingRestorePort()
        self.runner = BatchRunner(self.manager, self.restore)


class TestTweakManager(UseCaseTestCase):
    def test_filters_by_category(self):
        self.assertEqual([t.id for t in self.manager.get_tweaks(TweakCategory.FPS)], ["b"])
        self.assertEqual(len(self.manager.get_tweaks()), 3)

    def test_search_ignores_case_and_accents(self):
        self.assertEqual([t.id for t in self.manager.get_tweaks(query="LATENCIA")], ["b"])

    def test_search_combines_with_category(self):
        self.assertEqual(self.manager.get_tweaks(TweakCategory.LATENCY, query="latencia"), [])

    def test_unexpected_adapter_error_becomes_failure_result(self):
        with mock.patch.object(self.port, "apply", side_effect=RuntimeError("boom")):
            result = self.manager.apply_tweak("a")
        self.assertFalse(result.ok)
        self.assertIn("boom", result.error)

    def test_get_statuses_covers_all_tweaks(self):
        self.assertEqual(set(self.manager.get_statuses()), {"a", "b", "clean"})


class TestBatchRunner(UseCaseTestCase):
    def test_apply_batch_reports_done_failed_and_restart(self):
        self.port.fail_ids = {"b"}
        report = self.runner.apply_batch(self.tweaks)

        self.assertEqual([o.tweak.id for o in report.done], ["a", "clean"])
        self.assertEqual([o.tweak.id for o in report.failed], ["b"])
        self.assertEqual(report.restart_required, ["Tweak a"])
        self.assertFalse(report.cancelled)

    def test_apply_batch_creates_restore_point_only_for_reversible_tweaks(self):
        self.runner.apply_batch([self.tweaks[2]])
        self.assertEqual(self.restore.descriptions, [])

        report = self.runner.apply_batch(self.tweaks[:1])
        self.assertEqual(len(self.restore.descriptions), 1)
        self.assertTrue(report.restore_point.ok)

    def test_already_active_tweaks_are_skipped(self):
        self.port.statuses["a"] = TweakStatus.ACTIVE
        report = self.runner.apply_batch(self.tweaks[:1])
        self.assertEqual(report.outcomes[0].kind, OutcomeKind.SKIPPED)
        self.assertEqual(self.port.calls, [])

    def test_unsupported_tweaks_are_skipped(self):
        self.port.statuses["a"] = TweakStatus.UNSUPPORTED
        report = self.runner.apply_batch(self.tweaks[:1])
        self.assertEqual(report.outcomes[0].kind, OutcomeKind.SKIPPED)

    def test_cancellation_stops_before_next_tweak(self):
        cancel_after_first = iter([False, True])
        report = self.runner.apply_batch(self.tweaks, should_cancel=lambda: next(cancel_after_first))
        self.assertTrue(report.cancelled)
        self.assertEqual(len(report.outcomes), 1)

    def test_progress_callback_receives_position_total_and_name(self):
        calls = []
        self.runner.apply_batch(self.tweaks[:2], progress=lambda *args: calls.append(args))
        self.assertEqual(calls, [(1, 2, "Tweak a"), (2, 2, "Latência de rede")])

    def test_revert_batch_ignores_actions_and_inactive_tweaks(self):
        self.port.statuses["a"] = TweakStatus.ACTIVE
        report = self.runner.revert_batch(self.tweaks)

        self.assertEqual([o.tweak.id for o in report.done], ["a"])
        self.assertEqual([o.tweak.id for o in report.skipped], ["b"])
        self.assertEqual(len(report.outcomes), 2)  # A ação "clean" nem entra no lote.

    def test_failure_of_restore_point_does_not_block_batch(self):
        runner = BatchRunner(self.manager, RecordingRestorePort(Result.failure("sem proteção do sistema")))
        report = runner.apply_batch(self.tweaks[:1])
        self.assertFalse(report.restore_point.ok)
        self.assertEqual(len(report.done), 1)


class TestPresetsManager(UseCaseTestCase):
    def setUp(self):
        super().setUp()
        presets = [Preset("p", "Preset", "desc", "x", ("a", "b", "inexistente"))]
        self.presets = PresetsManager(presets, self.manager, self.runner)

    def test_unknown_preset_raises(self):
        with self.assertRaises(PresetNotFoundError):
            self.presets.apply_preset("nope")

    def test_unknown_tweak_ids_are_ignored(self):
        self.assertEqual([t.id for t in self.presets.get_preset_tweaks("p")], ["a", "b"])

    def test_apply_and_revert_preset(self):
        self.assertEqual(len(self.presets.apply_preset("p").done), 2)
        self.assertEqual(self.presets.get_progress("p", self.manager.get_statuses()), (2, 2))
        self.assertEqual(len(self.presets.revert_preset("p").done), 2)
        self.assertEqual(self.presets.get_progress("p", self.manager.get_statuses()), (0, 2))

    def test_progress_ignores_unsupported_tweaks(self):
        statuses = {"a": TweakStatus.ACTIVE, "b": TweakStatus.UNSUPPORTED}
        self.assertEqual(self.presets.get_progress("p", statuses), (1, 1))


class TestDefaultPresets(unittest.TestCase):
    def test_default_presets_reference_only_existing_tweaks(self):
        from app.adapters.catalog import build_catalog
        from tests.fakes import make_context

        catalog_ids = {entry.tweak.id for entry in build_catalog(make_context())}
        self.assertEqual(len({p.id for p in DEFAULT_PRESETS}), len(DEFAULT_PRESETS))
        for preset in DEFAULT_PRESETS:
            self.assertTrue(set(preset.tweak_ids) <= catalog_ids, preset.id)


class TestStatusReport(unittest.TestCase):
    def test_report_lists_tweaks_grouped_by_category_with_totals(self):
        tweaks = [make_tweak("a"), make_tweak("b", category=TweakCategory.FPS)]
        statuses = {"a": TweakStatus.ACTIVE, "b": TweakStatus.INACTIVE}
        info = SystemInfo(is_admin=True, windows_label="Windows 11 (build 26100)", windows_build=26100)

        report = build_status_report(tweaks, statuses, info, datetime(2026, 1, 2, 3, 4))

        self.assertIn("02/01/2026 03:04", report)
        self.assertIn("== Latência & Vídeo ==", report)
        self.assertIn("[x] Tweak a - Ativo", report)
        self.assertIn("[ ] Tweak b - Inativo", report)
        self.assertIn("1 de 2 otimizações ativas", report)


if __name__ == "__main__":
    unittest.main()
