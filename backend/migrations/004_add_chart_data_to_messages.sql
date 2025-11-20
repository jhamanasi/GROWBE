-- Add chart_data column to chat_messages table for storing visualization configurations
ALTER TABLE chat_messages ADD COLUMN chart_data TEXT;

