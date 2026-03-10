from sqlalchemy import (
    Column, Integer, Float, String, Boolean,
    DateTime, Date, ForeignKey, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Team(Base):
    __tablename__ = "teams"
    id           = Column(Integer, primary_key=True)
    name         = Column(String(60), nullable=False)
    abbreviation = Column(String(4),  nullable=False, unique=True)
    city         = Column(String(40))
    conference   = Column(String(4))
    division     = Column(String(20))
    color_hex    = Column(String(7))
    logo_emoji   = Column(String(4))

    stats    = relationship("TeamStats",   back_populates="team", lazy="selectin")
    elo_ratings = relationship("EloRating", back_populates="team")
    injuries = relationship("PlayerInjury", back_populates="team")


class TeamStats(Base):
    __tablename__ = "team_stats"
    __table_args__ = (
        UniqueConstraint("team_id", "snapshot_date", name="uq_team_snapshot"),
    )
    id            = Column(Integer, primary_key=True, autoincrement=True)
    team_id       = Column(Integer, ForeignKey("teams.id"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    season        = Column(String(10), nullable=False)
    wins          = Column(Integer, default=0)
    losses        = Column(Integer, default=0)
    off_rating    = Column(Float)
    def_rating    = Column(Float)
    net_rating    = Column(Float)
    pace          = Column(Float)
    ts_pct        = Column(Float)
    last5_wins    = Column(Integer, default=0)
    streak        = Column(Integer, default=0)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    team = relationship("Team", back_populates="stats")


class Game(Base):
    __tablename__ = "games"
    __table_args__ = (
        UniqueConstraint("api_game_id", name="uq_api_game"),
    )
    id           = Column(Integer, primary_key=True, autoincrement=True)
    api_game_id  = Column(Integer, nullable=False)
    game_date    = Column(Date, nullable=False)
    season       = Column(String(10), nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    home_score   = Column(Integer)
    away_score   = Column(Integer)
    home_won     = Column(Boolean)
    status       = Column(String(20), default="scheduled")

    home_team  = relationship("Team", foreign_keys=[home_team_id])
    away_team  = relationship("Team", foreign_keys=[away_team_id])
    prediction = relationship("Prediction", back_populates="game", uselist=False)
    odds       = relationship("GameOdds", back_populates="game", uselist=False)


class Prediction(Base):
    __tablename__ = "predictions"
    id                 = Column(Integer, primary_key=True, autoincrement=True)
    game_id            = Column(Integer, ForeignKey("games.id"), nullable=False, unique=True)
    predicted_at       = Column(DateTime(timezone=True), server_default=func.now())
    home_win_prob      = Column(Float, nullable=False)
    predicted_home_win = Column(Boolean, nullable=False)
    model_version      = Column(String(20), default="elo_v3")
    elo_home           = Column(Float)
    elo_away           = Column(Float)
    net_rtg_delta      = Column(Float)
    form_delta         = Column(Float)
    streak_delta       = Column(Float)
    was_correct        = Column(Boolean)
    brier_score        = Column(Float)
    game = relationship("Game", back_populates="prediction")


class EloRating(Base):
    __tablename__ = "elo_ratings"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    team_id    = Column(Integer, ForeignKey("teams.id"), nullable=False)
    as_of_date = Column(Date, nullable=False)
    elo        = Column(Float, nullable=False)
    game_id    = Column(Integer, ForeignKey("games.id"), nullable=True)
    team = relationship("Team", back_populates="elo_ratings")


class PlayerInjury(Base):
    __tablename__ = "player_injuries"
    __table_args__ = (
        UniqueConstraint("player_name", "report_date", "team_id", name="uq_player_injury_date"),
    )
    id                     = Column(Integer, primary_key=True, autoincrement=True)
    team_id                = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_name            = Column(String(80), nullable=False)
    report_date            = Column(Date, nullable=False)
    status                 = Column(String(20), nullable=False)
    reason                 = Column(String(200))
    absence_probability    = Column(Float)
    estimated_contribution = Column(Float)
    source                 = Column(String(20), default="nba_official")
    team = relationship("Team", back_populates="injuries")


class TeamInjuryImpact(Base):
    __tablename__ = "team_injury_impact"
    __table_args__ = (
        UniqueConstraint("team_id", "report_date", name="uq_team_injury_date"),
    )
    id          = Column(Integer, primary_key=True, autoincrement=True)
    team_id     = Column(Integer, ForeignKey("teams.id"), nullable=False)
    report_date = Column(Date, nullable=False)
    impact_pct  = Column(Float, default=0.0)
    players_out = Column(Integer, default=0)


class GameOdds(Base):
    __tablename__ = "game_odds"
    __table_args__ = (
        UniqueConstraint("game_id", name="uq_game_odds"),
    )
    id                    = Column(Integer, primary_key=True, autoincrement=True)
    game_id               = Column(Integer, ForeignKey("games.id"), nullable=False)
    fetched_at            = Column(DateTime(timezone=True), nullable=False)
    consensus_home_ml     = Column(Float)
    consensus_away_ml     = Column(Float)
    consensus_home_spread = Column(Float)
    consensus_total       = Column(Float)
    implied_home_prob     = Column(Float)
    implied_away_prob     = Column(Float)
    vig_pct               = Column(Float)
    bookmaker_count       = Column(Integer, default=0)
    raw_bookmakers        = Column(JSON)
    game = relationship("Game", back_populates="odds")
