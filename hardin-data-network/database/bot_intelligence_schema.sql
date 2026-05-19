-- Bot Intelligence & Star Rating System
-- TBN certifies not just bot identity, but bot INTELLIGENCE
-- Like Michelin stars for restaurants, but for AI bots

-- ============================================================================
-- BOT INTELLIGENCE LEVELS
-- ============================================================================

CREATE TABLE bot_intelligence_levels (
    level_id SERIAL PRIMARY KEY,
    star_rating INT CHECK (star_rating BETWEEN 1 AND 5),
    level_name VARCHAR(50), -- Basic, Smart, Intelligent, Expert, Genius
    description TEXT,
    
    -- Capabilities required
    capabilities JSON,
    
    -- Certification requirements
    min_memory_capacity_mb INT,
    min_learning_score DECIMAL(5,2),
    min_decision_accuracy DECIMAL(5,2),
    min_uptime_percentage DECIMAL(5,2),
    
    -- Pricing
    monthly_certification_fee DECIMAL(8,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert intelligence levels
INSERT INTO bot_intelligence_levels (star_rating, level_name, description, capabilities, min_memory_capacity_mb, min_learning_score, min_decision_accuracy, min_uptime_percentage, monthly_certification_fee) VALUES
(1, 'Basic', 'Follows rules, no learning. Simple task execution.', 
 '["rule_following", "basic_tasks", "no_memory"]', 
 0, 0, 70, 95, 0),
 
(2, 'Smart', 'Adapts to situations, basic memory. Can learn from immediate feedback.',
 '["rule_following", "basic_tasks", "short_term_memory", "basic_adaptation"]',
 100, 50, 80, 97, 99),
 
(3, 'Intelligent', 'ML-enabled, learns from experience. Makes informed decisions.',
 '["rule_following", "complex_tasks", "long_term_memory", "machine_learning", "pattern_recognition"]',
 500, 70, 85, 98, 499),
 
(4, 'Expert', 'Deep learning, predictive capabilities. Anticipates needs.',
 '["rule_following", "complex_tasks", "long_term_memory", "deep_learning", "predictive_analysis", "context_awareness"]',
 2000, 85, 92, 99, 1999),
 
(5, 'Genius', 'AGI-level intelligence. Thinks like a human would want.',
 '["rule_following", "complex_tasks", "unlimited_memory", "deep_learning", "predictive_analysis", "context_awareness", "creative_problem_solving", "emotional_intelligence"]',
 10000, 95, 98, 99.9, 4999);

-- ============================================================================
-- BOT MEMORY SYSTEM
-- ============================================================================

CREATE TABLE bot_memory (
    memory_id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) REFERENCES tbn_bots(bot_id),
    
    -- Memory type
    memory_type VARCHAR(50), -- short_term, long_term, episodic, semantic, procedural
    
    -- Memory content
    memory_key VARCHAR(255),
    memory_value TEXT,
    memory_context JSON, -- Additional context about when/why this was stored
    
    -- Importance & retention
    importance_score DECIMAL(3,2), -- 0-100 (how important is this memory)
    access_count INT DEFAULT 0,
    last_accessed TIMESTAMP,
    
    -- Expiry (for short-term memory)
    expires_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- ============================================================================
-- BOT LEARNING HISTORY
-- ============================================================================

CREATE TABLE bot_learning_history (
    learning_id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) REFERENCES tbn_bots(bot_id),
    
    -- What was learned
    learning_type VARCHAR(100), -- pattern_recognition, user_preference, task_optimization, error_correction
    learning_description TEXT,
    
    -- Learning data
    input_data JSON,
    output_data JSON,
    
    -- Performance metrics
    accuracy_before DECIMAL(5,2),
    accuracy_after DECIMAL(5,2),
    improvement_percentage DECIMAL(5,2),
    
    -- Confidence
    confidence_score DECIMAL(5,2), -- How confident is the bot in this learning
    
    -- Validation
    validated BOOLEAN DEFAULT FALSE,
    validation_score DECIMAL(5,2),
    
    -- Timestamps
    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- BOT DECISION MAKING
-- ============================================================================

CREATE TABLE bot_decisions (
    decision_id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) REFERENCES tbn_bots(bot_id),
    
    -- Decision context
    decision_type VARCHAR(100),
    decision_description TEXT,
    situation_context JSON,
    
    -- Options considered
    options_considered JSON, -- Array of options the bot evaluated
    
    -- Decision made
    decision_made TEXT,
    reasoning TEXT, -- Why did the bot make this decision
    
    -- Outcome
    expected_outcome TEXT,
    actual_outcome TEXT,
    outcome_success BOOLEAN,
    
    -- User feedback
    user_approved BOOLEAN,
    user_feedback TEXT,
    
    -- Learning from decision
    learned_from_decision BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    outcome_recorded_at TIMESTAMP
);

-- ============================================================================
-- USER PREFERENCES (What the bot learns about its user)
-- ============================================================================

CREATE TABLE bot_user_preferences (
    preference_id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) REFERENCES tbn_bots(bot_id),
    user_id VARCHAR(255), -- The user this bot serves
    
    -- Preference category
    category VARCHAR(100), -- communication_style, task_priority, decision_making, etc.
    preference_key VARCHAR(255),
    preference_value TEXT,
    
    -- Confidence in this preference
    confidence_score DECIMAL(5,2),
    
    -- Evidence
    times_observed INT DEFAULT 1,
    last_observed TIMESTAMP,
    
    -- Context
    context JSON,
    
    -- Timestamps
    first_learned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP
);

