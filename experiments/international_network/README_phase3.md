# Phase 3 probability mechanisms

The existing OLR, local dip and additive cyclic-rating conditions are preserved.
Generate the additional probability suite with:

```sh
python -m experiments.international_network.generate_phase3_matches OUTPUT_DIR --teams 180 --seed 42 --probability-suite --rating-drift 5
```

Use `--rating-drift 0` for static latent strengths (same initial strengths and
fixtures). Three separate RNG streams control ratings, fixed balanced styles,
and outcome sampling; all probability mechanisms share the outcome uniforms.
`true_rating#*`, `true_forecast#*` and `team_styles.csv` are evaluation information,
not model inputs.

## Direct style probability mixture

For home style advantage, q=(.90,.05,.05); disadvantage reverses win/loss;
equal styles use (.475,.05,.475). In home/draw/away order:

`p = (1-weight) * p_OLR_strength + weight * q_style`

Files direct_000/050/080/100 correspond to weight 0/.5/.8/1.
The endpoint removes strength from the outcome mechanism, although strength
metadata remains available for paired comparisons. Direct_000 is the unchanged
ordinary OLR condition. This is a probability mixture, not an additive logit or
rating shift. Its draw frequency changes with mixture weight.

## Nonlinear probability shapes

Let d=home true strength minus away true strength. Matched constant-draw
conditions use draw=.05 and home=.95*q(d), away=.95*(1-q(d)):

- nonolr_monotone: q(d)=sigmoid(.006*d); monotonic control, not an exact OLR model.
- nonolr_wave: q(d)=.5+.45*sin(pi*d/200); periodic reversal, period 400.
- nonolr_band: q(d)=.5+.45*tanh(d/50)*b(d), with b=-1 for 100<=abs(d)<250,
  otherwise +1. Optional broad reversal condition, generated but not included
  in the initial forecasting screen.

nonolr_draw uses draw=.05+.75*exp(-.5*((abs(d)-160)/45)^2),
home=(1-draw)*sigmoid(.006*d), and away=(1-draw)*(1-sigmoid(.006*d)).
The draw shape changes while the decisive home-win function matches the control.
All nonlinear rules satisfy p_home(-d)=p_away(d) and p_draw(-d)=p_draw(d).

These are deliberately engineered diagnostics. Non-OLR generation does not
by itself establish Elo failure or GNN learnability; both require held-out
forecast comparisons. Elo can reorder ratings and refit the OLR slope.

## Same-style draw ablation and equivalence check

- direct_highdraw: same cross-style (.90,.05,.05) as direct_100; only
  equal-style probabilities change to (.1192029220,.7615941560,.1192029220).
  This isolates whether draws provide an easy same-style grouping signal.
- direct_legacy: explicit table equal to the previous pure-cycle severity=.7
  probabilities. Cross-style favored win=.9321377064, loss=.0013316553;
  equal styles use the high draw probabilities above. Its fixture keys,
  probabilities and outcomes reproduce the previous condition (floating-point
  tolerance only). No fresh model training is needed to establish this
  parameterization equivalence.

## Main four-mechanism sweep (one changed parameter at a time)

All settings use teams=180, seed=42 and the default rating trajectories.
Nonlinear maps retain their common default probabilities except for the swept
parameter. The direct-style mechanism ignores latent strengths in sampling;
the additive-score mechanism retains the strength term.

| Family | Parameter | Values |
| --- | --- | --- |
| Periodic outcome probabilities | --period-points | 200, 400, 800 |
| Two draw-probability peaks | --peak-width | 30, 45, 90 |
| Direct style probability table | --fixed-style-win | .475, .60, .80, .90 |
| Additive cyclic rating difference | --severity (times 250 points) | 0, .15, .30, .50, .70, 1 |

All three new flags require --probability-suite to affect probability-suite
outputs. Direct style draw probability remains .05, loss=.95-win, and
same-style probabilities stay (.475,.05,.475); .475 means zero cyclic edge.
The two-peak height stays .8 at ±160; changing width also changes probabilities
away from the peaks, including at zero rating difference. Use separate output
directories for every parameter setting. Existing defaults are unchanged.

## Staircase probability mechanism

`--probability-suite --staircase-width H` additionally writes
`nonolr_staircase.csv`. Let d be the true home-away rating difference.
Draw probability is .05. The decisive home share q is symmetric:

| d | q | absolute home-win probability |
| --- | --- | --- |
| d <= -2H | .10 | .0950 |
| -2H < d <= -H | .25 | .2375 |
| -H < d < H | .50 | .4750 |
| H <= d < 2H | .75 | .7125 |
| d >= 2H | .90 | .8550 |

The implementation defines threshold equality through abs(d), preserving
q(-d)=1-q(d); at d=-2H it uses .10 and at d=-H it uses .25.
Away probability is .95*(1-q). Default H=100, with experiment sweep50/100/200.
Fixtures, latent rating trajectories, split and outcome-sampling uniforms are
shared with all previous probability conditions. True values remain evaluation
information only. Existing mechanism formulas are unchanged.
