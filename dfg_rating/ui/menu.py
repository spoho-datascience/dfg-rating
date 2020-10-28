import click
from dfg_rating.ui.commands import actions


def header():
    click.echo(click.style("Rating Simulation Framework V0.1- Deutsche Sporthochschule Köln", bold=True, fg='white'))


def get_action_from_list():
    click.echo(click.style("Commands:", bold=True))
    for index, label in enumerate(actions):
        click.echo(f"{index + 1} - {label}")

    action = click.prompt('Select a command', type=int)
    if (action < 0) or (action > len(actions)):
        return -1
    else:
        click.echo(click.style(f"{actions[action - 1]} selected", fg='yellow'))
        return action


def get_interactive_action():
    while 1:
        command = click.prompt('$ ', type=str)
        parsed_command = command.replace(" ", "_").lower()
        if command.startswith("show"):
            return 1
        for index, action in enumerate(actions):
            if action.replace(" ", "_").lower() == parsed_command:
                return index + 1
        return -1
