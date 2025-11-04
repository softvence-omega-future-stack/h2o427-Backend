# Admin Background Check Report Endpoints

## Overview
These endpoints allow administrators to fill out and submit background check reports after manually reviewing the submitted requests.

## Workflow
1. User submits background check request
2. Admin views pending requests
3. Admin fills out report form with verification results
4. Admin submits report
5. Request status changes to "Completed"
6. Client can view the completed report

---

## Endpoint 1: Get Pending Reports (Admin)

**URL:** `GET /api/requests/api/pending-reports/`  
**Permission:** Admin only  
**Purpose:** Get list of all requests that need reports filled out

### Request
```http
GET /api/requests/api/pending-reports/
Authorization: Bearer <admin_token>
```

### Response
```json
{
  "success": true,
  "count": 3,
  "requests": [
    {
      "id": 25,
      "name": "John Michael Doe",
      "email": "john@example.com",
      "phone_number": "+1234567890",
      "dob": "1990-05-15",
      "city": "Los Angeles",
      "state": "California",
      "status": "Pending",
      "created_at": "2025-11-01T08:00:00Z",
      "days_pending": 3,
      "user": {
        "username": "johndoe",
        "email": "johndoe@example.com"
      },
      "form_url": "/api/requests/api/25/admin-report-form/"
    }
  ]
}
```

---

## Endpoint 2: Get Report Form Data (Admin)

**URL:** `GET /api/requests/api/{request_id}/admin-report-form/`  
**Permission:** Admin only  
**Purpose:** Get request details and existing report data (if any) for the admin form

### Request
```http
GET /api/requests/api/25/admin-report-form/
Authorization: Bearer <admin_token>
```

### Response
```json
{
  "success": true,
  "request": {
    "id": 25,
    "name": "John Michael Doe",
    "dob": "1990-05-15",
    "email": "john@example.com",
    "phone_number": "+1234567890",
    "city": "Los Angeles",
    "state": "California",
    "status": "Pending",
    "created_at": "2025-11-01T08:00:00Z",
    "user": {
      "id": 5,
      "username": "johndoe",
      "email": "johndoe@example.com"
    }
  },
  "existing_report": null,
  "has_report": false,
  "form_sections": {
    "identity_verification": [
      "ssn_validation",
      "address_history",
      "identity_cross_reference",
      "database_match"
    ],
    "criminal_history": [
      "federal_criminal_records",
      "state_criminal_records",
      "state_searched",
      "county_criminal_records",
      "county_searched",
      "adult_offender_registry"
    ],
    "address_history": [
      "address_history_details"
    ],
    "education_verification": [
      "education_verified",
      "education_degree",
      "education_institution",
      "education_graduation_year",
      "education_status"
    ],
    "employment_verification": [
      "employment_verified",
      "employment_details"
    ],
    "final_summary": [
      "final_summary",
      "recommendation",
      "verification_status"
    ]
  }
}
```

---

## Endpoint 3: Submit Report Form (Admin)

**URL:** `POST /api/requests/api/{request_id}/submit-report/`  
**Permission:** Admin only  
**Purpose:** Submit complete background check report after manual verification

### Request
```http
POST /api/requests/api/25/submit-report/
Authorization: Bearer <admin_token>
Content-Type: application/json
```

### Request Body (All Fields)
```json
{
  "pdf": null,
  "notes": "Background check completed successfully",
  
  "ssn_validation": "Verified",
  "address_history": "Clear",
  "identity_cross_reference": "Clear",
  "database_match": "Verified",
  
  "federal_criminal_records": "No records found",
  "state_criminal_records": "Clear",
  "state_searched": "California, Nevada",
  "county_criminal_records": "Clear",
  "county_searched": "Los Angeles County, Orange County",
  "adult_offender_registry": "No match found",
  
  "address_history_details": "All addresses verified and confirmed",
  
  "education_verified": true,
  "education_degree": "Bachelor of Science in Computer Science",
  "education_institution": "University of California Los Angeles",
  "education_graduation_year": "2012",
  "education_status": "Confirmed by Registrar",
  
  "employment_verified": false,
  "employment_details": "",
  
  "final_summary": "Candidate has successfully passed all background checks with no adverse findings. All verifications completed without issues.",
  "recommendation": "Approved for employment consideration",
  "verification_status": "clear"
}
```

### Request Body (Minimal Required Fields)
```json
{
  "ssn_validation": "Verified",
  "address_history": "Clear",
  "identity_cross_reference": "Clear",
  "database_match": "Verified",
  "verification_status": "clear"
}
```

