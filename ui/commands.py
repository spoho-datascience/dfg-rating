from typing import List

import click

from logic.controller import Controller

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
    r_type = click.prompt('Type of rating', type=str)
    mc.add_new_rating(n_name, r_type)
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

    elif action == 4:
        add_new_rating(mc)
    else:
        click.echo(click.style('Command not implemented yet', fg='white'))
