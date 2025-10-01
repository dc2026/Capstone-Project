-- if using workbench: use create new schema to create the database

-- only run once to create the database if using MySQL Shell
-- CREATE DATABASE menu_recommender

-- run to start programming in the database if using MySQL shell
-- USE menu_recommender

-- creates the table for recipes 
CREATE TABLE recipes(
	RECIPE_NAME VARCHAR(50),
    INGREDIENTS VARCHAR(1024),
    ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY
);

-- change file path to match your path
-- loads data from csv into the recipes table
LOAD DATA INFILE '/Users/izzienielsen/Documents/CSC Capstone/github downloads/recipe_info.csv'
INTO TABLE recipes 
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS;




