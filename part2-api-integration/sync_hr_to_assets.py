#!/usr/bin/env python3  # [Meta] Run with Python 3 when executed directly on Unix-like systems.

"""
sync_hr_to_assets_super_commented.py
===============================================================================
ETL-style script (Extract → Transform → Load) for your assignment, with
deep beginner-friendly comments and explicit requirement tags.

NUMBERED REQUIREMENTS (used as tags like [REQ 2.2 — Generate asset_id]):
  REQ 1  — Fetch employee data from HR API (Extract)
  REQ 2  — Transform data according to mapping
    REQ 2.1 — Handle nested objects properly (name, location)
    REQ 2.2 — Generate asset_id in the specified format
    REQ 2.3 — Extract only the date portion from timestamps
    REQ 2.4 — Create the sync_metadata section
    REQ 2.5 — Set default values for fields not in source data
  REQ 3  — Validate the data
    REQ 3.1 — Ensure all required fields are present
    REQ 3.2 — Check that email addresses contain "@"
    REQ 3.3 — Verify UUIDs are valid format
  REQ 4  — Output results
    REQ 4.1 — Save to asset_sync_output.json
    REQ 4.2 — Format with proper indentation (2 or 4 spaces)
    REQ 4.3 — Ensure valid JSON structure
  REQ 5  — Error handling
    REQ 5.1 — Handle API failures gracefully
    REQ 5.2 — Skip records with missing critical fields (log them)
    REQ 5.3 — Provide summary of successful/failed transformations
  REQ 6  — Bonus points
    REQ 6.1 — Add a --filter-state option
    REQ 6.2 — Calculate and include days_since_hire
    REQ 6.3 — Add phone number format validation
    REQ 6.4 — Create a comparison mode vs previous sync

USAGE (examples):
  python3 sync_hr_to_assets_super_commented.py
  python3 sync_hr_to_assets_super_commented.py --results 25 --indent 4
  python3 sync_hr_to_assets_super_commented.py --filter-state Texas,California
  python3 sync_hr_to_assets_super_commented.py --compare previous_output.json
  python3 sync_hr_to_assets_super_commented.py --enforce-phone
"""

# ===============================
# 1) Standard library imports
# ===============================

import argparse  # Build CLI for flags (results/indent/output/filter/compare/enforce-phone). [REQ 4, REQ 6]
import json      # Parse API JSON and write final JSON file. [REQ 1, REQ 4]
import sys       # Print to stderr and exit with specific codes on failure. [REQ 5]
from datetime import datetime, timezone  # Timestamps in UTC for fields and metadata. [REQ 2, REQ 4]
import ssl       # Create custom SSL contexts to fix cert issues. [REQ 5.1]
import certifi   # Provide Mozilla CA bundle path for SSL verification. [REQ 5.1]
from urllib.request import Request, urlopen  # HTTP client to fetch RandomUser data. [REQ 1]
from urllib.error import HTTPError, URLError # Distinguish HTTP vs network failures. [REQ 5.1]
from typing import Any, Dict, List, Tuple, Optional  # Type hints for clarity; no runtime effect. [Meta]
import re        # Regex validations for UUID/email/phone. [REQ 3]
from copy import deepcopy  # Safe copies for comparison diffs. [REQ 6.4]

# ===============================
# 2) Configuration / Constants
# ===============================

API_URL_TEMPLATE = "https://randomuser.me/api/?results={results}&nat=us"  # API base with dynamic result count. [REQ 1]

UUID_RE = re.compile(  # RFC4122 UUID pattern (v1–v5; correct variant). [REQ 3.3]
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-"
    r"[0-9a-fA-F]{12}$"
)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")  # Lenient email sanity check (has '@' and dot). [REQ 3.2]

PHONE_RE = re.compile(  # Common US-style phone format (optional enforcement). [REQ 6.3]
    r"^\+?1?[\s\-\.]?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}$"
)

# ===============================
# 3) Small helper functions
# ===============================

