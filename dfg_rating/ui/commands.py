import click

from dfg_rating.logic.controller import Controller

actions = [
    'Show <networks | ratings | actions>',
    'Create Network',
    'Load Network',
    'Print Network',
    'Add new rating',
]


def create_network(mc):
    n_name = click.prompt('Name of the network', type=str)
    n_type = click.prompt('Type of network', type=str)
    params = {}
    for key, value in mc.inputs['network'][n_type].items():
        params[key] = click.prompt(value['label'], type=value['type'])
    mc.new_network(n_name, n_type, params)
    click.echo(params)


def add_new_rating(mc):
    n_name = click.prompt('Name of the network', type=str)
    team_id = click.prompt('Team identifier', type=int)
    r_type = click.prompt('Type of rating (function)', type=str)
    r_name = click.prompt('Name of the rating', type=str)
    if r_type == 'function':
        func_name = click.prompt('Distribution method (normal)', type=str)
        if func_name != 'normal':
            click.echo(click.style("Method not known", fg='red'))
            return
        loc = click.prompt('Mean', type=str)
        scale = click.prompt('Standard deviation (non-negative)', type=int)
    else:
        pass

    mc.add_new_rating(n_name, team_id, r_type, r_name, func_name, loc, scale)
    pass


def run(action, mc: Controller):
    if action == 1:
        click.echo(click.style("actions | networks", fg='white'))
        attribute = click.prompt("-> ", type=str)
        if attribute == 'actions':
            for action in actions:
                click.echo(action)
        else:
            for object_name, object_type in mc.list(attribute):
                click.echo(click.style(f"- {object_name}: {object_type}", fg='white'))
    elif action == 2:
        create_network(mc)
    elif action == 4:
        success, message = mc.print_network(click.prompt("Name of the network", type=str))
        if not success:
            click.echo(click.style(message, fg='red'))
    elif action == 5:

        add_new_rating(mc)
    else:
        click.echo(click.style('Command not implemented yet', fg='white'))
