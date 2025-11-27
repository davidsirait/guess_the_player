# ⚽ Guess the Player

A web-based football trivia game where players guess footballers based on their career paths. Built with React, FastAPI, and Scrapy.

![Game Preview](docs/preview.png)

## 🎮 How It Works

1. You're shown a sequence of club logos representing a player's career path
2. Guess which footballer had this exact career journey
3. The game uses fuzzy matching to accept various name spellings
4. Score points and track your accuracy!

## 🏗️ Project Architecture

```
guess-the-player/
├── scraper/                    # Data collection & processing
│   ├── spiders/                # Scrapy spiders
│   │   ├── player_spider.py    # Collects player data
│   │   └── transfer_spider.py  # Collects transfer history
│   ├── data_preparation/       # Data processing scripts
│   │   ├── extract_clubs.py    # Extract unique clubs
│   │   └── create_sequence.py  # Build career sequences
│   ├── items.py                # Scrapy item definitions
│   ├── settings.py             # Scrapy configuration
│   ├── db_pipeline.py          # DuckDB storage
│   └── json_pipeline.py        # JSON output
│
├── backend/                    # REST API
│   └── app/
│       ├── main.py             # FastAPI application
│       ├── config.py           # Configuration
│       ├── routers/            # API endpoints
│       │   ├── session.py      # Session management
│       │   ├── game.py         # Game logic
│       │   └── player.py       # Player lookup
│       ├── services/           # Business logic
│       │   ├── game_service.py # Core game logic
│       │   └── session_service.py
│       └── utils/              # Utilities
│           ├── fuzzy_match.py  # Name matching
│           └── image_helpers.py
│
├── frontend/                   # React SPA
│   └── src/
│       ├── components/         # UI components
│       │   ├── GameSetup.jsx   # Configuration screen
│       │   ├── GamePlay.jsx    # Main game view
│       │   └── GameResult.jsx  # Result screen
│       ├── services/
│       │   └── api.js          # API client
│       └── App.jsx             # Main component
│
├── transfermarkt.db            # DuckDB database (generated)
├── Makefile                    # Build & run commands
├── scrapy.cfg                  # Scrapy configuration
└── requirements.txt            # Python dependencies
```

## 📊 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA PIPELINE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐    │
│  │ Transfermarkt│────▶│Player Spider │────▶│                  │    │
│  │   Website    │     └──────────────┘     │                  │    │
│  └──────────────┘                          │   DuckDB         │    │
│         │                                  │   Database       │    │
│         │              ┌──────────────┐    │                  │    │
│         └─────────────▶│Transfer Spider────▶│  - players      │    │
│                        └──────────────┘    │  - transfers     │    │
│                                            │  - clubs         │    │
│                                            │  - sequences     │    │
│                        ┌──────────────┐    │                  │    │
│                        │ Data Prep    │───▶│                  │    │
│                        │ Scripts      │    └──────────────────┘    │
│                        └──────────────┘                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ transfermarkt.db
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         APPLICATION                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                     React Frontend                          │    │
│  │                                                             │    │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────────┐           │    │
│  │  │GameSetup │──▶│ GamePlay │──▶│ GameResult   │           │    │
│  │  └──────────┘   └──────────┘   └──────────────┘           │    │
│  │       │              │               │                     │    │
│  └───────┼──────────────┼───────────────┼─────────────────────┘    │
│          │              │               │                           │
│          └──────────────┼───────────────┘                           │
│                         │ HTTP/REST                                  │
│                         ▼                                            │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                   FastAPI Backend                           │    │
│  │                                                             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │    │
│  │  │Session Router│  │ Game Router  │  │Player Router │     │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │    │
│  │         │                 │                  │              │    │
│  │         ▼                 ▼                  ▼              │    │
│  │  ┌─────────────────────────────────────────────────┐       │    │
│  │  │              Service Layer                       │       │    │
│  │  │  - SessionService (game state, scoring)         │       │    │
│  │  │  - GameService (questions, fuzzy matching)      │       │    │
│  │  └─────────────────────────────────────────────────┘       │    │
│  │                         │                                   │    │
│  │                         ▼                                   │    │
│  │  ┌─────────────┐  ┌─────────────┐                          │    │
│  │  │  DuckDB     │  │  In-Memory  │                          │    │
│  │  │  (Questions)│  │  (Sessions) │                          │    │
│  │  └─────────────┘  └─────────────┘                          │    │
│  │                                                             │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/guess-the-player.git
cd guess-the-player

# Install all dependencies
make install
```

### Option 1: Use Pre-built Database

If you have a pre-built `transfermarkt.db`, place it in the root directory and skip to running the application.

### Option 2: Build Database from Scratch

```bash
# Run the full data pipeline (takes 1-2 hours)
make pipeline

