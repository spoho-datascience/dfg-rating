def get_assigned_teams(day, graph):
    """[summary]

    Args:
        team ([type]): [description]
        graph ([type]): [description]

    Returns:
        [type]: [description]
    """
    assigned_rounds = list(
        map(
            lambda x: [x[0:2]],
            filter(lambda x: x[2] == round, graph.edges(data='day'))
        )
    )
    return assigned_rounds
