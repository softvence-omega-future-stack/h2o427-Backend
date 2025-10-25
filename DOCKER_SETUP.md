# 🐳 Docker Setup Guide

## 📦 Files Created

1. **Dockerfile** - Main application container configuration
2. **docker-compose.yml** - Multi-container orchestration
3. **nginx.conf** - Nginx reverse proxy configuration
4. **.dockerignore** - Files to exclude from Docker build

## 🚀 Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### Option 2: Using Docker Only (Without Compose)

```bash
# Build the image
docker build -t h2o427-backend .

# Run the container
docker run -p 8000:8000 --env-file .env h2o427-backend
```

## 🔧 Configuration

### Environment Variables

The Docker setup uses your existing `.env` file. Make sure it contains:

```env
SECRET_KEY=your-secret-key
DEBUG=False

# Database (Docker will use internal db service)
dbname=h2o427
user=root
password=kX8AHlyySRgEXqx7H86ZQdy60o7kUhS9

# Stripe
STRIPE_TEST_PUBLIC_KEY=pk_test_...
STRIPE_TEST_SECRET_KEY=sk_test_...
STRIPE_TEST_ENDPOINT_SECRET=whsec_...

# Twilio
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=...

# Email
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...

# Frontend
FRONTEND_URL=http://localhost:3000
```

## 📋 Docker Compose Services

### 1. Database (PostgreSQL)
- **Container**: `h2o427_db`
- **Port**: 5432
- **Volume**: Persistent data storage
- **Health Check**: Ensures DB is ready before starting web service

### 2. Web Application (Django)
- **Container**: `h2o427_web`
- **Port**: 8000
- **Workers**: 3 Gunicorn workers
- **Auto-migration**: Runs migrations on startup
- **Static Files**: Collected automatically

### 3. Nginx (Optional)
- **Container**: `h2o427_nginx`
- **Port**: 80
- **Purpose**: Reverse proxy, static file serving
- **Features**: Caching, compression, load balancing

## 🛠️ Common Commands

### Start Services
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Rebuild and start
docker-compose up --build
```

### Stop Services
```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs web
docker-compose logs db

# Follow logs
docker-compose logs -f web
```

### Execute Commands in Container
```bash
# Run Django management commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic

# Access Django shell
docker-compose exec web python manage.py shell

# Access PostgreSQL
docker-compose exec db psql -U root -d h2o427
```

### Database Management
```bash
# Create backup
docker-compose exec db pg_dump -U root h2o427 > backup.sql

# Restore backup
docker-compose exec -T db psql -U root h2o427 < backup.sql

# Reset database
docker-compose down -v
docker-compose up -d db
docker-compose exec web python manage.py migrate
```

## 🔍 Accessing the Application

After running `docker-compose up`, access:

- **Django Application**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/swagger/
- **Admin Panel**: http://localhost:8000/admin/
- **Via Nginx**: http://localhost (if nginx service is running)

## 🐛 Troubleshooting

### Issue: Database connection failed
```bash
# Check if database is healthy
docker-compose ps

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Issue: Port already in use
```bash
# Stop existing services
docker-compose down

# Or change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

### Issue: Static files not loading
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Restart web service
docker-compose restart web
```

### Issue: Migration errors
```bash
# Run migrations manually
docker-compose exec web python manage.py migrate

# Reset migrations (BE CAREFUL - loses data)
docker-compose down -v
docker-compose up -d db
docker-compose exec web python manage.py migrate
```

## 🔧 Development vs Production

### Development Setup
```yaml
# In docker-compose.yml, set:
environment:
  - DEBUG=True
volumes:
  - .:/app  # Mount source code for live reload
```

### Production Setup
```yaml
# In docker-compose.yml, set:
environment:
  - DEBUG=False
# Remove volume mounting for security
# Use environment-specific .env file
```

## 📊 Container Management

### Check Container Status
```bash
docker-compose ps
```

### View Resource Usage
```bash
docker stats
```

### Remove Unused Resources
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything
docker system prune -a
```

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Already in .gitignore
2. **Use secrets** for production (Docker secrets or environment variables)
3. **Update base images** regularly
4. **Scan for vulnerabilities**: `docker scan h2o427-backend`
5. **Run as non-root user** in production
6. **Use specific image versions** instead of `latest`

## 🚢 Deployment

### Push to Docker Hub
```bash
# Login
docker login

# Tag image
docker tag h2o427-backend yourusername/h2o427-backend:v1.0

# Push
docker push yourusername/h2o427-backend:v1.0
```

### Deploy to Cloud

#### AWS ECS / Azure Container Instances / Google Cloud Run
```bash
# Build for production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build

# Push to registry
docker push yourusername/h2o427-backend:latest

# Deploy using cloud provider CLI
```

#### Render.com (Current Deployment)
Your current Render.com deployment can also use Docker:
1. Add `render.yaml` with Docker configuration
2. Render will automatically detect and use Dockerfile

## 📦 Volume Management

### Backup Volumes
```bash
# Backup database volume
docker run --rm -v h2o427-backend_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/db-backup.tar.gz -C /data .

# Backup media files
docker run --rm -v h2o427-backend_media_volume:/data -v $(pwd):/backup alpine tar czf /backup/media-backup.tar.gz -C /data .
```

### Restore Volumes
```bash
# Restore database volume
docker run --rm -v h2o427-backend_postgres_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/db-backup.tar.gz"
```

## 🎯 Benefits of Docker Setup

✅ **Consistency** - Same environment everywhere (dev, staging, production)
✅ **Isolation** - No dependency conflicts with host system
✅ **Scalability** - Easy to scale services independently
✅ **Portability** - Run anywhere Docker is installed
✅ **Fast Setup** - New developers can start in minutes
✅ **Easy Deployment** - Build once, deploy anywhere
✅ **Version Control** - Infrastructure as code

## 📝 Next Steps

1. **Test the setup**: `docker-compose up`
2. **Create superuser**: `docker-compose exec web python manage.py createsuperuser`
3. **Access Swagger**: http://localhost:8000/swagger/
4. **Run tests**: `docker-compose exec web python manage.py test`
5. **Configure CI/CD** to build and deploy Docker images

---

**Need Help?**
- Docker Docs: https://docs.docker.com/
- Docker Compose Docs: https://docs.docker.com/compose/
- Django Docker Guide: https://docs.djangoproject.com/en/stable/howto/deployment/

**Your Docker setup is ready!** 🐳✨
