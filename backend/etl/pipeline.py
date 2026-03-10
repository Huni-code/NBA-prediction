import logging
from datetime import date
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from database import AsyncSessionLocal
from models import Team, TeamStats, EloRating

logger = logging.getLogger(__name__)

SEASON = "2025-26"

FALLBACK_TEAMS = [
    {"id":1,  "name":"Boston Celtics",           "abbreviation":"BOS","city":"Boston",        "conference":"East","division":"Atlantic",  "color_hex":"#007A33","logo_emoji":"🍀"},
    {"id":2,  "name":"Cleveland Cavaliers",       "abbreviation":"CLE","city":"Cleveland",     "conference":"East","division":"Central",   "color_hex":"#6F263D","logo_emoji":"⚔️"},
    {"id":3,  "name":"New York Knicks",           "abbreviation":"NYK","city":"New York",      "conference":"East","division":"Atlantic",  "color_hex":"#006BB6","logo_emoji":"🗽"},
    {"id":4,  "name":"Indiana Pacers",            "abbreviation":"IND","city":"Indianapolis",  "conference":"East","division":"Central",   "color_hex":"#002D62","logo_emoji":"🏎️"},
    {"id":5,  "name":"Milwaukee Bucks",           "abbreviation":"MIL","city":"Milwaukee",     "conference":"East","division":"Central",   "color_hex":"#00471B","logo_emoji":"🦌"},
    {"id":6,  "name":"Miami Heat",                "abbreviation":"MIA","city":"Miami",         "conference":"East","division":"Southeast", "color_hex":"#98002E","logo_emoji":"🔥"},
    {"id":7,  "name":"Oklahoma City Thunder",     "abbreviation":"OKC","city":"Oklahoma City", "conference":"West","division":"Northwest", "color_hex":"#007AC1","logo_emoji":"⚡"},
    {"id":8,  "name":"Houston Rockets",           "abbreviation":"HOU","city":"Houston",       "conference":"West","division":"Southwest", "color_hex":"#CE1141","logo_emoji":"🚀"},
    {"id":9,  "name":"Denver Nuggets",            "abbreviation":"DEN","city":"Denver",        "conference":"West","division":"Northwest", "color_hex":"#4FA3E0","logo_emoji":"⛏️"},
    {"id":10, "name":"Dallas Mavericks",          "abbreviation":"DAL","city":"Dallas",        "conference":"West","division":"Southwest", "color_hex":"#00538C","logo_emoji":"🤠"},
    {"id":11, "name":"Golden State Warriors",     "abbreviation":"GSW","city":"San Francisco", "conference":"West","division":"Pacific",   "color_hex":"#1D428A","logo_emoji":"🌉"},
    {"id":12, "name":"Los Angeles Lakers",        "abbreviation":"LAL","city":"Los Angeles",   "conference":"West","division":"Pacific",   "color_hex":"#552583","logo_emoji":"👑"},
    {"id":13, "name":"Phoenix Suns",              "abbreviation":"PHX","city":"Phoenix",       "conference":"West","division":"Pacific",   "color_hex":"#E56020","logo_emoji":"☀️"},
    {"id":14, "name":"San Antonio Spurs",         "abbreviation":"SAS","city":"San Antonio",   "conference":"West","division":"Southwest", "color_hex":"#8A8D8F","logo_emoji":"🌹"},
    {"id":15, "name":"Memphis Grizzlies",         "abbreviation":"MEM","city":"Memphis",       "conference":"West","division":"Southwest", "color_hex":"#5D76A9","logo_emoji":"🐻"},
    {"id":16, "name":"Minnesota Timberwolves",    "abbreviation":"MIN","city":"Minneapolis",   "conference":"West","division":"Northwest", "color_hex":"#0C2340","logo_emoji":"🐺"},
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


async def run_full_pipeline():
    logger.info("ETL 시작...")
    async with AsyncSessionLocal() as db:
        today = date.today()

        for t in FALLBACK_TEAMS:
            stmt = pg_insert(Team).values(**t).on_conflict_do_update(
                index_elements=["id"], set_={"name": t["name"]}
            )
            await db.execute(stmt)

        for abbr, s in FALLBACK_STATS.items():
            team_id = next(t["id"] for t in FALLBACK_TEAMS if t["abbreviation"] == abbr)
            stmt = pg_insert(TeamStats).values(
                team_id=team_id, snapshot_date=today, season=SEASON,
                net_rating=round(s["off_rating"] - s["def_rating"], 2), **s,
            ).on_conflict_do_update(
                constraint="uq_team_snapshot",
                set_={"wins": s["wins"], "losses": s["losses"],
                      "off_rating": s["off_rating"], "def_rating": s["def_rating"],
                      "net_rating": round(s["off_rating"] - s["def_rating"], 2)}
            )
            await db.execute(stmt)

        await db.commit()

        result = await db.execute(select(TeamStats).where(TeamStats.snapshot_date == today))
        for stats in result.scalars().all():
            total = stats.wins + stats.losses
            win_pct = stats.wins / total if total > 0 else 0.5
            elo = round(1200 + win_pct * 600, 1)
            stmt = pg_insert(EloRating).values(
                team_id=stats.team_id, as_of_date=today, elo=elo
            ).on_conflict_do_nothing()
            await db.execute(stmt)

        await db.commit()
    logger.info("ETL 완료!")
