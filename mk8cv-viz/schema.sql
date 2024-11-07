CREATE TABLE IF NOT EXISTS race_positions (
    timestamp INTEGER NOT NULL,
    player_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    race_id TEXT NOT NULL,
    PRIMARY KEY (race_id, timestamp, player_id)
);

CREATE INDEX IF NOT EXISTS idx_race_positions
ON race_positions(race_id, timestamp);

INSERT INTO race_positions (timestamp, player_id, position, race_id) VALUES
(strftime('%s','now'), 'P1', 1, 'RACE_001'),
(strftime('%s','now'), 'P3', 2, 'RACE_001'),
(strftime('%s','now'), 'P4', 3, 'RACE_001');