# MarketPulse · run `just` to see this list

set dotenv-load := false

# List all commands
default:
    @just --list

# One-time setup: Python deps + frontend deps
setup:
    uv sync --group dev
    cd frontend && npm install
    @echo "Setup done. Copy .env.example to .env and add your keys if you have not."

# Start Postgres (Docker)
db:
    docker compose up -d
    @echo "Postgres running on localhost:5442"

# Run the FastAPI backend (live Oxylabs scraping)
backend: db
    uv run uvicorn backend.api:app --port 8010

# Run the backend with saved mock data (no scraping credits used)
backend-mock: db
    OXYLABS_MOCK=true uv run uvicorn backend.api:app --port 8010

# Run the React frontend
frontend:
    cd frontend && npm run dev

# Run backend + frontend together (Ctrl+C stops both)
run: db
    #!/usr/bin/env bash
    trap 'kill 0' EXIT
    uv run uvicorn backend.api:app --port 8010 &
    sleep 2
    cd frontend && npm run dev

# Chat with the agent in the terminal (great for demos)
cli thread="cli-demo":
    uv run python -m backend.cli --thread {{thread}}

# CLI with mock data
cli-mock thread="cli-demo":
    OXYLABS_MOCK=true uv run python -m backend.cli --thread {{thread}}

# Open the concept notebooks (checkpointers + summarization)
notebooks:
    uv run jupyter lab concepts/

# Open a psql shell to inspect the checkpoints table live in class
psql:
    docker exec -it marketpulse-postgres psql -U postgres -d marketpulse

# Re-export architecture diagrams from .drawio to .png
diagrams:
    cd diagrams && for f in *.drawio; do drawio -x -f png -s 2 --crop -o "${f%.drawio}.png" "$f"; done

# Stop Postgres and clean caches
clean:
    docker compose down
    rm -rf backend/__pycache__ .pytest_cache
