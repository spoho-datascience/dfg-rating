from dfg_rating.model.forecast.base_forecast import SimpleForecast

f_simple = SimpleForecast('simple', ['home', 'draw', 'away'])
f_hw = SimpleForecast('simple', ['home', 'draw', 'away'], [45.23, 29.75, 25.01])
print(f_simple.get_forecast())
print(f_hw.get_forecast())