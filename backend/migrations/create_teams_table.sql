-- チーム管理テーブルの作成
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    leader_agent_id INTEGER NOT NULL,
    member_ids TEXT,  -- JSON array
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (leader_agent_id) REFERENCES agents(id)
);

-- インデックスの作成
CREATE INDEX IF NOT EXISTS idx_teams_leader_agent_id ON teams(leader_agent_id);
CREATE INDEX IF NOT EXISTS idx_teams_is_active ON teams(is_active);

