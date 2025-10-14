# Part 3: Research & Interview Preparation

## Objective
Research HiBob, your chosen IDP (Entra ID or Okta), and Google Workspace integration to prepare for technical interview discussion about **new employee onboarding automation**.

## No Submission Required

This part does not require any code or documentation submission. It's solely to help you prepare for the technical interview conversation about automating new employee onboarding across three systems.

## Your Research Focus

### System Stack
- **HiBob** - HR system (source of truth for employee data)
- **Entra ID OR Okta** - Identity Provider (you choose which to research)
- **Google Workspace** - Productivity suite

### Onboarding Workflow
Research how to automate provisioning when a new employee joins the company.

## What to Research

### 1. HiBob API
- Employee creation webhooks
- Available employee data fields
- API authentication methods
- New hire information structure

### 2. Your Chosen IDP (Pick ONE)

**If you choose Microsoft Entra ID:**
- Microsoft Graph API for user creation
- Group and role assignment
- SSO configuration with Google Workspace
- Automatic provisioning capabilities

**If you choose Okta:**
- Okta Users API
- Group management
- Application assignment
- Okta integration with Google Workspace

### 3. Google Workspace APIs
- Google Directory API for user provisioning
- How it integrates with your chosen IDP
- Automatic vs. manual provisioning
- Group and OU (Organizational Unit) management

### 4. Integration Architecture
- Sequence of provisioning (HiBob → IDP → Google?)
- Role of IDP in the workflow
- Event-driven vs. scheduled sync
- Error handling and retry logic


```
Example:
1. New employee added to HiBob
2. HiBob webhook triggers integration service
3. Integration creates user in Entra ID/Okta
4. IDP provisions user to Google Workspace
5. User assigned to appropriate groups
```

### Key Integration Points
[System-to-system connections you identified]

### Edge Cases & Challenges
[Potential issues you've thought about]

### Questions for Interview
[Things you want to discuss or clarify]

---

## Resources

**HiBob:**
- API Documentation: https://apidocs.hibob.com/

**Microsoft Entra ID:**
- Microsoft Graph API: https://learn.microsoft.com/en-us/graph/api/overview
- User Provisioning: https://learn.microsoft.com/en-us/graph/api/user-post-users
- Google Workspace Integration: https://learn.microsoft.com/en-us/entra/identity/saas-apps/google-apps-tutorial

**Okta:**
- API Documentation: https://developer.okta.com/docs/reference/
- Users API: https://developer.okta.com/docs/reference/api/users/
- Google Workspace Integration: https://www.okta.com/integrations/google-workspace/

**Google Workspace:**
- Admin SDK: https://developers.google.com/admin-sdk
- Directory API: https://developers.google.com/admin-sdk/directory/v1/guides

---

**Remember:** During the interview, we'll discuss:
- Why you chose your IDP
- How you would architect the onboarding workflow
- Integration approach and error handling
- Trade-offs between different approaches

Focus on **new employee onboarding only** - we're not discussing offboarding in this exercise.