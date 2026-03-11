import logging
import httpx
from datetime import date
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from database import AsyncSessionLocal
from models import Team, TeamStats, EloRating

logger = logging.getLogger(__name__)

SEASON = "2024-25"
BDL_BASE = "https://api.balldontlie.io/v1"

TEAM_META = {
    "Atlanta Hawks":          {"abbreviation":"ATL","conference":"East","division":"Southeast","color_hex":"#C1D32F","logo_emoji":"🦅"},
    "Boston Celtics":         {"abbreviation":"BOS","conference":"East","division":"Atlantic",  "color_hex":"#007A33","logo_emoji":"🍀"},
    "Brooklyn Nets":          {"abbreviation":"BKN","conference":"East","division":"Atlantic",  "color_hex":"#000000","logo_emoji":"🕸️"},
    "Charlotte Hornets":      {"abbreviation":"CHA","conference":"East","division":"Southeast","color_hex":"#1D1160","logo_emoji":"🐝"},
    "Chicago Bulls":          {"abbreviation":"CHI","conference":"East","division":"Central",   "color_hex":"#CE1141","logo_emoji":"🐂"},
    "Cleveland Cavaliers":    {"abbreviation":"CLE","conference":"East","division":"Central",   "color_hex":"#6F263D","logo_emoji":"⚔️"},
    "Dallas Mavericks":       {"abbreviation":"DAL","conference":"West","division":"Southwest", "color_hex":"#00538C","logo_emoji":"🤠"},
    "Denver Nuggets":         {"abbreviation":"DEN","conference":"West","division":"Northwest", "color_hex":"#4FA3E0","logo_emoji":"⛏️"},
    "Detroit Pistons":        {"abbreviation":"DET","conference":"East","division":"Central",   "color_hex":"#C8102E","logo_emoji":"⚙️"},
    "Golden State Warriors":  {"abbreviation":"GSW","conference":"West","division":"Pacific",   "color_hex":"#1D428A","logo_emoji":"🌉"},
    "Houston Rockets":        {"abbreviation":"HOU","conference":"West","division":"Southwest", "color_hex":"#CE1141","logo_emoji":"🚀"},
    "Indiana Pacers":         {"abbreviation":"IND","conference":"East","division":"Central",   "color_hex":"#002D62","logo_emoji":"🏎️"},
    "Los Angeles Clippers":   {"abbreviation":"LAC","conference":"West","division":"Pacific",   "color_hex":"#C8102E","logo_emoji":"⛵"},
    "Los Angeles Lakers":     {"abbreviation":"LAL","conference":"West","division":"Pacific",   "color_hex":"#552583","logo_emoji":"👑"},
    "Memphis Grizzlies":      {"abbreviation":"MEM","conference":"West","division":"Southwest", "color_hex":"#5D76A9","logo_emoji":"🐻"},
    "Miami Heat":             {"abbreviation":"MIA","conference":"East","division":"Southeast","color_hex":"#98002E","logo_emoji":"🔥"},
    "Milwaukee Bucks":        {"abbreviation":"MIL","conference":"East","division":"Central",   "color_hex":"#00471B","logo_emoji":"🦌"},
    "Minnesota Timberwolves": {"abbreviation":"MIN","conference":"West","division":"Northwest", "color_hex":"#0C2340","logo_emoji":"🐺"},
    "New Orleans Pelicans":   {"abbreviation":"NOP","conference":"West","division":"Southwest", "color_hex":"#0C2340","logo_emoji":"🦢"},
    "New York Knicks":        {"abbreviation":"NYK","conference":"East","division":"Atlantic",  "color_hex":"#006BB6","logo_emoji":"🗽"},
    "Oklahoma City Thunder":  {"abbreviation":"OKC","conference":"West","division":"Northwest", "color_hex":"#007AC1","logo_emoji":"⚡"},
    "Orlando Magic":          {"abbreviation":"ORL","conference":"East","division":"Southeast","color_hex":"#0077C0","logo_emoji":"🪄"},
    "Philadelphia 76ers":     {"abbreviation":"PHI","conference":"East","division":"Atlantic",  "color_hex":"#006BB6","logo_emoji":"🔔"},
    "Phoenix Suns":           {"abbreviation":"PHX","conference":"West","division":"Pacific",   "color_hex":"#E56020","logo_emoji":"☀️"},
    "Portland Trail Blazers": {"abbreviation":"POR","conference":"West","division":"Northwest", "color_hex":"#E03A3E","logo_emoji":"🌲"},
    "Sacramento Kings":       {"abbreviation":"SAC","conference":"West","division":"Pacific",   "color_hex":"#5A2D81","logo_emoji":"👑"},
    "San Antonio Spurs":      {"abbreviation":"SAS","conference":"West","division":"Southwest", "color_hex":"#8A8D8F","logo_emoji":"🌹"},
    "Toronto Raptors":        {"abbreviation":"TOR","conference":"East","division":"Atlantic",  "color_hex":"#CE1141","logo_emoji":"🦖"},
    "Utah Jazz":              {"abbreviation":"UTA","conference":"West","division":"Northwest", "color_hex":"#002B5C","logo_emoji":"🎵"},
    "Washington Wizards":     {"abbreviation":"WAS","conference":"East","division":"Southeast","color_hex":"#002B5C","logo_emoji":"🧙"},
}

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
    "ATL": {"wins":28,"losses":38,"off_rating":113.2,"def_rating":116.8,"pace":100.2,"ts_pct":0.578,"last5_wins":2,"streak":-1},
    "BKN": {"wins":22,"losses":44,"off_rating":109.5,"def_rating":117.3,"pace":97.8,"ts_pct":0.561,"last5_wins":1,"streak":-3},
    "CHA": {"wins":18,"losses":48,"off_rating":108.2,"def_rating":118.5,"pace":99.1,"ts_pct":0.552,"last5_wins":1,"streak":-4},
    "CHI": {"wins":25,"losses":41,"off_rating":110.3,"def_rating":115.6,"pace":98.3,"ts_pct":0.568,"last5_wins":2,"streak":-1},
    "DET": {"wins":23,"losses":43,"off_rating":109.1,"def_rating":116.9,"pace":97.6,"ts_pct":0.559,"last5_wins":1,"streak":-2},
    "LAC": {"wins":31,"losses":34,"off_rating":112.1,"def_rating":112.5,"pace":96.5,"ts_pct":0.581,"last5_wins":2,"streak":1},
    "NOP": {"wins":21,"losses":45,"off_rating":108.7,"def_rating":117.1,"pace":98.7,"ts_pct":0.556,"last5_wins":1,"streak":-2},
    "ORL": {"wins":33,"losses":33,"off_rating":111.4,"def_rating":112.0,"pace":95.8,"ts_pct":0.576,"last5_wins":3,"streak":2},
    "PHI": {"wins":24,"losses":42,"off_rating":109.8,"def_rating":116.2,"pace":97.2,"ts_pct":0.563,"last5_wins":2,"streak":-1},
    "POR": {"wins":20,"losses":46,"off_rating":108.4,"def_rating":117.8,"pace":99.3,"ts_pct":0.554,"last5_wins":1,"streak":-3},
    "SAC": {"wins":29,"losses":36,"off_rating":113.5,"def_rating":114.1,"pace":100.1,"ts_pct":0.583,"last5_wins":2,"streak":0},
    "TOR": {"wins":21,"losses":45,"off_rating":109.2,"def_rating":117.4,"pace":98.5,"ts_pct":0.557,"last5_wins":1,"streak":-2},
    "UTA": {"wins":23,"losses":43,"off_rating":110.1,"def_rating":116.5,"pace":98.8,"ts_pct":0.565,"last5_wins":2,"streak":1},
    "WAS": {"wins":15,"losses":51,"off_rating":106.5,"def_rating":118.9,"pace":97.9,"ts_pct":0.547,"last5_wins":1,"streak":-4},
}


