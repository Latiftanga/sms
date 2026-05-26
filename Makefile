.PHONY: help dev down migrate createsuperuser seeddev shell logs

help:
	@echo "Usage:"
	@echo "  make dev               Start all services"
	@echo "  make down              Stop all services"
	@echo "  make migrate           Run database migrations"
	@echo "  make createsuperuser   Create a superadmin user (interactive)"
	@echo "  make seeddev           Seed a demo school + school admin (admin@demo.school / Admin1234!)"
	@echo "  make shell             Open Python shell inside the API container"
	@echo "  make logs              Tail API logs"

dev:
	docker compose up

down:
	docker compose down

migrate:
	docker compose run --rm migrate

createsuperuser:
	docker compose run --rm api python scripts/create_superuser.py

seeddev:
	docker compose run --rm api python scripts/seed_dev.py

shell:
	docker compose exec api python

logs:
	docker compose logs -f api
