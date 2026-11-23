"""Regression tests for address verification's worker and screen coordination."""
import threading
from unittest.mock import patch

from seedsigner.gui import lvgl_screen_runner
from seedsigner.helpers import embit_utils
from seedsigner.models.threads import ThreadsafeCounter
from seedsigner.views.seed_views import SeedAddressVerificationView


class _FakeLV:
    def __init__(self, events):
        self.events = list(events)
        self.timeouts = []
        self.progress = []

    def set_screensaver_timeout(self, value):
        self.timeouts.append(value)

    def clear_result_queue(self):
        pass

    def seed_address_verification_screen(self, cfg):
        self.cfg = cfg

    def poll_for_result(self):
        return self.events.pop(0)

    def seed_address_verification_set_progress(self, text):
        self.progress.append(text)


def _run_screen(counter, verified, lv):
    with patch.object(lvgl_screen_runner, "_lv", lv), \
         patch.object(lvgl_screen_runner, "ensure_lvgl_runtime"), \
         patch.object(lvgl_screen_runner, "_sleep_ms"):
        return lvgl_screen_runner.run_seed_address_verification_screen(
            address="test-address", type_network="test", network="mainnet",
            title="Verify Address", skip_label="Skip 10", cancel_label="Cancel",
            threadsafe_counter=counter, verified_index=verified)


def test_skip_then_cancel_while_worker_is_calculating():
    entered, release = threading.Event(), threading.Event()
    counter = ThreadsafeCounter()
    verified = ThreadsafeCounter(initial_value=None)
    branch = ThreadsafeCounter(initial_value=None)
    worker = SeedAddressVerificationView.BruteForceAddressVerificationThread(
        address="no-match", seed=None, descriptor=object(), script_type="test",
        embit_network="main", derivation_path="m", threadsafe_counter=counter,
        verified_index=verified, verified_index_is_change=branch)

    def calculate(**kwargs):
        entered.set()
        assert release.wait(3), "test worker was not released"
        return "not-the-target"

    lv = _FakeLV([("button_selected", 0, "Skip 10"),
                  None, ("button_selected", 1, "Cancel")])
    with patch.object(embit_utils, "get_multisig_address", side_effect=calculate):
        worker.start()
        try:
            assert entered.wait(3), "test worker did not start"
            assert _run_screen(counter, verified, lv) is False
            assert counter.cur_count == 10
            assert lv.progress == ["Checking address 10"]
            worker.stop()
        finally:
            release.set()
            worker.join(3)
        assert not worker.is_alive()
        assert verified.cur_count is None


def test_match_branch_is_available_when_index_is_published():
    for is_change in (False, True):
        branch = ThreadsafeCounter(initial_value=None)

        class ObservedIndex(ThreadsafeCounter):
            def set_value(self, value):
                assert branch.cur_count == int(is_change)
                super().set_value(value)

        verified = ObservedIndex(initial_value=None)
        worker = SeedAddressVerificationView.BruteForceAddressVerificationThread(
            address="match", seed=None, descriptor=object(), script_type="test",
            embit_network="main", derivation_path="m", threadsafe_counter=ThreadsafeCounter(),
            verified_index=verified, verified_index_is_change=branch)
        worker.keep_running = True
        with patch.object(embit_utils, "get_multisig_address",
                          side_effect=lambda **kw: "match" if kw["is_change"] == is_change else "other"):
            worker.run()
        assert verified.cur_count == 0
        assert branch.cur_count == int(is_change)


if __name__ == "__main__":
    test_skip_then_cancel_while_worker_is_calculating()
    test_match_branch_is_available_when_index_is_published()
    print("Address verification synchronization tests passed")