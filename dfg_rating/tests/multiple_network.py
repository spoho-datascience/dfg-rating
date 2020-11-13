from dfg_rating.model.network.multiple_network import LeagueNetwork

multiple_network = LeagueNetwork(
    teams=4,
    seasons=1,
    league_teams=3
)
multiple_network.create_data()
multiple_network.all_teams_have_true_rating()
multiple_network.print_data(schedule=True)
