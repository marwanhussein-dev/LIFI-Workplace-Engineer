# Sample Expected Output for Part 2

## File: asset_sync_output.json

This is an example of what your output should look like after transforming data from 3 employees from the Random User API.

```json
{
  "sync_metadata": {
    "sync_timestamp": "2025-10-12T14:30:00Z",
    "source_system": "HR_API",
    "record_count": 3
  },
  "employees": [
    {
      "asset_id": "ASSET-a1b2c3d4-1728742200",
      "employee_full_name": "Sarah Johnson",
      "employee_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "work_email": "sarah.johnson@example.com",
      "contact_number": "(503) 555-0123",
      "office_location": {
        "city": "Portland",
        "state": "Oregon",
        "country": "United States"
      },
      "employee_status": "active",
      "hire_date": "2018-03-10",
      "department": "unassigned"
    },
    {
      "asset_id": "ASSET-f9e8d7c6-1728742200",
      "employee_full_name": "Michael Chen",
      "employee_id": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
      "work_email": "michael.chen@example.com",
      "contact_number": "(415) 555-0456",
      "office_location": {
        "city": "San Francisco",
        "state": "California",
        "country": "United States"
      },
      "employee_status": "active",
      "hire_date": "2019-07-15",
      "department": "unassigned"
    },
    {
      "asset_id": "ASSET-1a2b3c4d-1728742200",
      "employee_full_name": "Emily Rodriguez",
      "employee_id": "1a2b3c4d-5e6f-7890-abcd-1234567890ab",
      "work_email": "emily.rodriguez@example.com",
      "contact_number": "(512) 555-0789",
      "office_location": {
        "city": "Austin",
        "state": "Texas",
        "country": "United States"
      },
      "employee_status": "active",
      "hire_date": "2020-01-20",
      "department": "unassigned"
    }
  ]
}
```

## Key Points to Note

1. **JSON Structure**: 
   - Top level has `sync_metadata` and `employees` arrays
   - Each employee is an object in the array

2. **sync_metadata**:
   - `sync_timestamp`: Current time in ISO 8601 format
   - `source_system`: Always "HR_API"
   - `record_count`: Matches the number of employees in the array

3. **asset_id Format**: 
   - Pattern: `ASSET-{first-8-chars-of-uuid}-{unix-timestamp}`
   - Example: `ASSET-a1b2c3d4-1728742200`

4. **employee_full_name**: 
   - Concatenation of first and last name with a space
   - Example: "Sarah Johnson" from first: "Sarah", last: "Johnson"

5. **hire_date Format**: 
   - Date only, no time: `YYYY-MM-DD`
   - Extracted from API's `registered.date` field

6. **office_location**: 
   - Nested object (not flat)
   - Contains city, state, country

7. **Static Fields**:
   - `employee_status`: Always "active"
   - `department`: Always "unassigned"

## Validation Checklist

Before submitting, verify:
- ✅ File is valid JSON (use `jq . asset_sync_output.json` to test)
- ✅ All employee_ids are full UUIDs
- ✅ All asset_ids follow the ASSET-{8chars}-{timestamp} pattern
- ✅ All timestamps use shortened UUIDs (first 8 characters only)
- ✅ employee_full_name has both first and last names
- ✅ office_location is an object, not a string
- ✅ hire_date is date only (no time component)
- ✅ record_count matches actual number of employees
- ✅ All required fields are present

## Testing Your Output

```bash
# Validate JSON syntax
jq . asset_sync_output.json

# Count employees
jq '.employees | length' asset_sync_output.json

# Check a specific employee structure
jq '.employees[0]' asset_sync_output.json

# Verify all asset_ids follow pattern
jq '.employees[].asset_id' asset_sync_output.json
```