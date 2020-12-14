CREATE TABLE matches (
    match_id VARCHAR(255) PRIMARY KEY,
    network_name VARCHAR(255) NOT NULL,
    home_team INTEGER NOT NULL,
    away_team INTEGER NOT NULL,
    season INTEGER NOT NULL,
    round INTEGER NOT NULL,
    day INTEGER NOT NULL,
    winner VARCHAR(255)
);

CREATE TABLE forecasts (
    forecast_name VARCHAR(255) NOT NULL,
    network_name VARCHAR(255) NOT NULL,
    match_id VARCHAR(255) NOT NULL,
    home REAL,
    draw REAL,
    away REAL,
    FOREIGN KEY (match_id)
    REFERENCES matches (match_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE ratings (
    rating_name VARCHAR(255) NOT NULL,
    network_name VARCHAR(255) NOT NULL,
    team_id VARCHAR(255) NOT NULL,
    team_name VARCHAR(255) NOT NULL,
    season INTEGER NOT NULL,
    rating_number INTEGER NOT NULL,
    value REAL NOT NULL,
    trend REAL NOT NULL,
    starting_point REAL NOT NULL
);