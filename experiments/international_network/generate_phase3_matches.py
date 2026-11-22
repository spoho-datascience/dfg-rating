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


def generate(output_dir, teams, seed, severity, pure_cycle=False, probability_suite=False,
             rating_drift=5.0, period_points=400.0, peak_width=45.0, fixed_style_win=.90):
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
            delta=normal(0, rating_drift),
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
    if probability_suite:
        if pure_cycle:
            raise ValueError("probability suite requires the ordinary strength trajectories")
        base = pd.read_csv(output_dir / "olr.csv")
        base_probs = base[[f"true_forecast#{name}" for name in OUTCOMES]].to_numpy()
        style_home = np.where(style_effect == 1, fixed_style_win,
                              np.where(style_effect == -1, .95-fixed_style_win, .475))
        style_probs = np.column_stack([style_home, np.full(len(base), .05), .95 - style_home])
        probabilities = {
            f"direct_{int(weight * 100):03d}": (1 - weight) * base_probs + weight * style_probs
            for weight in (0.0, .5, .8, 1.0)
        }
        # Explicit probability table equivalent to the old severity=.7 pure
        # cycle: preserve the same-style draw signal as a positive control.
        favored_win = .9321377064230059
        favored_loss = .0013316552752606
        neutral_win = .11920292202211755
        legacy_home = np.where(style_effect == 1, favored_win,
                               np.where(style_effect == -1, favored_loss, neutral_win))
        legacy_away = np.where(style_effect == 1, favored_loss,
                               np.where(style_effect == -1, favored_win, neutral_win))
        probabilities["direct_legacy"] = np.column_stack([
            legacy_home, 1 - legacy_home - legacy_away, legacy_away
        ])
        highdraw_home = np.where(style_effect == 0, neutral_win, style_home)
        highdraw_draw = np.where(style_effect == 0, 1 - 2 * neutral_win, .05)
        probabilities["direct_highdraw"] = np.column_stack([
            highdraw_home, highdraw_draw, 1 - highdraw_home - highdraw_draw
        ])
        # No style labels enter these three maps. Fixed draw probability matches
        # the nonlinear controls; swapping teams reverses the decisive odds.
        monotone = 1 / (1 + np.exp(-.006 * diff))
        wave = .5 + .45 * np.sin(2 * np.pi * diff / period_points)
        reversal = np.where((np.abs(diff) >= 100) & (np.abs(diff) < 250), -1, 1)
        band = .5 + .45 * np.tanh(diff / 50) * reversal
        for name, decisive_home in (("monotone", monotone), ("wave", wave), ("band", band)):
            probabilities[f"nonolr_{name}"] = np.column_stack([
                .95 * decisive_home, np.full(len(base), .05), .95 * (1 - decisive_home)
            ])
        draw_peak = .05 + .75 * np.exp(-.5 * ((np.abs(diff) - 160) / peak_width) ** 2)
        probabilities["nonolr_draw"] = np.column_stack([
            (1 - draw_peak) * monotone, draw_peak, (1 - draw_peak) * (1 - monotone)
        ])
        for name, probs in probabilities.items():
            assert np.isfinite(probs).all() and (probs >= 0).all()
            np.testing.assert_allclose(probs.sum(axis=1), 1)
            frame = base.copy()
            frame[[f"true_forecast#{outcome}" for outcome in OUTCOMES]] = probs
            frame["Result"] = np.where(uniforms < probs[:, 0], "home", np.where(
                uniforms < probs[:, 0] + probs[:, 1], "draw", "away"))
            frame.to_csv(output_dir / f"{name}.csv", index=False)
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
    parser.add_argument("--probability-suite", action="store_true",
                        help="Add direct cyclic probability mixtures and nonmonotone strength maps.")
    parser.add_argument("--rating-drift", type=float, default=5.0,
                        help="Per-round strength increment standard deviation; zero gives static strengths.")
    parser.add_argument("--period-points", type=float, default=400.0,
                        help="Period of the periodic probability map, in rating-difference points.")
    parser.add_argument("--peak-width", type=float, default=45.0,
                        help="Gaussian width of the two draw peaks, in rating points.")
    parser.add_argument("--fixed-style-win", type=float, default=.90,
                        help="Favored-style win probability; draw stays .05 and loss is the remainder.")
    args = parser.parse_args()
    if args.teams < 6 or args.teams % 6:
        parser.error("--teams must be a positive multiple of six")
    if not np.isfinite(args.severity) or args.severity < 0:
        parser.error("--severity must be finite and nonnegative")
    if not np.isfinite(args.rating_drift) or args.rating_drift < 0:
        parser.error("--rating-drift must be finite and nonnegative")
    if args.probability_suite and args.pure_cycle:
        parser.error("--probability-suite cannot be combined with --pure-cycle")
    if not np.isfinite(args.period_points) or args.period_points <= 0:
        parser.error("--period-points must be finite and positive")
    if not np.isfinite(args.peak_width) or args.peak_width <= 0:
        parser.error("--peak-width must be finite and positive")
    if not np.isfinite(args.fixed_style_win) or not .475 <= args.fixed_style_win <= .95:
        parser.error("--fixed-style-win must be between .475 and .95")
    generate(args.output_dir, args.teams, args.seed, args.severity, args.pure_cycle,
             args.probability_suite, args.rating_drift, args.period_points, args.peak_width,
             args.fixed_style_win)
