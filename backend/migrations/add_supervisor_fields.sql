-- Supervisor Pattern用フィールドの追加
-- 実行日: 2026-02-19

-- agent_typeフィールドを追加（デフォルト: worker）
ALTER TABLE agents ADD COLUMN agent_type VARCHAR(20) DEFAULT 'worker';

-- supervisor_idフィールドを追加（外部キー: agents.id）
ALTER TABLE agents ADD COLUMN supervisor_id INTEGER REFERENCES agents(id);

-- インデックスを作成（パフォーマンス向上）
CREATE INDEX idx_agents_supervisor_id ON agents(supervisor_id);
CREATE INDEX idx_agents_agent_type ON agents(agent_type);

-- 既存のエージェントをすべてworkerタイプに設定
UPDATE agents SET agent_type = 'worker' WHERE agent_type IS NULL;

-- コメント追加
COMMENT ON COLUMN agents.agent_type IS 'エージェントタイプ: supervisor（監督者）, worker（作業者）';
COMMENT ON COLUMN agents.supervisor_id IS '所属するSupervisorエージェントのID';

