from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from datetime import date

from database import get_db
from models import Team, TeamStats, EloRating, Game, PlayerInjury, TeamInjuryImpact, GameOdds
from model.predictor import model, TeamSnapshot, OddsSnapshot

teams_router       = APIRouter()
games_router       = APIRouter()
predictions_router = APIRouter()


# ── Teams ─────────────────────────────────────────────────
@teams_router.get("")
async def get_all_teams(db=Depends(get_db)):
    result = await db.execute(select(Team).order_by(Team.conference, Team.name))
    teams = result.scalars().all()
    out = []
    for t in teams:
        s = t.stats[-1] if t.stats else None
        out.append({
            "id": t.id, "name": t.name, "abbreviation": t.abbreviation,
            "city": t.city, "conference": t.conference,
            "color": t.color_hex, "logo": t.logo_emoji,
            "record":     f"{s.wins}-{s.losses}" if s else "N/A",
            "net_rating": round(s.off_rating - s.def_rating, 1) if s else 0,
        })
    return out


@teams_router.get("/{abbr}/stats")
async def get_team_stats(abbr: str, db=Depends(get_db)):
    r = await db.execute(select(Team).where(Team.abbreviation == abbr.upper()))
    team = r.scalar_one_or_none()
    if not team: raise HTTPException(404, f"팀 '{abbr}' 없음")

    r = await db.execute(
        select(TeamStats).where(TeamStats.team_id == team.id)
        .order_by(TeamStats.snapshot_date.desc()).limit(1)
    )
    s = r.scalar_one_or_none()
    if not s: raise HTTPException(404, "스탯 없음. /api/etl/seed 먼저 실행하세요.")

    r = await db.execute(
        select(EloRating).where(EloRating.team_id == team.id)
        .order_by(EloRating.as_of_date.desc()).limit(1)
    )
    elo_row = r.scalar_one_or_none()

    return {
        "team":    {"name": team.name, "abbreviation": team.abbreviation, "color": team.color_hex},
        "record":  {"wins": s.wins, "losses": s.losses},
        "advanced":{"off_rating": s.off_rating, "def_rating": s.def_rating,
                    "net_rating": s.net_rating, "pace": s.pace, "ts_pct": s.ts_pct},
        "form":    {"last5_wins": s.last5_wins, "streak": s.streak},
        "elo":     elo_row.elo if elo_row else 1500.0,
        "as_of":   s.snapshot_date.isoformat(),
    }


# ── Games ─────────────────────────────────────────────────
@games_router.get("/today")
async def get_today_games(db=Depends(get_db)):
    today = date.today()
    r = await db.execute(select(Game).where(Game.game_date == today))
    games = r.scalars().all()
    if not games:
        return {"date": today.isoformat(), "games": [], "message": "오늘 경기 없음"}
    return {
        "date": today.isoformat(),
        "games": [{"game_id": g.id, "home_team": g.home_team.abbreviation,
                   "away_team": g.away_team.abbreviation, "status": g.status} for g in games]
    }


# ── Predictions ───────────────────────────────────────────
async def _load_snapshot(db, abbr: str) -> TeamSnapshot:
    r = await db.execute(select(Team).where(Team.abbreviation == abbr.upper()))
    team = r.scalar_one_or_none()
    if not team: raise HTTPException(404, f"팀 '{abbr}' 없음")

    r = await db.execute(
        select(TeamStats).where(TeamStats.team_id == team.id)
        .order_by(TeamStats.snapshot_date.desc()).limit(1)
    )
    s = r.scalar_one_or_none()
    if not s: raise HTTPException(404, "스탯 없음. POST /api/etl/seed 실행하세요.")

    r = await db.execute(
        select(EloRating).where(EloRating.team_id == team.id)
        .order_by(EloRating.as_of_date.desc()).limit(1)
    )
    elo_row = r.scalar_one_or_none()

    r = await db.execute(
        select(TeamInjuryImpact).where(
            and_(TeamInjuryImpact.team_id == team.id,
                 TeamInjuryImpact.report_date == date.today())
        )
    )
    impact = r.scalar_one_or_none()

    r = await db.execute(
        select(PlayerInjury).where(
            and_(PlayerInjury.team_id == team.id,
                 PlayerInjury.report_date == date.today())
        )
    )
    injured = r.scalars().all()

    return TeamSnapshot(
        team_id=team.id, name=team.name, abbreviation=team.abbreviation,
        color=team.color_hex or "#888",
        wins=s.wins, losses=s.losses,
        off_rating=s.off_rating, def_rating=s.def_rating, pace=s.pace,
        last5_wins=s.last5_wins, streak=s.streak,
        elo=elo_row.elo if elo_row else 1500.0,
        injury_impact=impact.impact_pct if impact else 0.0,
        injured_players=[
            {"player_name": i.player_name, "status": i.status,
             "reason": i.reason, "impact": i.estimated_contribution}
            for i in injured if i.status in ("Out","Doubtful","Questionable","GTD")
        ],
    )


@predictions_router.get("/predict")
async def predict_game(home: str, away: str, db=Depends(get_db)):
    home_snap = await _load_snapshot(db, home)
    away_snap = await _load_snapshot(db, away)
    return model.predict(home_snap, away_snap)


@predictions_router.get("/injuries/{team_abbr}")
async def get_injuries(team_abbr: str, db=Depends(get_db)):
    r = await db.execute(select(Team).where(Team.abbreviation == team_abbr.upper()))
    team = r.scalar_one_or_none()
    if not team: raise HTTPException(404)

    r = await db.execute(
        select(PlayerInjury).where(
            and_(PlayerInjury.team_id == team.id,
                 PlayerInjury.report_date == date.today())
        ).order_by(PlayerInjury.estimated_contribution.desc())
    )
    injuries = r.scalars().all()
    return {
        "team": team_abbr.upper(),
        "report_date": date.today().isoformat(),
        "players": [{"name": i.player_name, "status": i.status, "reason": i.reason} for i in injuries]
    }