### Response (Success)
```json
{
  "success": true,
  "message": "Background check report submitted successfully",
  "report_id": 8,
  "request_status": "Completed",
  "report": {
    "id": 8,
    "request": 25,
    "pdf": null,
    "notes": "Background check completed successfully",
    "ssn_validation": "Verified",
    "address_history": "Clear",
    "identity_cross_reference": "Clear",
    "database_match": "Verified",
    "federal_criminal_records": "No records found",
    "state_criminal_records": "Clear",
    "state_searched": "California, Nevada",
    "county_criminal_records": "Clear",
    "county_searched": "Los Angeles County, Orange County",
    "adult_offender_registry": "No match found",
    "address_history_details": "All addresses verified and confirmed",
    "education_verified": true,
    "education_degree": "Bachelor of Science in Computer Science",
    "education_institution": "University of California Los Angeles",
    "education_graduation_year": "2012",
    "education_status": "Confirmed by Registrar",
    "employment_verified": false,
    "employment_details": "",
    "final_summary": "Candidate has successfully passed all background checks with no adverse findings.",
    "recommendation": "Approved for employment consideration",
    "verification_status": "clear"
  }
}
```

### Response (Validation Error)
```json
{
  "success": false,
  "errors": {
    "education_degree": [
      "Education degree and institution are required when education is verified"
    ]
  }
}
```

---

## Endpoint 4: Update Existing Report (Admin)

**URL:** `PUT /api/requests/api/{request_id}/submit-report/`  
**Permission:** Admin only  
**Purpose:** Update an existing report (partial updates allowed)

### Request
```http
PUT /api/requests/api/25/submit-report/
Authorization: Bearer <admin_token>
Content-Type: application/json
```

### Request Body (Partial Update)
```json
{
  "notes": "Updated after additional verification",
  "final_summary": "Candidate cleared all checks after secondary verification",
  "recommendation": "Strongly approved"
}
```

### Response
Same as POST response with status 200 OK

---

## Endpoint 5: View Completed Report (Client)

**URL:** `GET /api/requests/api/{request_id}/view-report/`  
**Permission:** Report owner or admin  
**Purpose:** Client views their completed background check report

### Request
```http
GET /api/requests/api/25/view-report/
Authorization: Bearer <user_token>
```

### Response
```json
{
  "success": true,
  "report_header": {
    "title": "Comprehensive Background Check Report",
    "report_id": 8,
    "generated_at": "2025-11-04T10:30:00Z",
    "verification_status": "clear",
    "status_label": "Verification Complete"
  },
  "subject_information": {
    "full_name": "John Michael Doe",
    "date_of_birth": "1990-05-15",
    "email": "john@example.com",
    "phone": "+1234567890",
    "location": "Los Angeles, California",
    "city": "Los Angeles",
    "state": "California"
  },
  "identity_verification": {
    "section_title": "Identity Verification",
    "status": "verified",
    "checks": {
      "ssn_validation": {
        "label": "Social Security Number Validation",
        "status": "Verified",
        "icon": "verified"
      },
      "address_history": {
        "label": "Address History",
        "status": "Clear",
        "icon": "verified"
      },
      "identity_cross_reference": {
        "label": "Identity Cross-Reference",
        "status": "Clear",
        "icon": "clear"
      },
      "database_match": {
        "label": "Database Match",
        "status": "Verified",
        "icon": "verified"
      }
    }
  },
  "criminal_history_check": {
    "section_title": "Criminal History Check",
    "status": "clear",
    "checks": {
      "federal_criminal_records": {
        "label": "Federal Criminal Records Search",
        "status": "No records found",
        "details": "No records found"
      },
      "state_criminal_records": {
        "label": "State Criminal Records Search",
        "status": "Clear",
        "searched": "California, Nevada",
        "details": "Searched: California, Nevada - Clear"
      },
      "county_criminal_records": {
        "label": "County Criminal Records Search",
        "status": "Clear",
        "searched": "Los Angeles County, Orange County",
        "details": "Searched: Los Angeles County, Orange County - Clear"
      },
      "sex_offender_registry": {
        "label": "National Sex Offender Registry",
        "status": "No match found",
        "details": "No match found"
      }
    }
  },
  "education_verification": {
    "section_title": "Education Verification",
    "status": "verified",
    "verified": true,
    "details": {
      "degree": "Bachelor of Science in Computer Science",
      "institution": "University of California Los Angeles",
      "graduation_year": "2012",
      "status": "Confirmed by Registrar"
    }
  },
  "final_summary": {
    "section_title": "Final Summary & Recommendation",
    "summary_points": [
      "Has successfully passed all required checks with no adverse findings.",
      "No criminal records found at federal, state, or county levels",
      "Credit standing is good with no negative marks",
      "Professional references provided positive feedback"
    ],
    "detailed_summary": "Candidate has successfully passed all background checks with no adverse findings.",
    "recommendation": "Approved for employment consideration",
    "overall_status": "clear"
  }
}
```

