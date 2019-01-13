CREATE TABLE IF NOT EXISTS user_settings (
    user_id BIGINT PRIMARY KEY,
    profile_color VARCHAR(50) NOT NULL DEFAULT 'white',
    time_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_name VARCHAR(512) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS user_timers (
    user_id BIGINT NOT NULL REFERENCES user_settings(user_id) ON DELETE CASCADE,
    end_time TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    timer_type INT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_stats (
    user_id BIGINT PRIMARY KEY NOT NULL REFERENCES user_settings(user_id) ON DELETE CASCADE,
    uwus BIGINT NOT NULL,
    foes_killed BIGINT NOT NULL,
    total_deaths BIGINT NOT NULL,
    current_level BIGINT NOT NULL DEFAULT 1,
    current_xp BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS marriages (
    user1_id BIGINT PRIMARY KEY NOT NULL REFERENCES user_settings(user_id) ON DELETE CASCADE,
    user2_id BIGINT NOT NULL,
    time_married TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS commands_used (
    commands_used BIGINT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS p_user_timer (
    user_id BIGINT PRIMARY KEY NOT NULL REFERENCES p_users(user_id) ON DELETE CASCADE,
    next_time TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS p_users (
    user_id BIGINT PRIMARY KEY NOT NULL REFERENCES user_settings(user_id) ON DELETE CASCADE,
    tier VARCHAR(20) NOT NULL,
    patron_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS guessing (
    guild_id BIGINT PRIMARY KEY NOT NULL,
    channel_id BIGINT NOT NULL,
    host_id BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS children (
    lover1_id BIGINT NOT NULL REFERENCES marriages(user_id) ON DELETE CASCADE,
    lover2_id BIGINT NOT NULL REFERENCES user_settings(user_id) ON DELETE CASCADE,
    child_name VARCHAR(512) NOT NULL,
    age BIGINT NOT NULL,
    gender VARCHAR(25) NOT NULL,
    last_bd TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    birthdate TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS user_pets (
    pet_id SERIAL NOT NULL PRIMARY KEY,
    pet_name VARCHAR(512),
    pet_type VARCHAR(512),
    gender VARCHAR(25) NOT NULL,
    love BIGINT DEFAULT 0 NOT NULL,
    user_id BIGINT NOT NULL,
    birthdate TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS spc_user_pets (
    pet_id SERIAL NOT NULL PRIMARY KEY,
    pet_name VARCHAR(512),
    pet_type VARCHAR(512),
    gender VARCHAR(25) NOT NULL,
    love BIGINT DEFAULT 0 NOT NULL,
    user_id BIGINT NOT NULL,
    birthdate TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS del_snipe (
    channel_id BIGINT PRIMARY KEY NOT NULL,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    message VARCHAR(2000) NOT NULL,
    msg_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    msg_type INT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_adventures (
    user_id BIGINT PRIMARY KEY REFERENCES user_settings(user_id) ON DELETE CASCADE,
    finish_time TIMESTAMP WITHOUT TIME ZONE
);

CREATE TABLE IF NOT EXISTS user_explores (
    user_id BIGINT PRIMARY KEY REFERENCES user_settings(user_id) ON DELETE CASCADE,
    finish_time TIMESTAMP WITHOUT TIME ZONE
);

CREATE TABLE IF NOT EXISTS user_boosters (
    pet_id BIGINT PRIMARY KEY REFERENCES spc_user_pets(pet_id) ON DELETE CASCADE, 
    active_boosters VARCHAR(50) NOT NULL,
    boost_amount INT NOT NULL,
    boost_type VARCHAR(10) NOT NULL,
    user_id BIGINT NOT NULL,
    expire_time TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE TABLE IF NOT EXISTS pet_boosters (
    pet_id BIGINT REFERENCES spc_user_pets(pet_id) ON DELETE CASCADE,    
    booster_name VARCHAR(50) NOT NULL,
    booster_id SERIAL NOT NULL
);