# Backend API

FastAPI-based REST API for the Guess the Player game. Handles game sessions, player guessing logic, and score tracking.

## Overview

The backend provides a session-based game API where users can:
- Start new game sessions with configurable difficulty
- Submit guesses with fuzzy name matching
- Track scores across multiple questions
- Get statistics about available questions

## Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── dependencies.py      # Dependency injection
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── rate_limit_handler.py  # Rate limiting
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── game.py          # Game endpoints
│   │   ├── player.py        # Player lookup endpoints
│   │   └── session.py       # Session management endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── database.py      # DuckDB connection management
│   │   ├── game_service.py  # Game business logic
│   │   ├── session_service.py    # Session management
│   │   ├── storage_interface.py  # Abstract storage interface
│   │   └── in_memory_storage.py  # In-memory session storage
│   └── utils/
│       ├── __init__.py
│       ├── fuzzy_match.py   # Name matching utilities
│       └── image_helpers.py # Image URL handling
├── tests/
│   ├── __init__.py
│   └── test_api.py          # API tests
├── static/
│   └── images/              # Static image assets
│       ├── players/
│       ├── clubs/
│       └── placeholders/
├── create_placeholder.py    # Placeholder image generator
├── download_images.py       # Image downloader script
├── requirements.txt
└── pytest.ini
```

## API Endpoints

### Session Management

#### Start Session
```http
POST /session/start
Content-Type: application/json

{
  "difficulty": "short",    // short | moderate | long
  "top_n": 200              // Player pool size (1-5000)
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "question": {
    "player_id": "12345",
    "difficulty": "short",
    "num_moves": 3,
    "shared_by": 1,
    "clubs": [...]
  },
  "score": 0,
  "total_attempts": 0
}
```

#### Submit Guess
```http
POST /session/{session_id}/guess
Content-Type: application/json

{
  "guess": "Lionel Messi"
}
```

**Response:**
```json
{
  "correct": true,
  "actual_answer": "Lionel Messi",
  "actual_answer_img_url": "https://...",
  "similarity_score": 100.0,
  "all_possible_answers": ["Lionel Messi"],
  "all_possible_answers_img_urls": ["https://..."],
  "session_score": 1,
  "total_attempts": 1
}
```

#### Get Next Question
```http
POST /session/{session_id}/next
Content-Type: application/json

{
  "difficulty": "moderate",  // Optional: override difficulty
  "top_n": 500               // Optional: override player pool
}
```

#### End Session
```http
DELETE /session/{session_id}
```

**Response:**
```json
{
  "session_id": "uuid",
  "final_score": 5,
  "total_attempts": 7,
  "correct_guesses": 5,
  "accuracy": 71.4,
  "difficulty": "short",
  "duration": "5m 30s"
}
```

#### Get Session Status
```http
GET /session/{session_id}/status
```

### Game Endpoints

#### Get Random Question
```http
GET /game/question/{difficulty}
```

#### Check Guess (Stateless)
```http
POST /game/guess
Content-Type: application/json

{
  "player_id": "12345",
  "guess": "Cristiano Ronaldo"
}
```

#### Get Statistics
```http
GET /game/stats
```

### Player Lookup

#### Search Player
```http
GET /player/{player_name}
```

### Health Checks

```http
GET /           # Basic status
GET /health     # Health check with database status
```

## Core Components

### Configuration (`config.py`)

Environment-based configuration using Pydantic Settings.

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_PATH` | Path to DuckDB database | `transfermarkt.db` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `FUZZY_MATCH_THRESHOLD` | Min score for correct guess | `85` |
| `PLAYER_LOOKUP_THRESHOLD` | Min score for player search | `70` |
| `SESSION_TTL` | Session timeout (seconds) | `21600` (6 hours) |
| `SESSION_CLEANUP_INTERVAL` | Cleanup interval (seconds) | `300` |
| `ENVIRONMENT` | Runtime environment | `dev` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Game Service (`services/game_service.py`)

Core game logic:

- **`get_random_question(difficulty, top_n)`** - Fetches a random question filtered by difficulty and player market value ranking
- **`check_guess(player_id, guess)`** - Validates guesses using fuzzy matching
- **`lookup_player(player_name)`** - Searches for players by name
- **`get_statistics()`** - Returns question counts by difficulty

### Session Service (`services/session_service.py`)

