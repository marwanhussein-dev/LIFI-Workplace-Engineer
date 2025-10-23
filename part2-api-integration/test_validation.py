#!/usr/bin/env python3
"""
test_validation.py

Purpose:
  Exercise transform_employee() with handcrafted inputs to verify
  validation and error-handling behaviors that are hard to trigger
  with the RandomUser API (which usually returns valid data).

Covers:
  - bad_uuid                  → err='invalid uuid format: NOT-A-UUID'
  - bad_email                 → err="invalid email (must contain '@'): no-at-symbol"
  - missing_required          → err mentioning the missing key (e.g., 'last')
  - bad_date                  → err='invalid registered.date: oops'
  - bad_phone_no_enforce      → out exists, _phone_quality_ok is False
  - bad_phone_enforced        → err='invalid phone format (data quality): 123'
"""

from datetime import datetime, timezone
from copy import deepcopy
import sys

# Import the function under test from your main script
# Assumes test_validation.py is in the same directory as sync_hr_to_assets.py
from sync_hr_to_assets import transform_employee

# ---------- Helpers ----------

def make_valid_record() -> dict:
    """Return a fully valid RandomUser-like record."""
    return {
        "login": {"uuid": "123e4567-e89b-12d3-a456-426614174000"},  # valid v1 UUID format
        "email": "jane.doe@example.com",
        "phone": "+1 (555) 123-4567",
        "name": {"first": "Jane", "last": "Doe"},
        "location": {
            "city": "Austin",
            "state": "Texas",
            "country": "United States"
        },
        # RandomUser uses ISO timestamps; our transform extracts date-only
        "registered": {"date": "2020-02-20T15:04:05.000Z"},
    }

def run_case(label: str, data: dict, enforce_phone: bool, expect_out: bool, expect_err_contains: str | None, expect_phone_ok: bool | None):
    """
    Execute transform_employee with given data and expectations.
    Prints a concise line like:
        bad_uuid → out=False  err='invalid uuid format: NOT-A-UUID'
    Returns True if the case meets expectations, else False.
    """
    run_dt = datetime.now(timezone.utc)
    out, err = transform_employee(data, run_dt, enforce_phone=enforce_phone)
    print(f"{label:>20} → out={bool(out)}  err={repr(err)}")

    ok = True

    # Check out presence/absence
    if bool(out) != expect_out:
        ok = False

    # Check error text when expected
    if expect_err_contains is not None:
        if not err or expect_err_contains not in str(err):
            ok = False

    # Check phone quality flag when applicable
    if expect_phone_ok is not None:
        if not out or out.get("_phone_quality_ok") is not expect_phone_ok:
            ok = False

    return ok

# ---------- Main runner ----------

def main() -> int:
    base = make_valid_record()
    passed = 0
    total = 0

    # 1) bad_uuid
    total += 1
    rec = deepcopy(base)
    rec["login"]["uuid"] = "NOT-A-UUID"
    if run_case(
        label="bad_uuid",
        data=rec,
        enforce_phone=False,
        expect_out=False,
        expect_err_contains="invalid uuid format: NOT-A-UUID",
        expect_phone_ok=None,
    ):
        passed += 1

    # 2) bad_email
    total += 1
    rec = deepcopy(base)
    rec["email"] = "no-at-symbol"
    if run_case(
        label="bad_email",
        data=rec,
        enforce_phone=False,
        expect_out=False,
        expect_err_contains="invalid email (must contain '@'): no-at-symbol",
        expect_phone_ok=None,
    ):
        passed += 1

    # 3) missing_required (e.g., name.last)
    total += 1
    rec = deepcopy(base)
    del rec["name"]["last"]
    # We expect the message to mention the missing key; your function formats like: "missing required field: 'last'"
    if run_case(
        label="missing_required",
        data=rec,
        enforce_phone=False,
        expect_out=False,
        expect_err_contains="missing required field",
        expect_phone_ok=None,
    ):
        passed += 1

    # 4) bad_date (registered.date malformed)
    total += 1
    rec = deepcopy(base)
    rec["registered"]["date"] = "oops"
    if run_case(
        label="bad_date",
        data=rec,
        enforce_phone=False,
        expect_out=False,
        expect_err_contains="invalid registered.date: oops",
        expect_phone_ok=None,
    ):
        passed += 1

    # 5) bad_phone_no_enforce (invalid phone, but do not enforce)
    total += 1
    rec = deepcopy(base)
    rec["phone"] = "123"  # fails the PHONE_RE
    if run_case(
        label="bad_phone_no_enforce",
        data=rec,
        enforce_phone=False,
        expect_out=True,        # record should still be returned
        expect_err_contains=None,
        expect_phone_ok=False,  # but the metadata flag should be False
    ):
        passed += 1

    # 6) bad_phone_enforced (invalid phone + enforce_phone=True)
    total += 1
    rec = deepcopy(base)
    rec["phone"] = "123"
    if run_case(
        label="bad_phone_enforced",
        data=rec,
        enforce_phone=True,
        expect_out=False,
        expect_err_contains="invalid phone format (data quality): 123",
        expect_phone_ok=None,
    ):
        passed += 1

    print("\nSummary:")
    print(f"  Passed {passed} / {total} cases")

    # Exit non-zero if any test failed (useful for CI or quick checks)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())