def http_get_json(results: int) -> Dict[str, Any]:  # Fetch N users from API and return parsed JSON. [REQ 1, REQ 5.1]
    url = API_URL_TEMPLATE.format(results=results)  # Fill URL with requested result count. [REQ 1]
    req = Request(url, headers={"User-Agent": "hr-sync/1.0"})  # Friendly UA header for API. [REQ 1]
    ctx = ssl.create_default_context(cafile=certifi.where())  # Use certifi CA bundle to verify SSL. [REQ 5.1]
    try:  # Gracefully catch and rephrase network/HTTP errors. [REQ 5.1]
        with urlopen(req, timeout=30, context=ctx) as resp:  # Perform HTTPS GET with timeout and SSL context. [REQ 1, REQ 5.1]
            if resp.status != 200:  # Treat non-200 as failure with clear message. [REQ 5.1]
                raise RuntimeError(f"API returned status {resp.status}")  # Bubble up for caller error handling. [REQ 5.1]
            raw = resp.read()  # Read response bytes from socket. [REQ 1]
            text = raw.decode("utf-8")  # Decode bytes to UTF-8 string. [REQ 1]
            return json.loads(text)  # Parse JSON into dict and return. [REQ 1]
    except HTTPError as e:  # Map HTTP errors to human-friendly message. [REQ 5.1]
        raise RuntimeError(f"HTTP error: {e.code} {e.reason}") from e  # Preserve traceback; improve message. [REQ 5.1]
    except URLError as e:  # Map network/SSL/DNS errors to friendly message. [REQ 5.1]
        raise RuntimeError(f"Network error: {e.reason}") from e  # Preserve traceback; improve message. [REQ 5.1]

def now_iso_utc() -> str:  # Current UTC time as ISO 8601 (e.g., 2025-10-18T14:05:00Z). [REQ 2.4]
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # Format for sync_metadata. [REQ 2.4]

def to_unix(dt: datetime) -> int:  # Convert datetime to UNIX seconds (used in asset_id). [REQ 2.2]
    return int(dt.replace(tzinfo=timezone.utc).timestamp())  # Force UTC then epoch seconds. [REQ 2.2]

def extract_date_only(iso_ts: str) -> Optional[str]:  # Take YYYY-MM-DD from ISO timestamp string. [REQ 2.3]
    if isinstance(iso_ts, str) and len(iso_ts) >= 10:  # Basic guard for shape. [REQ 2.3]
        return iso_ts[:10]  # Slice first 10 chars to get date-only portion. [REQ 2.3]
    return None  # Signal invalid input upstream. [REQ 5.2]

def validate_uuid(u: str) -> bool:  # Validate UUID format via regex. [REQ 3.3]
    return isinstance(u, str) and bool(UUID_RE.match(u))  # True if proper string and pattern. [REQ 3.3]

def validate_email(e: str) -> bool:  # Validate email has '@' and domain dot. [REQ 3.2]
    return isinstance(e, str) and bool(EMAIL_RE.match(e))  # True if basic email pattern matches. [REQ 3.2]

def phone_quality_ok(p: str) -> bool:  # Check phone format (metadata or enforced by flag). [REQ 6.3]
    if not isinstance(p, str) or not p.strip():  # Empty/non-string phones are invalid. [REQ 6.3]
        return False  # Not acceptable format. [REQ 6.3]
    return bool(PHONE_RE.match(p.strip()))  # True if US-ish number matches. [REQ 6.3]

def days_since(datestr: str) -> Optional[int]:  # Compute days from YYYY-MM-DD until now (UTC). [REQ 6.2]
    try:
        d = datetime.strptime(datestr, "%Y-%m-%d").replace(tzinfo=timezone.utc)  # Parse date and force UTC. [REQ 6.2]
        return max(0, (datetime.now(timezone.utc) - d).days)  # Non-negative day delta. [REQ 6.2]
    except Exception:
        return None  # Gracefully skip if input invalid. [REQ 6.2]

# ===============================
# 4) Transform one user record
# ===============================

