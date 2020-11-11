from dfg_rating.model.forecast.base_forecast import SimpleForecast

f_simple = SimpleForecast('simple', outcomes=['home', 'draw', 'away'])
f_hw = SimpleForecast('simple', outcomes=['home', 'draw', 'away'], probs=[0.4523, 0.2975, 0.2502])
print(f_simple.get_forecast())
print(f_hw.get_forecast())