Session lifecycle management:

- **`create_session(difficulty, top_n)`** - Initializes new game session
- **`get_session(session_id)`** - Retrieves session data
- **`submit_guess(session_id, guess)`** - Processes guesses within session context
- **`get_next_question(session_id, difficulty, top_n)`** - Advances to next question
- **`end_session(session_id)`** - Terminates session and returns statistics

### Storage (`services/storage_interface.py`, `in_memory_storage.py`)

Abstract storage interface for session data. Currently uses in-memory storage, but designed for easy Redis migration.

```python
class SessionStorage(ABC):
    def set(self, key: str, value: Dict, ttl: int) -> bool
    def get(self, key: str) -> Optional[Dict]
    def delete(self, key: str) -> bool
    def exists(self, key: str) -> bool
    def update(self, key: str, value: Dict) -> bool
    def cleanup_expired(self) -> int
```

### Fuzzy Matching (`utils/fuzzy_match.py`)

Uses RapidFuzz for intelligent name matching:

```python
from rapidfuzz import fuzz, process

def fuzzy_match_player(query: str, candidates: List[str]) -> Tuple[str, int]:
    """Returns (best_match, similarity_score)"""
```

**Matching Features:**
- Case-insensitive comparison
- Handles common misspellings
- Configurable threshold (default: 85%)

### Rate Limiting

Protects against abuse:
- 10 guesses per minute per IP
- Returns friendly error message with retry time

## Pydantic Models

### Request Models

```python
class SessionStartRequest(BaseModel):
    difficulty: str  # short | moderate | long
    top_n: int       # 1-5000

class SessionGuessRequest(BaseModel):
    guess: str       # Player name guess

class SessionNextQuestionRequest(BaseModel):
    difficulty: Optional[str]
    top_n: Optional[int]
```

### Response Models

```python
class Club(BaseModel):
    club: str
    logo: str
    season: str

class Question(BaseModel):
    player_id: str
    difficulty: str
    num_moves: int
    shared_by: int
    clubs: List[Club]

class GuessResponse(BaseModel):
    correct: bool
    actual_answer: str
    actual_answer_img_url: str
    similarity_score: float
    all_possible_answers: List[str]
    all_possible_answers_img_urls: List[str]
```

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Generate placeholder images
python create_placeholder.py

# Start development server
uvicorn app.main:app --reload --port 8000

# Or using make
make backend
```

### Running Tests

```bash
pytest -v

# With coverage
pytest --cov=app --cov-report=html
```

### Environment Setup

Create `.env` file:

```env
APP_NAME="Guess the Player API"
DATABASE_PATH=../transfermarkt.db
CORS_ORIGINS=http://localhost:5173
FUZZY_MATCH_THRESHOLD=85
PLAYER_LOOKUP_THRESHOLD=70
SESSION_TTL=21600
ENVIRONMENT=dev
LOG_LEVEL=DEBUG
```

## Static Files

### Image Handling

The API serves images with fallback logic:

1. Check for local image in `static/images/`
2. Fall back to Transfermarkt CDN URL
3. Fall back to placeholder image

### Placeholder Generation

```bash
python create_placeholder.py
```

Creates:
- `static/images/placeholders/default-player.png`
- `static/images/placeholders/default-club.png`

### Image Download (Optional)

Download images locally for offline use:

```bash
python download_images.py --limit 100  # Test with 100 images
python download_images.py              # Download all
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   FastAPI   │────▶│   DuckDB    │
│  (Frontend) │◀────│   Backend   │◀────│  Database   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  In-Memory  │
                    │   Session   │
                    │   Storage   │
                    └─────────────┘
```

### Request Flow

```
1. Client sends guess
2. Rate limiter checks IP
3. Session service validates session
4. Game service checks guess with fuzzy matching
5. Session service updates score
6. Response returned to client
```

## Deployment

### Production Settings

```env
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend-domain.com
LOG_LEVEL=INFO
```

### Health Checks

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production"
}
```

## Error Handling

| Status | Description |
|--------|-------------|
| 400 | Invalid request (bad session ID, empty guess) |
| 404 | Session/player not found |
| 422 | Validation error (invalid difficulty, etc.) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## Dependencies

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **DuckDB** - Database
- **RapidFuzz** - Fuzzy string matching
- **SlowAPI** - Rate limiting
- **Pillow** - Image processing