CREATE TABLE IF NOT EXISTS influencer_posts (
    id SERIAL PRIMARY KEY,
    influencer_id INT NOT NULL,
    post_id BIGINT NOT NULL,
    shortcode VARCHAR(255),
    likes INT,
    comments INT,
    thumbnail TEXT,
    text TEXT,
    post_date TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_influencer_posts_influencer_id ON influencer_posts (influencer_id);
