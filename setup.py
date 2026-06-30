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
    python_requires='>=3.9',
    # Core runtime needed to build networks and compute ratings (the model
    # package + the experiments/player_elo_export notebook). Optional
    # subsystems live in extras_require so the base install stays lean.
    install_requires=[
        'numpy>=2.0',
        'pandas>=2.2',
        'scipy>=1.11',
        'scikit-learn>=1.4',
        'networkx>=3.2',
        'tqdm>=4.60',
        'openpyxl>=3.1',   # read the .xlsx match data
        'xlrd>=2.0',
        'click>=7.1,<8',   # held <8 so a combined install with the Dash 1.x UI resolves
    ],
    extras_require={
        # Dash 1.x is pure-python and pinned to preserve its split-package
        # imports (dash_html_components, dash_core_components, ...). It requires
        # the Flask 1.x world and setuptools<81 (Dash 1.20 imports pkg_resources).
        'viz': [
            'dash==1.20.0',
            'dash-bootstrap-components==0.10.7',
            'dash-core-components==1.16.0',
            'dash-html-components==1.1.3',
            'dash-table==4.11.3',
            'dash-renderer==1.9.1',
            'dash-cytoscape==0.2.0',
            'dash-daq==0.5.0',
            'jupyter-dash==0.4.0',
            'plotly>=5.0',
            'matplotlib>=3.8',
            'halo>=0.0.31',
            'Flask>=1.1,<2',
            'Werkzeug>=1.0,<2',
            'Jinja2>=2.11,<3',
            'MarkupSafe>=2.0,<2.1',
            'itsdangerous>=1.1,<2',
            'setuptools<81',
        ],
        'db': ['psycopg2-binary>=2.9'],
        'stats': ['statsmodels>=0.14'],
        # Notebook + tests. nbconvert<6.5 / notebook<7 keep Jinja2 2.x so the
        # viz extra's Flask 1.x stack stays installable in the same environment.
        'dev': [
            'pytest>=7.0',
            'notebook>=6.4,<7',
            'nbconvert>=6.0,<6.5',
            'ipykernel>=6.0',
            'ipywidgets>=7,<8',
            'matplotlib>=3.8',
        ],
    },
    entry_points={
        "console_scripts": [
            'dfg_rating=dfg_rating.client:cli',
            'dfg_viz=dfg_rating.client:viz'
        ]
    },
    package_data={
        'dfg_rating': ['database.ini'],
    },
    author='Marc Garnica Caparrós',
    author_email='m.garnica@dshs-koeln.de'
)
