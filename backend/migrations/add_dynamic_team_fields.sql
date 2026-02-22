-- 動的チーム編成機能のためのフィールド追加
-- タスクごとにチームメンバーとリーダーを指定可能にする

-- team_member_ids: チームメンバーのエージェントIDリスト（JSON配列）
-- leader_agent_id: チームリーダーのエージェントID（外部キー）

ALTER TABLE tasks ADD COLUMN team_member_ids TEXT;  -- JSON配列として保存
ALTER TABLE tasks ADD COLUMN leader_agent_id INTEGER REFERENCES agents(id);

-- インデックス作成（パフォーマンス向上）
CREATE INDEX IF NOT EXISTS idx_tasks_leader_agent ON tasks(leader_agent_id);

-- 既存データの初期化（NULLのまま）
-- デフォルトは空で、ユーザーが必要に応じて設定する

