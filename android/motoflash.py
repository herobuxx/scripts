#!/usr/bin/env python3
"""
Motorola Firmware Flasher
Parses flashfile.xml and flashes firmware via fastboot with MD5 verification.
"""

import hashlib
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ANSI colors
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

FASTBOOT = "fastboot"


def log(msg, color=RESET):
    print(f"{color}{msg}{RESET}")


def md5sum(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_file(fw_dir: Path, filename: str, expected_md5: str) -> Path:
    filepath = fw_dir / filename
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    log(f"  Verifying MD5 for {filename} ...", CYAN)
    actual = md5sum(filepath)
    if actual.lower() != expected_md5.lower():
        raise ValueError(
            f"MD5 mismatch for {filename}!\n"
            f"  Expected : {expected_md5}\n"
            f"  Got      : {actual}"
        )
    log(f"  {GREEN}✓ MD5 OK{RESET}  ({actual})")
    return filepath


def run_fastboot(*args, check=True) -> subprocess.CompletedProcess:
    cmd = [FASTBOOT, *args]
    log(f"  $ {' '.join(cmd)}", YELLOW)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    if check and result.returncode != 0:
        raise RuntimeError(f"fastboot command failed (exit {result.returncode})")
    return result


def check_fastboot_device():
    log("\nChecking for fastboot device ...", CYAN)
    result = subprocess.run([FASTBOOT, "devices"], capture_output=True, text=True)
    output = result.stdout.strip()
    if not output:
        raise RuntimeError(
            "No device found in fastboot mode.\n"
            "Boot your device into bootloader/fastboot mode first."
        )
    log(f"  {GREEN}Device detected:{RESET} {output}")


def parse_flashfile(flashfile: Path):
    tree = ET.parse(flashfile)
    root = tree.getroot()

    header = root.find("header")
    model   = header.find("phone_model").get("model", "unknown")
    sw_ver  = header.find("software_version").get("version", "unknown")

    steps = []
    steps_el = root.find("steps")
    for step in steps_el.findall("step"):
        steps.append({
            "operation" : step.get("operation"),
            "var"       : step.get("var"),
            "partition" : step.get("partition"),
            "filename"  : step.get("filename"),
            "md5"       : step.get("MD5"),
        })

    return model, sw_ver, steps


def pre_verify_all(fw_dir: Path, steps: list):
    """Verify MD5 of every flash image before flashing anything."""
    log("\n" + "="*60, BOLD)
    log("  PRE-FLASH VERIFICATION", BOLD)
    log("="*60, BOLD)
    for step in steps:
        if step["operation"] == "flash" and step["filename"] and step["md5"]:
            verify_file(fw_dir, step["filename"], step["md5"])
    log(f"\n{GREEN}{BOLD}All files verified successfully!{RESET}\n")


def execute_steps(fw_dir: Path, steps: list):
    total  = len(steps)
    passed = 0

    for i, step in enumerate(steps, 1):
        op        = step["operation"]
        var       = step.get("var")
        partition = step.get("partition")
        filename  = step.get("filename")
        md5       = step.get("md5")

        log(f"\n[{i}/{total}] operation={op}" +
            (f"  partition={partition}" if partition else "") +
            (f"  var={var}" if var else ""), BOLD)

        try:
            if op == "getvar":
                run_fastboot("getvar", var)

            elif op == "oem":
                run_fastboot("oem", var)

            elif op == "flash":
                filepath = verify_file(fw_dir, filename, md5)
                log(f"  Flashing {filename} -> {partition} ...", CYAN)
                run_fastboot("flash", partition, str(filepath))
                log(f"  {GREEN}✓ Flashed{RESET}")

            elif op == "erase":
                log(f"  Erasing partition: {partition} ...", CYAN)
                run_fastboot("erase", partition)
                log(f"  {GREEN}✓ Erased{RESET}")

            else:
                log(f"  {YELLOW}Unknown operation '{op}', skipping.{RESET}")

            passed += 1

        except Exception as e:
            log(f"\n{RED}{BOLD}ERROR at step {i}: {e}{RESET}")
            raise

    return passed


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Flash Motorola firmware from flashfile.xml via fastboot."
    )
    parser.add_argument(
        "fw_dir",
        nargs="?",
        default=".",
        help="Directory containing flashfile.xml and firmware images (default: current dir)"
    )
    parser.add_argument(
        "--flashfile",
        default="flashfile.xml",
        help="flashfile.xml filename (default: flashfile.xml)"
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip pre-flash MD5 verification (not recommended)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and verify only, do NOT run any fastboot commands"
    )
    args = parser.parse_args()

    fw_dir    = Path(args.fw_dir).resolve()
    flashfile = fw_dir / args.flashfile

    log(f"\n{'='*60}", BOLD)
    log("  Motorola Firmware Flasher", BOLD)
    log(f"{'='*60}", BOLD)
    log(f"  Firmware dir : {fw_dir}")
    log(f"  Flash file   : {flashfile}")

    if not flashfile.exists():
        log(f"\n{RED}flashfile.xml not found at: {flashfile}{RESET}")
        sys.exit(1)

    model, sw_ver, steps = parse_flashfile(flashfile)
    log(f"\n  Model   : {model}")
    log(f"  SW Ver  : {sw_ver}")
    log(f"  Steps   : {len(steps)}")

    if not args.skip_verify:
        pre_verify_all(fw_dir, steps)

    if args.dry_run:
        log(f"\n{YELLOW}Dry-run mode — no fastboot commands executed.{RESET}")
        sys.exit(0)

    check_fastboot_device()

    log(f"\n{BOLD}{'='*60}{RESET}")
    log(f"  {RED}{BOLD}WARNING: This will flash your device and erase userdata!{RESET}")
    log(f"{BOLD}{'='*60}{RESET}")
    confirm = input("  Type YES to continue: ").strip()
    if confirm != "YES":
        log("Aborted.", YELLOW)
        sys.exit(0)

    log(f"\n{BOLD}Starting flash sequence...{RESET}")
    try:
        passed = execute_steps(fw_dir, steps)
    except Exception:
        log(f"\n{RED}{BOLD}Flashing FAILED. Your device may be in an inconsistent state.{RESET}")
        log("Reboot to bootloader and retry, or use rescue mode if available.", YELLOW)
        sys.exit(1)

    log(f"\n{'='*60}", BOLD)
    log(f"  {GREEN}{BOLD}Flashing complete! ({passed}/{len(steps)} steps){RESET}", BOLD)
    log(f"{'='*60}", BOLD)
    log("\nYou may now reboot your device:")
    log("  fastboot reboot", CYAN)


if __name__ == "__main__":
    main()
