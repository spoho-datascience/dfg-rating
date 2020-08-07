import click
from logic import controller
from ui import menu, commands


@click.command()
@click.option('-i', is_flag=True)
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
