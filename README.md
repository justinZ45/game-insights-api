# game-insights-api

A Python-based REST API for querying video game data, built as a project to explore FastAPI, SQLAlchemy, PostgreSQL, Docker, and data ingestion pipelines. The project ingests a real video game dataset and exposes it through a filterable, paginated API.

## Tech Stack

- **Python 3.12** - managed and packaged via **Poetry**
- **FastAPI** - REST API framework with auto-generated interactive docs
- **SQLAlchemy** - ORM and database session management
- **Pydantic** - data validation for both ingestion pipeline and API schemas
- **PostgreSQL 16** - relational database
- **Docker + Docker Compose** - fully containerized db & api
- **Pytest** - unit and integration testing
- **Argparse** - custom CLI (`gia`) for database and ingestion management
- **Httpx** - HTTP client utilized to fetch the CORGIS dataset during pipeline ingestion, as well as powering pytest API integration tests

---

## Project Structure

```
game-insights-api/
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── main.py                      # FastAPI app entry point + lifespan
│   │   ├── dependencies.py              # shared DB session dependency injection
│   │   └── routers/
│   │       ├── games.py                 # game endpoints
│   │       ├── genres.py                # genre endpoints
│   │       └── publishers.py            # publisher endpoints
│   ├── cli/
│   │   └── cli.py                       # CLI entry point (gia command)
│   ├── db/
│   │   └── db.py                        # database engine, session, and utility methods
│   │   └── ingest.py                    # JSON ingestion pipeline
│   └── models/
│       ├── orm_models/                  # SQLAlchemy ORM table definitions
│       │   ├── base.py
│       │   ├── game.py
│       │   ├── game_genre.py
│       │   ├── game_length.py
│       │   ├── game_publisher.py
│       │   ├── genre.py
│       │   └── publisher.py
│       └── pydantic_models/             # Pydantic validation and response schemas
│           ├── api/                     # API response schemas
│           │   ├── game_response.py
│           │   ├── game_summary.py
│           │   ├── game_length_response.py
│           │   ├── genre_response.py
│           │   └── publisher_response.py
│           └── ingestion/               # ingestion validation schemas
│               ├── game_input.py
│               ├── features.py
│               ├── metadata.py
│               ├── metrics.py
│               ├── release.py
│               ├── length.py
│               └── playstyle.py
├── tests/
│   ├── conftest.py                      # shared pytest fixtures
│   ├── test_ingest.py                   # unit tests for ingestion logic
│   ├── test_db_integration.py           # integration tests for database
│   └── api/
│       ├── test_games.py                # API tests for games endpoints
│       ├── test_genres.py               # API tests for genres endpoints
│       └── test_publishers.py           # API tests for publishers endpoints
├── Dockerfile                           # containerizes the FastAPI app
├── compose.yaml                         # orchestrates app + postgres
├── pyproject.toml
├── .env.example                         # template - committed, no real values
```

## Input Data Format

The ingestion pipeline expects a JSON file containing an array of game objects. Each object must follow this structure:

```json
[
  {
    "Title": "Super Mario 64 DS",
    "Features": {
      "Handheld?": true,
      "Max Players": 1,
      "Multiplatform?": true,
      "Online?": true
    },
    "Metadata": {
      "Genres": "Action,Adventure",
      "Licensed?": true,
      "Publishers": "Nintendo",
      "Sequel?": true
    },
    "Metrics": {
      "Review Score": 85,
      "Sales": 4.69,
      "Used Price": 24.95
    },
    "Release": {
      "Console": "Nintendo DS",
      "Rating": "E",
      "Re-release?": true,
      "Year": 2004
    },
    "Length": {
      "Main Story": {
        "Average": 14.3,
        "Leisure": 18.3,
        "Median": 14.5,
        "Polled": 21,
        "Rushed": 9.7
      }
    }
  }
]
```

**Validation rules applied at ingestion:**
- `Review Score` must be between 0 and 100
- All game length attributes (`average, leisure, median, polled, rushed`) must be greater than or equal to 0
- `Max Players` must be greater than or equal to 1
- `Rating` must be a valid ESRB rating (`E`, `M`, `T`, `A`, `RP`, `E10+`) - defaults to `RP` if unknown
- `Sales` and `Used Price` must be non-negative and to 2 decimal places
- `Year` must be between 1950 and the current year
- `Genres` and `Publishers` support multiple values separated by `,` or `/`
- `Title` must not be null or empty
- Games that fail validation are skipped with a warning - the rest of the file continues ingesting

