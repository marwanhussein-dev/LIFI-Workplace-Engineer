# Workplace Engineer - Take Home Exercise

**Time Allocation:** 2-3 hours  
**Focus Areas:** Automation, Application Integration, Scripting

## Overview

This exercise evaluates your ability to automate common workplace engineering tasks, integrate with APIs, and write maintainable scripts. You'll work on three scenarios that reflect real-world challenges in managing employee technology and workplace systems.

---

## Getting Started

### Fork the Repository

1. **Fork this repository** to your personal GitHub account
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/workplace-engineer-exercise.git
   cd workplace-engineer-exercise
   ```
3. **Create a new branch** for your work:
   ```bash
   git checkout -b solution
   ```
4. Complete the exercises in the appropriate directories
5. **Commit your changes** regularly with clear commit messages
6. **Push to your fork** when complete
7. **Share the link** to your repository with us

### Repository Structure

Your forked repository should maintain this structure:
```
/part1-app-deployment
  - your-script-here.sh (or .py, .ps1)
  - README.md
/part2-api-integration
  - your-sync-script-here.py (or .sh, .ps1)
  - asset_sync_output.json (sample output)
  - README.md
/part3-architecture-design
  - README.md
README.md (your main documentation)
```

---

## Part 1: Application Deployment Script (45-60 minutes)

### Scenario
Your company needs to standardize the installation of Slack on macOS devices. Create an automated installation script that can be deployed to new employee machines.

### Requirements

Write a script in **one** of the following languages (your choice):
- Bash
- Python
- PowerShell (for cross-platform support)

Your script should:

1. **Check prerequisites:**
   - Verify the script is running on macOS
   - Check for administrative privileges
   - Verify internet connectivity

2. **Install Slack:**
   - Download the latest Slack .dmg file from the official source
   - Mount the disk image
   - Copy the application to /Applications
   - Clean up temporary files
   - Verify successful installation

3. **Include proper error handling:**
   - Exit gracefully if prerequisites aren't met
   - Provide clear error messages
   - Log installation steps

4. **Bonus points:**
   - Make the script idempotent (safe to run multiple times)
   - Add a configuration option to install other applications
   - Include a dry-run mode

### Deliverables
- The installation script
- A README with:
  - How to run the script
  - Any assumptions made
  - Testing approach used

---

## Part 2: API Integration & Data Transformation (60-75 minutes)

### Scenario
Your organization uses multiple systems for managing employee accounts. The HR system uses one data format, while your IT Asset Management system uses a completely different schema. You need to build a tool that fetches data from the HR API and transforms it to match the Asset Management system's requirements.

### Source: HR System API

**Endpoint:** `https://randomuser.me/api/?results=10&nat=us`  
**Method:** GET

**Actual Response Structure:**
```json
{
  "results": [
    {
      "gender": "male",
      "name": {
        "title": "Mr",
        "first": "John",
        "last": "Doe"
      },
      "location": {
        "street": {
          "number": 1234,
          "name": "Main St"
        },
        "city": "Austin",
        "state": "Texas",
        "country": "United States",
        "postcode": 12345
      },
      "email": "john.doe@example.com",
      "login": {
        "uuid": "7f3d4e2a-9c8b-4a1e-8d6f-2b5c9e1a3f4d",
        "username": "silverfish123"
      },
      "dob": {
        "date": "1985-03-15T08:30:00.000Z",
        "age": 40
      },
      "registered": {
        "date": "2020-01-15T12:00:00.000Z",
        "age": 5
      },
      "phone": "(555) 123-4567",
      "cell": "(555) 987-6543",
      "picture": {
        "large": "https://randomuser.me/api/portraits/men/75.jpg",
        "medium": "https://randomuser.me/api/portraits/med/men/75.jpg",
        "thumbnail": "https://randomuser.me/api/portraits/thumb/men/75.jpg"
      },
      "nat": "US"
    }
  ],
  "info": {
    "seed": "abc123",
    "results": 10,
    "page": 1,
    "version": "1.4"
  }
}
```

### Destination: Asset Management System Schema

Your Asset Management system requires data in this completely different format:

```json
{
  "sync_metadata": {
    "sync_timestamp": "2025-10-12T10:30:00Z",
    "source_system": "HR_API",
    "record_count": 10
  },
  "employees": [
    {
      "asset_id": "ASSET-7f3d4e2a-1728736200",
      "employee_full_name": "John Doe",
      "employee_id": "7f3d4e2a-9c8b-4a1e-8d6f-2b5c9e1a3f4d",
      "work_email": "john.doe@example.com",
      "contact_number": "(555) 123-4567",
      "office_location": {
        "city": "Austin",
        "state": "Texas",
        "country": "United States"
      },
      "employee_status": "active",
      "hire_date": "2020-01-15",
      "department": "unassigned"
    }
  ]
}
```

