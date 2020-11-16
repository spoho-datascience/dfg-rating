from dfg_rating.model.forecast.base_forecast import SimpleForecast

f_simple = SimpleForecast(outcomes=['home', 'draw', 'away'])
f_hw = SimpleForecast(outcomes=['home', 'draw', 'away'], probs=[0.4523, 0.2975, 0.2501])
print(f_simple.print())
print(f_hw.print())
