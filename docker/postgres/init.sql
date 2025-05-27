-- インフルエンサー投稿のテーブル定義
CREATE TABLE IF NOT EXISTS influencer_posts (
    id SERIAL PRIMARY KEY,
    influencer_id INT NOT NULL,
    post_id BIGINT NOT NULL UNIQUE,  -- ユニーク制約を追加
    shortcode VARCHAR(50) NOT NULL,
    likes INT NOT NULL DEFAULT 0,
    comments INT NOT NULL DEFAULT 0,
    thumbnail TEXT,
    text TEXT,
    post_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- インフルエンサーIDに対するインデックス（頻繁に検索・集計に使用されるため）
CREATE INDEX IF NOT EXISTS idx_influencer_posts_influencer_id ON influencer_posts (influencer_id);

-- 投稿日時に対するインデックス（日付範囲での検索・ソートに使用）
CREATE INDEX IF NOT EXISTS idx_influencer_posts_post_date ON influencer_posts (post_date);

-- いいね数に対するインデックス（ランキング表示に使用）
CREATE INDEX IF NOT EXISTS idx_influencer_posts_likes ON influencer_posts (likes DESC);

-- コメント数に対するインデックス（ランキング表示に使用）
CREATE INDEX IF NOT EXISTS idx_influencer_posts_comments ON influencer_posts (comments DESC);

CREATE INDEX IF NOT EXISTS idx_influencer_posts_influencer_id ON influencer_posts (influencer_id);