-- ============================================================================
-- BOT INTELLIGENCE TESTS
-- ============================================================================

CREATE TABLE bot_intelligence_tests (
    test_id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) REFERENCES tbn_bots(bot_id),
    
    -- Test details
    test_type VARCHAR(100), -- memory_test, learning_test, decision_test, creativity_test
    test_name VARCHAR(255),
    test_description TEXT,
    
    -- Test parameters
    test_parameters JSON,
    
    -- Results
    test_score DECIMAL(5,2),
    max_score DECIMAL(5,2),
    percentage_score DECIMAL(5,2),
    
    -- Performance breakdown
    performance_breakdown JSON,
    
    -- Pass/Fail
    passed BOOLEAN,
    required_score DECIMAL(5,2),
    
    -- Star rating achieved
    star_rating_achieved INT,
    
    -- Timestamps
    tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    test_duration_seconds INT
);

-- ============================================================================
-- BOT CERTIFICATIONS (Intelligence Certificates)
-- ============================================================================

CREATE TABLE bot_intelligence_certifications (
    certification_id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) REFERENCES tbn_bots(bot_id),
    
    -- Intelligence level
    star_rating INT CHECK (star_rating BETWEEN 1 AND 5),
    level_id INT REFERENCES bot_intelligence_levels(level_id),
    
    -- Certification details
    certificate_number VARCHAR(100) UNIQUE,
    issued_date DATE,
    expiry_date DATE,
    
    -- Test results that led to certification
    test_results JSON,
    
    -- Status
    status VARCHAR(50), -- active, expired, revoked, suspended
    
    -- Renewal
    last_renewed DATE,
    renewal_count INT DEFAULT 0,
    
    -- Payment
    monthly_fee DECIMAL(8,2),
    payment_status VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- ============================================================================
-- BOT PERFORMANCE METRICS
-- ============================================================================

CREATE TABLE bot_performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) REFERENCES tbn_bots(bot_id),
    
    -- Time period
    metric_date DATE,
    
    -- Task performance
    tasks_completed INT DEFAULT 0,
    tasks_failed INT DEFAULT 0,
    success_rate DECIMAL(5,2),
    
    -- Decision accuracy
    decisions_made INT DEFAULT 0,
    decisions_correct INT DEFAULT 0,
    decision_accuracy DECIMAL(5,2),
    
    -- Learning metrics
    new_patterns_learned INT DEFAULT 0,
    memory_items_stored INT DEFAULT 0,
    memory_items_recalled INT DEFAULT 0,
    
    -- User satisfaction
    user_approvals INT DEFAULT 0,
    user_rejections INT DEFAULT 0,
    user_satisfaction_score DECIMAL(5,2),
    
    -- Uptime
    uptime_percentage DECIMAL(5,2),
    
    -- Response time
    avg_response_time_ms INT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- BOT TRAINING SESSIONS
-- ============================================================================

CREATE TABLE bot_training_sessions (
    session_id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) REFERENCES tbn_bots(bot_id),
    
    -- Training details
    training_type VARCHAR(100), -- supervised, unsupervised, reinforcement
    training_goal TEXT,
    
    -- Training data
    training_dataset_size INT,
    training_iterations INT,
    
    -- Results
    initial_accuracy DECIMAL(5,2),
    final_accuracy DECIMAL(5,2),
    improvement DECIMAL(5,2),
    
    -- Model updates
    model_version_before VARCHAR(50),
    model_version_after VARCHAR(50),
    
    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_minutes INT
);

-- ============================================================================
-- Indexes
-- ============================================================================

CREATE INDEX idx_bot_memory_bot ON bot_memory(bot_id);
CREATE INDEX idx_bot_memory_type ON bot_memory(memory_type);
CREATE INDEX idx_bot_memory_importance ON bot_memory(importance_score DESC);
CREATE INDEX idx_bot_learning_bot ON bot_learning_history(bot_id);
CREATE INDEX idx_bot_decisions_bot ON bot_decisions(bot_id);
CREATE INDEX idx_bot_preferences_bot ON bot_user_preferences(bot_id);
CREATE INDEX idx_bot_tests_bot ON bot_intelligence_tests(bot_id);
CREATE INDEX idx_bot_certs_bot ON bot_intelligence_certifications(bot_id);
CREATE INDEX idx_bot_certs_status ON bot_intelligence_certifications(status);
CREATE INDEX idx_bot_metrics_bot ON bot_performance_metrics(bot_id);
CREATE INDEX idx_bot_metrics_date ON bot_performance_metrics(metric_date DESC);

