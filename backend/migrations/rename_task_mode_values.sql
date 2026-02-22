-- タスクモードの値を変更
-- manual -> single (個人タスク)
-- team -> team (チームタスク、そのまま)
-- auto -> auto (自動選択、そのまま)

UPDATE tasks SET mode = 'single' WHERE mode = 'manual';

-- 既存のteamとautoはそのまま