### The bundled dataset is sourced from the [CORGIS Dataset Project](https://corgis-edu.github.io/corgis/json/video_games/).
#### **Direct Data Endpoint:** [`video_games.json`](https://corgis-edu.github.io/corgis/datasets/json/video_games/video_games.json)
---

## Database Schema

The dataset is normalized across 6 tables:

```
games                    core game data
├── game_lengths         playtime statistics per playstyle (one-to-many)
├── game_genres          junction table linking games to genres (many-to-many)
└── game_publishers      junction table linking games to publishers (many-to-many)

genres                   unique genre lookup table
publishers               unique publisher lookup table
```

### games
| Column | Type | Description |
|--------|------|-------------|
| `game_id` | int (PK) | auto-generated |
| `title` | varchar(255) | game title |
| `console` | varchar(255) | platform e.g. Nintendo DS |
| `release_year` | int | year of release |
| `esrb_rating` | varchar(5) | E, M, T, A, RP, E10+ |
| `review_score` | int | 0–100 |
| `sales_millions_usd` | numeric(10,2) | sales in millions |
| `used_price_usd` | numeric(7,2) | used market price |
| `is_handheld` | bool | |
| `max_players` | int | |
| `is_multiplatform` | bool | |
| `is_online` | bool | |
| `is_licensed` | bool | |
| `is_sequel` | bool | |
| `is_re_release` | bool | |

### game_lengths
| Column | Type | Description |
|--------|------|-------------|
| `game_lengths_id` | int (PK) | auto-generated |
| `game_id` | int (FK) | references games |
| `playstyle` | varchar(255) | Main Story, Main + Extras, Completionists, All PlayStyles |
| `avg_hours` | numeric(6,2) | average completion time |
| `median_hours` | numeric(6,2) | |
| `leisure_hours` | numeric(6,2) | |
| `rushed_hours` | numeric(6,2) | |
| `num_players_polled` | int | number of submissions |

### genres / publishers
| Column | Type | Description |
|--------|------|-------------|
| `genre_id` / `publisher_id` | int (PK) | auto-generated |
| `name` | varchar(255) | unique name |

---

## Quickstart - Docker (Recommended)

### Prerequisites
- Docker Desktop

### 1. Clone the repo

```bash
git clone https://github.com/justinZ45/game-insights-api
cd game-insights-api
```

### 2. Create a `.env` file

```bash
cp .env.example .env
```

Or create it manually:

```
DB_USER=postgres
DB_PASSWORD=replace_this_with_a_secure_password
DB_NAME=game-insights-db
DB_PORT=5432
AUTO_SEED=True
```

### 3. Start the full stack

```bash
docker compose up -d
```

This starts both PostgreSQL and the FastAPI app containers.

> **Important Note on First Boot:** If `AUTO_SEED=True` and the database contains zero records inside your core tables on boot, the application will automatically initialize the database schema and trigger the ingestion pipeline to seed the PostgreSQL instance with the CORGIS video game dataset. No manual database setup or CLI execution is required for the initial launch.


### 4. Access the API

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

---

## Local Development

Start only the database:
```bash
docker compose up -d db
```
Install dependencies, set up `.env`, then:
```bash
# 1. Install all dependencies and register the 'gia' CLI locally
poetry install

# 2. Run your development steps using poetry run
poetry run gia db reset schema
poetry run gia ingest
poetry run uvicorn src.api.main:app --reload
```

---

## CLI Reference (`gia`)

The `gia` CLI manages the database and data ingestion directly from your terminal.

>(use the `-h` flag after any command/subcommand for help on usage)

```bash

### Global Database Overrides
By default, `gia` reads database credentials from your `.env` file or environment variables. However, you can override these dynamically for any command using global flags:

# Force the CLI to connect to a database on a custom port or host
gia --port 5433 db status
gia --host staging-db-server --user admin db query games -c

# Database connection
gia db status                    # check if DB is reachable
gia db status -v                 # verbose - version, size, tables, connections

# Schema management
gia db reset schema              # drop and recreate all tables

# Table management
gia db reset table .             # truncate all tables
gia db reset table games         # truncate specific table (warns on cascade)

# Query data
gia db query games -c               # row count for games table
gia db query games -l 10            # show first 10 rows from games

# Ingest data
gia ingest                                          # No flags: Defaults to fetching and seeding from the CORGIS dataset
gia ingest -f data/video_games.json                 # Ingest from a local JSON file path
gia ingest -u https://custom-api.com/data.json      # Ingest from a custom JSON URL
```