---

## Field Definitions

### Identity Verification Fields
- `ssn_validation`: SSN validation result (e.g., "Verified", "Invalid", "Not Found")
- `address_history`: Address history verification status
- `identity_cross_reference`: Cross-reference verification result
- `database_match`: Database matching result

### Criminal History Fields
- `federal_criminal_records`: Federal criminal records search result (text)
- `state_criminal_records`: State criminal records search result (text)
- `state_searched`: States searched (comma-separated)
- `county_criminal_records`: County criminal records search result (text)
- `county_searched`: Counties searched (comma-separated)
- `adult_offender_registry`: Sex offender registry check result (text)

### Address History Fields
- `address_history_details`: Detailed address history information (text)

### Education Verification Fields
- `education_verified`: Boolean (true/false)
- `education_degree`: Degree obtained (required if verified)
- `education_institution`: Institution name (required if verified)
- `education_graduation_year`: Year of graduation (4 digits)
- `education_status`: Verification status details

### Employment Verification Fields
- `employment_verified`: Boolean (true/false)
- `employment_details`: Employment verification details (text)

### Final Summary Fields
- `final_summary`: Comprehensive summary of all checks (text)
- `recommendation`: Final recommendation (text)
- `verification_status`: Overall status - choices:
  - `"verified"` - Verification completed
  - `"clear"` - All checks passed
  - `"pending_review"` - Requires review
  - `"flagged"` - Issues found

---

## Complete Workflow Example

### Step 1: Admin Gets Pending Requests
```bash
GET /api/requests/api/pending-reports/
Authorization: Bearer <admin_token>
```

### Step 2: Admin Opens Form for Specific Request
```bash
GET /api/requests/api/25/admin-report-form/
Authorization: Bearer <admin_token>
```

### Step 3: Admin Fills Out and Submits Form
```bash
POST /api/requests/api/25/submit-report/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "ssn_validation": "Verified",
  "address_history": "Clear",
  "identity_cross_reference": "Clear",
  "database_match": "Verified",
  "federal_criminal_records": "No records found",
  "state_criminal_records": "Clear",
  "state_searched": "California",
  "county_criminal_records": "Clear",
  "county_searched": "Los Angeles County",
  "adult_offender_registry": "No match found",
  "address_history_details": "All addresses verified",
  "education_verified": true,
  "education_degree": "Bachelor of Science",
  "education_institution": "UCLA",
  "education_graduation_year": "2012",
  "education_status": "Confirmed",
  "final_summary": "All checks passed",
  "recommendation": "Approved",
  "verification_status": "clear"
}
```

### Step 4: Request Status Automatically Changes to "Completed"

### Step 5: Client Views Report
```bash
GET /api/requests/api/25/view-report/
Authorization: Bearer <user_token>
```

---

## Error Responses

### 404 - Request Not Found
```json
{
  "error": "Request not found"
}
```

### 400 - Validation Error
```json
{
  "success": false,
  "errors": {
    "education_degree": ["This field is required when education is verified"],
    "verification_status": ["This field is required"]
  }
}
```

### 403 - Permission Denied
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## Testing with cURL

### Get Pending Reports
```bash
curl -X GET "http://127.0.0.1:8000/api/requests/api/pending-reports/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Get Report Form
```bash
curl -X GET "http://127.0.0.1:8000/api/requests/api/25/admin-report-form/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Submit Report
```bash
curl -X POST "http://127.0.0.1:8000/api/requests/api/25/submit-report/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ssn_validation": "Verified",
    "address_history": "Clear",
    "identity_cross_reference": "Clear",
    "database_match": "Verified",
    "verification_status": "clear"
  }'
```

---

## Summary

All endpoints are now available:

1. GET `/api/requests/api/pending-reports/` - List pending reports (Admin)
2. GET `/api/requests/api/{id}/admin-report-form/` - Get form data (Admin)
3. POST `/api/requests/api/{id}/submit-report/` - Submit new report (Admin)
4. PUT `/api/requests/api/{id}/submit-report/` - Update report (Admin)
5. GET `/api/requests/api/{id}/view-report/` - View report (Client/Admin)

The system automatically updates request status to "Completed" when a report is submitted.
