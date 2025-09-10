CREATE TABLE networks (
    network_name VARCHAR(255) PRIMARY KEY,
    network_type VARCHAR(255),
    seasons INTEGER,
    rounds INTEGER,
    days_between_rounds INTEGER
);

CREATE TABLE matches (
    match_id VARCHAR(255) NOT NULL,
    network_name VARCHAR(255) NOT NULL,
    node1 VARCHAR(255) NOT NULL,
    node2 VARCHAR(255) NOT NULL,
    season VARCHAR(255) NOT NULL,
    round VARCHAR(255) NOT NULL,
    day INTEGER NOT NULL,
    winner VARCHAR(255),
    PRIMARY KEY (match_id, network_name),
    FOREIGN KEY (network_name)
    REFERENCES networks (network_name)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE forecasts (
    forecast_name VARCHAR(255) NOT NULL,
    network_name VARCHAR(255) NOT NULL,
    match_id VARCHAR(255) NOT NULL,
    attributes JSONB,
    PRIMARY KEY (forecast_name, network_name, match_id),
    FOREIGN KEY (match_id, network_name)
        REFERENCES matches (match_id, network_name)
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
    PRIMARY KEY (rating_name, network_name, node_id, rating_number),
    FOREIGN KEY (network_name)
        REFERENCES networks (network_name)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE odds (
   bookmaker_name VARCHAR(255) NOT NULL,
   network_name VARCHAR(255) NOT NULL,
   match_id VARCHAR(255) NOT NULL,
   attributes JSONB,
   PRIMARY KEY (bookmaker_name, network_name, match_id),
   FOREIGN KEY (match_id, network_name)
       REFERENCES matches (match_id, network_name)
       ON UPDATE CASCADE ON DELETE CASCADE,
   FOREIGN KEY (network_name)
       REFERENCES networks (network_name)
       ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE bets (
      bettor_name VARCHAR(255) NOT NULL,
      network_name VARCHAR(255) NOT NULL,
      match_id VARCHAR(255) NOT NULL,
      attributes JSONB,
      PRIMARY KEY (bettor_name, network_name, match_id),
      FOREIGN KEY (match_id, network_name)
          REFERENCES matches (match_id, network_name)
          ON UPDATE CASCADE ON DELETE CASCADE,
      FOREIGN KEY (network_name)
          REFERENCES networks (network_name)
          ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE metrics (
      metric_name VARCHAR(255) NOT NULL,
      network_name VARCHAR(255) NOT NULL,
      match_id VARCHAR(255) NOT NULL,
      attributes JSONB,
      PRIMARY KEY (metric_name, network_name, match_id),
      FOREIGN KEY (match_id, network_name)
          REFERENCES matches (match_id, network_name)
          ON UPDATE CASCADE ON DELETE CASCADE,
      FOREIGN KEY (network_name)
          REFERENCES networks (network_name)
          ON UPDATE CASCADE ON DELETE CASCADE
);