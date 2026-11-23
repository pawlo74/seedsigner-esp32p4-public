"""Tests for seed idle timeout settings, arming and protected operations."""
from unittest.mock import patch
import sys

from seedsigner.gui import lvgl_screen_runner
from seedsigner.models.seed_storage import SeedStorage
from seedsigner.models.settings import Settings, SettingsConstants, SettingsDefinition
from seedsigner.security import session_idle


def test_timeout_setting_options():
    entry = SettingsDefinition.get_settings_entry(SettingsConstants.SETTING__SEED_IDLE_TIMEOUT)
    assert entry.visibility == SettingsConstants.VISIBILITY__ADVANCED
    assert entry.selection_options == [(300, "5 minutes"), (900, "15 minutes"),
                                       (1800, "30 minutes"), (3600, "1 hour"),
                                       (0, "No limit")]
    assert entry.default_value == 1800
    assert SettingsDefinition.get_defaults()[entry.attr_name] == 1800


def test_timeout_invalid_falls_back_and_valid_applies():
    settings = object.__new__(Settings)
    settings._data = SettingsDefinition.get_defaults()
    calls = []
    with patch.object(settings, "save"), patch("seedsigner.models.settings.IS_MICROPYTHON", True), \
         patch.object(session_idle, "set_timeout", side_effect=calls.append):
        for value in (300, 900, 1800, 3600, 0):
            settings.set_value(SettingsConstants.SETTING__SEED_IDLE_TIMEOUT, value)
            assert settings.get_value(SettingsConstants.SETTING__SEED_IDLE_TIMEOUT) == value
        for value in (-1, 999, "300", True, None):
            settings.set_value(SettingsConstants.SETTING__SEED_IDLE_TIMEOUT, value)
            assert settings.get_value(SettingsConstants.SETTING__SEED_IDLE_TIMEOUT) == 1800
    assert calls == [300, 900, 1800, 3600, 0] + [1800] * 5


def test_seed_storage_arms_before_entry_and_pending_seed():
    storage = SeedStorage()
    with patch("seedsigner.models.seed_storage.arm_session_idle") as arm:
        storage.init_pending_mnemonic(12)
        storage.set_pending_seed(object())
        assert arm.call_count == 2


class _Native:
    def __init__(self):
        self.calls = []

    def session_idle_arm(self):
        self.calls.append(("arm",))

    def session_idle_set_timeout(self, value):
        self.calls.append(("timeout", value))

    def session_idle_set_paused(self, value):
        self.calls.append(("pause", value))


def test_native_watchdog_hooks():
    native = _Native()
    with patch.object(session_idle, "IS_MICROPYTHON", True), patch.object(session_idle, "_native", return_value=native):
        session_idle.set_timeout(900)
        session_idle.arm()
        session_idle.set_paused(True)
        session_idle.set_paused(False)
    assert native.calls == [("timeout", 900), ("arm",), ("pause", True), ("pause", False)]


def test_qr_pause_is_released_even_if_render_raises():
    class Encoder:
        def next_part(self): return "data"
        def seq_len(self): return 2

    class LV:
        def set_screensaver_timeout(self, value): pass
        def clear_result_queue(self): pass
        def qr_display_screen(self, cfg): raise RuntimeError("test failure")

    calls = []
    settings = object.__new__(Settings)
    settings._data = SettingsDefinition.get_defaults()
    with patch.object(lvgl_screen_runner, "ensure_lvgl_runtime"), \
         patch.object(lvgl_screen_runner, "_lv", LV()), \
         patch.object(Settings, "get_instance", return_value=settings), \
         patch.object(session_idle, "set_paused", side_effect=calls.append):
        try:
            lvgl_screen_runner.run_qr_display_screen(Encoder())
            raise AssertionError("expected the render failure")
        except RuntimeError:
            pass
    assert calls == [True, False]


def test_static_qr_does_not_pause_session_timer():
    class Encoder:
        def next_part(self): return "data"
        def seq_len(self): return 1

    class LV:
        def set_screensaver_timeout(self, value): pass
        def clear_result_queue(self): pass
        def qr_display_screen(self, cfg): pass
        def poll_for_result(self): return ("button_selected", 0, "done")

    settings = object.__new__(Settings)
    settings._data = SettingsDefinition.get_defaults()
    with patch.object(lvgl_screen_runner, "ensure_lvgl_runtime"), \
         patch.object(lvgl_screen_runner, "_lv", LV()), \
         patch.object(Settings, "get_instance", return_value=settings), \
         patch.object(session_idle, "set_paused") as pause:
        assert lvgl_screen_runner.run_qr_display_screen(Encoder()) == 0
        pause.assert_not_called()


def test_camera_failure_unpauses_session_timer():
    class Camera:
        def start(self, **kwargs): raise OSError("camera unavailable")

    class LV:
        def set_screensaver_timeout(self, value): pass

    calls = []
    with patch.object(lvgl_screen_runner, "ensure_lvgl_runtime"), \
         patch.object(lvgl_screen_runner, "_lv", LV()), \
         patch.dict(sys.modules, {"camera_scanner": Camera()}), \
         patch.object(session_idle, "arm") as arm, \
         patch.object(session_idle, "set_paused", side_effect=calls.append):
        assert lvgl_screen_runner.run_camera_scan(None) is None
        arm.assert_called_once()
    assert calls == [True, False]


if __name__ == "__main__":
    test_timeout_setting_options()
    test_timeout_invalid_falls_back_and_valid_applies()
    test_seed_storage_arms_before_entry_and_pending_seed()
    test_native_watchdog_hooks()
    test_qr_pause_is_released_even_if_render_raises()
    test_static_qr_does_not_pause_session_timer()
    test_camera_failure_unpauses_session_timer()
    print("Seed session timeout tests passed")