"""
etl/pipeline.py
실제 API 키가 없으면 FALLBACK 데이터로 DB를 채웁니다.
API 키가 있으면 자동으로 실제 데이터를 가져옵니다.
"""

import logging
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database import AsyncSessionLocal
from models import Team, TeamStats, Game, EloRating, Prediction

logger = logging.getLogger(__name__)

SEASON     = "2025-26"
SEASON_INT = 2025
BASE_ELO   = 1500.0
K_FACTOR   = 20.0

# ── 폴백 데이터 (API 키 없어도 앱이 돌아감) ──────────────
FALLBACK_TEAMS = [
    {"id":1,  "name":"Boston Celtics",           "abbreviation":"BOS","city":"Boston",        "conference":"East","division":"Atlantic",  "color":"#007A33","logo":"🍀"},
    {"id":2,  "name":"Cleveland Cavaliers",       "abbreviation":"CLE","city":"Cleveland",     "conference":"East","division":"Central",   "color":"#6F263D","logo":"⚔️"},
    {"id":3,  "name":"New York Knicks",           "abbreviation":"NYK","city":"New York",      "conference":"East","division":"Atlantic",  "color":"#006BB6","logo":"🗽"},
    {"id":4,  "name":"Indiana Pacers",            "abbreviation":"IND","city":"Indianapolis",  "conference":"East","division":"Central",   "color":"#002D62","logo":"🏎️"},
    {"id":5,  "name":"Milwaukee Bucks",           "abbreviation":"MIL","city":"Milwaukee",     "conference":"East","division":"Central",   "color":"#00471B","logo":"🦌"},
    {"id":6,  "name":"Miami Heat",                "abbreviation":"MIA","city":"Miami",         "conference":"East","division":"Southeast", "color":"#98002E","logo":"🔥"},
    {"id":7,  "name":"Oklahoma City Thunder",     "abbreviation":"OKC","city":"Oklahoma City", "conference":"West","division":"Northwest", "color":"#007AC1","logo":"⚡"},
    {"id":8,  "name":"Houston Rockets",           "abbreviation":"HOU","city":"Houston",       "conference":"West","division":"Southwest", "color":"#CE1141","logo":"🚀"},
    {"id":9,  "name":"Denver Nuggets",            "abbreviation":"DEN","city":"Denver",        "conference":"West","division":"Northwest", "color":"#0E2240","logo":"⛏️"},
    {"id":10, "name":"Dallas Mavericks",          "abbreviation":"DAL","city":"Dallas",        "conference":"West","division":"Southwest", "color":"#00538C","logo":"🤠"},
    {"id":11, "name":"Golden State Warriors",     "abbreviation":"GSW","city":"San Francisco", "conference":"West","division":"Pacific",   "color":"#1D428A","logo":"🌉"},
    {"id":12, "name":"Los Angeles Lakers",        "abbreviation":"LAL","city":"Los Angeles",   "conference":"West","division":"Pacific",   "color":"#552583","logo":"👑"},
    {"id":13, "name":"Phoenix Suns",              "abbreviation":"PHX","city":"Phoenix",       "conference":"West","division":"Pacific",   "color":"#E56020","logo":"☀️"},
    {"id":14, "name":"San Antonio Spurs",         "abbreviation":"SAS","city":"San Antonio",   "conference":"West","division":"Southwest", "color":"#C4CED4","logo":"🌹"},
    {"id":15, "name":"Memphis Grizzlies",         "abbreviation":"MEM","city":"Memphis",       "conference":"West","division":"Southwest", "color":"#5D76A9","logo":"🐻"},
    {"id":16, "name":"Minnesota Timberwolves",    "abbreviation":"MIN","city":"Minneapolis",   "conference":"West","division":"Northwest", "color":"#0C2340","logo":"🐺"},
]

