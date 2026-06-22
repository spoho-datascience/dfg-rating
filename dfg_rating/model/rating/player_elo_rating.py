import numpy as np

from dfg_rating.model.network.base_network import BaseNetwork, TeamId, base_edge_filter
from dfg_rating.model.rating.base_rating import BaseRating


class PlayerELORating(BaseRating):
    """Player-level Elo rating (Wolf, Schmitt & Schuller 2020, formulas 6-10).

    Players are rated individually. A team's rating for a match is the minute-weighted
    mean of its lineup's player ratings (formula 6). Player ratings **persist across
    seasons and team changes** (the scalar follows the player, not the team) -- this is
    the key behavioural divergence from team Elo, which reinitialises per season.

    The model reads each match's ``edge['lineups']`` (populated by ``WhiteNetwork``'s
    player-import mode) and, as a side effect, writes per-player rating time series into
    ``network.players[pid]['ratings'][rating_name][season]``. ``get_all_ratings`` returns
    the derived per-match *team* rating ``R_A`` as the standard ``[n_teams, n_rounds+2]``
    team matrix so the existing forecast / betting / export pipeline keeps working.

    Configurable parameters (``k``, ``q``, ``w`` accept a scalar or a callable):
      - ``k`` player adjustment factor (paper range 24-40, default 32)
      - ``q`` personal-vs-team weighting (paper range 0.5-1.0, default 0.75)
      - ``w`` match-importance weight (default 1.0)
      - ``initial_rating`` rating for unseen players (default ``rating_mean`` = 1000)
      - ``m_max`` maximum minutes (default 90)
    """

    def __init__(self, **kwargs):
        super().__init__('player-elo', **kwargs)
        self.rating_name = kwargs.get('rating_name', 'player_elo_rating')
        self.initial_rating = kwargs.get('initial_rating', self.rating_mean)
        self.m_max = kwargs.get('m_max', 90.0)
        self.home_score_key = kwargs.get('home_score_key', 'home_score')
        self.away_score_key = kwargs.get('away_score_key', 'away_score')
        w = kwargs.get('w', 1.0)
        k = kwargs.get('k', 32.0)
        q = kwargs.get('q', 0.75)
        self.w_fn = w if callable(w) else (lambda **ctx: w)
        self.k_fn = k if callable(k) else (lambda pid, **ctx: k)
        self.q_fn = q if callable(q) else (lambda pid, **ctx: q)
        self.props = {}
        self.current = {}  # player_id -> current scalar rating (persists across seasons)

    # --- exact formula helpers -------------------------------------------------
    @staticmethod
    def expected(r_self, r_opp):
        """Formula 7 / team E_A: E = 1 / (1 + 10^((R_opp - R_self)/400))."""
        return 1.0 / (1.0 + 10.0 ** ((r_opp - r_self) / 400.0))

    @staticmethod
    def score_from_diff(d):
        """Formula 8 / team S_A from (personal or team) goal difference."""
        if d > 0:
            return 1.0
        if d == 0:
            return 0.5
        return 0.0

    def team_rating(self, roster):
        """Formula 6: R_A = sum(R_i * M_i) / sum(M_i) over the lineup.

        Lazily seeds unseen players to ``initial_rating`` in ``self.current``.
        """
        num = 0.0
        den = 0.0
        for p in roster:
            r = self.current.setdefault(p['player_id'], self.initial_rating)
            num += r * p['minutes']
            den += p['minutes']
        return num / den if den > 0 else self.initial_rating

    def individual_change(self, s, e, d, minutes, w):
        """Formula 9: C_Ai = w*(S-E)*|D|^(1/3) if D != 0 else w*(S-E)*(M/M_max)."""
        if d != 0:
            return w * (s - e) * (abs(d) ** (1.0 / 3.0))
        return w * (s - e) * (minutes / self.m_max)

    def team_change(self, s_a, e_a, d_a, w):
        """Team overall change C_A = w*(S_A - E_A)*|D_A|^(1/3) (0 on a drawn match)."""
        return w * (s_a - e_a) * (abs(d_a) ** (1.0 / 3.0))

    # --- per-match update ------------------------------------------------------
    def _process_match(self, match_data):
        """Apply formulas 6-10 for one match, mutating ``self.current``.

        Returns ``(r_home, r_away)`` -- the pre-match minute-weighted team ratings
        (formula 6), used as the derived team rating stored for each side.
        """
        lineups = match_data['lineups']
        home_roster = lineups['home']
        away_roster = lineups['away']
        # Formula 6 -- pre-match team ratings from CURRENT player ratings.
        r_home = self.team_rating(home_roster)
        r_away = self.team_rating(away_roster)
        home_goals = match_data[self.home_score_key]
        away_goals = match_data[self.away_score_key]
        w = self.w_fn(match=match_data)
        # Team-level change C_A for each side (drives the (1-q) term of formula 10).
        d_home = home_goals - away_goals
        d_away = away_goals - home_goals
        c_team_home = self.team_change(self.score_from_diff(d_home), self.expected(r_home, r_away), d_home, w)
        c_team_away = self.team_change(self.score_from_diff(d_away), self.expected(r_away, r_home), d_away, w)
        # Compute all new ratings from the pre-match snapshot, commit afterwards
        # (no intra-match order dependence).
        updates = {}
        for roster, r_opp, c_team in (
            (home_roster, r_away, c_team_home),
            (away_roster, r_home, c_team_away),
        ):
            for p in roster:
                pid = p['player_id']
                r_old = self.current[pid]  # already seeded by team_rating
                minutes = p['minutes']
                d_i = p['goal_diff']
                e_i = self.expected(r_old, r_opp)              # formula 7
                s_i = self.score_from_diff(d_i)                 # formula 8
                c_i = self.individual_change(s_i, e_i, d_i, minutes, w)  # formula 9
                k_i = self.k_fn(pid, match=match_data)
                q_i = self.q_fn(pid, match=match_data)
                change = k_i * (q_i * c_i + (1 - q_i) * c_team * (minutes / self.m_max))  # formula 10
                updates[pid] = r_old + change
        self.current.update(updates)
        return r_home, r_away

    # --- BaseRating interface --------------------------------------------------
    def get_all_ratings(self, n: BaseNetwork, edge_filter=None, season=None):
        edge_filter = edge_filter or base_edge_filter
        seasons = n.get_seasons()
        if season is None:
            season = seasons[0]
        # Reset persistent state at the first season so repeated full runs are idempotent.
        if season == seasons[0]:
            self.current = {}
        self.teams = list(n.data.nodes)
        n_teams = len(self.teams)
        n_rounds, round_values = n.get_rounds()
        team_index = {t: i for i, t in enumerate(self.teams)}
        ratings = np.full([n_teams, n_rounds + 2], float(self.initial_rating))

        # Season-start snapshot for player report series (carried from previous season).
        season_start = dict(self.current)
        games_by_round = {}
        for a, h, k, d in filter(edge_filter, n.data.edges(keys=True, data=True)):
            if 'lineups' in d:
                games_by_round.setdefault(d['round'], []).append((a, h, k, d))

        player_series = {}

        def ensure_series(pid):
            if pid not in player_series:
                arr = [None] * (n_rounds + 2)
                arr[0] = season_start.get(pid, self.initial_rating)
                player_series[pid] = arr
            return player_series[pid]

        for r in range(n_rounds):
            pos = r + 1
            r_value = round_values[r]
            teams_playing = set()
            for a, h, k, d in games_by_round.get(r_value, []):
                r_home, r_away = self._process_match(d)
                ratings[team_index[h], pos] = r_home
                ratings[team_index[a], pos] = r_away
                teams_playing.update([h, a])
                for p in d['lineups']['home'] + d['lineups']['away']:
                    ensure_series(p['player_id'])[pos] = self.current[p['player_id']]
            for ti, t in enumerate(self.teams):
                if t not in teams_playing:
                    ratings[ti, pos] = ratings[ti, pos - 1]
        ratings[:, n_rounds + 1] = ratings[:, n_rounds]

        # Forward-fill player series and store on the network registry.
        for pid, arr in player_series.items():
            last = arr[0]
            for i in range(n_rounds + 2):
                if arr[i] is None:
                    arr[i] = last
                else:
                    last = arr[i]
            n.players.setdefault(pid, {'ratings': {}, 'teams': {}}).setdefault(
                'ratings', {}
            ).setdefault(self.rating_name, {})[season] = arr

        return ratings, self.props

    def get_ratings(self, n: BaseNetwork, t: [TeamId], edge_filter=None):
        raise NotImplementedError(
            "PlayerELORating rates all players in one pass; use add_player_rating / add_rating."
        )