async def fetch_bdl_standings():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BDL_BASE}/standings", params={"season": 2024})
            if r.status_code == 200:
                data = r.json().get("data", [])
                result = {}
                for item in data:
                    team_name = item.get("team", {}).get("full_name", "")
                    meta = TEAM_META.get(team_name)
                    if meta:
                        abbr = meta["abbreviation"]
                        result[abbr] = {
                            "wins": item.get("wins", 0),
                            "losses": item.get("losses", 0),
                        }
                logger.info(f"BallDontLie 스탠딩 {len(result)}개 팀 가져옴")
                return result
    except Exception as e:
        logger.warning(f"BallDontLie 스탠딩 실패: {e}")
    return {}


async def fetch_bdl_team_ids():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BDL_BASE}/teams", params={"per_page": 30})
            if r.status_code == 200:
                mapping = {}
                for t in r.json().get("data", []):
                    name = t.get("full_name", "")
                    meta = TEAM_META.get(name)
                    if meta:
                        mapping[meta["abbreviation"]] = t["id"]
                return mapping
    except Exception as e:
        logger.warning(f"팀 ID 조회 실패: {e}")
    return {}


async def fetch_bdl_recent_games(bdl_team_id: int, abbr: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BDL_BASE}/games", params={
                "seasons[]": 2024,
                "team_ids[]": bdl_team_id,
                "per_page": 10,
            })
            if r.status_code == 200:
                games = r.json().get("data", [])
                finished = [g for g in games if g.get("status") == "Final"]
                finished = sorted(finished, key=lambda g: g["date"], reverse=True)

                last5_wins = 0
                for g in finished[:5]:
                    home = g["home_team"]["id"] == bdl_team_id
                    won = (home and g["home_team_score"] > g["visitor_team_score"]) or \
                          (not home and g["visitor_team_score"] > g["home_team_score"])
                    if won:
                        last5_wins += 1

                streak = 0
                if finished:
                    home0 = finished[0]["home_team"]["id"] == bdl_team_id
                    last_won = (home0 and finished[0]["home_team_score"] > finished[0]["visitor_team_score"]) or \
                               (not home0 and finished[0]["visitor_team_score"] > finished[0]["home_team_score"])
                    for g in finished:
                        home = g["home_team"]["id"] == bdl_team_id
                        won = (home and g["home_team_score"] > g["visitor_team_score"]) or \
                              (not home and g["visitor_team_score"] > g["home_team_score"])
                        if won == last_won:
                            streak += 1 if last_won else -1
                        else:
                            break

                return {"last5_wins": last5_wins, "streak": streak}
    except Exception as e:
        logger.warning(f"최근 경기 실패 ({abbr}): {e}")
    return None


