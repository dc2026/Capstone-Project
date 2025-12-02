-- ================================
-- SQLite compatible schema
-- ================================

-- Create recipe table
CREATE TABLE IF NOT EXISTS recipes (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    RECIPE_NAME TEXT NOT NULL,
    INGREDIENTS TEXT NOT NULL,
    TIME INT,
    INSTRUCTIONS TEXT,
    CUSINE_TYPE TEXT
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    USER_NAME TEXT PRIMARY KEY,
    PASSWORD TEXT
);

-- Create ingredients table for users
CREATE TABLE IF NOT EXISTS ingredients (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    INGREDIENT TEXT NOT NULL,
    USER_NAME TEXT NOT NULL,
    FOREIGN KEY (USER_NAME) REFERENCES users(USER_NAME)
);

-- ================================
-- Data import for recipes
-- ================================

-- Temporary staging table
CREATE TABLE IF NOT EXISTS temp (
    RECIPE_NAME TEXT NOT NULL,
    INGREDIENTS TEXT NOT NULL,
    TIME INT,
    INSTRUCTIONS TEXT,
    CUSINE_TYPE TEXT
);

-- Switch to CSV mode and import
.mode csv


-- Copy into recipes table
INSERT INTO recipes (RECIPE_NAME, INGREDIENTS, TIME, INSTRUCTIONS, CUSINE_TYPE)
SELECT RECIPE_NAME, INGREDIENTS, TIME, INSTRUCTIONS, CUSINE_TYPE
FROM temp;

-- Drop temp table
DROP TABLE temp;
