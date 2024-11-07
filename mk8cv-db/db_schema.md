# MarioKart 8 CV Database Schema

## Race Metadata
Metadata describing a given race.

Primary Key: `race_id`

| race_id (int) | name (text) | num_laps (int) | map_name (text) |
|---------------|-------------|----------------|-----------------|
| _unique identifier of the race_ | _human-readable name of the race_ | _total number of laps_ | _name of the map_ |
| `001` | `2025 Elly Cup Race 01` | `3` | `Mario Kart Stadium` |
| `002` | `2025 Elly Cup Race 02` | `3` | `Water Park` |

## Racer Metadata
Metadata describing a given racer in a given race. One row per racer per race.

Primary Key: `race_id + player_id`

| race_id (int) | player_id (int) | device_id (int) | device_player_num (int) | player_name (text) | character (text) |
|---------------|-----------------|-------------------------|-----------------|--------------------|------------------|
| _unique identifier of the race_ | _overall player number, 1-12 (ie `device_id * 2 + device_player_num`)_ | _stream device id, 0-5_ | _player number within a given device, 1 or 2_ | _human-readable name of the racer_  |  _name of the character_  |
| `001` | `1` | `0` | `1` | `Alice` | `Mario` |
| `001` | `2` | `0` | `2` | `Bob` | `Luigi` |
| `001` | `3` | `1` | `1` | `Carol` | `Peach` |
| `001` | `4` | `1` | `2` | `Duncan` | `Baby Mario` |
| `001` | `5` | `2` | `1` | `Evan` | `Bowser` |
| `001` | `6` | `2` | `2` | `Felix` | `Yoshi` |

## Racer Data
Time-series data describing the events of a race.

Primary Key: `race_id + timestamp + player_id`

| race_id (int) | timestamp (int) | player_id (int) | lap (int) | position (int) | coins (int) | item_1 (text) | item_2 (text) |
|---------------|-----------------|-----------------|-----------|----------------|-------------|---------------|---------------|
| _unique identifier of the race_ | _timestamp of the event (ms)_ | _player number_ | _lap_ | _position_ | _coin count_ | _item in slot 1_ |  _item in slot 2_ |
| `001` | `1537849600000` | `1` | `1` | `12` | `10` | `Green Shell` | `None` |