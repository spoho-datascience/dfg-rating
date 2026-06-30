"""Tests for the player-level Elo rating (Wolf, Schmitt & Schuller 2020, formulas 6-10)."""
from io import StringIO

import numpy as np
import pandas as pd
import pytest

from dfg_rating.model import factory
from dfg_rating.model.network.base_network import WhiteNetwork
from dfg_rating.model.rating.player_elo_rating import PlayerELORating

RATING_NAME = "player_elo_rating"

# The 12-row sample provided with the feature request (4 player slots per side).
SAMPLE = """season round home_team away_team home_score away_score result Player1_home Player2_home Player3_home Player4_home Player1_home_minutes Player2_home_minutes Player3_home_minutes Player4_home_minutes Player1_home_start_score Player2_home_start_score Player3_home_start_score Player4_home_start_score Player1_home_end_score Player2_home_end_score Player3_home_end_score Player4_home_end_score Player1_home_score Player2_home_score Player3_home_score Player4_home_score Player1_away Player2_away Player3_away Player4_away Player1_away_minutes Player2_away_minutes Player3_away_minutes Player4_away_minutes Player1_away_score Player2_away_score Player3_away_score Player4_away_score Player1_away_start_score Player2_away_start_score Player3_away_start_score Player4_away_start_score Player1_away_end_score Player2_away_end_score Player3_away_end_score Player4_away_end_score
1 1 A B 0 0 Draw 1 2 3 4 90 85 90 5 0 0 0 0 0 0 0 0 0 0 0 0 6 7 8 10 36 54 90 90 0 0 0 0 0 0 0 0 0 0 0 0
1 1 C D 0 2 Away 12 13 14 15 45 90 90 45 -2 0 0 0 -2 -2 -2 -2 0 -2 -2 -2 16 17 18 19 90 90 30 60 2 2 1 1 0 0 1 0 2 2 1 2
1 2 B C 4 1 Home 6 7 8 10 90 26 64 90 0 0 -1 0 3 -1 3 3 3 -1 4 3 11 12 13 15 90 45 45 90 -3 -2 -1 -3 0 0 -2 0 -3 -2 -3 -3
1 2 D A 2 3 Away 16 17 18 19 32 58 90 90 0 0 0 0 1 0 1 1 1 0 1 1 1 2 3 4 90 80 90 10 1 1 1 0 0 0 0 1 1 1 1 1
1 3 C A 1 1 Draw 11 13 14 15 25 90 90 65 0 0 0 0 0 0 0 0 0 0 0 0 1 2 3 4 90 85 90 5 0 0 0 0 0 0 0 0 0 0 0 0
1 3 D B 0 1 Away 16 17 19 20 70 90 20 90 0 0 -1 0 -1 -1 -1 -1 -1 -1 0 -1 6 7 8 10 90 15 90 75 1 0 1 1 0 0 0 0 1 0 1 1
2 1 A B 0 0 Draw 6 2 3 4 90 85 90 5 0 0 0 0 0 0 0 0 0 0 0 0 1 7 8 10 36 54 90 90 0 0 0 0 0 0 0 0 0 0 0 0
2 1 C D 0 2 Away 12 13 14 15 45 90 90 45 -2 0 0 0 -2 -2 -2 -2 0 -2 -2 -2 16 17 18 19 90 90 30 60 2 2 1 1 0 0 1 0 2 2 1 2
2 2 B C 4 1 Home 1 7 8 9 90 26 64 90 0 0 -1 0 3 -1 3 3 3 -1 4 3 11 12 13 15 90 45 45 90 -3 -2 -1 -3 0 0 -2 0 -3 -2 -3 -3
2 2 D A 2 3 Away 16 17 18 19 32 58 90 90 0 0 0 0 1 0 1 1 1 0 1 1 6 2 3 4 90 80 90 10 1 1 1 0 0 0 0 1 1 1 1 1
2 3 C A 1 1 Draw 11 13 14 15 25 90 90 65 0 0 0 0 0 0 0 0 0 0 0 0 6 2 3 4 90 85 90 5 0 0 0 0 0 0 0 0 0 0 0 0
2 3 D B 0 1 Away 16 17 19 20 70 90 20 90 0 0 -1 0 -1 -1 -1 -1 -1 -1 0 -1 7 8 9 10 90 15 90 75 1 0 1 1 0 0 0 0 1 0 1 1
"""


