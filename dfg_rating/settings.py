import os

DIR_PATH = os.path.abspath(os.path.dirname(__file__))


def get_relative_path(relative_path):
    return os.path.join(DIR_PATH, relative_path)
