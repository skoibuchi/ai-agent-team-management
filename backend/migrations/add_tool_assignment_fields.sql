-- Add tool_names field to agents table
ALTER TABLE agents ADD COLUMN tool_names TEXT;

-- Add additional_tool_names field to tasks table
ALTER TABLE tasks ADD COLUMN additional_tool_names TEXT;