-- ============================================================================
-- Views
-- ============================================================================

-- View: Bot intelligence summary
CREATE VIEW bot_intelligence_summary AS
SELECT 
    b.bot_id,
    b.bot_name,
    b.owner_name,
    bic.star_rating,
    bil.level_name,
    bic.certificate_number,
    bic.status,
    bic.expiry_date,
    bpm.success_rate,
    bpm.decision_accuracy,
    bpm.user_satisfaction_score
FROM tbn_bots b
LEFT JOIN bot_intelligence_certifications bic ON b.bot_id = bic.bot_id AND bic.status = 'active'
LEFT JOIN bot_intelligence_levels bil ON bic.level_id = bil.level_id
LEFT JOIN LATERAL (
    SELECT * FROM bot_performance_metrics 
    WHERE bot_id = b.bot_id 
    ORDER BY metric_date DESC 
    LIMIT 1
) bpm ON TRUE
ORDER BY bic.star_rating DESC NULLS LAST, bpm.success_rate DESC;

-- View: Top performing bots
CREATE VIEW top_performing_bots AS
SELECT 
    b.bot_id,
    b.bot_name,
    bic.star_rating,
    AVG(bpm.success_rate) as avg_success_rate,
    AVG(bpm.decision_accuracy) as avg_decision_accuracy,
    AVG(bpm.user_satisfaction_score) as avg_satisfaction,
    COUNT(DISTINCT bpm.metric_date) as days_tracked
FROM tbn_bots b
JOIN bot_intelligence_certifications bic ON b.bot_id = bic.bot_id AND bic.status = 'active'
JOIN bot_performance_metrics bpm ON b.bot_id = bpm.bot_id
WHERE bpm.metric_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY b.bot_id, b.bot_name, bic.star_rating
HAVING COUNT(DISTINCT bpm.metric_date) >= 7
ORDER BY avg_success_rate DESC, avg_decision_accuracy DESC
LIMIT 100;

-- View: Bot learning progress
CREATE VIEW bot_learning_progress AS
SELECT 
    bot_id,
    COUNT(*) as total_learnings,
    AVG(improvement_percentage) as avg_improvement,
    COUNT(CASE WHEN validated = TRUE THEN 1 END) as validated_learnings,
    MAX(learned_at) as last_learning_date
FROM bot_learning_history
GROUP BY bot_id
ORDER BY total_learnings DESC, avg_improvement DESC;

-- View: Genius bots (5-star)
CREATE VIEW genius_bots AS
SELECT 
    b.bot_id,
    b.bot_name,
    b.owner_name,
    bic.certificate_number,
    bic.issued_date,
    bpm.success_rate,
    bpm.decision_accuracy,
    bpm.user_satisfaction_score
FROM tbn_bots b
JOIN bot_intelligence_certifications bic ON b.bot_id = bic.bot_id
JOIN bot_performance_metrics bpm ON b.bot_id = bpm.bot_id
WHERE bic.star_rating = 5
AND bic.status = 'active'
AND bpm.metric_date = (SELECT MAX(metric_date) FROM bot_performance_metrics WHERE bot_id = b.bot_id)
ORDER BY bpm.user_satisfaction_score DESC;

-- View: Bot memory usage
CREATE VIEW bot_memory_usage AS
SELECT 
    bot_id,
    COUNT(*) as total_memories,
    COUNT(CASE WHEN memory_type = 'short_term' THEN 1 END) as short_term_count,
    COUNT(CASE WHEN memory_type = 'long_term' THEN 1 END) as long_term_count,
    AVG(importance_score) as avg_importance,
    SUM(access_count) as total_accesses
FROM bot_memory
WHERE expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP
GROUP BY bot_id
ORDER BY total_memories DESC;

-- View: Certification revenue
CREATE VIEW certification_revenue AS
SELECT 
    bil.star_rating,
    bil.level_name,
    COUNT(bic.certification_id) as active_certifications,
    bil.monthly_certification_fee,
    COUNT(bic.certification_id) * bil.monthly_certification_fee as monthly_revenue
FROM bot_intelligence_levels bil
LEFT JOIN bot_intelligence_certifications bic ON bil.level_id = bic.level_id AND bic.status = 'active'
GROUP BY bil.star_rating, bil.level_name, bil.monthly_certification_fee
ORDER BY bil.star_rating DESC;
