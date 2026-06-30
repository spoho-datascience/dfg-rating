"""Compute and export player-level Elo ratings from real match data.

This script runs the full pipeline end-to-end on ``data_test.xlsx`` and writes one row
per player *appearance* to a CSV:

    Player, season, round, team_at, rating, date

where ``rating`` is the player's Elo **after** that match (Wolf, Schmitt & Schuller 2020,
formulas 6-10; see ``dfg_rating/model/rating/player_elo_rating.py``).

Why a few preprocessing steps are needed
----------------------------------------
``data_test.xlsx`` does not match the loader's expectations out of the box:

1. **Score column.** The clean final score lives in ``home_score_x`` / ``away_score_x``
   (integers, no gaps); ``*_y`` has missing values. We rename ``*_x`` -> ``home_score`` /
   ``away_score`` because ``PlayerELORating`` reads those names.
2. **No round column.** The source only has timestamps. The player rating is a *per-round*
   time series, so we synthesize ``round`` = the chronological match index within each
   season (1..N, ordered by ``date``). One unique round per match gives per-match
   resolution.
3. **Lineups as lists.** Players/minutes/goal-diffs are stored as per-side JSON lists
   (e.g. ``home_player_list``). The ``player-soccer-lists`` mapping tells ``WhiteNetwork``
   to parse them in "lists" mode and drop non-player tokens such as ``red_card_1``.

Players are identified by name; the rating follows the person across teams and seasons.

Usage
-----
    python -m experiments.player_elo_export.run \
        --input data_test.xlsx --output player_ratings.csv

(or run the file directly). Requires ``openpyxl`` for reading .xlsx.
"""
import argparse

import pandas as pd

from dfg_rating.model import factory
from dfg_rating.model.network.base_network import WhiteNetwork
from dfg_rating.model.rating.player_elo_rating import PlayerELORating

# Columns carried through to the network (match metadata + per-side lineup lists).
LINEUP_COLUMNS = [
    "home_player_list", "away_player_list",
    "home_minutes_list", "away_minutes_list",
    "home_goal_diff_list", "away_goal_diff_list",
]
KEEP_COLUMNS = [
    "season_id", "competition", "date", "home_team", "away_team",
    "home_score", "away_score", "result",
] + LINEUP_COLUMNS


def load_matches(input_path):
    """Read the workbook and shape it into the columns the loader expects."""
    df = pd.read_excel(input_path)
    # 1) Clean final score -> the names PlayerELORating reads.
    df = df.rename(columns={"home_score_x": "home_score", "away_score_x": "away_score"})
    # 2) Chronological round index within each season (the source has no rounds).
    df = df.sort_values(["season_id", "date"]).reset_index(drop=True)
    df["round"] = df.groupby("season_id").cumcount() + 1
    return df[KEEP_COLUMNS + ["round"]]


def build_network(df):
    """Construct the player-aware network from the prepared DataFrame."""
    return WhiteNetwork(data=df, mapping=factory.pre_mappings["player-soccer-lists"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data_test.xlsx", help="Path to the .xlsx match file")
    parser.add_argument("--output", default="player_ratings.csv", help="Output CSV path")
    parser.add_argument("--k", type=float, default=32.0, help="Elo k factor (paper range 24-40)")
    parser.add_argument("--q", type=float, default=0.75, help="Personal/team blend (paper range 0.5-1.0)")
    parser.add_argument("--initial-rating", type=float, default=1000.0, help="Starting rating for new players")
    args = parser.parse_args()

    print(f"Reading matches from {args.input} ...")
    df = load_matches(args.input)
    print(f"  {len(df)} matches, {df['season_id'].nunique()} season(s), "
          f"{pd.unique(df[['home_team', 'away_team']].values.ravel()).size} teams")

    print("Building network (parsing line-ups) ...")
    net = build_network(df)
    print(f"  {len(net.players)} distinct players imported")

    print("Computing player Elo ratings (formulas 6-10) ...")
    net.add_player_rating(PlayerELORating(k=args.k, q=args.q, initial_rating=args.initial_rating))

    print(f"Exporting per-appearance ratings to {args.output} ...")
    out = net.export_player_match_ratings(filename=args.output)
    print(f"  wrote {len(out)} rows for {out['Player'].nunique()} players")
    print("Done.")


if __name__ == "__main__":
    main()