def make_df():
    return pd.read_csv(StringIO(SAMPLE), sep=r"\s+")


def make_network():
    return WhiteNetwork(data=make_df(), mapping=factory.pre_mappings["player-soccer"])


def run_player_elo(**kwargs):
    net = make_network()
    rating = PlayerELORating(**kwargs)
    net.add_player_rating(rating)
    return net, rating


# --- formula helpers -------------------------------------------------------

def test_expected_is_symmetric_and_correct():
    assert PlayerELORating.expected(1000, 1000) == 0.5
    # 400-point gap -> ~0.909 for the stronger side
    assert PlayerELORating.expected(1400, 1000) == pytest.approx(10 / 11, abs=1e-9)


def test_score_from_diff():
    assert PlayerELORating.score_from_diff(3) == 1.0
    assert PlayerELORating.score_from_diff(0) == 0.5
    assert PlayerELORating.score_from_diff(-2) == 0.0


def test_team_rating_is_minute_weighted_avg():
    """Formula 6."""
    rating = PlayerELORating(initial_rating=1000)
    rating.current = {1: 1000.0, 2: 1200.0}
    roster = [
        {"player_id": 1, "minutes": 90},
        {"player_id": 2, "minutes": 10},
    ]
    assert rating.team_rating(roster) == pytest.approx((1000 * 90 + 1200 * 10) / 100, abs=1e-9)


def test_draw_uses_minutes_branch():
    """Formula 9, D == 0 branch: w*(S-E)*(M/M_max)."""
    rating = PlayerELORating(m_max=90)
    change = rating.individual_change(s=0.5, e=0.4, d=0, minutes=45, w=1.0)
    assert change == pytest.approx(1.0 * (0.5 - 0.4) * (45 / 90), abs=1e-12)


def test_single_match_update_matches_formula_10():
    """End-to-end of one match through formulas 6-10 with default k=32, q=0.75."""
    rating = PlayerELORating(k=32, q=0.75, w=1.0, initial_rating=1000, m_max=90)
    match = {
        "lineups": {
            "home": [{"player_id": "h1", "minutes": 90, "goal_diff": 2}],
            "away": [{"player_id": "a1", "minutes": 90, "goal_diff": -2}],
        },
        "home_score": 2,
        "away_score": 0,
    }
    r_home, r_away = rating._process_match(match)
    assert r_home == 1000 and r_away == 1000  # pre-match team ratings
    expected_change = 32 * (2 ** (1 / 3)) * 0.5  # q*C_i + (1-q)*C_A coincide here
    assert rating.current["h1"] == pytest.approx(1000 + expected_change, abs=1e-9)
    assert rating.current["a1"] == pytest.approx(1000 - expected_change, abs=1e-9)


# --- end-to-end on the sample data ----------------------------------------

def test_network_imports_lineups_and_players():
    net = make_network()
    assert net.players, "player registry should be populated"
    # every match edge carries a 4-player lineup per side
    for _, _, _, data in net.data.edges(keys=True, data=True):
        assert len(data["lineups"]["home"]) == 4
        assert len(data["lineups"]["away"]) == 4


def test_winning_player_rating_rises():
    _, rating = run_player_elo()
    # player 6 wins big as B in season 1 round 2 (4-1) and keeps winning -> above initial
    assert rating.current[6] > rating.initial_rating


def test_team_rating_written_to_nodes_matches_formula_6():
    net, rating = run_player_elo()
    # First match (season 1, round 1, A vs B): all players still at initial -> R_A == initial
    series_a = net.data.nodes["A"]["ratings"][RATING_NAME][1]
    assert series_a[1] == pytest.approx(rating.initial_rating, abs=1e-9)


def test_carry_forward_when_absent():
    net, rating = run_player_elo()
    # player 20 only plays season 1 round 3 -> absent rounds 1 and 2 (carry forward)
    series = net.players[20]["ratings"][RATING_NAME][1]
    assert series[1] == pytest.approx(rating.initial_rating, abs=1e-9)  # round 1, absent
    assert series[2] == pytest.approx(rating.initial_rating, abs=1e-9)  # round 2, absent
    assert series[3] < rating.initial_rating  # round 3 loss -> drops


