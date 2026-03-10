import math
from dataclasses import dataclass, field
from typing import Optional

BASE_ELO       = 1500.0
HOME_ELO_BONUS = 100.0


@dataclass
class TeamSnapshot:
    team_id:      int
    name:         str
    abbreviation: str
    color:        str
    wins:         int
    losses:       int
    off_rating:   float
    def_rating:   float
    pace:         float
    last5_wins:   int
    streak:       int
    elo:          float = BASE_ELO
    injury_impact: float = 0.0
    injured_players: list = field(default_factory=list)


@dataclass
class OddsSnapshot:
    home_ml:           Optional[float] = None
    away_ml:           Optional[float] = None
    home_spread:       Optional[float] = None
    total_line:        Optional[float] = None
    implied_home_prob: Optional[float] = None
    implied_away_prob: Optional[float] = None
    vig_pct:           Optional[float] = None
    bookmaker_count:   int = 0


def decimal_to_american(d):
    if d is None: return None
    return f"+{round((d-1)*100)}" if d >= 2.0 else f"{round(-100/(d-1))}"


class WinProbabilityModel:
    WEIGHTS = {"elo": 0.40, "net": 0.30, "form": 0.15, "streak": 0.10, "home": 0.05}

    def predict(self, home: TeamSnapshot, away: TeamSnapshot,
                odds: Optional[OddsSnapshot] = None) -> dict:
        base = self._base_prob(home, away)
        adj  = max(0.10, min(0.90,
            base
            - min(home.injury_impact * 0.8, 0.15)
            + min(away.injury_impact * 0.8, 0.15)
        ))

        net_h = round(home.off_rating - home.def_rating, 2)
        net_a = round(away.off_rating - away.def_rating, 2)
        gap   = abs(adj - 0.5)

        return {
            "home_team":         home.name,
            "away_team":         away.name,
            "home_abbreviation": home.abbreviation,
            "away_abbreviation": away.abbreviation,
            "home_color":        home.color,
            "away_color":        away.color,
            "base_home_prob":    round(base, 4),
            "adj_home_prob":     round(adj, 4),
            "adj_away_prob":     round(1 - adj, 4),
            "predicted_winner":  home.name if adj >= 0.5 else away.name,
            "predicted_score":   self._score(home, away, adj),
            "confidence":        "High" if gap > 0.20 else "Medium" if gap > 0.10 else "Low",
            "home_injury_impact": round(home.injury_impact, 4),
            "away_injury_impact": round(away.injury_impact, 4),
            "home_injured":      home.injured_players,
            "away_injured":      away.injured_players,
            "odds":              self._odds_resp(odds),
            "value_bet":         self._value_bet(adj, odds),
            "factors": {
                "elo":     {"home": round(home.elo, 1), "away": round(away.elo, 1)},
                "net_rtg": {"home": net_h, "away": net_a},
                "form":    {"home": home.last5_wins, "away": away.last5_wins},
                "streak":  {"home": home.streak, "away": away.streak},
                "record":  {"home": f"{home.wins}-{home.losses}", "away": f"{away.wins}-{away.losses}"},
            },
        }

    def _base_prob(self, h, a):
        elo_p    = 1 / (1 + 10**((a.elo - (h.elo + HOME_ELO_BONUS)) / 400))
        net_p    = 1 / (1 + math.exp(-((h.off_rating-h.def_rating) - (a.off_rating-a.def_rating)) / 10))
        form_p   = ((h.last5_wins/5) + (1 - a.last5_wins/5)) / 2
        streak_p = ((math.tanh(h.streak*0.2) - math.tanh(a.streak*0.2)) + 2) / 4
        return elo_p*0.40 + net_p*0.30 + form_p*0.15 + streak_p*0.10 + 0.60*0.05

    def _score(self, h, a, prob):
        margin = (prob - 0.5) * 12
        return f"{round(113+(h.off_rating-h.def_rating)*0.2+margin/2)}-{round(113+(a.off_rating-a.def_rating)*0.2-margin/2)}"

    def _value_bet(self, prob, odds):
        empty = {"has_value":False,"home_edge":None,"away_edge":None,"best_bet":None,
                 "strength":None,"home_kelly_frac":0,"away_kelly_frac":0,
                 "home_american":None,"away_american":None}
        if not odds or not odds.implied_home_prob:
            return empty
        h_edge = round(prob - odds.implied_home_prob, 4)
        a_edge = round((1-prob) - odds.implied_away_prob, 4)
        def kelly(p, d):
            if not d or d <= 1: return 0
            b = d - 1
            return max(0, round((b*p-(1-p))/b, 4))
        T = 0.04
        best = "home" if h_edge>a_edge and h_edge>T else "away" if a_edge>T else None
        return {
            "has_value":       h_edge>T or a_edge>T,
            "home_edge":       h_edge, "away_edge": a_edge,
            "best_bet":        best,
            "strength":        "🔥 Strong" if max(h_edge,a_edge)>0.08 else "✅ Moderate" if max(h_edge,a_edge)>T else "⚠️ Weak",
            "home_kelly_frac": kelly(prob, odds.home_ml),
            "away_kelly_frac": kelly(1-prob, odds.away_ml),
            "home_american":   decimal_to_american(odds.home_ml),
            "away_american":   decimal_to_american(odds.away_ml),
        }

    def _odds_resp(self, odds):
        if not odds: return None
        return {
            "home_ml_decimal":   odds.home_ml,
            "home_ml_american":  decimal_to_american(odds.home_ml),
            "away_ml_decimal":   odds.away_ml,
            "away_ml_american":  decimal_to_american(odds.away_ml),
            "home_spread":       odds.home_spread,
            "total_line":        odds.total_line,
            "implied_home_prob": odds.implied_home_prob,
            "implied_away_prob": odds.implied_away_prob,
            "vig_pct":           odds.vig_pct,
            "bookmaker_count":   odds.bookmaker_count,
        }


model = WinProbabilityModel()
