# MarketPulse · run `just` to see this list

set dotenv-load := false

# List all commands
default:
    @just --list

# One-time setup: Python deps + frontend deps + database, everything
setup:
    uv sync --group dev
    cd frontend && npm install
    just db
    @echo ""
    @echo "Setup complete. Next:  just cli   or   just run"
    @echo "(Keys go in .env — copy .env.example if you have not.)"

# Start Postgres (Docker) and wait until it accepts connections
db:
    #!/usr/bin/env bash
    if ! docker info >/dev/null 2>&1; then
        echo "Docker is not running. Start Docker Desktop first, then re-run."
        exit 1
    fi
    docker compose up -d
    for i in $(seq 1 30); do
        if docker exec marketpulse-postgres pg_isready -U postgres >/dev/null 2>&1; then
            echo "Postgres ready on localhost:5442"
            exit 0
        fi
        sleep 1
    done
    echo "Postgres did not become ready in 30s"; exit 1

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
cli thread="cli-demo": db
    uv run python -m backend.cli --thread {{thread}}

# CLI with mock data
cli-mock thread="cli-demo": db
    OXYLABS_MOCK=true uv run python -m backend.cli --thread {{thread}}

# Open the concept notebooks (checkpointers + summarization)
notebooks:
    uv run jupyter lab concepts/

# Run an Oxylabs concept script: just oxy 1 ... just oxy 5 (live scraping)
oxy n:
    uv run python oxylabs_concepts/0{{n}}_*.py

# Open a psql shell to inspect the checkpoints table live in class
psql:
    docker exec -it marketpulse-postgres psql -U postgres -d marketpulse

# Open the visual database viewer (pgweb) in the browser
viewer: db
    @echo "Opening database viewer at http://localhost:8081"
    @open http://localhost:8081 || xdg-open http://localhost:8081 || true

# Re-export architecture diagrams from .drawio to .png
diagrams:
    cd diagrams && for f in *.drawio; do drawio -x -f png -s 2 --crop -o "${f%.drawio}.png" "$f"; done

# Stop Postgres and clean caches
clean:
    docker compose down
    rm -rf backend/__pycache__ .pytest_cache
