-- Sports & Public Information Data Schema
-- Free public data collected by TBN-certified bots

-- ============================================================================
-- FOOTBALL (Premier League, Championship, etc.)
-- ============================================================================

CREATE TABLE football_teams (
    team_id SERIAL PRIMARY KEY,
    team_name VARCHAR(255),
    league VARCHAR(100),
    stadium VARCHAR(255),
    city VARCHAR(100),
    founded_year INT,
    team_logo_url VARCHAR(500),
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP
);

CREATE TABLE football_matches (
    match_id SERIAL PRIMARY KEY,
    home_team_id INT REFERENCES football_teams(team_id),
    away_team_id INT REFERENCES football_teams(team_id),
    match_date TIMESTAMP,
    league VARCHAR(100),
    season VARCHAR(20),
    
    -- Scores
    home_score INT,
    away_score INT,
    half_time_home INT,
    half_time_away INT,
    
    -- Match details
    status VARCHAR(50), -- scheduled, live, finished
    venue VARCHAR(255),
    attendance INT,
    referee VARCHAR(255),
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP
);

CREATE TABLE football_standings (
    standing_id SERIAL PRIMARY KEY,
    team_id INT REFERENCES football_teams(team_id),
    league VARCHAR(100),
    season VARCHAR(20),
    position INT,
    played INT,
    won INT,
    drawn INT,
    lost INT,
    goals_for INT,
    goals_against INT,
    goal_difference INT,
    points INT,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP
);

