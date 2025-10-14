# Part 2: API Integration & Data Transformation

## Objective
Build a synchronization tool that fetches employee data from the HR API and transforms it to match the Asset Management system's schema (with different field names and structure).

## Your Solution

### Script Name
[Name of your script file]

### Language Used
[Bash / Python / PowerShell]

### How to Run

```bash
# Add your command here
# Example: python transform_employees.py
```

### API Used
- **Source Endpoint:** https://randomuser.me/api/?results=10&nat=us
- **Method:** GET
- **Destination:** Local JSON file with transformed schema

### Data Transformation Implemented

#### Field Mappings
- [ ] `login.uuid` → `employee_id`
- [ ] `login.uuid` + timestamp → `asset_id` (format: ASSET-{uuid}-{timestamp})
- [ ] `name.first` + `name.last` → `employee_full_name`
- [ ] `email` → `work_email`
- [ ] `phone` → `contact_number`
- [ ] `location.*` → `office_location` (nested object)
- [ ] `registered.date` → `hire_date` (date only)
- [ ] Static values: `employee_status`, `department`
- [ ] Metadata: `sync_timestamp`, `source_system`, `record_count`

### Features Implemented

- [ ] Fetches employee data from HR API
- [ ] Transforms nested objects (name, location)
- [ ] Generates unique asset tags
- [ ] Extracts dates from timestamps
- [ ] Creates sync metadata
- [ ] Validates data (emails, required fields)
- [ ] Outputs to JSON file with proper structure
- [ ] Error handling for API failures
- [ ] Logs skipped/failed records
- [ ] Summary of successful/failed transformations

### Bonus Features (if implemented)

- [ ] Filter by state option
- [ ] Calculate days_since_hire
- [ ] Phone number format validation
- [ ] Comparison with previous sync

### Output Format

The script generates `asset_sync_output.json` with this structure:

```json
{
  "sync_metadata": {
    "sync_timestamp": "ISO-8601 timestamp",
    "source_system": "HR_API",
    "record_count": 10
  },
  "employees": [
    {
      "asset_id": "ASSET-{uuid-prefix}-{timestamp}",
      "employee_full_name": "First Last",
      "employee_id": "full-uuid",
      "work_email": "email@example.com",
      "contact_number": "(555) 123-4567",
      "office_location": {
        "city": "City",
        "state": "State",
        "country": "Country"
      },
      "employee_status": "active",
      "hire_date": "YYYY-MM-DD",
      "department": "unassigned"
    }
  ]
}
```

### Testing

[Describe how you tested the transformation logic]

### Data Validation Rules

[Describe what validation checks you implemented]

### Assumptions

[List any assumptions you made about the data or requirements]

### Dependencies

[List any libraries or tools required]
- Example: `requests`, `json`, `datetime`

### Known Limitations

[List any limitations or edge cases not handled]

### Example Transformations

[Show 1-2 examples of how you transformed specific records]