"""Bitcoin address QR decoding on CPython and MicroPython.

These tests exercise text and camera-style byte payloads without a camera.  They
also run as a script on MicroPython, whose regex engine has a smaller compiler.
"""
from seedsigner.models.decode_qr import DecodeQR, DecodeQRStatus
from seedsigner.models.settings import SettingsConstants


# BIP-86 public test vector (m/86'/0'/0'/0/0). Never use for real funds.
TAPROOT = "bc1p5cyxnuxmeuwuvkwfem96lqzszd02n6xdcjrs20cac6yqjjwudpxqkedrcr"


def test_address_qr_formats():
    # The decoder classifies address-shaped strings; these fixtures do not
    # imply checksum validation or represent wallets to use with real funds.
    cases = (
        (TAPROOT, SettingsConstants.TAPROOT, SettingsConstants.MAINNET),
        ("bc1q" + "a" * 38, SettingsConstants.NATIVE_SEGWIT, SettingsConstants.MAINNET),
        ("tb1q" + "a" * 38, SettingsConstants.NATIVE_SEGWIT, SettingsConstants.TESTNET),
        ("bcrt1q" + "a" * 38, SettingsConstants.NATIVE_SEGWIT, SettingsConstants.REGTEST),
        ("tb1p" + "a" * 58, SettingsConstants.TAPROOT, SettingsConstants.TESTNET),
        ("bcrt1p" + "a" * 58, SettingsConstants.TAPROOT, SettingsConstants.REGTEST),
        ("1" + "a" * 25, SettingsConstants.LEGACY_P2PKH, SettingsConstants.MAINNET),
        ("m" + "a" * 25, SettingsConstants.LEGACY_P2PKH, SettingsConstants.TESTNET),
        ("3" + "a" * 25, SettingsConstants.NESTED_SEGWIT, SettingsConstants.MAINNET),
        ("2" + "a" * 25, SettingsConstants.NESTED_SEGWIT, SettingsConstants.TESTNET),
    )
    for address, script_type, network in cases:
        for payload in (address, address.encode(), "bitcoin:" + address + "?amount=0.1"):
            decoder = DecodeQR()
            assert decoder.add_data(payload) == DecodeQRStatus.COMPLETE, address
            assert decoder.is_address, address
            assert decoder.get_address() == address, address
            assert decoder.get_address_type() == (script_type, network), address

    decoder = DecodeQR()
    assert decoder.add_data(TAPROOT.upper().encode()) == DecodeQRStatus.COMPLETE
    assert decoder.get_address() == TAPROOT


def test_address_camera_payload_completes_scan():
    from seedsigner.hardware.scan_consumer import run_scan

    class Scanner:
        FRAME_NEW = 1

        def __init__(self):
            self.payload = TAPROOT.encode()
            self.completed = False
            self.reports = []

        def poll_new(self):
            payload = self.payload
            self.payload = None
            return payload

        def report(self, frame_status, percent):
            self.reports.append((frame_status, percent))

        def report_complete(self):
            self.completed = True

    scanner = Scanner()
    decoder = DecodeQR()
    result = run_scan(decoder, scanner=scanner, poll_interval_ms=0, completion_hold_ms=0)
    assert result.complete and scanner.completed
    assert scanner.reports == [(scanner.FRAME_NEW, 100)]
    assert decoder.get_address() == TAPROOT


if __name__ == "__main__":
    test_address_qr_formats()
    test_address_camera_payload_completes_scan()
    print("Bitcoin address QR tests passed")