import click

from dfg_rating.model import factory
from dfg_rating.utils import command_line

from dfg_rating.logic.controller import Controller

actions = [
    'Show entities',
    'Create Network',
    'Load Network',
    'Save Network',
    'Simulate results',
    'Print Network',
    'Add new rating',
    'Add new forecast',
    'Create Bookmaker',
    'Add betting odds',
    'Create Betting Strategy',
    'Bet'
]


def automatic_params(mc, entity: str, entity_type):
    params = {}
    for key, value in mc.inputs[entity][entity_type].items():
        if value['type'] == "custom_args_list":
            prompt_value = click.prompt(value['label'], type=str)
            if prompt_value != "-":
                params[key] = command_line.read_args_list(prompt_value, cast=value.get('cast', None))
        elif value['type'] == "custom_key_value":
            custom_key_value = click.prompt(value['label'], type=str).replace(" ", "").lower()
            for read_key, read_value in command_line.read_custom_key_value(custom_key_value, value.get('cast', None)):
                params[read_key] = read_value
        elif value['type'] == "custom_class":
            click.echo(value['label'])
            params[key] = mc.get_new_class(value['cast'], **automatic_params(mc, "classes", value['cast']))
        else:
            params[key] = click.prompt(value['label'], type=value['type'])
    return params


def create_network(mc):
    n_name = click.prompt('Name of the network', type=str)
    n_type = click.prompt('Type of network', type=str)
    params = automatic_params(mc, "network", n_type)
    mc.new_network(n_name, n_type, **params)
    pass


def load_network(mc):
    load_type = click.prompt('Loading from (sql | tabular-file)', type=str)
    n_name = click.prompt('Name of the network', type=str)
    result = 0
    if load_type == 'sql':
        result, message = mc.load_network_from_sql(n_name)
    elif load_type == 'tabular-file':
        file_path = click.prompt('File path', type=click.Path(exists=True))
        mapping_options = list(factory.pre_mappings.keys())
        click.echo(click.style(
            " | ".join(mapping_options),
            fg='white'
        ))
        new_mapping = click.prompt('Load mapping', type=str)
        click.echo(click.style("Loading network"))
        result, message = mc.load_network_from_tabular(n_name, file_path, new_mapping)
    if result:
        click.echo(click.style(f"{message}"))
    else:
        click.echo(click.style(f"{message}", fg='red'))


def save_network(mc):
    save_type = click.prompt('Save mode (sql | csv)', type=str)
    n_name = click.prompt('Name of the network', type=str)
    if save_type == 'sql':
        result, message = mc.save_network(n_name)
        click.echo(click.style(message, fg='white' if result == 1 else 'red'))
    elif save_type == 'csv':
        result, message = mc.export_network(
            n_name
        )


def add_new_rating(mc):
    n_name = click.prompt('Name of the network', type=str)
    r_name = click.prompt('Name of the rating', type=str)
    r_type = click.prompt('Type of rating', type=str)
    params = automatic_params(mc, "rating", r_type)
    mc.add_new_rating(n_name, r_type, r_name, **params)
    pass


def add_new_forecast(mc):
    n_name = click.prompt('Name of the network', type=str)
    f_name = click.prompt('Name of the forecast', type=str)
    f_type = click.prompt('Type of forecast', type=str)
    rating_options = mc.get_ranking_list(n_name)
    click.echo(click.style(
        " | ".join(rating_options),
        fg='white'
    ))
    r_name = click.prompt('Base rating for the forecast', type=str)
    params = automatic_params(mc, "forecast", f_type)
    mc.add_new_forecast(n_name, f_type, f_name, r_name, **params)
    pass


def new_forecast_error(mc):
    add_forecast_error = click.confirm("Add error to base forecast?", default=False)
    if add_forecast_error:
        bme_type = click.prompt('Type of the bookmaker error', type=str)
        params = automatic_params(mc, "bookmaker_error", bme_type)
        return mc.new_forecast_error(bme_type, **params)
    return None


def new_bookmaker_margin(mc):
    bmm_type = click.prompt('Type of the bookmaker margin', type=str)
    params = automatic_params(mc, "bookmaker_margin", bmm_type)
    return mc.new_bookmaker_margin(bmm_type, **params)


def create_bookmaker(mc):
    bm_name = click.prompt('Name of the bookmaker', type=str)
    bm_type = click.prompt('Type of the bookmaker', type=str)
    params = automatic_params(mc, 'bookmaker', bm_type)
    f_error = new_forecast_error(mc)
    bm_margin = new_bookmaker_margin(mc)
    mc.create_bookmaker(bm_name, bm_type, error=f_error, margin=bm_margin, **params)


def create_betting_strategy(mc):
    bs_name = click.prompt('Name of the Betting strategy', type=str)
    bs_type = click.prompt('Type of the Betting strategy', type=str)
    f_error = new_forecast_error(mc)
    params = automatic_params(mc, 'betting', bs_type)
    params['error'] = f_error
    mc.create_betting_strategy(bs_name, bs_type, **params)


def add_odds(mc):
    network_name = click.prompt('Name of the network', type=str)
    bookmaker_name = click.prompt('Name of the bookmaker', type=str)
    forecast_options = mc.get_forecasts_list()
    click.echo(click.style(
        " | ".join(forecast_options), fg='white')
    )
    base_forecast = click.prompt('Base forecast for the bookmaker', type=str)
    mc.add_odds(network_name, bookmaker_name, base_forecast)


def add_bets(mc):
    network_name = click.prompt('Name of the network', type=str)
    betting_name = click.prompt('Name of the bettings strategy', type=str)
    bookmaker_name = click.prompt('Name of the bookmaker', type=str)
    forecast_options = mc.get_forecasts_list()
    click.echo(click.style(
        " | ".join(forecast_options),
        fg='white'
    ))
    base_forecast = click.prompt('Base forecast for the betting', type=str)
    mc.add_bets(network_name, bookmaker_name, betting_name, base_forecast)


def run(action, mc: Controller):
    # Show actions
    if action == 1:
        click.echo(click.style(
            "actions | networks | bookmakers | betting_strategies",
            fg='white'
        ))
        attribute = click.prompt("-> ", type=str)
        if attribute == 'actions':
            for action in actions:
                click.echo(action)
        else:
            for object_name, object_type in mc.list(attribute):
                click.echo(click.style(f"- {object_name}: {object_type}", fg='white'))
    # Create Network
    elif action == 2:
        create_network(mc)
    # Load Network
    elif action == 3:
        load_network(mc)
    # Save Network
    elif action == 4:
        save_network(mc)
    # Simulate results
    elif action == 5:
        network_name = click.prompt('Name of the network', type=str)
        mc.play_network(network_name)
    # Print Network
    elif action == 6:
        network_name = click.prompt("Name of the network", type=str)
        params = {}
        args_list = click.prompt("Elements to print: ", type=str)
        for read_key in command_line.read_args_list(args_list):
            params[read_key] = True
        success, message = mc.print_network(network_name, **params)
        if not success:
            click.echo(click.style(message, fg='red'))
    # Add new Rating
    elif action == 7:
        add_new_rating(mc)
    # Add new Forecast
    elif action == 8:
        add_new_forecast(mc)
    # Create Bookmaker
    elif action == 9:
        create_bookmaker(mc)
    # Add odds
    elif action == 10:
        add_odds(mc)
    # Create Betting strategy
    elif action == 11:
        create_betting_strategy(mc)
    # Bet
    elif action == 12:
        add_bets(mc)
    # Default
    else:
        click.echo(click.style('Command not implemented yet', fg='white'))
