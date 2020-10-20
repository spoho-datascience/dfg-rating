import click

from dfg_rating.logic import controller
from dfg_rating.ui import commands, menu


@click.command()
@click.option('-i', is_flag=True, help='Enable interactive command line')
def cli(i):
    """Framework interaction menu"""
    main_controller = controller.Controller()
    menu.header()
    while 1:
        if i:
            action = menu.get_interactive_action()
        else:
            action = menu.get_action_from_list()
        if action < 0:
            pass
        else:
            commands.run(action, main_controller)
