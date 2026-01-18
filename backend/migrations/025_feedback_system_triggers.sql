-- Feedback System Triggers and Functions
-- Run this AFTER 025_feedback_system.sql

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_feature_requests_updated_at BEFORE UPDATE ON feature_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feature_comments_updated_at BEFORE UPDATE ON feature_comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bug_reports_updated_at BEFORE UPDATE ON bug_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feedback_notifications_updated_at BEFORE UPDATE ON feedback_notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update votes_count when votes are added/removed
CREATE OR REPLACE FUNCTION update_feature_votes_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE feature_requests 
        SET votes_count = votes_count + 1 
        WHERE id = NEW.feature_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE feature_requests 
        SET votes_count = votes_count - 1 
        WHERE id = OLD.feature_id;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER feature_votes_count_trigger
AFTER INSERT OR DELETE ON feature_votes
FOR EACH ROW EXECUTE FUNCTION update_feature_votes_count();

-- Function to update comments_count when comments are added/removed
CREATE OR REPLACE FUNCTION update_feature_comments_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE feature_requests 
        SET comments_count = comments_count + 1 
        WHERE id = NEW.feature_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE feature_requests 
        SET comments_count = comments_count - 1 
        WHERE id = OLD.feature_id;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER feature_comments_count_trigger
AFTER INSERT OR DELETE ON feature_comments
FOR EACH ROW EXECUTE FUNCTION update_feature_comments_count();
