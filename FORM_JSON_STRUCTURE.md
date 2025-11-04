# Admin Report Form - Complete JSON Structure

## Full Form Submission Example

```json
{
  "notes": "Background check completed after manual verification",
  
  "ssn_validation": "Verified",
  "address_history": "Clear",
  "identity_cross_reference": "Clear",
  "database_match": "Verified",
  
  "federal_criminal_records": "No records found in federal databases",
  "state_criminal_records": "No records found",
  "state_searched": "California, Nevada",
  "county_criminal_records": "No records found",
  "county_searched": "Los Angeles County, Orange County",
  "adult_offender_registry": "No matches found in registry",
  
  "address_history_details": "All address history has been verified and confirmed. Subject has maintained consistent residence records.",
  
  "education_verified": true,
  "education_degree": "Bachelor of Science in Computer Science",
  "education_institution": "University of California Los Angeles",
  "education_graduation_year": "2012",
  "education_status": "Confirmed by Registrar",
  
  "employment_verified": false,
  "employment_details": "",
  
  "final_summary": "Candidate has successfully passed all background checks with no adverse findings. All verifications completed without issues.",
  "recommendation": "Approved for employment consideration. No flags or concerns identified.",
  "verification_status": "clear"
}
```

## Minimal Required Fields

```json
{
  "ssn_validation": "Verified",
  "address_history": "Clear",
  "identity_cross_reference": "Clear",
  "database_match": "Verified",
  "verification_status": "clear"
}
```

## Field Value Examples

### Identity Verification
```json
{
  "ssn_validation": "Verified" | "Invalid" | "Not Found",
  "address_history": "Clear" | "Verified" | "Discrepancies Found",
  "identity_cross_reference": "Clear" | "Match Found" | "No Issues",
  "database_match": "Verified" | "No Match" | "Partial Match"
}
```

### Criminal History
```json
{
  "federal_criminal_records": "No records found in federal databases",
  "state_criminal_records": "No records found",
  "state_searched": "California, Nevada, Arizona",
  "county_criminal_records": "No records found",
  "county_searched": "Los Angeles County, Orange County",
  "adult_offender_registry": "No matches found in registry"
}
```

### Address History
```json
{
  "address_history_details": "All address history has been verified and confirmed. Subject has maintained consistent residence records over the past 10 years."
}
```

### Education Verification (When Verified)
```json
{
  "education_verified": true,
  "education_degree": "Bachelor of Science in Computer Science",
  "education_institution": "University of California Los Angeles",
  "education_graduation_year": "2012",
  "education_status": "Confirmed by Registrar"
}
```

### Education Verification (When Not Verified)
```json
{
  "education_verified": false,
  "education_degree": "",
  "education_institution": "",
  "education_graduation_year": "",
  "education_status": ""
}
```

### Employment Verification (When Verified)
```json
{
  "employment_verified": true,
  "employment_details": "Current employer: Tech Corp Inc. Position: Senior Software Engineer. Employment verified with HR department. Employment dates: January 2015 - Present"
}
```

### Employment Verification (When Not Verified)
```json
{
  "employment_verified": false,
  "employment_details": ""
}
```

### Final Summary
```json
{
  "final_summary": "Candidate has successfully passed all background checks with no adverse findings. Identity verification confirmed all personal information. Criminal history searches across federal, state, and county levels returned clear results. Education history verified and confirmed. No adverse findings or concerns were identified.",
  "recommendation": "Approved for employment consideration. Candidate has cleared all background checks with no flags or concerns.",
  "verification_status": "clear"
}
```

### Verification Status Options
```json
{
  "verification_status": "clear"      // All checks passed, no issues
  "verification_status": "verified"   // Verification completed successfully
  "verification_status": "pending_review"  // Requires additional review
  "verification_status": "flagged"    // Issues found requiring attention
}
```

## Common Form Patterns

