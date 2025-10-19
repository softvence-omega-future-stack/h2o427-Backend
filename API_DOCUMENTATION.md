# Background Check App - API Documentation

## Overview
This is a simplified background check application where clients can submit background check requests and admins can manage them through a dashboard.

## Authentication
The API uses JWT (JSON Web Tokens) for authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Base URL
```
http://127.0.0.1:8000/api/
```

## API Endpoints

### Authentication Endpoints

#### 1. Register User
- **URL:** `POST /api/auth/register/`
- **Permission:** Allow Any
- **Description:** Register a new user account
- **Request Body:**
```json
{
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
}
```
- **Response:**
```json
{
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_staff": false
    },
    "tokens": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
}
```

#### 2. Login User
- **URL:** `POST /api/auth/login/`
- **Permission:** Allow Any
- **Description:** Login user and get JWT tokens
- **Request Body:**
```json
{
    "username": "johndoe",
    "password": "securepassword123"
}
```
- **Response:**
```json
{
    "message": "Login successful",
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_staff": false
    },
    "tokens": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
}
```

#### 3. User Profile
- **URL:** `GET /api/auth/profile/`
- **Permission:** Authenticated Users
- **Description:** Get current user profile
- **Response:**
```json
{
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_staff": false
}
```

- **URL:** `PUT /api/auth/profile/`
- **Permission:** Authenticated Users
- **Description:** Update current user profile
- **Request Body:**
```json
{
    "email": "newemail@example.com",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Client Request Endpoints

#### 4. Submit Background Check Request
- **URL:** `POST /api/requests/`
- **Permission:** Authenticated Users
- **Description:** Submit a new background check request
- **Request Body:**
```json
{
    "name": "John Doe",
    "dob": "1990-01-15",
    "city": "New York",
    "state": "NY",
    "email": "john@example.com",
    "phone_number": "+1234567890"
}
```
- **Response:**
```json
{
    "id": 1,
    "user": 1,
    "user_name": "johndoe",
    "name": "John Doe",
    "dob": "1990-01-15",
    "city": "New York",
    "state": "NY",
    "email": "john@example.com",
    "phone_number": "+1234567890",
    "status": "Pending",
    "created_at": "2025-10-19T10:30:00Z",
    "updated_at": "2025-10-19T10:30:00Z"
}
```

#### 5. List User's Requests
- **URL:** `GET /api/requests/`
- **Permission:** Authenticated Users
- **Description:** Get all requests for the authenticated user (clients see only their own, admins see all)
- **Response:**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": 1,
            "user_name": "johndoe",
            "name": "John Doe",
            "dob": "1990-01-15",
            "city": "New York",
            "state": "NY",
            "email": "john@example.com",
            "phone_number": "+1234567890",
            "status": "Completed",
            "created_at": "2025-10-19T10:30:00Z",
            "updated_at": "2025-10-19T11:30:00Z"
        }
    ]
}
```

#### 6. Get Request Details
- **URL:** `GET /api/requests/{id}/`
- **Permission:** Authenticated Users
- **Description:** Get details of a specific request
- **Response:** Same as individual request object above

#### 7. Download Report
- **URL:** `GET /api/requests/{id}/download_report/`
- **Permission:** Authenticated Users
- **Description:** Download the background check report for a completed request
- **Response:**
```json
{
    "report_url": "http://127.0.0.1:8000/media/reports/report_123.pdf",
    "generated_at": "2025-10-19T11:30:00Z",
    "notes": "Background check completed successfully"
}
```

### Admin Dashboard Endpoints

#### 8. Admin - Get All Requests
- **URL:** `GET /api/admin/requests/`
- **Permission:** Admin Users Only
- **Description:** Get all background check requests for admin dashboard
- **Response:** Same format as request list above, but includes all users' requests

#### 9. Admin - Update Request Status
- **URL:** `PATCH /api/admin/requests/{request_id}/status/`
- **Permission:** Admin Users Only
- **Description:** Update the status of a background check request
- **Request Body:**
```json
{
    "status": "In Progress"
}
```
- **Response:**
```json
{
    "message": "Status updated successfully",
    "request": {
        "id": 1,
        "user": 1,
        "user_name": "johndoe",
        "name": "John Doe",
        "status": "In Progress",
        "updated_at": "2025-10-19T12:00:00Z"
    }
}
```

#### 10. Admin - Upload Report
- **URL:** `POST /api/admin/reports/`
- **Permission:** Admin Users Only
- **Description:** Upload a PDF report for a background check request
- **Request Body:** (multipart/form-data)
```
request_id: 1
pdf: <PDF file>
notes: "Background check completed successfully"
```
- **Response:**
```json
{
    "message": "Report uploaded successfully",
    "report": {
        "id": 1,
        "request": 1,
        "request_name": "John Doe",
        "pdf": "/media/reports/report_123.pdf",
        "generated_at": "2025-10-19T12:30:00Z",
        "notes": "Background check completed successfully"
    }
}
```

#### 11. Admin - Get All Reports
- **URL:** `GET /api/admin/reports/`
- **Permission:** Admin Users Only
- **Description:** Get all reports for admin dashboard
- **Response:**
```json
[
    {
        "id": 1,
        "request": 1,
        "request_name": "John Doe",
        "pdf": "/media/reports/report_123.pdf",
        "generated_at": "2025-10-19T12:30:00Z",
        "notes": "Background check completed successfully"
    }
]
```

## Status Values
- **Pending:** Initial status when request is submitted
- **In Progress:** Admin has started working on the request
- **Completed:** Background check is finished and report is available

## Error Responses
All endpoints return appropriate HTTP status codes and error messages:

```json
{
    "error": "Error message description"
}
```

Common status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

## Admin Credentials
- **Username:** admin
- **Password:** admin123

## Testing the API
You can test the API using tools like Postman, curl, or any HTTP client. Make sure to:
1. Register a user or login to get tokens
2. Include the access token in the Authorization header for protected endpoints
3. Use the admin credentials to test admin-only endpoints

## Example Workflow
1. Client registers/logs in → gets JWT tokens
2. Client submits background check request → gets request ID
3. Admin logs in → sees all requests in dashboard
4. Admin updates request status to "In Progress"
5. Admin uploads PDF report → request status automatically becomes "Completed"
6. Client can now download the report using the download endpoint