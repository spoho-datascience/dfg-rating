"""setuptools setup module

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
"""
from setuptools import setup, find_packages

setup(
    name='dfg_rating',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'Networkx'
    ],
    entry_points={
        "console_scripts": [
            'dfg_rating=dfg_rating.client:cli',
            'dfg_viz=dfg_rating.client:viz'
        ]
    },
    author='Marc Garnica Caparrós',
    author_email='m.garnica@dshs-koeln.de'
)
