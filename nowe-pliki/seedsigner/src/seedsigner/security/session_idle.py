"""ESP32 secret-session idle watchdog integration.

This is separate from the screensaver. The firmware watchdog runs independently
of the Python VM and stays armed after any seed material enters the session,
until hardware restart. It ends access to in-memory state but does NOT promise
physical zeroization of every immutable Python/native copy.
"""
from seedsigner.compat import IS_MICROPYTHON


def _native():
    # A missing native binding is an error, not a silently disabled safeguard.
    import _seedsigner_lvgl_screens
    return _seedsigner_lvgl_screens


def set_timeout(seconds):
    if IS_MICROPYTHON:
        _native().session_idle_set_timeout(seconds)


def arm():
    if IS_MICROPYTHON:
        _native().session_idle_arm()


def set_paused(paused):
    if IS_MICROPYTHON:
        _native().session_idle_set_paused(paused)