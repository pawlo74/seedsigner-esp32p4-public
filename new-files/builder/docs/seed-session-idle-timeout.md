# Seed-session idle timeout on ESP32

The advanced setting **Seed session timeout** offers 5, 15, 30 and 60 minutes
and **No limit**; the default is 30 minutes. **No limit disables automatic idle
restart**, so a loaded seed remains accessible until manually discarded or the
device is restarted or powered off. It is independent of the two-minute screensaver.
The selected value persists across restarts only when SeedSigner's existing
Persistent Settings feature is enabled and its microSD settings file is available.

Once a secret-bearing workflow is entered, a native ESP32 watchdog is armed
until restart (unless **No limit** disables expiry). This includes seed entry, dice entry, creating/loading a seed and
opening the scanner: a scan may capture a SeedQR before Python can identify it.
The timer therefore remains armed after a cancelled scan or seed discard; this
conservative policy also covers references retained outside the seed list.

Actual LVGL input events restart the idle interval. The watchdog uses a monotonic
ESP timer and runs independently of Python and the screensaver. Camera preview
and animated QR display pause the timeout; after leaving either flow, a full new
idle interval begins. Static QR screens do not pause it. A paused flow left open
or stuck can delay the restart indefinitely; this is an explicit usability/security
trade-off. On expiry the device automatically restarts, ending the session and
discarding unsaved work. Keep a verified offline seed backup before using it.

This is **not a secure-zeroization guarantee**: MicroPython seed material includes
immutable strings/bytes and can have additional Python, native or hardware copies.
Restarting drops live session references, but neither a restart nor garbage
collection proves all physical memory locations were overwritten. It does not
erase persistent settings, the internal filesystem, a microSD card or external
seed backups. See `docs/knowledge/micropython-secret-memory-scrubbing.md`.

The implementation is currently ESP32-only; on other platforms the advanced
entry routes to the existing unsupported-setting screen. Before relying on this
feature, test the actual device with a **public test mnemonic**, including each
timeout, touches before expiry, screensaver wake, camera/animated-QR pause and
exit, cancellation and restart. Verify that seed data no longer appears in the
application after restart. These functional checks cannot prove physical wiping.