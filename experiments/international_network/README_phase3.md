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
