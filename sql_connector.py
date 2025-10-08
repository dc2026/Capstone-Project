import mysql.connector

# connects user to MySQL database
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    database="menu_recommender"
)

# example/instructions on accessing and using info from the database
# creates cursor to run commands
cursor = connection.cursor()

# how to execute queries
cursor.execute("SELECT * FROM recipes;")

# how to retreive results from queries
results = cursor.fetchall()

# printing query results
for row in results:
    print(row)

# close connections at the end!
cursor.close()
connection.close()