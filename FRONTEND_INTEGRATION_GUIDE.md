# Frontend Integration - Quick Start Guide

## Endpoint Overview

**URL:** `GET /api/requests/{id}/view-report/`  
**Purpose:** Fetch comprehensive background check report details  
**Authentication:** Required (JWT Bearer Token)

## Quick Start

### 1. Basic Request
```javascript
const API_BASE_URL = 'http://127.0.0.1:8000'; // or 'https://h2o427-backend-u9bx.onrender.com'

const getReportDetails = async (requestId, accessToken) => {
  const response = await fetch(
    `${API_BASE_URL}/api/requests/${requestId}/view-report/`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  return await response.json();
};
```

### 2. React Component Example
```jsx
import React, { useState, useEffect } from 'react';

const BackgroundCheckReport = ({ requestId, accessToken }) => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchReport();
  }, [requestId]);

  const fetchReport = async () => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/requests/${requestId}/view-report/`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch report');
      }

      const data = await response.json();
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading report...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!report) return <div>No report available</div>;

  return (
    <div className="report-container">
      {/* Header Section */}
      <header className="report-header">
        <h1>{report.report_header.title}</h1>
        <div className={`status-badge ${report.report_header.verification_status}`}>
          {report.report_header.status_label}
        </div>
        <p>Report ID: {report.report_header.report_id}</p>
        <p>Generated: {new Date(report.report_header.generated_at).toLocaleDateString()}</p>
      </header>

      {/* Subject Information */}
      <section className="subject-info">
        <h2>Subject Information</h2>
        <div className="info-grid">
          <div>
            <label>Full Name:</label>
            <span>{report.subject_information.full_name}</span>
          </div>
          <div>
            <label>Date of Birth:</label>
            <span>{report.subject_information.date_of_birth}</span>
          </div>
          <div>
            <label>Email:</label>
            <span>{report.subject_information.email}</span>
          </div>
          <div>
            <label>Phone:</label>
            <span>{report.subject_information.phone}</span>
          </div>
          <div>
            <label>Location:</label>
            <span>{report.subject_information.location}</span>
          </div>
        </div>
      </section>

      {/* Verification Status */}
      <section className="verification-status">
        <div className="status-message">
          ✓ {report.verification_complete.message}
        </div>
      </section>

      {/* Identity Verification */}
      <section className="identity-verification">
        <h2>{report.identity_verification.section_title}</h2>
        <div className="checks-list">
          {Object.entries(report.identity_verification.checks).map(([key, check]) => (
            <div key={key} className="check-item">
              <span className={`icon icon-${check.icon}`}>✓</span>
              <div>
                <strong>{check.label}</strong>
                <span className="status">{check.status}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Address History Check */}
      <section className="address-history">
        <h2>{report.address_history_check.section_title}</h2>
        <div className="checks-list">
          {Object.entries(report.address_history_check.checks).map(([key, check]) => (
            <div key={key} className="check-item">
              <strong>{check.label}:</strong> {check.status}
            </div>
          ))}
        </div>
        <p className="details">{report.address_history_check.details}</p>
      </section>

      {/* Criminal History Check */}
      <section className="criminal-history">
        <h2>{report.criminal_history_check.section_title}</h2>
        <div className="checks-list">
          {Object.entries(report.criminal_history_check.checks).map(([key, check]) => (
            <div key={key} className="check-item">
              <h3>{check.label}</h3>
              <p>{check.details}</p>
              {check.searched && <p className="searched">Searched: {check.searched}</p>}
            </div>
          ))}
        </div>
      </section>

      {/* Education Verification */}
      {report.education_verification.verified && (
        <section className="education-verification">
          <h2>{report.education_verification.section_title}</h2>
          <div className="education-details">
            <p><strong>Degree:</strong> {report.education_verification.details.degree}</p>
            <p><strong>Institution:</strong> {report.education_verification.details.institution}</p>
            <p><strong>Graduation Year:</strong> {report.education_verification.details.graduation_year}</p>
            <p><strong>Status:</strong> {report.education_verification.details.status}</p>
          </div>
        </section>
      )}

      {/* Employment Verification */}
      {report.employment_verification.verified && (
        <section className="employment-verification">
          <h2>{report.employment_verification.section_title}</h2>
          <p>{report.employment_verification.details}</p>
        </section>
      )}

      {/* Final Summary */}
      <section className="final-summary">
        <h2>{report.final_summary.section_title}</h2>
        <ul className="summary-points">
          {report.final_summary.summary_points.map((point, index) => (
            <li key={index}>{point}</li>
          ))}
        </ul>
        {report.final_summary.detailed_summary && (
          <p className="detailed-summary">{report.final_summary.detailed_summary}</p>
        )}
        <div className="recommendation">
          <h3>Recommendation:</h3>
          <p>{report.final_summary.recommendation}</p>
        </div>
        <div className={`overall-status ${report.final_summary.overall_status}`}>
          Overall Status: {report.final_summary.overall_status.toUpperCase()}
        </div>
      </section>

      {/* Download Section */}
      {report.download.available && (
        <section className="download-section">
          <h3>Download Full Report</h3>
          <a 
            href={`http://127.0.0.1:8000${report.download.pdf_url}`}
            download={report.download.filename}
            className="download-button"
          >
            📄 Download PDF Report ({report.download.file_size})
          </a>
          <p className="note">{report.download.note}</p>
        </section>
      )}

      {/* Admin Notes */}
      {report.admin_notes && (
        <section className="admin-notes">
          <h3>Administrator Notes</h3>
          <p>{report.admin_notes}</p>
        </section>
      )}

      {/* Metadata Footer */}
      <footer className="report-metadata">
        <p>Request ID: {report.metadata.request_id}</p>
        <p>Submitted: {new Date(report.metadata.submitted_date).toLocaleDateString()}</p>
        <p>Completed: {new Date(report.metadata.completed_date).toLocaleDateString()}</p>
        <p>Requestor: {report.metadata.requestor.username} ({report.metadata.requestor.email})</p>
      </footer>
    </div>
  );
};

export default BackgroundCheckReport;
```

### 3. Basic Styling (CSS)
```css
.report-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.report-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px;
  border-radius: 10px;
  margin-bottom: 30px;
}

