import pandas as pd
import numpy as np
from typing import Dict

from dfg_rating.db.postgres import PostgreSQLDriver
from dfg_rating.model import factory
from dfg_rating.model.betting.betting import BaseBetting
from dfg_rating.model.bookmaker.base_bookmaker import BookmakerError, BookmakerMargin, BaseBookmaker
from dfg_rating.model.network.base_network import BaseNetwork, WhiteNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating
from dfg_rating.model.rating.function_rating import FunctionRating

class Controller:
    """Execution controller for the simulator
    It manages all the commands sent to the model and stores all the staging entities.

    Attributes:
        inputs (Dict): Gathers each entity input parameters
    """
    inputs = {
        "network": {
            "round-robin": {
                "teams": {
                    "label": "Number of teams",
                    "type": int
                },
                "days_between_rounds": {
                    "label": "Days between rounds",
                    "type": int
                }
            },
            "multiple-round-robin": {
                "teams": {
                    "label": "Number of teams",
                    "type": int
                },
                "days_between_rounds": {
                    "label": "Days between rounds",
                    "type": int
                },
                "seasons": {
                    "label": "Number of seasons",
                    "type": int
                },
                "league_teams": {
                    "label": "Number of teams in the league",
                    "type": int
                },
                "league_promotion": {
                    "label": "Number of delegation/promotion spots",
                    "type": int
                }
            }
        },
        "rating": {
            "random-function": {
                "distribution": {
                    "label": "Distribution method",
                    "type": str
                },
                "dist_args": {
                    "label": "Distribution args (arg1_name=arg1_value, argN_name=argN_value)",
                    "type": "custom_key_value",
                    "cast": "float"
                }
            },
            "league-rating": {},
            "controlled-random": {
                "starting_point": {
                    "label": "Ranking starting point definition",
                    "type": "custom_class",
                    "cast": "controlled-random-function"
                },
                "delta": {
                    "label": "Ranking daily delta definition",
                    "type": "custom_class",
                    "cast": "controlled-random-function"
                },
                "trend": {
                    "label": "Ranking daily trend definition",
                    "type": "custom_class",
                    "cast": "controlled-random-function"
                },
                "season_delta": {
                    "label": "Ranking season delta definition",
                    "type": "custom_class",
                    "cast": "controlled-random-function"
                }

            }
        },
        "forecast": {
            "simple": {
                "outcomes": {
                    "label": "Outcomes list",
                    "type": "custom_args_list"
                },
                "probs": {
                    "label": "Predefined probabilities",
                    "type": "custom_args_list",
                    "cast": "float"
                }
            },
            "logistic-function": {
                "outcomes": {
                    "label": "Outcomes list",
                    "type": "custom_args_list"
                },
                "coefficients": {
                    "label": "List of coefficients",
                    "type": "custom_args_list",
                    "cast": "float"
                }
            }
        },
        "bookmaker": {
            "simple": {}
        },
        "bookmaker_error": {
            "factor": {
                "error": {
                    "label": "Deviation error",
                    "type": float
                },
                "scope": {
                    "label": "Error scope (positive | negative | both)",
                    "type": str
                }
            },
            "simulated": {
                "error": {
                    "label": "Bookmaker error distribution",
                    "type": str,
                },
                "error_args": {
                    "label": "Distribution args (arg1_name=arg1_value, argN_name=argN_value)",
                    "type": "custom_key_value",
                    "cast": "float"
                }
            }
        },
        "bookmaker_margin": {
            "simple": {
                "margin": {
                    "label": "Bookmaker margin",
                    "type": float
                }
            }
        },
        "betting": {
            "fixed": {
                "bank_role": {
                    "label": "Bank role",
                    "type": float
                }
            }
        },
        "classes": {
            "controlled-random-function": {
                "distribution": {
                    "label": "Distribution method",
                    "type": str
                },
                "dist_args": {
                    "label": "Distribution args (arg1_name=arg1_value, argN_name=argN_value)",
                    "type": "custom_key_value",
                    "cast": "float"
                }
            }
        }
    }

    def __init__(self):
        self.networks: Dict[str, BaseNetwork] = {}
        self.bookmakers: Dict[str, BaseBookmaker] = {}
        self.bettings: Dict[str, BaseBetting] = {}
        self.db = PostgreSQLDriver()

    def print_network(self, name, **kwargs):
        if name in self.networks:
            n = self.networks[name]
            n.print_data(**kwargs)
            return True, ""
        else:
            return False, "Network not found"

    def new_network(self, network_name: str, network_type: str, **kwargs):
        n = factory.new_network(network_type, **kwargs)
        n.create_data()
        self.networks[network_name] = n
        return 1

    def load_network_from_tabular(self, network_name: str, file_path: str, new_mapping: str):
        if network_name in self.networks:
            return 0, f"Network <{network_name}> already exists"
        extension = file_path.split('.')[1]
        if extension == 'csv':
            network_df = pd.read_csv(file_path)
        elif extension == 'xlsx':
            network_df = pd.read_excel(file_path, engine="openpyxl")
        else:
            return 0, f"Unknown file extension {extension}"
        if network_df.empty:
            return 0, f"Network <{network_name}> empty at {file_path}"
        self.networks[network_name] = WhiteNetwork(
            data=network_df,
            mapping=factory.pre_mappings.get(new_mapping, {})
        )
        return 1, "Network loaded correctly"

    def load_network_from_sql(self, network_name: str):
        if network_name in self.networks:
            return 0, f"Network <{network_name}> already exists"
        self.db.connect()
        db_networks = self.db.execute_query(query=f"SELECT * FROM public.networks m WHERE m.network_name = '{network_name}'")
        if len(db_networks) == 0:
            return 0, f"Database does not contain network <{network_name}>"
        matches = self.db.execute_query(query=f"SELECT * FROM public.matches m WHERE m.network_name = '{network_name}'")
        forecasts = self.db.execute_query(query=f"SELECT * FROM public.forecasts f WHERE f.network_name = '{network_name}'")
        ratings = self.db.execute_query(query=f"SELECT * FROM public.ratings r WHERE r.network_name = '{network_name}'")
        for network in db_networks:
            self.networks.setdefault(
                network['network_name'],
                factory.new_network(network['network_type'])
            ).deserialize_network(
                matches=matches,
                forecasts=forecasts,
                ratings=ratings
            )
        return 1, "Network loaded correctly"

    def save_network(self, network_name: str):
        if network_name not in self.networks:
            return 0, f"Network <{network_name}> does not exist"
        self.db.connect()
        serialized_network = self.networks[network_name].serialize_network(network_name)
        for table, table_rows in serialized_network.items():
            columns = table_rows[0].keys()
            query_string = f"INSERT INTO {table}({','.join(columns)}) VALUES %s ON CONFLICT DO NOTHING"
            values = [[value for value in r.values()] for r in table_rows]
            self.db.insert_many(query_string, values)
        return 1, f"Network <{network_name}> saved correctly"

    def export_network(self, network_name: str, **kwargs):
        if network_name not in self.networks:
            return 0, f"Network <{network_name}> does not exist"
        return self.networks[network_name].export(**kwargs)



    def play_network(self, network_name: str):
        n = self.networks[network_name]
        n.play()

    def add_new_rating(self, network_name: str, rating_type: str, rating_name, **rating_kwargs):
        n = self.networks[network_name]
        new_rating = factory.new_rating(rating_type, **rating_kwargs)
        n.add_rating(new_rating, rating_name)

    def get_ranking_list(self, network_name: str):
        n = self.networks[network_name]
        return n.get_rankings()

    def add_new_forecast(
            self,
            network_name: str,
            forecast_type: str,
            forecast_name: str,
            base_ranking: str,
            **forecast_kwargs
    ):
        n = self.networks[network_name]
        new_forecast = factory.new_forecast(forecast_type, **forecast_kwargs)
        n.add_forecast(new_forecast, forecast_name, base_ranking)

    def list(self, attribute):
        return [
            (element, self.__getattribute__(attribute)[element].type) for element in
            self.__getattribute__(attribute).keys()
        ]

    def new_bookmaker_error(self, error_type, **error_kwargs):
        return factory.new_bookmaker_error(error_type, **error_kwargs)

    def new_bookmaker_margin(self, margin_type, **error_kwargs):
        return factory.new_bookmaker_margin(margin_type, **error_kwargs)

    def create_bookmaker(self, bookmaker_name: str, bookmaker_type: str, **kwargs):
        bm = factory.new_bookmaker(bookmaker_type, **kwargs)
        self.bookmakers[bookmaker_name] = bm

    def add_odds(self, network_name: str, bookmaker_name: str):
        n = self.networks[network_name]
        bm = self.bookmakers[bookmaker_name]
        n.add_odds(bookmaker_name, bm)

    def create_betting_strategy(self, betting_name: str, betting_type: str, **kwargs):
        bs = factory.new_betting_strategy(betting_type, **kwargs)
        self.bettings[betting_name] = bs

    def add_bets(self, network_name: str, bookmaker_name: str, betting_name: str, base_forecast: str):
        n = self.networks[network_name]
        betting_strategy = self.bettings[betting_name]
        n.add_bets(
            bettor_name=betting_name,
            bookmaker=bookmaker_name,
            betting=betting_strategy,
            base_forecast=base_forecast
        )

    def profitability_study(self, network, evaluator, odds, bets):
        n = self.networks[network]
        analysis_dict = []
        for away, home, match_id, match_attributes in n.iterate_over_games():
            for o_number, o in enumerate(odds):
                print(match_attributes)
                new_row = {
                    "HomeTeam": home,
                    "AwayTeam": away,
                    "Season": match_attributes.get('season', None),
                    "Round": match_attributes.get('season', None),
                    "Result": match_attributes.get('winner', None),
                }
                for forecast in ['true_forecast', 'elo_forecast']:
                    forecast_object = match_attributes.get('forecasts', {}).get(forecast, None)
                    if forecast_object is not None:
                        for i, outcome in enumerate(forecast_object.outcomes):
                            new_row[f"{forecast}#{outcome}"] = float(f"{forecast_object.probabilities[i]:.2f}")
                match_odds = match_attributes.get('odds', {}).get(o, [])
                match_bets = match_attributes.get('bets', {}).get(bets[o_number], [])
                print(match_odds, match_bets)
                for i_odd, odd in enumerate(match_odds):
                    new_row[f"odds#{forecast_object.outcomes[i_odd]}"] = float(f"{odd:.2f}")
                for i_bet, bet in enumerate(match_bets):
                    new_row[f"bet#{forecast_object.outcomes[i_bet]}"] = float(f"{bet:.2f}")
                new_row['Bettor'] = bets[o_number]
                new_row['Bookmaker'] = o
                obj_forecast = match_attributes.get('forecasts', {}).get('true_forecast', None)
                expected_results, actual_results = evaluator.eval(
                    bets=match_bets,
                    bettor_predictions=obj_forecast.probabilities,
                    bookmaker_odds=match_odds,
                    observed_result=new_row['Result']
                )
                for i_bet, bet in enumerate(match_bets):
                    new_row[f"expected#bet#{forecast_object.outcomes[i_bet]}"] = float(f"{expected_results[i_bet]:.2f}")
                    new_row[f"return#bet#{forecast_object.outcomes[i_bet]}"] = float(f"{actual_results[i_bet]:.2f}")
                analysis_dict.append(new_row)
        return analysis_dict

    def get_new_class(self, class_name: str, **kwargs):
        return factory.new_class(class_name, **kwargs)

    def run_demo(self):
        self.new_network(
            "test_network", "multiple-round-robin",
            teams=18, seasons=7, league_teams=18, league_promotion=0, days_between_rounds=3,
        )
        self.add_new_rating("test_network", "elo-rating", "elo_rating", trained=True)
        self.add_new_forecast(
            network_name="test_network",
            forecast_type='logistic-function',
            forecast_name='elo_forecast',
            base_ranking='elo_rating',
            outcomes=['home', 'draw', 'away'], coefficients=[-1.1, 0.1], beta_parameter=0.006
        )
        self.create_bookmaker(
            bookmaker_name='simple_bookmaker',
            bookmaker_type='simple',
            error=factory.new_bookmaker_error(error_type='simulated', error="uniform", low=0, high=1),
            margin=factory.new_bookmaker_margin('simple', margin=0.05)
        )
        self.add_odds(
            network_name="test_network",
            bookmaker_name="simple_bookmaker",
        )
        self.create_betting_strategy(
            betting_name='elo_bettor',
            betting_type='fixed',
            bank_role=100
        )
        self.add_bets(
            network_name="test_network",
            bookmaker_name="simple_bookmaker",
            betting_name='elo_bettor',
            base_forecast='elo_forecast'
        )
        """
        self.new_network(
            "test_network", "round-robin",
            teams=20, days_between_rounds=5,
        )
        self.play_network("test_network")
        self.print_network("test_network", schedule=True, forecasts=True, winner=True)
        self.add_new_rating(
            network_name="test_network",
            rating_name="function_rating",
            rating_type="controlled-random",
            starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=200),
            delta=ControlledRandomFunction(distribution='normal', loc=0, scale=1),
            trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.4),
            season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=0)

        )        
        df = pd.read_excel('/home/marc/Development/dshs/dfg-rating/data/real/nation_teams_competitions.xlsx', engine='openpyxl')
        white_network = WhiteNetwork(
            data=df,
            mapping=dict(
                date='Date',
                round='Round',
                home='Team home',
                away='Team away',
                winner_id='WinnerID',
                winner_name='Winner',
                loser_id='LooserID',
                loser_name='Looser',
            )
        )
        white_network.create_data()
        self.networks["real_soccer"] = white_network

        df = pd.read_csv(
            '/home/marc/Development/dshs/dfg-rating/data/real/ATP_Network_2010_2019.csv',
            parse_dates=['Date']
        )
        top_30_dict = {
            '283': 'Haase R.',
            '402': 'Lajovic D.',
            '190': 'Dzumhur D.',
            '221': 'Fritz',
            '324': 'Jaziri',
            '675': 'Sousa J.',
            '445': 'Mannarino A.',
            '361': 'Klizan M.',
            '117': 'Chardy J.',
            '191': 'Ebden M.',
            '701': 'Tiafoe F.',
            '322': 'Jarry N.',
            '222': 'Fucsovics M.',
            '398': 'Kyrgios N.',
            '366': 'Kohlschreiber P.',
            '641': 'Seppi A.',
            '328': 'Johnson S.',
            '479': 'Millman J.',
            '565': 'Pouille L.',
            '152': 'De Minaur A.',
            '657': 'Simon G.',
            '490': 'Monfils G.',
            '738': 'Verdasco F.',
            '648': 'Shapovalov D.',
            '234': 'Gasquet R.',
            '122': 'Chung H.',
            '54': 'Bautista Agut R.',
            '107': 'Carreno Busta P.',
            '250': 'Goffin D.',
            '52': 'Basilashvili N.',
            '111': 'Cecchinato, M.',
            '173': 'Dimitrov G.',
            '582': 'Raonic M.',
            '638': 'Schwartzamn',
            '466': 'Medvedev, D.',
            '715': 'Tsitsipas S.',
            '192': 'Edmund, K.',
            '218': 'Fognini F.',
            '133': 'Coric, B.',
            '345': 'Khachanov, K.',
            '316': 'Isner J.',
            '524': 'Nishikori K.',
            '698': 'Thiem D.',
            '124': 'Cilic M.',
            '17': 'Anderson K.',
            '781': 'Zverev A.',
            '160': 'Del Potro J.M.',
            '211': 'Federer R.',
            '508': 'Nadal R.',
            '176': 'Djokovic N.'
        }
        white_network = WhiteNetwork(
            data=df,
            mapping=dict(
                date='Date',
                round='Round',
                home='WinnerID',
                away='LoserID',
                winner_id='WinnerID',
                winner_name='Winner',
                loser_id='LoserID',
                loser_name='Loser',
            ),
            filter={
                "id": list(top_30_dict.keys())
            }
        )
        white_network.create_data()
        self.networks["real_tennis"] = white_network"""

    def load_all_database(self):
        self.db.connect()
        db_networks = self.db.execute_query(
            query=f"SELECT * FROM public.networks m")
        if len(db_networks) == 0:
            return 0, f"Database does not contain networks"
        for n in db_networks:
            network_name = n['network_name']
            matches = self.db.execute_query(query=f"SELECT * FROM public.matches m WHERE m.network_name = '{network_name}'")
            forecasts = self.db.execute_query(
                query=f"SELECT * FROM public.forecasts f WHERE f.network_name = '{network_name}'")
            ratings = self.db.execute_query(query=f"SELECT * FROM public.ratings r WHERE r.network_name = '{network_name}'")
            self.networks.setdefault(
                n['network_name'],
                factory.new_network(n['network_type'])
            ).deserialize_network(
                matches=matches,
                forecasts=forecasts,
                ratings=ratings
            )
            self.networks[network_name].play()

    def close(self):
        self.db.close()
