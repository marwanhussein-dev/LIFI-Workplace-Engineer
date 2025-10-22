HR → Assets Sync — Docs

# Big-picture logic & structure (why it’s organized like this)
# Fetch first (http_get_json) → because nothing else makes sense without the data.
# Optionally filter (bonus) → faster & cleaner to cut down the dataset before heavy work.
# One “run timestamp” → consistent asset_id format across all records.
# Transform + Validate in a loop → apply mapping and checks per record; don’t let one bad record kill the run.
# collect successes & skips → needed for output JSON and for the final human summary.
# Build final document → exactly the target schema (sync_metadata + employees).
# Optional compare (bonus) → extra info without affecting the core deliverable.
# Write JSON (indent 2/4) → satisfies output formatting requirement.
# Summaries → clear info for testers about what happened.

# This is the classic ETL flow: Extract → Transform/Validate → Load → Report.

This is a demo/assignment script, not a production HR connector.

⸻

Features you can use
	•	Fetch count: --results N (default 10).
	•	Indentation: --indent {2,4} for JSON output.
	•	Output path: --output FILE.json.
	•	Filter by state(s): --filter-state "Texas,California" (case-insensitive).
	•	Enforce phone format: --enforce-phone (skips bad phones).
	•	Compare runs: --compare previous.json (adds _comparison with new_ids/removed_ids/changed).

Under the hood:
	•	Generates asset_id like ASSET-<first8(uuid)>-<unix_timestamp>.
	•	Extracts hire_date (date-only) and days_since_hire.
	•	Adds defaults: employee_status="active", department="unassigned".

⸻

Prerequisites (to avoid errors)
	•	Python 3.9+ (works great on 3.11/3.12).
	•	Internet access (the script calls RandomUser API).
	•	Certs (macOS fix for SSL): the script already uses certifi-backed SSL.
	•	If you don’t have certifi, install it once:

pip3 install certifi



If you ever see SSL: CERTIFICATE_VERIFY_FAILED, make sure certifi is installed and you’re running the current script version (which passes an SSL context that uses certifi).

⸻

How to run (common examples)

# Basic: 10 users, 2-space indent, writes asset_sync_output.json
python3 sync_hr_to_assets.py

# Fetch 25 users, pretty indent 4, custom file
python3 sync_hr_to_assets.py --results 25 --indent 4 --output out.json

# Keep only specific states (case-insensitive; list allowed)
python3 sync_hr_to_assets.py --filter-state "Texas,California,New York"

# Strict phone validation (bad phones are skipped)
python3 sync_hr_to_assets.py --enforce-phone

# Compare vs a previous run
python3 sync_hr_to_assets.py --compare previous_output.json

Note on filtering: RandomUser returns different states every call. If you filter by a state that isn’t in this batch, you’ll get 0 employees—that’s normal. To test filtering deterministically, first run without filter, inspect which states you received, then re-run with a matching filter (see “Quick testing” below).

⸻

Quick testing

1) See how many employees got written

# Requires jq (brew install jq). If you don’t have jq, see Python alternative below.
jq '.employees | length' asset_sync_output.json

Python alternative (no jq):

python3 - <<'PY'
import json,sys
d=json.load(open("asset_sync_output.json"))
print(len(d.get("employees",[])))
PY

2) See which states you got this time

jq -r '.employees[].office_location.state' asset_sync_output.json | sort | uniq

Use those states in --filter-state to verify filtering works:

python3 sync_hr_to_assets.py --filter-state "Texas,Utah" --output filtered.json

3) Enforce phone format

python3 sync_hr_to_assets.py --enforce-phone --output phone_enforced.json
# Expect the same or fewer employees (bad phone entries get skipped).

4) Compare runs

python3 sync_hr_to_assets.py --results 6 --output t1.json
python3 sync_hr_to_assets.py --output t2.json        # new batch
python3 sync_hr_to_assets.py --compare t1.json --output t3.json
# Console prints: [COMPARE] new=…, removed=…, changed=…
# And t3.json contains a "_comparison" object.


⸻

Common pitfalls & fixes
	•	SSL error (CERTIFICATE_VERIFY_FAILED):
Install certifi and use the provided script (it sets an SSL context using certifi).

pip3 install certifi


	•	Filter returns 0 employees:
That means none of the current batch’s states matched your filter (RandomUser is random).
First run without filters, list states (see Quick testing #2), then filter using real states you just saw.
	•	Compare mode file missing or invalid:
You’ll see a [WARN] message; the script continues safely. Provide a valid previous JSON next time.
	•	Phone enforcement drops records:
That’s expected; --enforce-phone is strict on format.

⸻

Output shape (example)

{
  "sync_metadata": {
    "sync_timestamp": "2025-10-18T14:05:00Z",
    "source_system": "HR_API",
    "record_count": 10
  },
  "employees": [
    {
      "asset_id": "ASSET-9a8c2b41-1739960450",
      "employee_full_name": "Jane Smith",
      "employee_id": "9a8c2b41-1bfc-4e7d-8ac0-9e9cb42e6b22",
      "work_email": "jane.smith@example.com",
      "contact_number": "+1 555-123-4567",
      "office_location": {"city": "Austin","state": "Texas","country": "United States"},
      "employee_status": "active",
      "hire_date": "2023-05-10",
      "department": "unassigned",
      "days_since_hire": 526,
      "_phone_quality_ok": true
    }
  ]
}


⸻

## Validation and Error Handling Tests

Because the RandomUser API always returns valid and complete data, additional manual
tests were created to verify the script’s behavior with malformed or incomplete records.

These tests are contained in **test_validation.py**, located in the same directory as
the main script (`sync_hr_to_assets.py`).

They confirm the correctness of:
- [REQ 3] Data validation (UUID, email, required fields)
- [REQ 5] Error handling (skipping invalid records, clear error messages)
- [REQ 6.3] Optional phone number format enforcement

### How to Run the Tests

1. Make sure you have Python 3 installed.  
   You can verify with:
   ```bash
   python3 --version

2.	Run the test file directly from the same folder where your main script is located:

python3 test_validation.py


3.	The script will print one line per test case, showing whether each record was
transformed successfully (out=True) or skipped (out=False), and the reason if skipped.

Example output:

    bad_uuid → out=False  err='invalid uuid format: NOT-A-UUID'
    bad_email → out=False  err="invalid email (must contain '@'): no-at-symbol"
    missing_required → out=False  err="missing required field: 'last'"
    bad_date → out=False  err='invalid registered.date: oops'
    bad_phone_no_enforce → out=True   err=None
    bad_phone_enforced → out=False  err='invalid phone format (data quality): 123'

4.	Successful test output confirms:
	[REQ 3.1 – 3.3] Validation rules trigger correctly.
	[REQ 5.2] The script skips invalid records without crashing.
	[REQ 6.3] The optional --enforce-phone flag behaves as expected.

        


Summary:

These tests ensure that the script handles malformed or incomplete data safely and predictably — without crashing, and with clear messages explaining why each record was skipped.

⸻

File Reference:

File	                     Description
sync_hr_to_assets.py	     Main synchronization script implementing extraction, transformation, and loading
test_validation.py	         Independent test suite verifying data validation and error handling behaviors
sample_output.json	         Example of successful run output
