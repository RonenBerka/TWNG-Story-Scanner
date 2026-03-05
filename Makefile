.PHONY: dev down seed ingest score enrich load-viewer export-twng pipeline test logs clean help

# ---------- Core ----------

dev:                  ## Start the full stack (build + up)
	docker compose up --build -d

down:                 ## Stop all services
	docker compose down

clean:                ## Stop services AND remove volumes (DB data lost)
	docker compose down -v

# ---------- Setup ----------

seed:                 ## Run migrations + show admin credentials
	docker compose exec backend python -m app.db.seed

# ---------- Pipeline ----------

ingest:               ## Ingest Reddit posts
	docker compose exec backend python -m app.cli ingest-reddit

score:                ## Score unscored candidates
	docker compose exec backend python -m app.cli score-candidates

enrich:               ## Enrich candidates above threshold
	docker compose exec backend python -m app.cli enrich-candidates

load-viewer:          ## Load viewer extraction JSON into records
	docker compose exec backend python -m app.cli load-viewer-data seed_viewer_data.json

export-twng:          ## Export records to TWNG import JSON
	docker compose exec backend python -m app.cli export-twng -o /tmp/twng_export.json
	docker compose cp backend:/tmp/twng_export.json ./twng_export.json
	@echo "Export saved to ./twng_export.json"

pipeline: ingest score enrich   ## Run full pipeline: ingest → score → enrich

# ---------- Quality ----------

test:                 ## Run backend tests
	docker compose exec backend pytest -q

logs:                 ## Tail all service logs
	docker compose logs -f --tail 50

# ---------- Help ----------

help:                 ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