---

## API Reference

Full interactive documentation available at `/docs`.

### Games

#### `GET /games/`
Returns a paginated, filterable list of games.

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `console` | string | Filter by console e.g. `Nintendo DS` |
| `genre` | string | Filter by genre e.g. `Action` |
| `publisher` | string | Filter by publisher e.g. `Nintendo` |
| `min_review_score` | int | Minimum review score |
| `max_review_score` | int | Maximum review score |
| `min_release_year` | int | Earliest release year |
| `max_release_year` | int | Latest release year |
| `min_players` | int | Minimum max_players value |
| `max_players` | int | Maximum max_players value |
| `limit` | int | Results per page (default: 10) |
| `offset` | int | Pagination offset (default: 0) |

**Example:**
```
GET /games/?genre=Action&min_review_score=80&console=Nintendo DS&limit=5
```

**Response:** lightweight `GameSummary` objects - no playtime data, includes genre and publisher names.

#### `GET /games/{game_id}`
Returns a single game with full details including playtime statistics for all playstyles.

**Response:** full `GameResponse` object including nested `game_lengths`.


#### `POST /games/`
Creates a new game entry in the database. Natively maps the nested input JSON structure across your normalization tables, handles automated "Get or Create" routing for new unique Genres/Publishers, and auto-populates Game Playstyle statistics.

**Request Body:** Follows the exact structure defined in [Input Data Format](#input-data-format).

**Response:** Returns a full `GameResponse` payload containing a status code `201 Created` along with your assigned, database-generated `game_id`.

**Error Handling / Edge Cases:**
* **`422 Unprocessable Entity`**: Thrown instantly if data validation checks fail (e.g., empty string title, out-of-bounds review scores, wrong decimal place notation).
* **`409 Conflict`**: Thrown if a duplicate record matching both the identical `Title` and `Console` combination already exists in the database.

#### `PATCH /games/{game_id}`
Partially updates an existing game record, its nested properties, lookup tables, and playstyle durations. 

**Request Body:** A partial JSON object following the structure of your main schema. All fields and nested blocks are completely optional (e.g., you can send *only* a modified review score).

**Response:** Returns the fully updated `GameResponse` payload reflecting your modifications along with a `200 OK` status code.


**Error Handling:**
* **`404 Not Found`**: Returned if the target `game_id` cannot be located in the PostgreSQL database.
* **`422 Unprocessable Entity`**: Thrown if partial updates break field constraints.

#### `DELETE /games/{game_id}`
Deletes an entire game record from the database. 

**Response:** Status code `204 No Content` indicating a successful deletion.

**Cascading Safeguards:** Due to the relational schema configuring `ondelete="CASCADE"`, removing a game record safely cleans up and purges its linked, dependent `game_lengths`, `game_genres`, and `game_publishers` relational mappings without leaving orphaned foreign keys in your junction tables. Standalone entities inside the `genres` or `publishers` lookup lists remain preserved.

**Error Handling:**
* **`404 Not Found`**: Returned if the specified `game_id` does not exist in the database.

---

### Genres

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/genres/` | List all genres |
| `GET` | `/genres/{genre_id}` | Get a single genre by ID |

### Publishers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/publishers/` | List all publishers |
| `GET` | `/publishers/{publisher_id}` | Get a single publisher by ID |

---


## Running Tests

```bash
# Unit tests - no database required
poetry run pytest tests/test_ingest.py -v

# Integration tests - requires running Docker container
poetry run pytest tests/test_db_integration.py -v

# API tests - requires running Docker container and ingested data
poetry run pytest tests/api/ -v

# All tests
poetry run pytest -v

# Skip integration tests
poetry run pytest -m "not integration" -v
```

> Integration and API tests require the full stack running (`docker compose up -d`) with data ingested (`gia ingest`).

---

## Data Source

Video game data sourced from the [CORGIS Dataset Project](https://corgis-edu.github.io/corgis/json/video_games/) - a collection of cleaned, real-world datasets designed for educational use. The dataset includes 1,200+ games with metadata on platforms, genres, publishers, review scores, sales figures, and playtime statistics across four playstyle categories.

---

## Notes

This project does not implement authentication at this time. In a production environment, write endpoints (POST, PUT, DELETE) would be protected. The current implementation focuses on the data pipeline, ORM design, and CRUD API as a working MVP.