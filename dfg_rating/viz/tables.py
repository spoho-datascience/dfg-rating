import dash_table


def bettings_tables(df):
    return dash_table.DataTable(
        id="bettings-table",
        columns=[
            {"name": ["Match", "HomeTeam"], "id": "HomeTeam"},
            {"name": ["Match", "AwayTeam"], "id": "AwayTeam"},
            {"name": ["Match", "Season"], "id": "Season"},
            {"name": ["Match", "Round"], "id": "Round"},
            {"name": ["Match", "Result"], "id": "Result"},
            {"name": ["True forecast", "Home"], "id": "true_forecast#home"},
            {"name": ["True forecast", "Draw"], "id": "true_forecast#draw"},
            {"name": ["True forecast", "Away"], "id": "true_forecast#away"},
            {"name": ["Simple bookmaker odds", "Home"], "id": "odds#home"},
            {"name": ["Simple bookmaker odds", "Draw"], "id": "odds#draw"},
            {"name": ["Simple bookmaker odds", "Away"], "id": "odds#away"},
            {"name": ["ELO forecast", "Home"], "id": "elo_forecast#home"},
            {"name": ["ELO forecast", "Draw"], "id": "elo_forecast#draw"},
            {"name": ["ELO forecast", "Away"], "id": "elo_forecast#away"},
            {"name": ["ELO bets", "Home"], "id": "bet#home"},
            {"name": ["ELO bets", "Draw"], "id": "bet#draw"},
            {"name": ["ELO bets", "Away"], "id": "bet#away"},
            {"name": ["Expected returns", "Home"], "id": "expected#bet#home"},
            {"name": ["Expected returns", "Draw"], "id": "expected#bet#draw"},
            {"name": ["Expected returns", "Away"], "id": "expected#bet#away"},
            {"name": ["Actual returns", "Home"], "id": "return#bet#home"},
            {"name": ["Actual returns", "Draw"], "id": "return#bet#draw"},
            {"name": ["Actual returns", "Away"], "id": "return#bet#away"},
        ],
        merge_duplicate_headers=True,
        data=df.to_dict('records'),
        style_header={
            'backgroundColor': 'white',
            'fontWeight': 'bold',
        },
        style_cell={
            'textAlign': 'left',
            'whiteSpace': 'pre-line',
            'height': 'auto',
        },
        sort_action='native',
        page_size=20,
        page_action='native',
        filter_action='native'
    )
