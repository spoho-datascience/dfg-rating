CREATE TABLE networks (
    network_name VARCHAR(255) PRIMARY KEY,
    network_type VARCHAR(255)
);

CREATE TABLE matches (
    match_id VARCHAR(255) PRIMARY KEY,
    network_name VARCHAR(255) NOT NULL,
    node1 VARCHAR(255) NOT NULL,
    node2 VARCHAR(255) NOT NULL,
    season VARCHAR(255) NOT NULL,
    round VARCHAR(255) NOT NULL,
    day INTEGER NOT NULL,
    winner VARCHAR(255),
    FOREIGN KEY (network_name)
    REFERENCES networks (network_name)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE forecasts (
    forecast_name VARCHAR(255) NOT NULL,
    network_name VARCHAR(255) NOT NULL,
    match_id VARCHAR(255) NOT NULL,
    probability_home REAL,
    probability_draw REAL,
    probability_away REAL,
    PRIMARY KEY(forecast_name, network_name, match_id),
    FOREIGN KEY (match_id)
    REFERENCES matches (match_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (network_name)
    REFERENCES networks (network_name)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE ratings (
    rating_name VARCHAR(255) NOT NULL,
    network_name VARCHAR(255) NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    node_name VARCHAR(255) NOT NULL,
    season INTEGER NOT NULL,
    rating_number INTEGER NOT NULL,
    value REAL NOT NULL,
    trend REAL NOT NULL,
    starting_point REAL NOT NULL,
    PRIMARY KEY(rating_name, network_name, node_id, rating_number),
    FOREIGN KEY (network_name)
    REFERENCES networks (network_name)
    ON UPDATE CASCADE ON DELETE CASCADE
);