CREATE TABLE football_players (
    player_id SERIAL PRIMARY KEY,
    player_name VARCHAR(255),
    team_id INT REFERENCES football_teams(team_id),
    position VARCHAR(50),
    nationality VARCHAR(100),
    date_of_birth DATE,
    shirt_number INT,
    
    -- Stats
    goals_scored INT DEFAULT 0,
    assists INT DEFAULT 0,
    yellow_cards INT DEFAULT 0,
    red_cards INT DEFAULT 0,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- HORSE RACING
-- ============================================================================

CREATE TABLE horse_racing_courses (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(255),
    location VARCHAR(255),
    country VARCHAR(100),
    course_type VARCHAR(50), -- flat, national_hunt, all_weather
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE horse_racing_meetings (
    meeting_id SERIAL PRIMARY KEY,
    course_id INT REFERENCES horse_racing_courses(course_id),
    meeting_date DATE,
    meeting_time TIME,
    weather VARCHAR(100),
    going VARCHAR(100), -- firm, good, soft, heavy
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE horse_racing_races (
    race_id SERIAL PRIMARY KEY,
    meeting_id INT REFERENCES horse_racing_meetings(meeting_id),
    race_number INT,
    race_name VARCHAR(255),
    race_time TIME,
    distance VARCHAR(50),
    prize_money DECIMAL(10,2),
    race_class VARCHAR(50),
    
    -- Results
    status VARCHAR(50), -- scheduled, running, finished
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP
);

CREATE TABLE horse_racing_results (
    result_id SERIAL PRIMARY KEY,
    race_id INT REFERENCES horse_racing_races(race_id),
    position INT,
    horse_name VARCHAR(255),
    jockey_name VARCHAR(255),
    trainer_name VARCHAR(255),
    age INT,
    weight VARCHAR(50),
    odds VARCHAR(50),
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- UK NATIONAL LOTTERY
-- ============================================================================

CREATE TABLE lottery_draws (
    draw_id SERIAL PRIMARY KEY,
    lottery_name VARCHAR(100), -- lotto, euromillions, thunderball
    draw_date DATE,
    draw_number INT,
    
    -- Main numbers
    ball_1 INT,
    ball_2 INT,
    ball_3 INT,
    ball_4 INT,
    ball_5 INT,
    ball_6 INT,
    bonus_ball INT,
    
    -- Lucky stars (EuroMillions)
    lucky_star_1 INT,
    lucky_star_2 INT,
    
    -- Jackpot
    jackpot_amount DECIMAL(15,2),
    jackpot_winners INT,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lottery_statistics (
    stat_id SERIAL PRIMARY KEY,
    lottery_name VARCHAR(100),
    ball_number INT,
    times_drawn INT,
    last_drawn DATE,
    frequency_rank INT,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP
);

-- ============================================================================
-- WEATHER DATA (Public Information)
-- ============================================================================

CREATE TABLE weather_data (
    weather_id SERIAL PRIMARY KEY,
    city VARCHAR(255),
    country VARCHAR(100),
    date DATE,
    time TIME,
    
    -- Weather details
    temperature DECIMAL(5,2),
    feels_like DECIMAL(5,2),
    humidity INT,
    pressure INT,
    wind_speed DECIMAL(5,2),
    wind_direction VARCHAR(50),
    weather_condition VARCHAR(100),
    weather_description TEXT,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- UK PUBLIC HOLIDAYS
-- ============================================================================

CREATE TABLE uk_public_holidays (
    holiday_id SERIAL PRIMARY KEY,
    holiday_name VARCHAR(255),
    holiday_date DATE,
    region VARCHAR(100), -- england, scotland, wales, northern_ireland
    year INT,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CURRENCY EXCHANGE RATES
-- ============================================================================

CREATE TABLE exchange_rates (
    rate_id SERIAL PRIMARY KEY,
    base_currency VARCHAR(10),
    target_currency VARCHAR(10),
    rate DECIMAL(10,6),
    rate_date DATE,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- UK PETROL PRICES
-- ============================================================================

CREATE TABLE petrol_prices (
    price_id SERIAL PRIMARY KEY,
    region VARCHAR(100),
    fuel_type VARCHAR(50), -- unleaded, diesel, premium
    price_per_litre DECIMAL(5,3),
    price_date DATE,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- STOCK MARKET DATA (FTSE 100)
-- ============================================================================

CREATE TABLE stock_prices (
    stock_id SERIAL PRIMARY KEY,
    ticker_symbol VARCHAR(20),
    company_name VARCHAR(255),
    exchange VARCHAR(50),
    price DECIMAL(10,2),
    change_amount DECIMAL(10,2),
    change_percent DECIMAL(5,2),
    volume BIGINT,
    market_cap DECIMAL(15,2),
    price_date DATE,
    price_time TIME,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Football indexes
CREATE INDEX idx_football_matches_date ON football_matches(match_date DESC);
CREATE INDEX idx_football_matches_teams ON football_matches(home_team_id, away_team_id);
CREATE INDEX idx_football_standings_league ON football_standings(league, season, position);

-- Horse racing indexes
CREATE INDEX idx_racing_meetings_date ON horse_racing_meetings(meeting_date DESC);
CREATE INDEX idx_racing_races_time ON horse_racing_races(race_time);

-- Lottery indexes
CREATE INDEX idx_lottery_draws_date ON lottery_draws(draw_date DESC);
CREATE INDEX idx_lottery_draws_name ON lottery_draws(lottery_name);

-- Weather indexes
CREATE INDEX idx_weather_city_date ON weather_data(city, date DESC);

-- Stock indexes
CREATE INDEX idx_stock_ticker ON stock_prices(ticker_symbol, price_date DESC);

-- ============================================================================
-- Views for Easy Querying
-- ============================================================================

-- View: Today's football matches
CREATE VIEW todays_football_matches AS
SELECT 
    m.match_id,
    ht.team_name as home_team,
    at.team_name as away_team,
    m.match_date,
    m.league,
    m.home_score,
    m.away_score,
    m.status,
    m.collected_by_bot
FROM football_matches m
JOIN football_teams ht ON m.home_team_id = ht.team_id
JOIN football_teams at ON m.away_team_id = at.team_id
WHERE DATE(m.match_date) = CURRENT_DATE
ORDER BY m.match_date;

-- View: Latest lottery results
CREATE VIEW latest_lottery_results AS
SELECT 
    lottery_name,
    draw_date,
    draw_number,
    ball_1, ball_2, ball_3, ball_4, ball_5, ball_6,
    bonus_ball,
    jackpot_amount,
    jackpot_winners,
    collected_by_bot
FROM lottery_draws
WHERE draw_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY draw_date DESC;

-- View: Today's horse racing
CREATE VIEW todays_horse_racing AS
SELECT 
    c.course_name,
    m.meeting_date,
    r.race_time,
    r.race_name,
    r.distance,
    r.prize_money,
    r.status,
    r.collected_by_bot
FROM horse_racing_races r
JOIN horse_racing_meetings m ON r.meeting_id = m.meeting_id
JOIN horse_racing_courses c ON m.course_id = c.course_id
WHERE m.meeting_date = CURRENT_DATE
ORDER BY r.race_time;

-- View: Current weather for major UK cities
CREATE VIEW uk_weather_current AS
SELECT 
    city,
    temperature,
    feels_like,
    weather_condition,
    weather_description,
    humidity,
    wind_speed,
    collected_at
FROM weather_data
WHERE city IN ('London', 'Manchester', 'Birmingham', 'Edinburgh', 'Cardiff')
AND date = CURRENT_DATE
ORDER BY collected_at DESC;

-- View: FTSE 100 movers
CREATE VIEW ftse_top_movers AS
SELECT 
    ticker_symbol,
    company_name,
    price,
    change_amount,
    change_percent,
    volume,
    price_date
FROM stock_prices
WHERE exchange = 'LSE'
AND price_date = CURRENT_DATE
ORDER BY ABS(change_percent) DESC
LIMIT 20;
