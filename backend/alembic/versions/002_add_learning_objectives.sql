-- Add learning and lesson objectives to chapters and paragraphs

-- Add learning_objective column to chapters table
ALTER TABLE chapters ADD COLUMN learning_objective TEXT;

-- Add lesson_objective column to paragraphs table
ALTER TABLE paragraphs ADD COLUMN lesson_objective TEXT;
