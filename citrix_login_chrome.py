#!/usr/bin/env python3
"""
citrix_login_chrome.py
----------------------
Auto-logs in to Citrix Workspace using Chrome on macOS.
Handles the Microsoft SSO (Azure AD) login flow that Citrix redirects to.
URL: https://loblawremote.cloud.com/Citrix/StoreWeb/#/home

Requirements:
    pip3 install selenium webdriver-manager keyring --break-system-packages

Usage:
    python3 citrix_login_chrome.py

Credentials can be supplied via environment variables to skip the prompts:
    export CITRIX_USERNAME="robert.miller@loblaw.ca"
    export CITRIX_PASSWORD="yourpassword"
"""

import os
import time
import getpass
import keyring
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

CITRIX_URL  = "https://loblawremote.cloud.com/Citrix/StoreWeb/#/home"
CITRIX_HOST = "loblawremote.cloud.com"

# Microsoft SSO selectors (stable across Azure AD tenants)
MS_EMAIL_INPUT  = "input[name='loginfmt']"
MS_NEXT_BTN     = "input[id='idSIButton9']"
MS_PASSWORD_INPUT = "input[name='passwd']"
MS_SIGNIN_BTN   = "input[id='idSIButton9']"


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

DEFAULT_USERNAME = "robert.miller@loblaw.ca"
KEYCHAIN_SERVICE = "CitrixWorkspace"

def get_credentials() -> tuple[str, str]:
    """
    Retrieve credentials automatically:
      1. Env vars (CITRIX_USERNAME / CITRIX_PASSWORD) — highest priority
      2. macOS Keychain — looked up by username
      3. Interactive prompt — saves to Keychain so next run is automatic
    """
    username = os.environ.get("CITRIX_USERNAME", DEFAULT_USERNAME)

    # Try env var first, then Keychain
    password = os.environ.get("CITRIX_PASSWORD") or keyring.get_password(KEYCHAIN_SERVICE, username)

    if not password:
        print(f"  No saved password found for {username}.")
        password = getpass.getpass("  Enter password (will be saved to macOS Keychain): ")
        keyring.set_password(KEYCHAIN_SERVICE, username, password)
        print("  ✓  Password saved to Keychain — future runs will be fully automatic.")

    return username, password


def build_chrome_driver() -> webdriver.Chrome:
    """Launch Chrome — webdriver-manager auto-matches the ChromeDriver version."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # Keep the browser open after the script finishes
    options.add_experimental_option("detach", True)

    # Disable SSL verification for Loblaw's corporate proxy
    os.environ["WDM_SSL_VERIFY"] = "0"

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1280, 900)
    print(f"  ✓  Chrome {driver.capabilities.get('browserVersion', '')} ready.")
    return driver


# ──────────────────────────────────────────────
#  LOGIN FLOW
# ──────────────────────────────────────────────

def login(driver: webdriver.Chrome, username: str, password: str, timeout: int = 20) -> None:
    wait = WebDriverWait(driver, timeout)

    print("  →  Navigating to Citrix Workspace …")
    driver.get(CITRIX_URL)

    # Wait for any redirects to settle, then check where we landed
    time.sleep(3)

    # If we're still on Citrix (not redirected to Microsoft), we're already logged in
    if "microsoftonline.com" not in driver.current_url:
        print("  ✓  Already authenticated — Citrix home loaded.")
        return

    # ── Step 1: Microsoft SSO — enter email ──────────────────────────────────
    print("  →  Microsoft SSO — entering email …")
    email_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, MS_EMAIL_INPUT)))
    email_field.clear()
    email_field.send_keys(username)

    next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, MS_NEXT_BTN)))
    next_btn.click()

    # ── Step 2: Microsoft SSO — enter password ───────────────────────────────
    print("  →  Microsoft SSO — entering password …")
    password_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, MS_PASSWORD_INPUT)))
    password_field.clear()
    password_field.send_keys(password)

    signin_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, MS_SIGNIN_BTN)))
    signin_btn.click()

    # ── Step 3: "Stay signed in?" prompt (optional) ──────────────────────────
    try:
        stay_signed_in = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input#idSIButton9"))
        )
        # Click "Yes" to stay signed in (avoids prompt next time)
        stay_signed_in.click()
        print("  →  Dismissed 'Stay signed in?' prompt.")
    except Exception:
        pass  # Prompt didn't appear — that's fine

    # ── Step 4: Wait for Citrix home ─────────────────────────────────────────
    try:
        wait.until(EC.url_contains(CITRIX_HOST))
        print("  ✓  Login successful — Citrix home loaded.")
    except Exception:
        print("  !  Could not confirm login automatically.")
        print("     Check the browser — an MFA prompt may be waiting.")
        time.sleep(10)


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────

def main() -> None:
    print("\nCitrix Workspace Auto-Login (Chrome + Microsoft SSO)\n")

    username, password = get_credentials()
    driver = build_chrome_driver()

    try:
        login(driver, username, password)
        print("\n  ✓  Done — Chrome will stay open. Close it manually when finished.")
    except Exception as exc:
        print(f"\n  ✗  Error: {exc}")
        driver.quit()
        raise


if __name__ == "__main__":
    main()
