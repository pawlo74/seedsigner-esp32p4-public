# SeedSigner ESP32-P4 firmware - personal snapshot

Public snapshot of a custom firmware for the Waveshare ESP32-P4 WIFI6 Touch LCD
4.3, chip revisions **v0.0-v1.99** (`PRE_REV3`). The device used to test this
image reported revision v1.3. Do not flash this image to revision v3.x.

This is a personal, modified build, not an official SeedSigner release. The
owner reported that the flashed device works. That report does **not** establish
that every timeout, camera, signing or security scenario was independently
tested. The source and binary require review before use with real funds.

## What is included

- `firmware/`: the flashed MicroPython binary, bootloader, partition table and
  `flash_args`, as produced by the build. The files do not include `vfs.bin`.
- `builder.patch`, `seedsigner.patch`, `lvgl-screens.patch`: tracked changes
  against the respective upstream commits recorded in `builder-commit.txt` and
  `submodules.txt`.
- `new-files/`: added source, documentation and tests, which are untracked in
  the original repositories and therefore **not included in the patches**.
- `seedsigner_frozen_build.py`: build provenance. `SHA256SUMS` covers all files
  in this snapshot except itself.

Included changes comprise portrait orientation, UI changes, address QR parsing,
address verification coordination, and an ESP32 idle session timeout with
5/15/30 minutes, 1 hour and "No limit" (default: 30 minutes).

## Security and data limitations

The timeout restarts the device after inactivity. Restarting does **not** prove
that every physical copy of a seed has been overwritten. "No limit" disables
this automatic restart. Camera scanning and animated QR display pause the
timeout; leaving either open can delay it indefinitely. See
`new-files/builder/docs/seed-session-idle-timeout.md`.

No seed backup, microSD content, internal filesystem image or `vfs.bin` is
included. Do not upload seed phrases, passphrases, private keys, device flash
dumps, or other wallet secrets to GitHub, even in a private repository.

## Restore the code on the pinned base

Work only in a new clean checkout; these commands do not update the live working
tree. First set SNAPSHOT to the absolute path of this repository checkout.
Patches are tied to the pinned commits and may require adaptation after upstream
changes. Review all patches before applying them.

```bash
SNAPSHOT="$(pwd)"  # run from this repository's root
git clone https://github.com/kdmukai/seedsigner-micropython-builder.git builder
cd builder
git checkout a9f865c68b20457692ab4547e3394785114b507f
git submodule update --init --recursive deps/micropython/upstream deps/seedsigner-lvgl-screens deps/cUR deps/esp-secp256k1 ports/esp32/board_common
git submodule update --init deps/seedsigner deps/embit
git apply --check "$SNAPSHOT/builder.patch"
git -C deps/seedsigner apply --check "$SNAPSHOT/seedsigner.patch"
git -C deps/seedsigner-lvgl-screens apply --check "$SNAPSHOT/lvgl-screens.patch"
git apply "$SNAPSHOT/builder.patch"
git -C deps/seedsigner apply "$SNAPSHOT/seedsigner.patch"
git -C deps/seedsigner-lvgl-screens apply "$SNAPSHOT/lvgl-screens.patch"
cp -a "$SNAPSHOT/new-files/builder/." .
cp -a "$SNAPSHOT/new-files/seedsigner/." deps/seedsigner/
SS_APP_DIR="$PWD/deps/seedsigner" SS_EMBIT_DIR="$PWD/deps/embit" make docker-build-all BOARD=WAVESHARE_ESP32_P4_WIFI6_TOUCH_LCD_43 BOARD_VARIANT=PRE_REV3
```

This uses the builder's Docker image and build pipeline. Generated binary output
is not guaranteed bit-for-bit reproducible because provenance includes build time.

## Flash the saved image

`firmware/flash_args` uses relative paths. Run the following from the saved
`firmware/` directory, after identifying the actual serial port and chip revision:

```bash
python -m esptool --chip esp32p4 --port <PORT> write-flash @flash_args
```

This writes bootloader, partition table and application only. It does not write a
launcher/filesystem; a fresh device without an existing launcher may boot to the
MicroPython REPL. Verify the image and preserve your own offline backups first.

## Backup summary

The firmware and its local source modifications were copied to this **public**
repository for `pawlo74`; original local backups remain unchanged. This snapshot
does not contain a device filesystem, microSD backup, or wallet secrets. The
owner reported the firmware works on the board; comprehensive security testing
has not been established.