### Required Field Mappings

You must transform the HR API data to match the Asset Management schema:

| Source (HR API) | Destination (Asset Management) | Transformation Required |
|----------------|-------------------------------|------------------------|
| `login.uuid` | `employee_id` | Direct mapping |
| `login.uuid` + timestamp | `asset_id` | Generate: `ASSET-{first 8 chars of uuid}-{unix_timestamp}` |
| `name.first` + `name.last` | `employee_full_name` | Concatenate with space |
| `email` | `work_email` | Direct mapping |
| `phone` | `contact_number` | Direct mapping |
| `location.city` | `office_location.city` | Nested object |
| `location.state` | `office_location.state` | Nested object |
| `location.country` | `office_location.country` | Nested object |
| `registered.date` | `hire_date` | Extract date only (YYYY-MM-DD) |
| N/A | `employee_status` | Set to "active" for all |
| N/A | `department` | Set to "unassigned" for all |
| Current time | `sync_metadata.sync_timestamp` | ISO 8601 format |
| "HR_API" | `sync_metadata.source_system` | Static value |
| Count of results | `sync_metadata.record_count` | Count from API response |

### Requirements

Create a synchronization tool (in Python, Bash, or PowerShell) that:

1. **Fetches employee data** from the HR API (Random User API)

2. **Transforms the data** according to the mapping table above:
   - Handle nested objects properly (name, location)
   - Generate the asset_id in the specified format
   - Extract only the date portion from timestamps
   - Create the sync_metadata section
   - Set default values for fields not in source data

3. **Validates the data:**
   - Ensure all required fields are present
   - Check that email addresses contain "@"
   - Verify UUIDs are valid format

4. **Outputs results:**
   - Save to a JSON file named `asset_sync_output.json`
   - Format with proper indentation (2 or 4 spaces)
   - Ensure valid JSON structure

5. **Includes error handling:**
   - Handle API failures gracefully
   - Skip records with missing critical fields (log them)
   - Provide summary of successful/failed transformations

6. **Bonus points:**
   - Add a `--filter-state` option to only sync employees from specific states
   - Calculate and include `days_since_hire` field
   - Add data quality checks (e.g., phone number format validation)
   - Create a comparison mode that shows what changed from a previous sync

### Deliverables
- The synchronization script
- Sample output file
- Brief documentation explaining your approach

---

## Part 3: Research & Interview Preparation (30-45 minutes)

### Scenario
During your technical interview, we'll discuss integrating **HiBob** (HR system), **Entra ID or Okta** (Identity Provider), and **Google Workspace** to automate **new employee onboarding workflows**.

### Your Task

Research and prepare to discuss how you would architect an automated onboarding workflow when a new employee is added to HiBob. The workflow should provision the employee across all three systems.

**Choose ONE Identity Provider to focus on:**
- **Microsoft Entra ID** (formerly Azure Active Directory), OR
- **Okta**

### Key Questions to Research

#### 1. **System Integration Points (15-20 min)**
Research the APIs and integration capabilities:

**HiBob:**
- What APIs are available for employee data?
- Can HiBob send webhooks when a new employee is created?
- What employee information is available (name, email, department, start date, etc.)?

**Your chosen IDP (Entra ID OR Okta):**
- How do you create users programmatically?
- What authentication methods are available (OAuth, API keys, service accounts)?
- How do you assign groups/roles to new users?
- Can it sync to Google Workspace automatically?

**Google Workspace:**
- What APIs handle user provisioning?
- How does Google Workspace integrate with your chosen IDP?
- Can the IDP handle automatic provisioning to Google Workspace?

#### 2. **Onboarding Workflow Design (10-15 min)**

Design a workflow for when a new employee "Sarah Johnson" joins as a Software Engineer:

**Consider:**
- What is the sequence of provisioning? (HiBob → IDP → Google Workspace?)
- When should each system be updated? (Immediately vs. on start date)
- What user attributes flow between systems?
- How do you handle email address generation and conflicts?
- What groups/roles should be assigned automatically?

#### 3. **Integration Architecture (5-10 min)**

Think about:
- Should the IDP be the "source of truth" or just a pass-through?
- Real-time (webhooks) vs. scheduled sync vs. event-driven?
- Where does the integration logic live? (Middleware, cloud functions, etc.)
- How do the three systems communicate with each other?

#### 4. **Edge Cases & Error Handling (5-10 min)**