FALLBACK_STATS = {
    "BOS": {"wins":47,"losses":19,"off_rating":118.7,"def_rating":109.0,"pace":97.5,"ts_pct":0.617,"last5_wins":4,"streak":3},
    "CLE": {"wins":51,"losses":15,"off_rating":119.8,"def_rating":107.4,"pace":96.1,"ts_pct":0.621,"last5_wins":4,"streak":2},
    "NYK": {"wins":40,"losses":26,"off_rating":113.8,"def_rating":110.2,"pace":93.7,"ts_pct":0.594,"last5_wins":3,"streak":1},
    "IND": {"wins":39,"losses":27,"off_rating":119.9,"def_rating":116.5,"pace":101.4,"ts_pct":0.610,"last5_wins":3,"streak":-1},
    "MIL": {"wins":37,"losses":29,"off_rating":115.9,"def_rating":114.3,"pace":99.7,"ts_pct":0.601,"last5_wins":2,"streak":-2},
    "MIA": {"wins":32,"losses":34,"off_rating":111.5,"def_rating":113.1,"pace":95.4,"ts_pct":0.575,"last5_wins":2,"streak":1},
    "OKC": {"wins":52,"losses":13,"off_rating":120.5,"def_rating":108.8,"pace":99.1,"ts_pct":0.622,"last5_wins":5,"streak":5},
    "HOU": {"wins":40,"losses":25,"off_rating":114.3,"def_rating":110.9,"pace":98.6,"ts_pct":0.596,"last5_wins":3,"streak":2},
    "DEN": {"wins":38,"losses":27,"off_rating":116.2,"def_rating":112.4,"pace":97.8,"ts_pct":0.604,"last5_wins":3,"streak":1},
    "DAL": {"wins":33,"losses":32,"off_rating":112.4,"def_rating":112.8,"pace":96.2,"ts_pct":0.582,"last5_wins":2,"streak":-1},
    "GSW": {"wins":30,"losses":35,"off_rating":111.7,"def_rating":114.2,"pace":98.9,"ts_pct":0.579,"last5_wins":2,"streak":-2},
    "LAL": {"wins":36,"losses":30,"off_rating":113.0,"def_rating":111.8,"pace":97.1,"ts_pct":0.588,"last5_wins":3,"streak":1},
    "PHX": {"wins":29,"losses":37,"off_rating":110.6,"def_rating":114.9,"pace":96.8,"ts_pct":0.571,"last5_wins":1,"streak":-3},
    "SAS": {"wins":19,"losses":46,"off_rating":107.0,"def_rating":117.6,"pace":98.4,"ts_pct":0.554,"last5_wins":1,"streak":-2},
    "MEM": {"wins":34,"losses":31,"off_rating":113.8,"def_rating":113.5,"pace":99.0,"ts_pct":0.589,"last5_wins":2,"streak":0},
    "MIN": {"wins":35,"losses":30,"off_rating":112.9,"def_rating":111.7,"pace":97.4,"ts_pct":0.587,"last5_wins":2,"streak":1},
}


async def seed_fallback_data(db) -> None:
    """API 키 없이 폴백 데이터로 DB 채우기"""
    today = date.today()

    # 팀 삽입
    for t in FALLBACK_TEAMS:
        stmt = pg_insert(Team).values(**t).on_conflict_do_update(
            index_elements=["id"],
            set_={"name": t["name"]}
        )
        await db.execute(stmt)

    # 스탯 삽입
    for abbr, s in FALLBACK_STATS.items():
        team_id = next(t["id"] for t in FALLBACK_TEAMS if t["abbreviation"] == abbr)
        stmt = pg_insert(TeamStats).values(
            team_id=team_id,
            snapshot_date=today,
            season=SEASON,
            net_rating=round(s["off_rating"] - s["def_rating"], 2),
            **s,
        ).on_conflict_do_update(
            constraint="uq_team_snapshot",
            set_={
                "wins": s["wins"], "losses": s["losses"],
                "off_rating": s["off_rating"], "def_rating": s["def_rating"],
            }
        )
        await db.execute(stmt)

    await db.commit()
    logger.info("Fallback data seeded: %d teams", len(FALLBACK_TEAMS))


async def seed_elo_from_stats(db) -> None:
    """win% 기반으로 초기 ELO 설정 (1200~1800 범위)"""
    today = date.today()
    result = await db.execute(
        select(TeamStats).where(TeamStats.snapshot_date == today)
    )
    stats = result.scalars().all()

    for s in stats:
        total = s.wins + s.losses
        win_pct = s.wins / total if total > 0 else 0.5
        elo = 1200 + (win_pct * 600)   # 0% = 1200, 50% = 1500, 100% = 1800

        stmt = pg_insert(EloRating).values(
            team_id=s.team_id,
            as_of_date=today,
            elo=round(elo, 1),
        ).on_conflict_do_nothing()
        await db.execute(stmt)

    await db.commit()
    logger.info("ELO initialized from win%%")


async def run_full_pipeline() -> None:
    """전체 ETL 실행 (폴백 모드)"""
    logger.info("=== ETL Pipeline START ===")
    async with AsyncSessionLocal() as db:
        await seed_fallback_data(db)
        await seed_elo_from_stats(db)
    logger.info("=== ETL Pipeline DONE ===")