def transform_employee(  # Transform one RandomUser record into asset schema with validation. [REQ 2, REQ 3, REQ 5, REQ 6]
    src: Dict[str, Any],        # One RandomUser record (source). [REQ 2.1]
    run_dt: datetime,           # Batch timestamp for consistent asset_id time. [REQ 2.2]
    enforce_phone: bool = False # If True, reject records with bad phone format. [REQ 6.3]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:  # Return (record, None) or (None, reason). [REQ 5.2]
    try:
        uuid = src["login"]["uuid"]          # Extract employee_id from nested login.uuid. [REQ 2.1, REQ 3.1]
        email = src["email"]                 # Extract work_email. [REQ 2.1, REQ 3.1]
        phone = src.get("phone", "")         # Optional contact_number (default empty). [REQ 2.5]
        first = src["name"]["first"]         # First name for full name. [REQ 2.1, REQ 3.1]
        last  = src["name"]["last"]          # Last name for full name. [REQ 2.1, REQ 3.1]
        city    = src["location"]["city"]    # Office city. [REQ 2.1, REQ 3.1]
        state   = src["location"]["state"]   # Office state. [REQ 2.1, REQ 3.1]
        country = src["location"]["country"] # Office country. [REQ 2.1, REQ 3.1]
        reg_iso = src["registered"]["date"]  # Registered timestamp to derive hire_date. [REQ 2.3, REQ 3.1]
    except KeyError as e:
        return None, f"missing required field: {e}"  # Skip record and log cause. [REQ 5.2]

    if not validate_uuid(uuid):  # UUID must be valid. [REQ 3.3]
        return None, f"invalid uuid format: {uuid}"  # Skip invalid UUID. [REQ 5.2]
    if not validate_email(email):  # Email must contain '@' and domain dot. [REQ 3.2]
        return None, f"invalid email (must contain '@'): {email}"  # Skip invalid email. [REQ 5.2]

    phone_ok = phone_quality_ok(phone)  # Check phone quality for metadata/enforcement. [REQ 6.3]
    if enforce_phone and not phone_ok:  # Enforce only when flag is set. [REQ 6.3]
        return None, f"invalid phone format (data quality): {phone}"  # Skip on enforcement failure. [REQ 5.2]

    hire_date = extract_date_only(reg_iso)  # Convert ISO timestamp to YYYY-MM-DD. [REQ 2.3]
    if not hire_date:
        return None, f"invalid registered.date: {reg_iso}"  # Skip if date could not be parsed. [REQ 5.2]

    ts = to_unix(run_dt)  # Single-run UNIX seconds for asset_id stability. [REQ 2.2]
    asset_id = f"ASSET-{uuid[:8]}-{ts}"  # Asset ID format per spec. [REQ 2.2]

    full_name = f"{first.strip()} {last.strip()}".strip()  # Build clean full name. [REQ 2.2]

    rec = {  # Construct destination record shape. [REQ 2]
        "asset_id": asset_id,  # Generated ID. [REQ 2.2]
        "employee_full_name": full_name,  # Human-readable name. [REQ 2]
        "employee_id": uuid,  # Source UUID. [REQ 2]
        "work_email": email,  # Work email. [REQ 2]
        "contact_number": phone,  # Raw phone. [REQ 2]
        "office_location": {  # Nested location object. [REQ 2.1]
            "city": city,      # City. [REQ 2.1]
            "state": state,    # State. [REQ 2.1]
            "country": country # Country. [REQ 2.1]
        },
        "employee_status": "active",  # Default status. [REQ 2.5]
        "hire_date": hire_date,       # Date-only string. [REQ 2.3]
        "department": "unassigned",   # Default department. [REQ 2.5]
    }

    dsh = days_since(hire_date)    # Compute days since hire if possible. [REQ 6.2]
    if dsh is not None:
        rec["days_since_hire"] = dsh  # Include optional analytics field. [REQ 6.2]

    rec["_phone_quality_ok"] = phone_ok  # Keep phone check result as metadata. [REQ 6.3]

    return rec, None  # Success path: transformed record, no error. [REQ 2]

# ===============================
# 5) Bonus helpers: filtering & comparing
# ===============================

def filter_by_state(records: List[Dict[str, Any]], states: List[str]) -> List[Dict[str, Any]]:  # Filter records by state list. [REQ 6.1]
    wanted = {s.strip().lower() for s in states if s.strip()}  # Normalize requested states to lowercase set. [REQ 6.1]
    if not wanted:
        return records  # No states provided → no filtering. [REQ 6.1]

    out = []  # Collector for records that match. [REQ 6.1]
    for r in records:
        try:
            st = r["location"]["state"]  # Access nested state. [REQ 2.1]
            if isinstance(st, str) and any(s in st.strip().lower() for s in wanted):  # Substring/CI match. [REQ 6.1]
                out.append(r)  # Keep matching record. [REQ 6.1]
        except KeyError:
            pass  # Missing state → exclude silently in this helper. [REQ 5.2]
    return out  # Return filtered list. [REQ 6.1]

def compare_runs(prev: Dict[str, Any], curr: Dict[str, Any]) -> Dict[str, Any]:  # Compute new/removed/changed by employee_id. [REQ 6.4]
    p = {e["employee_id"]: e for e in prev.get("employees", []) if "employee_id" in e}  # Map prev by ID. [REQ 6.4]
    c = {e["employee_id"]: e for e in curr.get("employees", []) if "employee_id" in e}  # Map curr by ID. [REQ 6.4]

    new_ids = [eid for eid in c if eid not in p]  # Present now, absent before. [REQ 6.4]
    removed_ids = [eid for eid in p if eid not in c]  # Present before, absent now. [REQ 6.4]

    changed = []  # Collect shallow diffs per common ID. [REQ 6.4]
    for eid in set(p).intersection(c):  # Only compare common IDs. [REQ 6.4]
        prev_e = deepcopy(p[eid])  # Copy to avoid mutating input. [REQ 6.4]
        curr_e = deepcopy(c[eid])  # Copy to avoid mutating input. [REQ 6.4]
        diffs = {}  # Field differences holder. [REQ 6.4]
        for k in set(prev_e).union(curr_e):  # Compare union of keys. [REQ 6.4]
            if prev_e.get(k) != curr_e.get(k):  # Record changed/added/removed values. [REQ 6.4]
                diffs[k] = {"previous": prev_e.get(k), "current": curr_e.get(k)}  # Shallow diff. [REQ 6.4]
        if diffs:
            changed.append({"employee_id": eid, "diffs": diffs})  # Store diffs under the ID. [REQ 6.4]

    return {"new_ids": new_ids, "removed_ids": removed_ids, "changed": changed}  # Summary for reports. [REQ 6.4]

# ===============================
# 6) Main function (program entry)
# ===============================

def main() -> None:  # Orchestrate: args → fetch → filter → transform/validate → compare → write → summaries. [REQ 1–6]
    parser = argparse.ArgumentParser(  # CLI description for help output. [REQ 4]
        description="HR → Asset sync with validation, filtering, comparison, and extensive comments."
    )
    parser.add_argument("--results", type=int, default=10,  # Control number of API users to fetch. [REQ 1]
                        help="How many users to fetch (default: 10)")
    parser.add_argument("--output", type=str, default="asset_sync_output.json",  # Where to write final JSON. [REQ 4.1]
                        help="Output JSON file path (default: asset_sync_output.json)")
    parser.add_argument("--indent", type=int, default=2, choices=[2, 4],  # Pretty-print indentation. [REQ 4.2]
                        help="JSON indentation (2 or 4 spaces; default: 2)")
    parser.add_argument("--filter-state", type=str, default="",  # Comma-separated states to include. [REQ 6.1]
                        help="Comma-separated states to include (e.g., Texas,California)")
    parser.add_argument("--compare", type=str, default="",  # Compare against previous output file. [REQ 6.4]
                        help="Path to previous output to compare (optional)")
    parser.add_argument("--enforce-phone", action="store_true",  # Toggle to reject invalid phone formats. [REQ 6.3]
                        help="If set, records with invalid phone format are skipped (bonus).")

    args = parser.parse_args()  # Parse CLI into namespace. [REQ 4]

    try:
        payload = http_get_json(args.results)  # Fetch data from RandomUser API. [REQ 1, REQ 5.1]
    except Exception as e:
        print(f"[ERROR] fetch failed: {e}", file=sys.stderr)  # Clear, friendly failure message. [REQ 5.1]
        sys.exit(2)  # Exit with code 2 to indicate fetch failure. [REQ 5]

    src_records = payload.get("results", [])  # Pull the actual employee array, default to []. [REQ 1]

    if args.filter_state.strip():  # Only apply state filter if user provided states. [REQ 6.1]
        filter_states = [s for s in args.filter_state.split(",")]  # Split "A,B" to ["A","B"]. [REQ 6.1]
        src_records = filter_by_state(src_records, filter_states)  # Keep only matching records. [REQ 6.1]

    run_dt = datetime.now(timezone.utc)  # Single run timestamp for asset_id stability. [REQ 2.2]

    transformed: List[Dict[str, Any]] = []  # Hold successful transformed records. [REQ 4.3]
    skipped: List[Dict[str, Any]] = []      # Hold per-record skip reasons (index + reason). [REQ 5.2]

    for index, rec in enumerate(src_records, start=1):  # Process each input record with 1-based index. [REQ 2]
        out, err = transform_employee(rec, run_dt, enforce_phone=args.enforce_phone)  # Map + validate + extras. [REQ 2, REQ 3, REQ 6]
        if err:
            skipped.append({"index": index, "reason": err})  # Log skip reason for reporting. [REQ 5.2, REQ 5.3]
        else:
            transformed.append(out)  # Accept record into output set. [REQ 4.3]

    final_doc: Dict[str, Any] = {  # Final JSON structure to write. [REQ 4.3]
        "sync_metadata": {  # Metadata block about this run. [REQ 2.4]
            "sync_timestamp": now_iso_utc(),  # When we synced (UTC). [REQ 2.4]
            "source_system": "HR_API",        # Fixed source label. [REQ 2.4]
            "record_count": len(transformed), # Count of successes. [REQ 2.4]
        },
        "employees": transformed  # Final transformed employees array. [REQ 4.3]
    }

    if args.compare:  # Compare mode only if a previous output path was provided. [REQ 6.4]
        try:
            with open(args.compare, "r", encoding="utf-8") as f:  # Read previous JSON. [REQ 6.4]
                previous_output = json.load(f)  # Parse previous JSON to dict. [REQ 6.4]
            final_doc["_comparison"] = compare_runs(previous_output, final_doc)  # Attach diff results. [REQ 6.4]
        except FileNotFoundError:
            print(f"[WARN] compare file not found: {args.compare}", file=sys.stderr)  # Warn but continue. [REQ 5.1]
        except json.JSONDecodeError:
            print(f"[WARN] compare file invalid JSON: {args.compare}", file=sys.stderr)  # Warn but continue. [REQ 5.1]

    try:
        with open(args.output, "w", encoding="utf-8") as f:  # Create/overwrite output file. [REQ 4.1]
            json.dump(final_doc, f, indent=args.indent, ensure_ascii=False)  # Pretty-print JSON with chosen indent. [REQ 4.2, REQ 4.3]
        print(f"[OK] wrote {args.output} with {len(transformed)} employees")  # Success message. [REQ 4.1]
    except Exception as e:
        print(f"[ERROR] write failed: {e}", file=sys.stderr)  # Clear write failure message. [REQ 5.1]
        sys.exit(3)  # Exit with code 3 to indicate write failure. [REQ 5]

    if skipped:  # Print summary of skipped records (first 20). [REQ 5.3]
        print(f"[INFO] skipped {len(skipped)} record(s):")  # Count of skipped records. [REQ 5.3]
        for s in skipped[:20]:  # Avoid flooding console. [REQ 5.3]
            print(f"  - index {s['index']}: {s['reason']}")  # Reason per skipped record. [REQ 5.3]
        if len(skipped) > 20:
            print(f"  ... and {len(skipped)-20} more")  # Indicate additional skipped ones. [REQ 5.3]
    else:
        print("[INFO] no records skipped")  # Clean all-good message. [REQ 5.3]

    comp = final_doc.get("_comparison")  # Grab comparison summary if present. [REQ 6.4]
    if comp:
        print(f"[COMPARE] new={len(comp.get('new_ids', []))}, "  # Count of new IDs. [REQ 6.4]
              f"removed={len(comp.get('removed_ids', []))}, "    # Count of removed IDs. [REQ 6.4]
              f"changed={len(comp.get('changed', []))}")         # Count of changed records. [REQ 6.4]

# ===============================
# 7) Standard Python entry guard
# ===============================

if __name__ == "__main__":  # Run main() only when executed directly. [Meta]
    main()  # Kick off the ETL pipeline. [REQ 1–6]