What could go wrong?
- API downtime or rate limiting
- Duplicate email addresses
- Employee starts in 2 weeks (future-dated provisioning)
- Different employee types (full-time, contractor, intern)
- Partial failures (created in IDP but not Google Workspace)

### Deliverables

**You do NOT need to submit anything for Part 3.** 

Simply come prepared to discuss:
- Your chosen IDP (Entra ID or Okta) and why
- How you would connect these three systems
- Your proposed onboarding workflow
- Integration approach and architecture
- Error handling and edge cases
- Trade-offs between different approaches

### Research Resources

**HiBob:**
- API Documentation: https://apidocs.hibob.com/

**Microsoft Entra ID (if you choose this):**
- Microsoft Graph API: https://learn.microsoft.com/en-us/graph/api/overview
- User Provisioning: https://learn.microsoft.com/en-us/graph/api/user-post-users
- Entra ID + Google Workspace: https://learn.microsoft.com/en-us/entra/identity/saas-apps/google-apps-tutorial

**Okta (if you choose this):**
- Okta API: https://developer.okta.com/docs/reference/
- User API: https://developer.okta.com/docs/reference/api/users/
- Okta + Google Workspace: https://www.okta.com/integrations/google-workspace/

**Google Workspace:**
- Admin SDK: https://developers.google.com/admin-sdk
- Directory API: https://developers.google.com/admin-sdk/directory/v1/guides

### What We're Looking For

During the interview, we want to understand:
- Your ability to research and understand API documentation
- How you think about identity and access management
- Your understanding of system integration patterns
- How you handle complex multi-system workflows
- Your consideration of security and error handling
- How you communicate technical architecture decisions

### Tips

- **Pick ONE IDP** (Entra ID or Okta) and focus your research there
- Take notes on specific API endpoints and capabilities
- Think about the role of an IDP in the overall architecture
- Consider both the "happy path" and potential failure scenarios
- Be ready to explain WHY you would choose certain approaches
- Draw a simple diagram if it helps you think through the flow

**Remember:** There's no single "right answer" - we're interested in your thought process, research approach, and how you think about integrating identity systems.

---

## Submission Guidelines

### How to Submit

1. **Ensure all your work is committed and pushed** to your forked repository
2. **Make your repository public** (or give us access if you prefer to keep it private)
3. **Email us the link** to your GitHub repository: [hiring manager email]
4. **Include in your email:**
   - Link to your forked repository
   - Any special instructions for running your code
   - Estimated time spent on the exercise
   - Which IDP you researched for Part 3 (Entra ID or Okta)
   - Confirmation that you've researched the onboarding workflow and are ready to discuss
   - Any questions or feedback about the exercise

### What Your Repository Should Include

1. All scripts/code from Part 1 and Part 2
2. A main README.md in the root directory with:
   - Instructions to run each component
   - Any dependencies or prerequisites
   - Any assumptions you made
   - What you would do differently with more time
   - Questions or clarifications you would normally ask stakeholders

**Note:** Part 3 requires no submission - just come prepared to discuss HiBob/Google Workspace integration during your technical interview.

### Repository Checklist

Before submitting, make sure:
- [ ] All code for Parts 1 & 2 is committed and pushed
- [ ] README files exist in Part 1 and Part 2 directories
- [ ] Main README.md has clear instructions
- [ ] Scripts include comments and documentation
- [ ] Sample output files are included where applicable
- [ ] Repository is public or access has been granted
- [ ] Commit messages are clear and descriptive
- [ ] You've chosen an IDP (Entra ID or Okta) and researched it thoroughly
- [ ] You've researched HiBob and Google Workspace onboarding integration
- [ ] You're ready to discuss and draw your architecture approach in the interview (using Figma)

### Evaluation Criteria

We'll evaluate based on:

- **Functionality:** Does it work as specified?
- **Code Quality:** Is it readable, well-organized, and maintainable?
- **Error Handling:** Are edge cases considered?
- **Documentation:** Can someone else understand and use your work?
- **Problem-Solving:** How do you approach integration challenges?
- **Real-World Thinking:** Do you consider security, scalability, and operations?

---

## Notes

- **Use any resources:** You can use documentation, Google, Stack Overflow, etc. This reflects real-world work.
- **Ask questions:** If anything is unclear, email us. We value communication.
- **Time management:** You don't need to complete everything perfectly. Focus on demonstrating your approach and thought process.
- **Be pragmatic:** We value working solutions over perfect solutions. Document what you'd improve with more time.

---

## Questions?

If you have any questions about the exercise, please don't hesitate to reach out to [hiring manager email].

Good luck! We're excited to see your work.