def test_rating_persists_across_team_change():
    net, rating = run_player_elo()
    # player 1 plays for A in season 1, then for B in season 2
    season1 = net.players[1]["ratings"][RATING_NAME][1]
    season2 = net.players[1]["ratings"][RATING_NAME][2]
    assert season2[0] == pytest.approx(season1[-1], abs=1e-9)  # carried, not reset
    assert season2[0] != rating.initial_rating
    # provenance reflects the team change
    assert net.players[1]["teams"][1] == {"A"}
    assert net.players[1]["teams"][2] == {"B"}


def test_unseen_player_starts_at_initial():
    net, rating = run_player_elo()
    # player 9 first appears in season 2 -> no season 1 series, season 2 starts at initial
    assert 1 not in net.players[9]["ratings"][RATING_NAME]
    assert net.players[9]["ratings"][RATING_NAME][2][0] == pytest.approx(rating.initial_rating, abs=1e-9)


def test_idempotent_across_repeated_runs():
    net = make_network()
    rating = PlayerELORating()
    net.add_player_rating(rating)
    first = dict(rating.current)
    net.add_player_rating(rating)  # second full pass must reproduce the same result
    assert rating.current == first


# --- list-column lineups (player-soccer-lists mapping) ---------------------

def make_list_network():
    """Two matches, lineups stored as per-side JSON lists (with a noise token)."""
    df = pd.DataFrame([
        {
            "season_id": 1, "round": 1, "home_team": "A", "away_team": "B",
            "home_score": 2, "away_score": 0, "result": "home", "date": "2023-01-01",
            "home_player_list": '["Alpha A.", "Beta B.", "red_card_1"]',
            "away_player_list": '["Gamma G.", "Delta D."]',
            "home_minutes_list": "[90, 90, 0]",
            "away_minutes_list": "[90, 90]",
            "home_goal_diff_list": "[2, 2, 0]",
            "away_goal_diff_list": "[-2, -2]",
        },
        {
            "season_id": 1, "round": 2, "home_team": "B", "away_team": "A",
            "home_score": 0, "away_score": 1, "result": "away", "date": "2023-01-08",
            "home_player_list": '["Gamma G.", "Delta D."]',
            "away_player_list": '["Alpha A.", "Beta B."]',
            "home_minutes_list": "[90, 90]",
            "away_minutes_list": "[90, 90]",
            "home_goal_diff_list": "[-1, -1]",
            "away_goal_diff_list": "[1, 1]",
        },
    ])
    return WhiteNetwork(data=df, mapping=factory.pre_mappings["player-soccer-lists"])


def test_list_mode_parses_and_drops_noise():
    net = make_list_network()
    # noise token "red_card_1" must not become a player
    assert "red_card_1" not in net.players
    assert {"Alpha A.", "Beta B.", "Gamma G.", "Delta D."} <= set(net.players)
    # match 1 home roster: 2 real players, parsed from the list (noise dropped)
    edge = next(d for _, _, _, d in net.data.edges(keys=True, data=True) if d["round"] == 1)
    assert [p["player_id"] for p in edge["lineups"]["home"]] == ["Alpha A.", "Beta B."]
    assert edge["lineups"]["home"][0]["goal_diff"] == 2
    assert edge["lineups"]["away"][0]["minutes"] == 90


def test_list_mode_player_rating_rises_for_winner():
    net = make_list_network()
    rating = PlayerELORating()
    net.add_player_rating(rating)
    # Alpha A. wins both matches -> above initial; Gamma G. loses both -> below
    assert rating.current["Alpha A."] > rating.initial_rating
    assert rating.current["Gamma G."] < rating.initial_rating


def test_export_player_match_ratings_one_row_per_appearance(tmp_path):
    net = make_list_network()
    net.add_player_rating(PlayerELORating())
    out = net.export_player_match_ratings(filename=str(tmp_path / "out.csv"))
    assert list(out.columns) == ["Player", "season", "round", "team_at", "rating", "date"]
    # Alpha A. played both matches: for A (home, round 1) then for A (away, round 2)
    alpha = out[out.Player == "Alpha A."].sort_values("round")
    assert len(alpha) == 2
    assert alpha.iloc[0]["team_at"] == "A" and alpha.iloc[0]["round"] == 1
    assert alpha.iloc[1]["team_at"] == "A" and alpha.iloc[1]["round"] == 2
    # after-match rating matches the live rating object for the last appearance
    rating = PlayerELORating()
    net.add_player_rating(rating)
    assert alpha.iloc[1]["rating"] == pytest.approx(rating.current["Alpha A."], abs=1e-9)
