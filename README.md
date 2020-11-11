# dfg-rating: Artificial data generator for sports forecasting research
This research project aims at the validation and development of rating methods from which predictions can be extracted and which are based on networks of pair-by-pair comparisons

## Conceptual design

Check the complete entity diagram of the system [here](./docs/entity_diagram.pdf).

## Definitions

 - Match between teams are defined in a network.
 - A network structure scope can be a subset of games as well as one or multiple seasons in a sports competition.
 - Each games involves two competitors (teams or players in case of tennis).
 - Games have a round and date associated.
 - Games have 1..n forecasts. One forecast must be named 'true_forecast'.
 - Observed results can be computed by considering the true forecast of each game.
 - Bookmakers are the responsible classes to create certain betting odds per each outcome of each game.
 - Bookmakers are defined by:
  - A bookmaker error that transforms the true game forecast into a bookmaker forecast.
  - A margin that is applied to the odds computation.
 - Each team in the network have 0..m ratings. If a certain team has a rating value of x<sub>i</sub>, means that this team rating at round i was x.
 - Once betting odds are computed, a bettor can post bets on each game and evaluate the consequences.
