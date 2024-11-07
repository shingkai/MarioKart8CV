CREATE TABLE IF NOT EXISTS race_metadata (
    race_id INT NOT NULL,
    race_name TEXT NOT NULL,
    num_laps INT NOT NULL,
    map_name TEXT NOT NULL,
    PRIMARY KEY (race_id)
);

CREATE TABLE IF NOT EXISTS racer_metadata (
    race_id INT NOT NULL,
    player_id INT NOT NULL,
    device_id INT NOT NULL,
    device_player_num INT NOT NULL,
    player_name TEXT NOT NULL,
    character TEXT NOT NULL,
    PRIMARY KEY (race_id, player_id)
);

CREATE TABLE IF NOT EXISTS race_data (
    race_id INT NOT NULL,
    timestamp INT NOT NULL,
    player_id INT NOT NULL,
    lap INT NOT NULL,
    position INT NOT NULL,
    coins INT NOT NULL,
    item_1 TEXT NOT NULL,
    item_2 TEXT NOT NULL,
    PRIMARY KEY (race_id, timestamp, player_id)
);

CREATE INDEX IF NOT EXISTS race_data_time
ON race_data(race_id, timestamp);