# Scraper Module

This module handles web scraping from Transfermarkt and data preparation for the Guess the Player game.

## Overview

The scraper module consists of two main components:

1. **Scrapy Spiders** - Web crawlers that extract player and transfer data from Transfermarkt
2. **Data Preparation** - Scripts that process raw data into game-ready formats

## Directory Structure

```
scraper/
├── __init__.py
├── items.py              # Scrapy item definitions
├── settings.py           # Scrapy configuration
├── db_pipeline.py        # DuckDB storage pipeline
├── json_pipeline.py      # JSON file output pipeline
├── spiders/
│   ├── __init__.py
│   ├── player_spider.py  # Scrapes player information
│   └── transfer_spider.py # Scrapes transfer histories
└── data_preparation/
    ├── __init__.py
    ├── extract_clubs.py   # Extracts unique clubs from transfers
    └── create_sequence.py # Creates career path sequences
```

## Components

### Spiders

#### PlayerSpider (`player_spider.py`)

Crawls Transfermarkt league pages to collect player information.

**Data Collected:**
- Player ID
- Player name
- Player profile URL
- Player image URL
- Market value
- Current club
- League and division

**Leagues Covered:**
- England (Premier League)
- Spain (La Liga)
- Germany (Bundesliga)
- Italy (Serie A)
- France (Ligue 1)
- Portugal (Primeira Liga)
- Netherlands (Eredivisie)
- Saudi Arabia (Saudi Pro League)
- USA (MLS)

**Usage:**
```bash
scrapy crawl player_spider
# or
make scrape-players
```

#### TransferSpider (`transfer_spider.py`)

Fetches transfer history for each player using Transfermarkt's API.

**Data Collected:**
- Season
- Transfer fee
- From club (name + logo URL)
- To club (name + logo URL)
- Transfer date

**Usage:**
```bash
scrapy crawl transfer_spider -a player_file=output/players.json
# or
make scrape-transfers
```

### Pipelines

#### DuckDBPipeline (`db_pipeline.py`)

Stores scraped data in a DuckDB database for efficient querying.

**Tables Created:**
- `players` - Player basic information
- `transfers` - Full transfer history (JSON)
- `transfer_details` - Normalized transfer records

#### JsonWriterPipeline (`json_pipeline.py`)

Outputs data to JSON files for backup and portability.

**Output Files:**
- `output/players.json`
- `output/transfers.json`

### Data Preparation

#### extract_clubs.py

Extracts unique clubs and their logos from transfer data.

**Features:**
- Deduplicates clubs from both source and destination
- Extracts club IDs from logo URLs
- Populates the `clubs` table

**Usage:**
```bash
python scraper/data_preparation/extract_clubs.py
# or
make extract-clubs
```

#### create_sequence.py

Transforms raw transfer data into game-ready career sequences.

**Processing Steps:**
1. Filters out youth/reserve teams (U18, U21, Academy, etc.)
2. Merges loan + permanent transfers to same club
3. Removes consecutive duplicate clubs
4. Calculates difficulty based on career length:
   - **Short**: 2-4 clubs
   - **Moderate**: 5-7 clubs
   - **Long**: 8+ clubs

**Output:**
- `sequence_analysis` table with processed sequences
- `game_data_*.json` files for each difficulty level

**Usage:**
```bash
python scraper/data_preparation/create_sequence.py
# or
make create-sequences
```

## Configuration

### Scrapy Settings (`settings.py`)

Key configurations:

```python
# Rate limiting (respects robots.txt)
DOWNLOAD_DELAY = 3
CONCURRENT_REQUESTS = 8
AUTOTHROTTLE_ENABLED = True

# Caching (reduces duplicate requests)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400  # 24 hours

# Pipelines
ITEM_PIPELINES = {
    'scraper.json_pipeline.JsonWriterPipeline': 300,
    'scraper.db_pipeline.DuckDBPipeline': 400,
}

# Database
DUCKDB_DATABASE = 'transfermarkt.db'
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DUCKDB_DATABASE` | Path to DuckDB database | `transfermarkt.db` |
| `PLAYER_OUTPUT_FILE` | Player JSON output path | `output/players.json` |
| `TRANSFER_OUTPUT_FILE` | Transfer JSON output path | `output/transfers.json` |

## Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Transfermarkt  │────▶│  Player Spider   │────▶│  players.json   │
│    Website      │     │                  │     │  players table  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Transfermarkt  │────▶│ Transfer Spider  │────▶│ transfers.json  │
│      API        │     │                  │     │ transfers table │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Extract Clubs   │────▶│  clubs table    │
                        └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │ Create Sequence  │────▶│sequence_analysis│
                        └──────────────────┘     │     table       │
                                                 └─────────────────┘
```

## Scrapy Items

### PlayerItem

```python
class PlayerItem(scrapy.Item):
    player_id = scrapy.Field()
    player_name = scrapy.Field()
    player_url = scrapy.Field()
    player_img_url = scrapy.Field()
    market_value = scrapy.Field()
    league = scrapy.Field()
    division = scrapy.Field()
    club = scrapy.Field()
```

### TransferItem

```python
class TransferItem(scrapy.Item):
    player_id = scrapy.Field()
    player_name = scrapy.Field()
    transfers = scrapy.Field()  # List of transfer records
```

## Database Schema

### players
| Column | Type | Description |
|--------|------|-------------|
| player_id | VARCHAR | Primary key |
| player_name | VARCHAR | Player's name |
| player_url | VARCHAR | Transfermarkt profile URL |
| player_img_url | VARCHAR | Player photo URL |
| market_value | VARCHAR | Current market value (string) |
| market_value_numeric | FLOAT | Market value in millions |
| league | VARCHAR | League name |
| division | VARCHAR | Division name |
| club | VARCHAR | Current club |

### sequence_analysis
| Column | Type | Description |
|--------|------|-------------|
| player_id | VARCHAR | Primary key |
| player_name | VARCHAR | Player's name |
| market_value_numeric | FLOAT | Market value for sorting |
| num_moves | INTEGER | Number of club changes |
| num_players_with_same_seq | INTEGER | Players sharing same path |
| difficulty | VARCHAR | short/moderate/long |
| sequence_string | VARCHAR | Human-readable career path |
| club_jsons | JSON | Club details with logos |

## Troubleshooting

### Common Issues

**1. Rate Limiting (429 errors)**
```
Increase DOWNLOAD_DELAY in settings.py or wait before retrying.
```

**2. Missing Player Data**
```
Ensure player_spider ran successfully before transfer_spider.
Check output/players.json exists.
```

**3. Database Locked**
```
Close any open connections to transfermarkt.db.
Only one process should write at a time.
```

### Logs

Scrapy logs are output to stdout. To save:
```bash
scrapy crawl player_spider 2>&1 | tee spider.log
```

## License

This scraper is for educational purposes only. Please respect Transfermarkt's robots.txt and terms of service.