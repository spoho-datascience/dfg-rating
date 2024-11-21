import random
import math

def schedule_network(teams_level1, teams_level2, min_matches_per_team, season, leg_option='oneleg'):
    all_teams = teams_level1 + teams_level2
    num_teams = len(all_teams)
    
    avg_match_level1_level2 = 3
    min_matches_per_team = 2
    if leg_option=='oneleg':
        total_matches = math.ceil((num_teams * avg_match_level1_level2) / 2)
    elif leg_option=='twoleg':
        total_matches = math.ceil((num_teams * avg_match_level1_level2) / 4)

    print('Total matches:', total_matches)
    match_pairs = set()
    team_matches = {team: 0 for team in all_teams}

    # possible_matches = [(team1, team2) for team1 in all_teams for team2 in all_teams if team1 != team2]
    possible_matches = [(team1, team2) for idx1, team1 in enumerate(all_teams) for team2 in all_teams[idx1+1:]]
    random.shuffle(possible_matches)
    print(possible_matches)
    for match in possible_matches:
        team1, team2 = match
        # Check if both teams need more matches
        if team_matches[team1] < min_matches_per_team or team_matches[team2] < min_matches_per_team:
            if leg_option == 'oneleg':
                if random.choice([True, False]):
                    match = (team1, team2)
                else:
                    match = (team2, team1)
                match_pairs.add(match)
                possible_matches.remove((team1, team2))
                team_matches[team1] += 1
                team_matches[team2] += 1
            elif leg_option == 'twoleg':
                # Schedule both home and away matches
                match_pairs.add((team1, team2))
                match_pairs.add((team2, team1))
                possible_matches.remove(match)
                team_matches[team1] += 2
                team_matches[team2] += 2
        else:
            # Both teams have met the minimum matches requirement
            continue
        # Check if all teams have met the minimum matches requirement
        if all([team_matches[team] >= min_matches_per_team for team in all_teams]):
            break
    
    while possible_matches!=[] and len(match_pairs)<total_matches:
        pair = possible_matches.pop()
        team1, team2 = pair
        if leg_option == 'oneleg':
            if random.choice([True, False]):
                match = (team1, team2)
            else:
                match = (team2, team1)
            match_pairs.add(match)
            team_matches[team1] += 1
            team_matches[team2] += 1
        elif leg_option == 'twoleg':
            # Schedule both home and away matches
            match_pairs.add((team1, team2))
            match_pairs.add((team2, team1))
            team_matches[team1] += 2
            team_matches[team2] += 2

    return match_pairs

teams_level1 = ['A', 'B', 'C']
teams_level2 = ['D', 'E', 'F', 'G', 'H']
match_pairs = schedule_network(teams_level1, teams_level2, 3, '2021', leg_option='oneleg')
print(match_pairs)