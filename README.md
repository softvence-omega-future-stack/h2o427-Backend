# Background Check Application

A simplified Django REST API application for managing background check requests.

## Features

### Client Side
- User registration and authentication
- Submit background check requests with personal information
- Track request status (Pending, In Progress, Completed)
- Download completed background check reports

### Admin Side
- Admin dashboard to view all requests
- Update request status
- Upload PDF reports
- Manage all background check operations

## Technology Stack
- **Backend:** Django 5.2.7
- **API:** Django REST Framework 3.15.2
- **Authentication:** JWT (Simple JWT)
- **Database:** SQLite (development)
- **File Handling:** Django FileField for PDF uploads

## Quick Start

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

3. **Create Superuser (if needed):**
   ```bash
   python manage.py createsuperuser
   ```

4. **Start Development Server:**
   ```bash
   python manage.py runserver
   ```

5. **Access the API:**
   - API Base URL: `http://127.0.0.1:8000/api/`
   - Admin Panel: `http://127.0.0.1:8000/admin/`

## Default Admin Credentials
- **Username:** admin
- **Password:** admin123

## API Documentation
See `API_DOCUMENTATION.md` for detailed API endpoints and usage examples.

## Project Structure
```
background_check/
├── manage.py
├── requirements.txt
├── API_DOCUMENTATION.md
├── background_check/          # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── authentication/            # User authentication app
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── requests/                  # Background check requests app
│   ├── models.py             # Request and Report models
│   ├── views.py              # API views
│   ├── serializers.py        # Data serializers
│   └── urls.py
└── admin_dashboard/           # Admin-specific functionality
    ├── views.py              # Admin dashboard views
    ├── serializers.py
    └── urls.py
```

## API Endpoints Overview

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login user
- `GET /api/auth/profile/` - Get/Update user profile

### Client Requests
- `GET /api/requests/` - List user's requests
- `POST /api/requests/` - Submit new request
- `GET /api/requests/{id}/` - Get request details
- `GET /api/requests/{id}/download_report/` - Download report

### Admin Dashboard
- `GET /api/admin/requests/` - Get all requests
- `PATCH /api/admin/requests/{id}/status/` - Update request status
- `POST /api/admin/reports/` - Upload report
- `GET /api/admin/reports/` - Get all reports

## Development Notes
- The application uses JWT tokens for authentication
- File uploads are stored in the `media/reports/` directory
- Admin users can access all requests, regular users only see their own
- Request status automatically updates to "Completed" when a report is uploaded

## Next Steps
This backend API is ready for frontend integration. You can now:
1. Build a React/Vue/Angular frontend
2. Create mobile apps that consume these APIs
3. Add additional features like email notifications
4. Implement payment processing
5. Add more detailed reporting features