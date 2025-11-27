# Guess the Player - Makefile
# ============================
# Commands to run the data pipeline, backend, and frontend

.PHONY: help install install-backend install-frontend install-scraper \
        scrape-players scrape-transfers scrape-all \
        extract-clubs create-sequences prepare-data \
        backend frontend dev clean test

# Default target
help:
	@echo "Guess the Player - Available Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install           - Install all dependencies"
	@echo "  make install-backend   - Install backend dependencies"
	@echo "  make install-frontend  - Install frontend dependencies"
	@echo "  make install-scraper   - Install scraper dependencies"
	@echo ""
	@echo "Data Pipeline:"
	@echo "  make scrape-players    - Scrape player data from Transfermarkt"
	@echo "  make scrape-transfers  - Scrape transfer history for players"
	@echo "  make scrape-all        - Run both player and transfer scrapers"
	@echo "  make extract-clubs     - Extract club data from transfers"
	@echo "  make create-sequences  - Create player career sequences"
	@echo "  make prepare-data      - Run full data preparation pipeline"
	@echo ""
	@echo "Development:"
	@echo "  make backend           - Start backend server (port 8000)"
	@echo "  make frontend          - Start frontend dev server (port 5173)"
	@echo "  make dev               - Start both backend and frontend"
	@echo ""
	@echo "Utilities:"
	@echo "  make test              - Run backend tests"
	@echo "  make clean             - Clean generated files and caches"
	@echo "  make placeholders      - Generate placeholder images"

# ============================================================================
# INSTALLATION
# ============================================================================

install: install-scraper install-backend install-frontend
	@echo "✓ All dependencies installed"

install-scraper:
	@echo "Installing scraper dependencies..."
	pip install -r requirements.txt
	@echo "✓ Scraper dependencies installed"

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "✓ Backend dependencies installed"

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✓ Frontend dependencies installed"

# ============================================================================
# DATA PIPELINE - SCRAPING
# ============================================================================

scrape-players:
	@echo "========================================"
	@echo "Running Player Spider..."
	@echo "========================================"
	scrapy crawl player_spider
	@echo "✓ Player data saved to output/players.json"

scrape-transfers:
	@echo "========================================"
	@echo "Running Transfer Spider..."
	@echo "========================================"
	scrapy crawl transfer_spider -a player_file=output/players.json
	@echo "✓ Transfer data saved to output/transfers.json"

scrape-all: scrape-players scrape-transfers
	@echo "========================================"
	@echo "All scraping completed!"
	@echo "========================================"

# ============================================================================
# DATA PIPELINE - PROCESSING
# ============================================================================

extract-clubs:
	@echo "========================================"
	@echo "Extracting club data..."
	@echo "========================================"
	python scraper/data_preparation/extract_clubs.py
	@echo "✓ Club data extracted"

create-sequences:
	@echo "========================================"
	@echo "Creating player sequences..."
	@echo "========================================"
	python scraper/data_preparation/create_sequence.py
	@echo "✓ Player sequences created"

prepare-data: extract-clubs create-sequences
	@echo "========================================"
	@echo "Data preparation completed!"
	@echo "========================================"

# Full pipeline: scrape + process
pipeline: scrape-all prepare-data
	@echo "========================================"
	@echo "Full pipeline completed!"
	@echo "========================================"

# ============================================================================
# DEVELOPMENT SERVERS
# ============================================================================

backend:
	@echo "Starting backend server on http://localhost:8000..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "Starting frontend dev server on http://localhost:5173..."
	cd frontend && npm run dev

# Start both servers (requires running in separate terminals or using & for background)
dev:
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo ""
	@echo "Run these commands in separate terminals:"
	@echo "  Terminal 1: make backend"
	@echo "  Terminal 2: make frontend"

# ============================================================================
# UTILITIES
# ============================================================================

test:
	@echo "Running backend tests..."
	cd backend && pytest -v

placeholders:
	@echo "Generating placeholder images..."
	cd backend && python create_placeholder.py
	@echo "✓ Placeholder images created"

clean:
	@echo "Cleaning generated files..."
	rm -rf __pycache__
	rm -rf scraper/__pycache__
	rm -rf scraper/spiders/__pycache__
	rm -rf scraper/data_preparation/__pycache__
	rm -rf backend/__pycache__
	rm -rf backend/app/__pycache__
	rm -rf backend/.pytest_cache
	rm -rf frontend/node_modules/.cache
	rm -rf .scrapy
	rm -rf httpcache
	@echo "✓ Cleanup completed"

# Clean everything including data
clean-all: clean
	@echo "Cleaning all data files..."
	rm -rf output/*.json
	rm -f transfermarkt.db
	rm -f transfermarkt.db.wal
	rm -rf backend/static/images/players/*
	rm -rf backend/static/images/clubs/*
	@echo "✓ All data cleaned"