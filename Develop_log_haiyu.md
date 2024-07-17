# international competition
## national league
* n leagues within country
* games within league, two leg
* games between league, one leg
* prob control a game
* ranking control
* promotion
## international league
* n countries within international league
* choose team from 1st level

## logs
### 2024.07.03-04
reading code
consider national network first, don't consider multi-season, no promotion first
finished control number of teams per league, prob of games inter league, one leg control
Principle is not change existing code, adding functions..

### 2024.07.05
two ways to build a international network:
* create country league, re-lable and compose country networks (call countryleague class)
in this way, the function between nations may need to rewrite in the future.

* create a big graph first, then cluster nation, cluster leagues (edit from CountryLeague class)
in this way, the country league class should able to handle specific given team_id
Seems some functions in the RoundRobin cannot be used instantly by given team_id
Finished given team_id network build in countryLeague() (changed teams_list generate in RoundRobin (line 35-53))

### 2024.07.06
finished the structure of composing national network in international network

### 2024.07.08
finish the international network's country config reading
tested the national network with 3 levels, with same true_rating and true_forecasting

### 2024.07.09
finish the rating part of nation network, can control each level's rating now (added a new_cluster_rating function in ControlledRandomFunction)

### 2024.07.10
finish the forecast part of nation network
fixed the rating problem (fix the rating_values sent to self._add_rating_to_team)
tested national network with different team number setting, diff rating setting

### 2024.07.15
read the Ranking Rating code
finish the promotion and relegation structure, the logic in LeagueNetwork is quite simple, will not just use it

### 2024.07.16
Add the Ranking function, based on ranking after each season select promotion and relegation
Finish the logic that each rating only matters with each team, doesn't matter which level the team is in

### 2024.07.17
Add multi season, tested multi season promotion and relegation
One problem existing is when calculate ranking, considered all matches (including national cup)
International league is gonna based on countryLeague network