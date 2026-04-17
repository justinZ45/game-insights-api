CREATE TABLE games (
    game_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    is_handheld BOOLEAN,
    max_players INTEGER,
    is_multiplatform BOOLEAN,
    is_online BOOLEAN,
    is_licensed BOOLEAN,
    is_sequel BOOLEAN,
    review_score INTEGER,
    sales FLOAT,
    used_price FLOAT,
    console TEXT,
    esrb_rating TEXT,
    is_re_release BOOLEAN,
    release_year INTEGER
);
CREATE TABLE game_lengths (
    game_lengths_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(game_id) ON DELETE CASCADE,
    playstyle TEXT,
    avg_hours FLOAT,
    leisure_hours FLOAT,
    median_hours FLOAT,
    num_players_polled INT
);
-- Lookup table (one game -> many genres)
CREATE TABLE genres (
    genre_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);
-- Lookup table (one game -> many publishers)
CREATE TABLE publishers (
    publisher_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);
-- Junction/bridge table (map game id to genre id for lookup)
CREATE TABLE game_genres (
    game_id INT REFERENCES games(game_id) ON DELETE CASCADE,
    genre_id INT REFERENCES genres(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, genre_id)
);
-- Junction/bridge table (map game id to publisher id for lookup)
CREATE TABLE game_publishers (
    game_id INT REFERENCES games(game_id) ON DELETE CASCADE,
    publisher_id INT REFERENCES publishers(publisher_id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, publisher_id)
);