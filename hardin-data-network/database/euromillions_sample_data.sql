-- EuroMillions Historical Data & Statistics
-- Sample data showing the concept

-- ============================================================================
-- Recent EuroMillions Draws (Last 10 draws)
-- ============================================================================

INSERT INTO lottery_draws (lottery_name, draw_date, draw_number, ball_1, ball_2, ball_3, ball_4, ball_5, bonus_ball, lucky_star_1, lucky_star_2, jackpot_amount, jackpot_winners, collected_by_bot) VALUES
('EuroMillions', '2026-05-06', 1654, 7, 12, 23, 34, 45, NULL, 3, 9, 45000000.00, 0, 'tbn-bot-lottery-001'),
('EuroMillions', '2026-05-02', 1653, 5, 15, 28, 39, 42, NULL, 2, 11, 42000000.00, 1, 'tbn-bot-lottery-001'),
('EuroMillions', '2026-04-30', 1652, 3, 18, 25, 31, 48, NULL, 4, 8, 38000000.00, 0, 'tbn-bot-lottery-001'),
('EuroMillions', '2026-04-26', 1651, 9, 14, 22, 37, 44, NULL, 1, 10, 35000000.00, 0, 'tbn-bot-lottery-001'),
('EuroMillions', '2026-04-23', 1650, 6, 11, 27, 33, 41, NULL, 5, 7, 32000000.00, 0, 'tbn-bot-lottery-001'),
('EuroMillions', '2026-04-19', 1649, 4, 16, 24, 38, 47, NULL, 2, 9, 29000000.00, 2, 'tbn-bot-lottery-001'),
('EuroMillions', '2026-04-16', 1648, 8, 13, 21, 35, 43, NULL, 3, 12, 17000000.00, 0, 'tbn-bot-lottery-001'),
('EuroMillions', '2026-04-12', 1647, 2, 17, 26, 36, 46, NULL, 1, 8, 15000000.00, 0, 'tbn-bot-lottery-001'),
('EuroMillions', '2026-04-09', 1646, 10, 19, 29, 40, 49, NULL, 4, 11, 13000000.00, 0, 'tbn-bot-lottery-001'),
('EuroMillions', '2026-04-05', 1645, 1, 20, 30, 32, 50, NULL, 6, 10, 11000000.00, 1, 'tbn-bot-lottery-001');

-- ============================================================================
-- EuroMillions Ball Statistics (Most Common Numbers)
-- Based on historical data analysis
-- ============================================================================

INSERT INTO lottery_statistics (lottery_name, ball_number, times_drawn, last_drawn, frequency_rank, collected_by_bot) VALUES
-- Main balls (1-50) - Top 20 most common
('EuroMillions', 23, 156, '2026-05-06', 1, 'tbn-bot-lottery-001'),
('EuroMillions', 44, 152, '2026-04-26', 2, 'tbn-bot-lottery-001'),
('EuroMillions', 50, 148, '2026-04-05', 3, 'tbn-bot-lottery-001'),
('EuroMillions', 19, 145, '2026-04-09', 4, 'tbn-bot-lottery-001'),
('EuroMillions', 37, 143, '2026-04-26', 5, 'tbn-bot-lottery-001'),
('EuroMillions', 5, 141, '2026-05-02', 6, 'tbn-bot-lottery-001'),
('EuroMillions', 27, 139, '2026-04-23', 7, 'tbn-bot-lottery-001'),
('EuroMillions', 42, 138, '2026-05-02', 8, 'tbn-bot-lottery-001'),
('EuroMillions', 17, 136, '2026-04-12', 9, 'tbn-bot-lottery-001'),
('EuroMillions', 11, 135, '2026-04-23', 10, 'tbn-bot-lottery-001'),
('EuroMillions', 3, 134, '2026-04-30', 11, 'tbn-bot-lottery-001'),
('EuroMillions', 28, 133, '2026-05-02', 12, 'tbn-bot-lottery-001'),
('EuroMillions', 38, 132, '2026-04-19', 13, 'tbn-bot-lottery-001'),
('EuroMillions', 7, 131, '2026-05-06', 14, 'tbn-bot-lottery-001'),
('EuroMillions', 15, 130, '2026-05-02', 15, 'tbn-bot-lottery-001'),
('EuroMillions', 34, 129, '2026-05-06', 16, 'tbn-bot-lottery-001'),
('EuroMillions', 9, 128, '2026-04-26', 17, 'tbn-bot-lottery-001'),
('EuroMillions', 45, 127, '2026-05-06', 18, 'tbn-bot-lottery-001'),
('EuroMillions', 12, 126, '2026-05-06', 19, 'tbn-bot-lottery-001'),
('EuroMillions', 31, 125, '2026-04-30', 20, 'tbn-bot-lottery-001');