# Or run individual steps:
make scrape-players      # ~30 minutes
make scrape-transfers    # ~1 hour
make extract-clubs       # ~1 minute
make create-sequences    # ~1 minute
```

### Running the Application

**Terminal 1 - Backend:**
```bash
make backend
# Server starts at http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
make frontend
# App available at http://localhost:5173
```

Or run both with:
```bash
make dev
# Follow instructions to run in separate terminals
```

## 🎯 Game Features

### Difficulty Levels

| Level | Career Length | Description |
|-------|--------------|-------------|
| Short | 2-4 clubs | Quick games, easier guesses |
| Moderate | 5-7 clubs | Balanced challenge |
| Long | 8+ clubs | Complex careers, harder guesses |

### Player Pool

Select from top players by market value:
- **Top 50** - Superstars only (easiest)
- **Top 100** - Star players
- **Top 200** - Well-known players (default)
- **Top 500** - Including established players
- **Top 1000** - Full challenge (hardest)

### Scoring

- ✅ Correct guess: +1 point
- ❌ Wrong guess: 0 points (no penalty)
- 📊 Accuracy tracked throughout session

### Fuzzy Matching

The game accepts various name spellings:
- "Ronaldo" matches "Cristiano Ronaldo"
- "De Bruyne" matches "Kevin De Bruyne"
- Handles accents and special characters

## 📁 Database Schema

```sql
-- Core tables
players (player_id, player_name, market_value, club, league)
transfers (player_id, transfers_json)
transfer_details (player_id, season, from_club, to_club, fee)
clubs (club_id, club_name, logo_url)

-- Game-ready data
sequence_analysis (
  player_id,
  player_name,
  market_value_numeric,
  num_moves,
  difficulty,
  sequence_string,
  club_jsons
)
```

## 🔧 Available Commands

```bash
make help              # Show all available commands

# Installation
make install           # Install all dependencies
make install-backend   # Install backend only
make install-frontend  # Install frontend only
make install-scraper   # Install scraper only

# Data Pipeline
make scrape-players    # Scrape player data
make scrape-transfers  # Scrape transfer history
make scrape-all        # Run both scrapers
make extract-clubs     # Extract club data
make create-sequences  # Create career sequences
make prepare-data      # Run data preparation
make pipeline          # Full pipeline (scrape + prepare)

# Development
make backend           # Start backend server
make frontend          # Start frontend server
make dev               # Instructions for both

# Utilities
make test              # Run backend tests
make clean             # Clean cache files
make clean-all         # Clean everything including data
make placeholders      # Generate placeholder images
```

## 🌐 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

```
POST /session/start          # Start new game
POST /session/{id}/guess     # Submit guess
POST /session/{id}/next      # Get next question
DELETE /session/{id}         # End session
GET /game/stats              # Get statistics
GET /health                  # Health check
```

## 🛠️ Configuration

### Backend (`.env`)

```env
DATABASE_PATH=../transfermarkt.db
CORS_ORIGINS=http://localhost:5173
FUZZY_MATCH_THRESHOLD=85
SESSION_TTL=21600
ENVIRONMENT=dev
```

### Frontend (`.env`)

```env
VITE_API_URL=http://localhost:8000
```

## 📦 Tech Stack

### Scraper
- **Scrapy** - Web scraping framework
- **DuckDB** - Embedded analytics database

### Backend
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation
- **RapidFuzz** - Fuzzy string matching
- **SlowAPI** - Rate limiting

### Frontend
- **React 19** - UI framework
- **Vite** - Build tool
- **Axios** - HTTP client
- **Lucide React** - Icons

## 🔒 Rate Limiting

To prevent abuse, the API limits guesses:
- **10 guesses per minute** per IP address
- Friendly error message with retry time

## 🧪 Testing

```bash
# Run backend tests
cd backend
pytest -v

# With coverage
pytest --cov=app --cov-report=html
```

## 📝 Data Sources

Player and transfer data is scraped from [Transfermarkt](https://www.transfermarkt.co.uk/).

**Covered Leagues:**
- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League
- 🇪🇸 La Liga
- 🇩🇪 Bundesliga
- 🇮🇹 Serie A
- 🇫🇷 Ligue 1
- 🇵🇹 Primeira Liga
- 🇳🇱 Eredivisie
- 🇸🇦 Saudi Pro League
- 🇺🇸 MLS

## 🚧 Future Improvements

- [ ] Redis session storage for production
- [ ] Multiplayer mode
- [ ] Daily challenges
- [ ] Leaderboards
- [ ] More leagues coverage
- [ ] Mobile app (React Native)
- [ ] Hints system (nationality, position)

## 📄 License

This project is for educational purposes. Please respect Transfermarkt's terms of service when using the scraper.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 🙏 Acknowledgments

- [Transfermarkt](https://www.transfermarkt.co.uk/) for the data
- [Scrapy](https://scrapy.org/) for the scraping framework
- [FastAPI](https://fastapi.tiangolo.com/) for the amazing web framework
- [React](https://react.dev/) for the UI framework