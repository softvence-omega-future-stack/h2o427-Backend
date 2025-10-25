# Makefile for H2O427 Backend

.PHONY: help build up down restart logs shell migrate createsuperuser test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Docker Commands
build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up

up-d: ## Start all services in detached mode
	docker-compose up -d

down: ## Stop all services
	docker-compose down

down-v: ## Stop all services and remove volumes
	docker-compose down -v

restart: ## Restart all services
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-web: ## View logs from web service
	docker-compose logs -f web

logs-db: ## View logs from database service
	docker-compose logs -f db

# Django Commands
shell: ## Access Django shell
	docker-compose exec web python manage.py shell

dbshell: ## Access PostgreSQL shell
	docker-compose exec db psql -U root -d h2o427

migrate: ## Run database migrations
	docker-compose exec web python manage.py migrate

makemigrations: ## Create new migrations
	docker-compose exec web python manage.py makemigrations

createsuperuser: ## Create Django superuser
	docker-compose exec web python manage.py createsuperuser

collectstatic: ## Collect static files
	docker-compose exec web python manage.py collectstatic --noinput

# Testing
test: ## Run tests
	docker-compose exec web python manage.py test

test-coverage: ## Run tests with coverage
	docker-compose exec web coverage run --source='.' manage.py test
	docker-compose exec web coverage report

# Database Management
backup-db: ## Backup database
	docker-compose exec db pg_dump -U root h2o427 > backup_$$(date +%Y%m%d_%H%M%S).sql

restore-db: ## Restore database (use: make restore-db FILE=backup.sql)
	docker-compose exec -T db psql -U root h2o427 < $(FILE)

reset-db: ## Reset database (WARNING: deletes all data)
	docker-compose down -v
	docker-compose up -d db
	@sleep 5
	docker-compose exec web python manage.py migrate

# Production Commands
prod-build: ## Build for production
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-up: ## Start production services
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down: ## Stop production services
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

prod-logs: ## View production logs
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Cleanup
clean: ## Remove all containers, images, and volumes
	docker-compose down -v --rmi all --remove-orphans

prune: ## Remove unused Docker resources
	docker system prune -af --volumes

# Development
dev: ## Start development environment
	@echo "Starting development environment..."
	docker-compose up --build

dev-reset: ## Reset development environment
	@echo "Resetting development environment..."
	$(MAKE) down-v
	$(MAKE) up-d
	@sleep 5
	$(MAKE) migrate
	@echo "Development environment reset complete!"

# Health Checks
ps: ## Show running containers
	docker-compose ps

stats: ## Show container resource usage
	docker stats

health: ## Check service health
	@echo "Checking database health..."
	@docker-compose exec db pg_isready -U root
	@echo "Checking web service..."
	@curl -s http://localhost:8000/admin/ > /dev/null && echo "Web service is healthy" || echo "Web service is not responding"

# Quick Start
quickstart: ## Quick start (build, migrate, create superuser)
	@echo "Building Docker images..."
	$(MAKE) build
	@echo "Starting services..."
	$(MAKE) up-d
	@sleep 10
	@echo "Running migrations..."
	$(MAKE) migrate
	@echo "Creating superuser..."
	$(MAKE) createsuperuser
	@echo "Setup complete! Access Swagger at http://localhost:8000/swagger/"