### Pattern 1: Clean Background
```json
{
  "ssn_validation": "Verified",
  "address_history": "Clear",
  "identity_cross_reference": "Clear",
  "database_match": "Verified",
  "federal_criminal_records": "No records found",
  "state_criminal_records": "Clear",
  "county_criminal_records": "Clear",
  "adult_offender_registry": "No match found",
  "verification_status": "clear"
}
```

### Pattern 2: With Education
```json
{
  "ssn_validation": "Verified",
  "address_history": "Clear",
  "identity_cross_reference": "Clear",
  "database_match": "Verified",
  "education_verified": true,
  "education_degree": "Bachelor of Arts",
  "education_institution": "State University",
  "education_graduation_year": "2015",
  "education_status": "Confirmed",
  "verification_status": "clear"
}
```

### Pattern 3: Pending Review
```json
{
  "ssn_validation": "Verified",
  "address_history": "Discrepancies Found",
  "identity_cross_reference": "Needs Verification",
  "database_match": "Partial Match",
  "final_summary": "Some discrepancies found in address history requiring additional verification",
  "recommendation": "Recommend additional verification before final decision",
  "verification_status": "pending_review"
}
```

### Pattern 4: Issues Found
```json
{
  "ssn_validation": "Verified",
  "address_history": "Clear",
  "identity_cross_reference": "Clear",
  "database_match": "Verified",
  "federal_criminal_records": "Record found - misdemeanor 2018",
  "state_criminal_records": "Record found",
  "final_summary": "Criminal record found requiring review",
  "recommendation": "Review criminal history before proceeding",
  "verification_status": "flagged"
}
```

## Frontend Form Field Mapping

```javascript
// Map form fields to JSON
const formData = {
  // From Identity Verification section
  ssn_validation: document.getElementById('ssn_validation').value,
  address_history: document.getElementById('address_history').value,
  identity_cross_reference: document.getElementById('identity_cross_reference').value,
  database_match: document.getElementById('database_match').value,
  
  // From Criminal History section
  federal_criminal_records: document.getElementById('federal_criminal_records').value,
  state_criminal_records: document.getElementById('state_criminal_records').value,
  state_searched: document.getElementById('state_searched').value,
  county_criminal_records: document.getElementById('county_criminal_records').value,
  county_searched: document.getElementById('county_searched').value,
  adult_offender_registry: document.getElementById('adult_offender_registry').value,
  
  // From Address History section
  address_history_details: document.getElementById('address_history_details').value,
  
  // From Education section
  education_verified: document.getElementById('education_verified').checked,
  education_degree: document.getElementById('education_degree').value,
  education_institution: document.getElementById('education_institution').value,
  education_graduation_year: document.getElementById('education_graduation_year').value,
  education_status: document.getElementById('education_status').value,
  
  // From Employment section
  employment_verified: document.getElementById('employment_verified').checked,
  employment_details: document.getElementById('employment_details').value,
  
  // From Final Summary section
  final_summary: document.getElementById('final_summary').value,
  recommendation: document.getElementById('recommendation').value,
  verification_status: document.getElementById('verification_status').value
};
```

## Validation Rules

1. Required Fields:
   - ssn_validation
   - address_history
   - identity_cross_reference
   - database_match
   - verification_status

2. Conditional Required:
   - If education_verified = true:
     - education_degree (required)
     - education_institution (required)

3. Optional Fields:
   - All other fields can be empty/null

4. Field Types:
   - Boolean: education_verified, employment_verified
   - Text: All other fields

## Response After Submission

```json
{
  "success": true,
  "message": "Background check report submitted successfully",
  "report_id": 8,
  "request_status": "Completed",
  "report": {
    "id": 8,
    "request": 25,
    "all_form_fields": "..."
  }
}
```

## Error Response

```json
{
  "success": false,
  "errors": {
    "verification_status": ["This field is required"],
    "education_degree": ["Education degree and institution are required when education is verified"]
  }
}
```