.report-header h1 {
  margin: 0 0 10px 0;
}

.status-badge {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 14px;
  margin: 10px 0;
}

.status-badge.clear {
  background-color: #4CAF50;
}

.status-badge.verified {
  background-color: #2196F3;
}

.status-badge.pending_review {
  background-color: #FFC107;
  color: #333;
}

.status-badge.flagged {
  background-color: #F44336;
}

section {
  background: white;
  padding: 25px;
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

section h2 {
  color: #333;
  border-bottom: 2px solid #667eea;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.info-grid > div {
  display: flex;
  flex-direction: column;
}

.info-grid label {
  font-weight: bold;
  color: #666;
  font-size: 14px;
  margin-bottom: 5px;
}

.info-grid span {
  color: #333;
  font-size: 16px;
}

.verification-status {
  background-color: #e8f5e9;
  border-left: 4px solid #4CAF50;
}

.status-message {
  font-size: 18px;
  color: #2e7d32;
  font-weight: 500;
}

.checks-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.check-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 5px;
}

.check-item .icon {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.icon-verified {
  background-color: #4CAF50;
  color: white;
}

.icon-clear {
  background-color: #2196F3;
  color: white;
}

.check-item strong {
  display: block;
  color: #333;
  margin-bottom: 5px;
}

.check-item .status {
  color: #666;
  font-size: 14px;
}

.summary-points {
  list-style-type: none;
  padding: 0;
}

.summary-points li {
  padding: 10px;
  margin-bottom: 10px;
  background-color: #f8f9fa;
  border-left: 3px solid #667eea;
  padding-left: 20px;
}

.recommendation {
  background-color: #e3f2fd;
  padding: 20px;
  border-radius: 5px;
  margin-top: 20px;
}

.recommendation h3 {
  margin-top: 0;
  color: #1976d2;
}

.overall-status {
  text-align: center;
  padding: 15px;
  border-radius: 5px;
  margin-top: 20px;
  font-weight: bold;
  font-size: 18px;
}

.overall-status.clear {
  background-color: #c8e6c9;
  color: #2e7d32;
}

.overall-status.verified {
  background-color: #bbdefb;
  color: #1565c0;
}

.download-button {
  display: inline-block;
  padding: 15px 30px;
  background-color: #667eea;
  color: white;
  text-decoration: none;
  border-radius: 5px;
  font-weight: bold;
  transition: background-color 0.3s;
}

.download-button:hover {
  background-color: #5568d3;
}

.download-section .note {
  color: #666;
  font-style: italic;
  margin-top: 10px;
}

.admin-notes {
  background-color: #fff3e0;
  border-left: 4px solid #ff9800;
}

.report-metadata {
  background-color: #f5f5f5;
  padding: 20px;
  border-radius: 5px;
  font-size: 14px;
  color: #666;
}

.report-metadata p {
  margin: 5px 0;
}
```

## Key Response Fields to Use

### For Status Badges
```javascript
report.report_header.verification_status // 'clear', 'verified', 'pending_review', 'flagged'
report.report_header.status_label       // Human-readable label
```

### For Subject Display
```javascript
report.subject_information.full_name
report.subject_information.location  // "City, State"
report.subject_information.email
report.subject_information.phone
```

### For Verification Sections
```javascript
// Identity checks
report.identity_verification.checks.ssn_validation.status
report.identity_verification.checks.address_history.status
report.identity_verification.checks.identity_cross_reference.status
report.identity_verification.checks.database_match.status

// Criminal history
report.criminal_history_check.checks.federal_criminal_records.status
report.criminal_history_check.checks.state_criminal_records.details
report.criminal_history_check.checks.county_criminal_records.searched
report.criminal_history_check.checks.sex_offender_registry.status
```

### For Education/Employment
```javascript
// Check if verified first
if (report.education_verification.verified) {
  report.education_verification.details.degree
  report.education_verification.details.institution
  report.education_verification.details.graduation_year
}

if (report.employment_verification.verified) {
  report.employment_verification.details
}
```

### For Summary
```javascript
report.final_summary.summary_points         // Array of bullet points
report.final_summary.detailed_summary       // Full text summary
report.final_summary.recommendation         // Final recommendation
report.final_summary.overall_status         // Overall status value
```

### For Download
```javascript
if (report.download.available) {
  const pdfUrl = `${API_BASE_URL}${report.download.pdf_url}`;
  const filename = report.download.filename;
  const fileSize = report.download.file_size;
}
```

## Error Handling

```javascript
try {
  const response = await fetch(url, options);
  
  if (response.status === 404) {
    // Report not found or not ready yet
    setError('Background check report is not available yet');
  } else if (response.status === 403) {
    // Permission denied
    setError('You do not have permission to view this report');
  } else if (!response.ok) {
    setError('Failed to load report');
  } else {
    const data = await response.json();
    setReport(data);
  }
} catch (error) {
  setError('Network error: ' + error.message);
}
```

## Testing the Endpoint

### 1. Get an Access Token
First, login to get your token:
```bash
POST http://127.0.0.1:8000/api/authentication/login/
{
  "username": "your_username",
  "password": "your_password"
}
```

### 2. Use the Token to Fetch Report
```bash
GET http://127.0.0.1:8000/api/requests/1/view-report/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 3. Or use Swagger UI
Navigate to: http://127.0.0.1:8000/swagger/
- Find `GET /api/requests/{id}/view-report/`
- Click "Try it out"
- Enter request ID
- Click "Authorize" and add token
- Click "Execute"

## Common Issues

### Issue: 404 - Report not found
**Solution:** Ensure the background check status is "Completed" and a Report has been created by admin

### Issue: 403 - Permission denied
**Solution:** Make sure the authenticated user owns the request or is staff

### Issue: PDF not downloading
**Solution:** Use the full URL: `${API_BASE_URL}${report.download.pdf_url}`

### Issue: Empty verification fields
**Solution:** Admin needs to populate Report fields in Django admin panel before report is viewable

## Next Steps

1. ✅ Copy the React component code
2. ✅ Copy the CSS styling
3. ✅ Update API_BASE_URL to your backend URL
4. ✅ Implement authentication to get access token
5. ✅ Pass requestId and accessToken as props
6. ✅ Test with a completed background check

## Support

For questions or issues:
- Check Swagger documentation at `/swagger/`
- Review full API documentation in `COMPREHENSIVE_REPORT_API.md`
- Contact backend development team

---
**Quick Start Guide v1.0** | Last Updated: January 2024
