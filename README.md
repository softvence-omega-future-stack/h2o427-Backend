# Background Check Application

A simplified Django REST API application for managing background check requests with comprehensive Swagger/OpenAPI documentation.

## Features

### Client Side
- User registration and authentication (JWT)
- OTP verification via Twilio
- Submit background check requests with personal information
- Track request status (Pending, In Progress, Completed)
- Download completed background check reports
- User profile management with profile pictures
- Real-time notifications
- Subscription management with Stripe

### Admin Side
- Admin dashboard to view all requests
- Update request status
- Upload PDF reports
- Manage all background check operations
- Bulk notifications to users
- Subscription and payment management

### API Documentation
- **Interactive Swagger UI** with pre-filled test data
- **ReDoc** for clean documentation reading
- **30+ documented endpoints** with examples
- **Instant API testing** without external tools

## Technology Stack
- **Backend:** Django 5.2.7
- **API:** Django REST Framework 3.15.2
- **Authentication:** JWT (Simple JWT)
- **Database:** PostgreSQL (Render.com) / SQLite (development)
- **File Handling:** Django FileField for uploads
- **API Documentation:** drf-yasg (Swagger/OpenAPI)
- **Payment Processing:** Stripe
- **SMS/OTP:** Twilio
- **Email:** Gmail SMTP

## Quick Start

### Option 1: Docker (Recommended) 

1. **Install Docker Desktop:**
   - Windows/Mac: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Linux: Install Docker Engine and Docker Compose

2. **Clone and Setup:**
   ```bash
   git clone <repository-url>
   cd h2o427-Backend
   cp .env.example .env  # Edit with your credentials
   ```

3. **Start with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

4. **Create Superuser:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Access the Application:**
   - **Swagger UI:** `http://localhost:8000/swagger/` 
   - **Admin Panel:** `http://localhost:8000/admin/`
   - **Via Nginx:** `http://localhost/` (reverse proxy)

** See `DOCKER_SETUP.md` for complete Docker documentation**

### Option 2: Local Development

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create Superuser (if needed):**
   ```bash
   python manage.py createsuperuser
   ```

5. **Start Development Server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the Application:**
   - **Swagger UI:** `http://127.0.0.1:8000/swagger/`  **Start here!**
   - **ReDoc:** `http://127.0.0.1:8000/redoc/`
   - **API Base:** `http://127.0.0.1:8000/api/`
   - **Admin Panel:** `http://127.0.0.1:8000/admin/`

## API Documentation

### Quick Test with Swagger
1. Open http://127.0.0.1:8000/swagger/
2. All endpoints have **pre-filled test data**
3. Click "Try it out" on any endpoint
4. Click "Execute" to test instantly!

### Documentation Files
- **`SWAGGER_TEST_DATA.md`** - Complete API reference with 30+ examples
- **`QUICK_TEST_DATA.md`** - Copy-paste ready test data
- **`SWAGGER_VISUAL_GUIDE.md`** - Visual guide for using Swagger UI
- **`SWAGGER_IMPLEMENTATION_SUMMARY.md`** - Technical implementation details

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