-- Lucky Stars (1-12) - All frequencies
INSERT INTO lottery_statistics (lottery_name, ball_number, times_drawn, last_drawn, frequency_rank, collected_by_bot) VALUES
('EuroMillions_LuckyStar', 9, 89, '2026-05-06', 1, 'tbn-bot-lottery-001'),
('EuroMillions_LuckyStar', 2, 87, '2026-05-02', 2, 'tbn-bot-lottery-001'),
('EuroMillions_LuckyStar', 3, 85, '2026-05-06', 3, 'tbn-bot-lottery-001'),
('EuroMillions_LuckyStar', 11, 83, '2026-05-02', 4, 'tbn-bot-lottery-001'),
('EuroMillions_LuckyStar', 8, 81, '2026-04-30', 5, 'tbn-bot-lottery-001'),
('EuroMillions_LuckyStar', 4, 79, '2026-04-30', 6, 'tbn-bot-lottery-001'),
('EuroMillions_LuckyStar', 1, 77, '2026-04-26', 7, 'tbn-bot-lottery-001'),
('EuroMillions_LuckyStar', 10, 75, '2026-04-09', 8, 'tbn-bot-lottery-001'),
('EuroMillions_LuckyStar', 5, 73, '2026-04-23', 9, 'tbn-bot-lottery-001'),
('EuroMillions_LuckyStar', 7, 71, '2026-04-23', 10, 'tbn-bot-lottery-001'),
('EuroMillions_LuckyStar', 12, 69, '2026-04-16', 11, 'tbn-bot-lottery-001'),
('EuroMillions_LuckyStar', 6, 67, '2026-04-05', 12, 'tbn-bot-lottery-001');

-- ============================================================================
-- UK National Lottery (Lotto) Data
-- ============================================================================

INSERT INTO lottery_draws (lottery_name, draw_date, draw_number, ball_1, ball_2, ball_3, ball_4, ball_5, ball_6, bonus_ball, lucky_star_1, lucky_star_2, jackpot_amount, jackpot_winners, collected_by_bot) VALUES
('UK Lotto', '2026-05-07', 3245, 5, 12, 23, 31, 42, 58, 15, NULL, NULL, 8500000.00, 0, 'tbn-bot-lottery-001'),
('UK Lotto', '2026-05-04', 3244, 7, 18, 27, 35, 44, 59, 22, NULL, NULL, 7200000.00, 1, 'tbn-bot-lottery-001'),
('UK Lotto', '2026-05-01', 3243, 3, 14, 25, 33, 47, 56, 9, NULL, NULL, 4000000.00, 0, 'tbn-bot-lottery-001');

-- ============================================================================
-- Thunderball Data
-- ============================================================================

INSERT INTO lottery_draws (lottery_name, draw_date, draw_number, ball_1, ball_2, ball_3, ball_4, ball_5, bonus_ball, lucky_star_1, lucky_star_2, jackpot_amount, jackpot_winners, collected_by_bot) VALUES
('Thunderball', '2026-05-07', 2156, 8, 15, 22, 31, 38, 12, NULL, NULL, 500000.00, 0, 'tbn-bot-lottery-001'),
('Thunderball', '2026-05-06', 2155, 4, 11, 19, 27, 34, 7, NULL, NULL, 500000.00, 1, 'tbn-bot-lottery-001');

-- ============================================================================
-- Views for Analysis
-- ============================================================================

-- Most common EuroMillions numbers
CREATE OR REPLACE VIEW euromillions_hot_numbers AS
SELECT 
    ball_number,
    times_drawn,
    last_drawn,
    frequency_rank,
    ROUND((times_drawn::DECIMAL / (SELECT SUM(times_drawn) FROM lottery_statistics WHERE lottery_name = 'EuroMillions')) * 100, 2) as percentage
FROM lottery_statistics
WHERE lottery_name = 'EuroMillions'
ORDER BY times_drawn DESC
LIMIT 10;

-- Most common Lucky Stars
CREATE OR REPLACE VIEW euromillions_hot_lucky_stars AS
SELECT 
    ball_number as lucky_star,
    times_drawn,
    last_drawn,
    frequency_rank
FROM lottery_statistics
WHERE lottery_name = 'EuroMillions_LuckyStar'
ORDER BY times_drawn DESC;

-- Recent jackpot winners
CREATE OR REPLACE VIEW recent_lottery_winners AS
SELECT 
    lottery_name,
    draw_date,
    draw_number,
    jackpot_amount,
    jackpot_winners,
    CASE 
        WHEN lottery_name = 'EuroMillions' THEN 
            CONCAT(ball_1, ', ', ball_2, ', ', ball_3, ', ', ball_4, ', ', ball_5, ' + ', lucky_star_1, ', ', lucky_star_2)
        ELSE 
            CONCAT(ball_1, ', ', ball_2, ', ', ball_3, ', ', ball_4, ', ', ball_5, ', ', ball_6, ' (Bonus: ', bonus_ball, ')')
    END as winning_numbers
FROM lottery_draws
WHERE jackpot_winners > 0
ORDER BY draw_date DESC
LIMIT 20;

-- Biggest jackpots
CREATE OR REPLACE VIEW biggest_jackpots AS
SELECT 
    lottery_name,
    draw_date,
    jackpot_amount,
    jackpot_winners,
    CASE 
        WHEN lottery_name = 'EuroMillions' THEN 
            CONCAT(ball_1, ', ', ball_2, ', ', ball_3, ', ', ball_4, ', ', ball_5, ' + ', lucky_star_1, ', ', lucky_star_2)
        ELSE 
            CONCAT(ball_1, ', ', ball_2, ', ', ball_3, ', ', ball_4, ', ', ball_5, ', ', ball_6)
    END as winning_numbers
FROM lottery_draws
ORDER BY jackpot_amount DESC
LIMIT 20;
