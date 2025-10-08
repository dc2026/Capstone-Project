
import os
from flask import Flask
import csv


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)



@app.route('/')
def home():
    

    return print('home')


    

@app.route('/get_recipes')
def get_recipes():
#    token = cache_handler.get_cached_token()

    recipe_list = []

    with open('recipe_info.csv', mode='r', newline='') as file:
        rows = csv.DictReader(file)
        for row in rows:
            recipe_list.append(row)
  
        
    

    

    
    # with open('user_info.csv', 'w', newline='') as csvfile:
    #     fieldnames = ['artist', 'id', 'title']
    #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #     writer.writeheader()
    #     for row in track_info_list: # type: ignore
    #         writer.writerow(row) 


    return recipe_list
    


# @app.route('/logout')
# def logout(): 
#     session.clear()
#     return redirect(url_for('home')) 


if __name__ == '__main__': 
    app.run(debug=True)