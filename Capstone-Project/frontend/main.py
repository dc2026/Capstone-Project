# Flask web application that connects frontend, backend algorithm, and database
# This serves as the main backend server for the recipe recommendation system

import os
import sys
import webbrowser
import threading
from flask import Flask, redirect, render_template, request, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


# get the absolute path to the project root directory
# ensures imports work regardless of where the script is run from
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# do we need this anymore since Danielle-Carrol would not be the root?
sys.path.append(os.path.join(project_root, 'Danielle-Carrol'))

# Import the recipe matching algorithm from Danielle's folder
from recipealgorithm import RecipeFinder

basedir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(basedir, '..', 'backend', 'forkcast.db')

# Initialize Flask web application
app = Flask(__name__, 
            template_folder='templates',  # templates folder in frontend
            static_folder=os.path.join(basedir, '..', 'static'),  # static folder in project root
            static_url_path='/static')
app.config['SECRET_KEY'] = os.urandom(64)  # Random secret key for session security

#app.config['SECRET_KEY'] = 'f3d8e9a7b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1'


# Initialize the recipe recommendation algorithm with the CSV data
# This loads all recipes and prepares the machine learning model
#finder = RecipeFinder('/Users/izzienielsen/Desktop/CSC Capstone/github downloads/Capstone-Project/backend/recipe.csv')

# should match everyone's directory
recipe_csv_path = os.path.join(basedir, '..', 'backend', 'recipe.csv')
finder = RecipeFinder(recipe_csv_path)

# database helper method
def get_db_connection():
    # replace with your db path
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle log-in requests and fetch existing user data"""
    print(f"DEBUG: Login route called - Method: {request.method}, Headers: {dict(request.headers)}")

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE USER = ?', (username,)).fetchone()
        conn.close()
        
        #print("username:", username)
        #print("user row:", dict(user) if user else None)

        if user and check_password_hash(user['PASSWORD'], password):
            session['username'] = username
            return redirect('/')
        else:
            #print("password hash check failed")
            return "Invalid credentials"
    
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle new user registration"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # hash the password safely
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (USER, PASSWORD) VALUES (?, ?)',
                (username, hashed_pw)
            )
            conn.commit()
            print(f"Added user {username} successfully")
        except sqlite3.IntegrityError as e:
            print("Database error:", e)
            return "Username already exists or invalid"
        finally:
            conn.close()

        return redirect('/login')

    return render_template('signup.html')

@app.route('/')
def home():
    """Serve the main frontend HTML page when user visits the root URL"""
    # Go to log in page first if the user is not already in session
    if 'username' not in session:
        return redirect('/login')
    # Read and return the HTML file from the frontend folder
    frontend_path = os.path.join(project_root, 'frontend', 'index.html')
    with open(frontend_path, 'r') as f:
        return f.read()

@app.route('/submit', methods=['POST'])
def submit():
    """Handle form submission: save user data and return recipe recommendations"""
    # Get JSON data sent from the frontend form
    data = request.get_json()
    
    # Connect to SQLite database and save user information
    # USER_NAME is auto-increment INTEGER, PASSWORD stores email, USER stores ingredients
    db_path = os.path.join(project_root, 'Izzie-Nielsen', 'forkcast.db')
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users (PASSWORD, USER) 
                         #VALUES (?, ?)''', 
                      (data['email'], data['ingredients']))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        pass
    
    # Use the recipe algorithm to find matching recipes based on user's ingredients
    # Algorithm uses TF-IDF vectorization and cosine similarity for matching
    matches = finder.find_recipes(data['ingredients'], top_n=5)
    
    # Convert numpy data types to Python native types for JSON serialization
    for match in matches:
        match['cook_time'] = int(match['cook_time'])  # Convert numpy int64 to Python int
        match['similarity'] = float(match['similarity'])  # Convert numpy float to Python float
    
    # Return the results as JSON for the frontend to display
    return jsonify({
        'status': 'success',
        'recipes': matches
    })

@app.route('/get_recipes')
def get_recipes():
    """API endpoint to retrieve all recipes from the database"""
    # Connect to database and fetch all recipe records
    db_path = os.path.join(project_root, 'frontend', 'forkcast.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes')
    recipes = cursor.fetchall()
    conn.close()
    
    # Convert database rows to JSON format for API response
    recipe_list = []
    for recipe in recipes:
        recipe_list.append({
            'id': recipe[0],           # Recipe ID
            'name': recipe[1],         # Recipe name
            'ingredients': recipe[2],  # Ingredients list
            'time': recipe[3],         # Cooking time
            'instructions': recipe[4], # Cooking instructions
            'cuisine': recipe[5]       # Cuisine type
        })
    
    return jsonify(recipe_list)


# Run the Flask development server when script is executed directly
if __name__ == '__main__':
    port = 5005

    # Automatically open browser after server starts
    def open_browser():
        webbrowser.open(f'http://localhost:{port}')

    # Start browser opening in a separate thread after 1 second delay
    threading.Timer(1, open_browser).start()

    print(f"\n Starting Forkcast Recipe Recommendation System...")
    print(f" Browser will open automatically at http://localhost:{port}")
    print(f" Enter your ingredients to get personalized recipe recommendations!\n")

    app.run(debug=True, port=port)  # Debug mode for development (shows errors and auto-reloads)

