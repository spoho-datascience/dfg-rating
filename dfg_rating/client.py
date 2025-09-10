"""Main client class handling the command line interface

"""
import click

from dfg_rating.logic import controller
from dfg_rating.ui import commands, menu
from dfg_rating.ui import gui


@click.command()
@click.option('-i', is_flag=True, help='Enable interactive command line')
def cli(i: bool):
    """Framework interaction menu

    While(true) loop. Executes the commands specified by command line and shows results

    Args:
        i: Optional; If i is True the interface is interactive by text
    """
    main_controller = controller.Controller()
    menu.header()
    while 1:
        try:
            if i:
                action = menu.get_interactive_action()
            else:
                action = menu.get_action_from_list()
            if action < 0:
                pass
            else:
                commands.run(action, main_controller)
        except KeyError as key_error_exception:
            click.echo(
                click.style(f"Method or argument [{key_error_exception.args[0]}] not present in the system", fg='red'))
            pass
        except ValueError as value_error:
            click.echo(click.style(f"Factory error [{value_error.args[0]}]", fg='red'))
            print(value_error.args)
            pass
        except click.exceptions.Abort:
            click.echo(click.style(" \b Closing session and connections", fg='white'))
            main_controller.close()
            break
        except KeyboardInterrupt as k:
            click.echo(click.style(" \b Closing session and connections", fg='white'))
            main_controller.close()
            break
        except Exception as e:
            click.echo(click.style('Error in the execution consult logs', fg='red'))
            print(e)
            pass


def viz():
    """Launches Visualization App"""
    gui.init()
