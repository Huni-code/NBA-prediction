# 🏀 NBA Win Predictor

A full-stack NBA game prediction app that estimates win probabilities using Elo ratings, advanced stats, injury reports, and betting odds analysis.

**Built with:** FastAPI · PostgreSQL · React · Vite

---

## Features

- **Win Probability Model** — Weighted ensemble of Elo rating, net rating, recent form, streak, and home court advantage
- **Live ETL Pipeline** — Fetches real-time standings and recent game data from BallDontLie API with fallback stats for reliability
- **Injury Impact Adjustment** — Factors in player absences to adjust predictions
- **Betting Odds Analysis** — Value bet detection with Kelly Criterion sizing across 30+ bookmakers
- **Team Rankings** — East/West conference standings with net rating display
- **React Frontend** — Dark-themed UI with team colors, animated probability bars, and interactive matchup selection

---

## How It Works

### Prediction Model (`model/predictor.py`)

The model calculates home win probability using a weighted combination:

| Factor | Weight | Source |
|--------|:---:|--------|
| Elo Rating | 40% | Dynamic rating based on win/loss record |
| Net Rating | 30% | Offensive rating − Defensive rating |
| Recent Form | 15% | Last 5 games win count |
| Streak | 10% | Current win/loss streak (tanh-scaled) |
| Home Court | 5% | Fixed home advantage bonus |

The base probability is then adjusted for injury impact (capped at ±15%) and clamped between 10–90%.

### ETL Pipeline (`etl/pipeline.py`)

On startup, the pipeline:
1. Seeds all 30 NBA teams with metadata (conference, division, colors, emoji)
2. Fetches live standings from BallDontLie API
3. Pulls recent game results to calculate form and streak
4. Falls back to hardcoded season stats if API is unavailable
5. Computes Elo ratings from win percentage

### Database Schema (`models.py`)

| Table | Purpose |
|-------|---------|
| `teams` | Team info (name, abbreviation, conference, colors) |
| `team_stats` | Snapshot of wins, losses, off/def rating, pace, TS%, form |
| `elo_ratings` | Historical Elo ratings per team per date |
| `games` | Game schedule and results |
| `predictions` | Stored predictions with accuracy tracking (Brier score) |
| `player_injuries` | Individual injury reports with estimated impact |
| `team_injury_impact` | Aggregated team-level injury impact percentage |
| `game_odds` | Bookmaker odds with implied probabilities and vig |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/teams` | All teams with record and net rating |
| `GET` | `/api/teams/{abbr}/stats` | Detailed stats for a team |
| `GET` | `/api/games/today` | Today's scheduled games |
| `GET` | `/api/predictions/predict?home=BOS&away=LAL` | Predict matchup |
| `GET` | `/api/predictions/injuries/{abbr}` | Team injury report |
| `POST` | `/api/etl/seed` | Manually trigger ETL pipeline |

---

## Project Structure

```
NBA-prediction/
├── backend/
│   ├── main.py              # FastAPI app with lifespan ETL
│   ├── database.py          # Async PostgreSQL (SQLAlchemy + asyncpg)
│   ├── models.py            # 8 SQLAlchemy ORM models
│   ├── routers.py           # API route handlers
│   ├── requirements.txt
│   ├── .env
│   ├── etl/
│   │   └── pipeline.py      # Data fetching + seeding pipeline
│   └── model/
│       └── predictor.py     # Win probability model
└── frontend/
    ├── src/
    │   ├── App.jsx           # Full React app (single-file)
    │   └── main.jsx
    ├── index.html
    ├── package.json
    └── vite.config.js
```

---

## Setup & Run

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL

### 1. Database Setup
```sql
CREATE DATABASE nba_predictor;
CREATE USER nba_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE nba_predictor TO nba_user;
```

### 2. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
uvicorn main:app --reload
```
Backend runs at `http://localhost:8000` (Swagger docs at `/docs`)

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`

---

## Tech Stack

**Backend:** Python, FastAPI, SQLAlchemy (async), asyncpg, PostgreSQL, httpx

**Frontend:** React 18, Vite, Vanilla CSS-in-JS

**Data Sources:** BallDontLie API, NBA official injury reports