async def run_full_pipeline():
    logger.info("ETL 시작...")
    async with AsyncSessionLocal() as db:
        today = date.today()
        await db.execute(text("TRUNCATE teams CASCADE"))
        await db.commit()
        team_id_map = {}
        for i, (name, meta) in enumerate(TEAM_META.items(), start=1):
            row = {"name": name, "city": name.rsplit(" ", 1)[0], **meta}
            stmt = pg_insert(Team).values(**row).on_conflict_do_update(
            index_elements=["abbreviation"], 
            set_={
            "name": name,
            "conference": meta["conference"],
            "division": meta["division"],
            "color_hex": meta["color_hex"],
            "logo_emoji": meta["logo_emoji"],
            }
)
            await db.execute(stmt)
            team_id_map[meta["abbreviation"]] = i
        await db.commit()

        live_standings = await fetch_bdl_standings()
        bdl_ids = await fetch_bdl_team_ids()

        for abbr, fallback in FALLBACK_STATS.items():
            team_id = team_id_map.get(abbr)
            if not team_id:
                continue

            wins   = live_standings.get(abbr, {}).get("wins",   fallback["wins"])
            losses = live_standings.get(abbr, {}).get("losses", fallback["losses"])

            form = None
            if abbr in bdl_ids:
                form = await fetch_bdl_recent_games(bdl_ids[abbr], abbr)

            last5_wins = form["last5_wins"] if form else fallback["last5_wins"]
            streak     = form["streak"]     if form else fallback["streak"]

            stmt = pg_insert(TeamStats).values(
                team_id=team_id,
                snapshot_date=today,
                season=SEASON,
                wins=wins,
                losses=losses,
                off_rating=fallback["off_rating"],
                def_rating=fallback["def_rating"],
                net_rating=round(fallback["off_rating"] - fallback["def_rating"], 2),
                pace=fallback["pace"],
                ts_pct=fallback["ts_pct"],
                last5_wins=last5_wins,
                streak=streak,
            ).on_conflict_do_update(
                index_elements=["abbreviation"],
                set_={"name": name}
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

    logger.info(f"ETL 완료! 실시간 스탠딩 {len(live_standings)}팀 반영")