import utils

from dfg_rating.model.rating.elo_rating import GoalsELORating, OddsELORating
from dfg_rating.model.rating.multi_mode_rating import ELORating

from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.evaluators.accuracy import RankProbabilityScore, Likelihood


def elo_goals(k, lam, data_network, training_seasons, league_average, param_adjust):
    rating = "elo_goals_rating"
    forecast = "elo_goals_forecast"
    if param_adjust is False:
        data_network.add_rating(
            rating=GoalsELORating(trained=True, param_k=k, param_lam=lam, rating_name=rating,
                                  league_average=league_average, param_adjust=param_adjust),
            rating_name=rating
        )
    else:
        data_network.add_rating(
            rating=GoalsELORating(trained=True, param_split_k=k, param_split_lam=lam, rating_name=rating,
                                  league_average=league_average, param_adjust=param_adjust),
            rating_name=rating
        )
    coeffs = utils.get_log_coeffs(training_seasons, data_network, rating)
    beta = coeffs[0]
    data_network.add_forecast(
        forecast=LogFunctionForecast(outcomes=['home', 'draw', 'away'], coefficients=[coeffs[1], coeffs[2]],
                                     beta_parameter=beta),
        forecast_name=forecast,
        base_ranking=rating
    )
    rps = RankProbabilityScore(outcomes=['home', 'draw', 'away'], forecast_name=forecast)
    llh = Likelihood(outcomes=['home', 'draw', 'away'], forecast_name=forecast)
    data_network.add_evaluation([(rps, 'rps')])
    data_network.add_evaluation([(llh, 'loglikelihood')])

    return data_network


def elo_odds(k, data_network, training_seasons, league_average, param_adjust):
    rating = "elo_odds_rating"
    forecast = "elo_odds_forecast"
    if param_adjust is False:
        data_network.add_rating(
            rating=OddsELORating(
                trained=True,
                param_k=k,
                home_odds_pointer="home_odds_new",
                draw_odds_pointer="draw_odds_new",
                away_odds_pointer="away_odds_new",
                rating_name=rating,
                league_average=league_average,
                param_adjust=param_adjust
            ),
            rating_name=rating
        )
    else:
        data_network.add_rating(
            rating=OddsELORating(
                trained=True,
                param_split_k=k,
                home_odds_pointer="home_odds_new",
                draw_odds_pointer="draw_odds_new",
                away_odds_pointer="away_odds_new",
                rating_name=rating,
                league_average=league_average,
                param_adjust=param_adjust
            ),
            rating_name=rating
        )
    coeffs = utils.get_log_coeffs(training_seasons, data_network, rating)
    beta = coeffs[0]
    data_network.add_forecast(
        forecast=LogFunctionForecast(outcomes=['home', 'draw', 'away'], coefficients=[coeffs[1], coeffs[2]],
                                     beta_parameter=beta),
        forecast_name=forecast,
        base_ranking=rating
    )
    rps = RankProbabilityScore(outcomes=['home', 'draw', 'away'], forecast_name=forecast)
    llh = Likelihood(outcomes=['home', 'draw', 'away'], forecast_name=forecast)
    data_network.add_evaluation([(rps, 'rps')])
    data_network.add_evaluation([(llh, 'loglikelihood')])

    return data_network


def elo_results(k, data_network, training_seasons, league_average, param_adjust):
    rating = "elo_result_rating"
    forecast = "elo_result_forecast"
    if param_adjust is False:
        data_network.add_rating(
            rating=ELORating(
                trained=True,
                rating_mode='keep',
                rating_mean=1000,
                param_k=k,
                rating_name=rating,
                league_average=league_average,
                param_adjust=param_adjust
            ),
            rating_name=rating
        )
    else:
        data_network.add_rating(
            rating=ELORating(
                trained=True,
                rating_mode='keep',
                rating_mean=1000,
                param_split_k=k,
                rating_name=rating,
                league_average=league_average,
                param_adjust=param_adjust
            ),
            rating_name=rating
        )
    coeffs = utils.get_log_coeffs(training_seasons, data_network, rating)
    beta = coeffs[0]
    data_network.add_forecast(
        forecast=LogFunctionForecast(outcomes=['home', 'draw', 'away'], coefficients=[coeffs[1], coeffs[2]],
                                     beta_parameter=beta),
        forecast_name=forecast,
        base_ranking=rating
    )
    rps = RankProbabilityScore(outcomes=['home', 'draw', 'away'], forecast_name=forecast)
    llh = Likelihood(outcomes=['home', 'draw', 'away'], forecast_name=forecast)
    data_network.add_evaluation([(rps, 'rps')])
    data_network.add_evaluation([(llh, 'loglikelihood')])

    return data_network


def evaluate_model(param, data_network, training_seasons, test_seasons, rating, league_average, param_adjust):
    param_split_k = {}
    param_split_lam = {}
    if rating == 'ELO odds':
        if param_adjust is False:
            k = param[0]
            data_network = elo_odds(k, data_network, training_seasons, league_average, param_adjust)
        else:
            param_split_k['National'] = param[0]
            param_split_k['International'] = param[1]
            param_split_k['Cup'] = param[2]
            data_network = elo_odds(param_split_k, data_network, training_seasons, league_average, param_adjust)
    elif rating == 'ELO goals':
        if param_adjust is False:
            k, lam = param
            data_network = elo_goals(k, lam, data_network, training_seasons, league_average, param_adjust)
        else:
            param_split_k['National'] = param[0]
            param_split_lam['National'] = param[1]
            param_split_k['International'] = param[2]
            param_split_lam['International'] = param[3]
            param_split_k['Cup'] = param[4]
            param_split_lam['Cup'] = param[5]
            data_network = elo_goals(param_split_k, param_split_lam, data_network, training_seasons,
                                     league_average, param_adjust)
    elif rating == 'ELO results':
        if param_adjust is False:
            k = param[0]
            data_network = elo_results(k, data_network, training_seasons, league_average, param_adjust)
        else:
            param_split_k['National'] = param[0]
            param_split_k['International'] = param[1]
            param_split_k['Cup'] = param[2]
            data_network = elo_results(param_split_k, data_network, training_seasons, league_average, param_adjust)

    rps = utils.get_rps(data_network, test_seasons)
    return rps
