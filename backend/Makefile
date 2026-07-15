.PHONY: help up down seed test clean logs

help:
	@echo "IELTS Tutor Backend - Available Commands"
	@echo "=========================================="
	@echo "make up       - Start all services with Docker Compose"
	@echo "make down     - Stop all services"
	@echo "make seed     - Run database migrations and seed data"
	@echo "make test     - Run integration tests"
	@echo "make clean    - Remove all containers and volumes"
	@echo "make logs     - View logs from backend"
	@echo "make health   - Check backend health"

up:
	docker compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 15
	@echo "Backend started at http://localhost:8000"

down:
	docker compose down

seed:
	docker compose exec backend python -m shared.seed

test:
	docker compose exec backend pytest -v

clean:
	docker compose down -v

logs:
	docker compose logs -f backend

health:
	@curl -s http://localhost:8000/health || echo "Backend not ready"