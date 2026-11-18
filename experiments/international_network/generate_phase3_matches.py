"""Generate paired OLR, win-probability dip, and cyclic-style round robins.

Run from the repository root with:
    python -m experiments.international_network.generate_phase3_matches OUTPUT_DIR

Each condition shares fixtures, pre-match strengths and sampling uniforms.
Use --pure-cycle to generate a stress test with equal team strengths, no home
advantage, and outcomes determined by style. Use true_rating#*, true_forecast#*,
and team_styles.csv for evaluation only.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import (
    ControlledRandomFunction,
    ControlledTrendRating,
)


OUTCOMES = ("home", "draw", "away")
CYCLE = np.array([[0, 1, -1], [-1, 0, 1], [1, -1, 0]])


def generate(output_dir, teams, seed, severity, pure_cycle=False):
    rating_seed, style_seed, draw_seed = np.random.SeedSequence(seed).spawn(3)
    rating_rng = np.random.default_rng(rating_seed)
    style_rng = np.random.default_rng(style_seed)
    draw_rng = np.random.default_rng(draw_seed)

    def normal(loc, scale):
        return ControlledRandomFunction(
            distribution="normal", loc=loc, scale=scale, random_number_generator=rating_rng
        )

    network = RoundRobinNetwork(teams=teams, days_between_rounds=1, create=False, play=False)
    network.fill_graph()
    if not pure_cycle:
        rating = ControlledTrendRating(
            starting_point=normal(1000, 100),
            delta=normal(0, 5),
            trend=normal(0, 0),
            season_delta=normal(0, 0),
            rating_name="true_rating",
            random_number_generator=rating_rng,
        )
        network.add_rating(rating, "true_rating", season=0)
    rows = []
    for away, home, _, match in network.iterate_over_games():
        day, round_id = match["day"], match["round"]
        if pure_cycle:
            home_rating = away_rating = 1000.0
        else:
            home_rating = network.data.nodes[home]["ratings"]["true_rating"][0][round_id]
            away_rating = network.data.nodes[away]["ratings"]["true_rating"][0][round_id]
        rows.append({
            "Home": home,
            "Away": away,
            "Season": 0,
            "Round": round_id,
            "Day": day,
            "true_rating#Home": home_rating,
            "true_rating#Away": away_rating,
        })
    matches = pd.DataFrame(rows)
    matches["League_ID"] = 0
    matches["Competition"] = 0
    matches["state"] = "active"
    matches["competition_type"] = "League"

    styles = style_rng.permutation(np.arange(teams) % 3)
    uniforms = draw_rng.random(len(matches))
    style_effect = CYCLE[styles[matches["Home"]], styles[matches["Away"]]]
    if pure_cycle:
        differences = {"pure_cycle": severity * 1100 * style_effect}
        coefficients = [-2.0, 2.0]
    else:
        diff = (matches["true_rating#Home"] - matches["true_rating#Away"]).to_numpy()
        # An odd perturbation makes the favored side's win probability dip for either sign.
        positive_bump = np.exp(-0.5 * ((diff - 220) / 60) ** 2)
        negative_bump = np.exp(-0.5 * ((diff + 220) / 60) ** 2)
        differences = {
            "olr": diff,
            "dip": diff - severity * 180 * (positive_bump - negative_bump),
            "cycle": diff + severity * 250 * style_effect,
        }
        coefficients = [-0.9, 0.3]
    forecast = LogFunctionForecast(outcomes=OUTCOMES, coefficients=coefficients, beta_parameter=0.006)
    output_dir.mkdir(parents=True, exist_ok=True)
    for condition, effective_diff in differences.items():
        frame = matches.copy()
        p_away = forecast.logit_link_function(1, effective_diff)
        p_not_home = forecast.logit_link_function(2, effective_diff)
        frame["true_forecast#away"] = p_away
        frame["true_forecast#draw"] = p_not_home - p_away
        frame["true_forecast#home"] = 1 - p_not_home
        frame["Result"] = np.where(
            uniforms < 1 - p_not_home, "home", np.where(uniforms < 1 - p_away, "draw", "away")
        )
        frame.to_csv(output_dir / f"{condition}.csv", index=False)
    pd.DataFrame({"Team": np.arange(teams), "Style": styles}).to_csv(
        output_dir / "team_styles.csv", index=False
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--teams", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--severity", type=float, default=1.0)
    parser.add_argument("--pure-cycle", action="store_true", help="Generate the style-only condition.")
    args = parser.parse_args()
    if args.teams < 6 or args.teams % 6:
        parser.error("--teams must be a positive multiple of six")
    if not np.isfinite(args.severity) or args.severity < 0:
        parser.error("--severity must be finite and nonnegative")
    generate(args.output_dir, args.teams, args.seed, args.severity, args.pure_cycle)
