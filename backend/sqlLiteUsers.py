
import sqlite3



con = sqlite3.connect('forkcast.db')
cur= con.cursor()



# script = "INSERT INTO users (USER_EMAIL, USER_NAME, INGREDIENTS, USER_ID) VALUES (?, ?, ?) "


# cur.execute(script, (email, name, ingredients ))

cur.execute('''INSERT INTO users (EMAIL_ADDRESS, USER_NAME, INGREDIENTS) 
             VALUES (?, ?, ?)''', ('samanthaphill@gmail.com', 'samantha', 'eggs, tofu, test, milk'))


con.commit()

for r in cur.execute('''SELECT * FROM users'''):
    print(r)


