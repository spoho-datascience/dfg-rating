import click
from dfg_rating.utils import command_line

from dfg_rating.logic.controller import Controller

actions = [
    'Show <networks | ratings | actions>',
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
            custom_key_value = click.prompt(value['label'], type=str)
            for read_key, read_value in command_line.read_custom_key_value(custom_key_value, value.get('cast', None)):
                params[read_key] = read_value
        elif value['type'] == "custom_class":
            params[key] = mc.get_new_class(value['cast'], automatic_params(mc, "classes", value['cast']))
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
    n_name = click.prompt('Name of the network', type=str)
    result, message = mc.load_network(n_name)
    if result:
        click.echo(click.style(f"{message}"))
    else:
        click.echo(click.style(f"{message}", fg='red'))

def save_network(mc):
    n_name = click.prompt('Name of the network', type=str)
    result, message = mc.save_network(n_name)


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
    params = automatic_params(mc, "forecast", f_type)
    mc.add_new_forecast(n_name, f_type, f_name, **params)
    pass


def new_bookmaker_error(mc):
    bme_type = click.prompt('Type of the bookmaker error', type=str)
    params = automatic_params(mc, "bookmaker_error", bme_type)
    return mc.new_bookmaker_error(bme_type, **params)


def new_bookmaker_margin(mc):
    bmm_type = click.prompt('Type of the bookmaker margin', type=str)
    params = automatic_params(mc, "bookmaker_margin", bmm_type)
    return mc.new_bookmaker_margin(bmm_type, **params)


def create_bookmaker(mc):
    bm_name = click.prompt('Name of the bookmaker', type=str)
    bm_type = click.prompt('Type of the bookmaker', type=str)
    params = automatic_params(mc, 'bookmaker', bm_type)
    bm_error = new_bookmaker_error(mc)
    bm_margin = new_bookmaker_margin(mc)
    mc.create_bookmaker(bm_name, bm_type, error=bm_error, margin=bm_margin, **params)


def create_betting_strategy(mc):
    bs_name = click.prompt('Name of the Betting strategy', type=str)
    bs_type = click.prompt('Type of the Betting strategy', type=str)
    params = automatic_params(mc, 'betting', bs_type)
    mc.create_betting_strategy(bs_name, bs_type, **params)


def new_betting(mc):
    pass


def run(action, mc: Controller):
    # Show actions
    if action == 1:
        click.echo(click.style(
            "actions | networks | ratings",
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
        network_name = click.prompt('Name of the network', type=str)
        bookmaker_name = click.prompt('Name of the bookmaker', type=str)
        mc.add_odds(network_name, bookmaker_name)
    # Create Betting strategy
    elif action == 11:
        create_betting_strategy(mc)
    # Bet
    elif action == 12:
        new_betting(mc)
    # Default
    else:
        click.echo(click.style('Command not implemented yet', fg='white'))
