.PHONY: help dev down build migrate test test-k create-test-db createsuperuser seeddev shell logs

help:
	@echo "Usage:"
	@echo "  make dev               Start all services"
	@echo "  make down              Stop all services"
	@echo "  make build             Rebuild images (needed after Dockerfile or dep changes)"
	@echo "  make migrate           Run database migrations"
	@echo "  make test              Run the full test suite"
	@echo "  make test-k k=<expr>   Run tests matching an expression (e.g. make test-k k=test_login)"
	@echo "  make create-test-db    Create the test database (only needed once on existing setups)"
	@echo "  make createsuperuser   Create a superadmin user (interactive)"
	@echo "  make seeddev           Seed a demo school + school admin (admin@demo.school / Admin1234!)"
	@echo "  make shell             Open Python shell inside the API container"
	@echo "  make logs              Tail API logs"

dev:
	docker compose up

down:
	docker compose down

build:
	docker compose build

migrate:
	docker compose --profile migrate run --rm migrate

test:
	docker compose --profile test run --rm test

test-k:
	docker compose --profile test run --rm test python -m pytest tests/ -v --tb=short -k "$(k)"

create-test-db:
	docker compose exec db psql -U ttek -d ttek_sis -c "CREATE DATABASE ttek_sis_test" 2>/dev/null || true
	docker compose exec db psql -U ttek -d ttek_sis -c "GRANT ALL PRIVILEGES ON DATABASE ttek_sis_test TO ttek" 2>/dev/null || true

createsuperuser:
	docker compose run --rm api python scripts/create_superuser.py

seeddev:
	docker compose run --rm api python scripts/seed_dev.py

shell:
	docker compose exec api python

logs:
	docker compose logs -f api
