#!/usr/bin/env python3
"""
launch_apps.py
--------------
Auto-launches a list of macOS applications using the `open` command.

Usage:
    python3 launch_apps.py

Edit the APPS list below to specify which apps you want to launch.
Use the exact app name as it appears in your /Applications folder.
"""

import subprocess
import sys

# ──────────────────────────────────────────────
#  CONFIGURE YOUR APPS HERE
#  Add or remove app names as needed.
#  Use the name exactly as it appears in /Applications (without .app)
# ──────────────────────────────────────────────
APPS = [
    "Microsoft Outlook",
    "Opera",
    "Microsoft OneNote",
    "Microsoft Teams",
    "TickTick",
    "Mail+ for Gmail",
    "Claude",



]

# ──────────────────────────────────────────────
#  OPTIONAL SETTINGS
# ──────────────────────────────────────────────

# Set to True to print a status message for each app
VERBOSE = True


def launch_app(app_name: str) -> bool:
    """
    Launch a macOS application by name using the `open` command.
    Returns True if the launch command succeeded, False otherwise.
    """
    try:
        result = subprocess.run(
            ["open", "-a", app_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            if VERBOSE:
                print(f"  ✓  Launched: {app_name}")
            return True
        else:
            error = result.stderr.strip()
            print(f"  ✗  Failed to launch '{app_name}': {error}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"  ✗  Error launching '{app_name}': {e}", file=sys.stderr)
        return False


def main():
    if not APPS:
        print("No apps listed in APPS. Edit the script to add your apps.")
        sys.exit(0)

    print(f"Launching {len(APPS)} app(s)...\n")

    succeeded = 0
    failed = 0

    for app in APPS:
        if launch_app(app):
            succeeded += 1
        else:
            failed += 1

    print(f"\nDone — {succeeded} launched, {failed} failed.")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
