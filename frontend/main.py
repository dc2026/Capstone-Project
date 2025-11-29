# Flask web application that connects frontend, backend algorithm, and database
# This serves as the main backend server for the recipe recommendation system

import os
import sys
import webbrowser
import threading
from flask import Flask, redirect, render_template, request, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Get the absolute path to the project root directory
# Ensures imports work regardless of where the script is run from
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add path for recipe algorithm imports
sys.path.append(os.path.join(project_root, 'Danielle-Carrol'))

# Import the recipe matching algorithm
from recipealgorithm import RecipeFinder

# Setup paths
basedir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(basedir, '..', 'backend', 'forkcast.db')

# Initialize Flask web application
app = Flask(__name__, 
            template_folder='templates',  # templates folder in frontend
            static_folder=os.path.join(basedir, '..', 'static'),  # static folder in project root
            static_url_path='/static')
app.config['SECRET_KEY'] = os.urandom(64)  # Random secret key for session security

# Initialize the recipe recommendation algorithm with the CSV data
recipe_csv_path = os.path.join(basedir, '..', 'backend', 'recipe.csv')
finder = RecipeFinder(recipe_csv_path)


# ============== DATABASE HELPER ==============
def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============== AUTHENTICATION ROUTES ==============
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle log-in requests and fetch existing user data"""
    print(f"DEBUG: Login route called - Method: {request.method}")

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE USER = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['PASSWORD'], password):
            session['username'] = username
            return redirect('/')
        else:
            return "Invalid credentials", 401
    
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle new user registration"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hash the password safely
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
            return "Username already exists or invalid", 400
        finally:
            conn.close()

        return redirect('/login')

    return render_template('signup.html')


@app.route('/logout')
def logout():
    """Log out the current user"""
    session.pop('username', None)
    return redirect('/login')


# ============== MAIN APPLICATION ROUTES ==============
@app.route('/')
def home():
    """Serve the main frontend HTML page when user visits the root URL"""
    # Redirect to login page if user is not logged in
    if 'username' not in session:
        return redirect('/login')
    
    # Serve the main application page
    frontend_path = os.path.join(project_root, 'frontend', 'index.html')
    with open(frontend_path, 'r') as f:
        return f.read()


@app.route('/submit', methods=['POST'])
def submit():
    """Handle form submission: save user data and return recipe recommendations"""
    # Check if user is logged in
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    
    # Get JSON data sent from the frontend form
    data = request.get_json()
    
    # Optional: Save user's search to database for history/analytics
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # You might want to create a separate table for search history
        # This is just an example - adjust based on your schema
        cursor.execute('''INSERT INTO user_searches (username, ingredients, timestamp) 
                         VALUES (?, ?, datetime('now'))''', 
                      (session['username'], data.get('ingredients', '')))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        # Don't fail the request if logging fails
        pass
    
    # Use the recipe algorithm to find matching recipes
    matches = finder.find_recipes(data['ingredients'], top_n=5)
    
    # Convert numpy data types to Python native types for JSON serialization
    for match in matches:
        match['cook_time'] = int(match['cook_time'])
        match['similarity'] = float(match['similarity'])
    
    # Return the results as JSON
    return jsonify({
        'status': 'success',
        'recipes': matches
    })


@app.route('/get_recipes')
def get_recipes():
    """API endpoint to retrieve all recipes from the database"""
    # Optional: Require login for this endpoint too
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Connect to database and fetch all recipe records
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes')
    recipes = cursor.fetchall()
    conn.close()
    
    # Convert database rows to JSON format
    recipe_list = []
    for recipe in recipes:
        recipe_list.append({
            'id': recipe[0],
            'name': recipe[1],
            'ingredients': recipe[2],
            'time': recipe[3],
            'instructions': recipe[4],
            'cuisine': recipe[5]
        })
    
    return jsonify(recipe_list)


# ============== RUN SERVER ==============
if __name__ == '__main__':
    port = 5005

    def open_browser():
        """Automatically open browser after server starts"""
        webbrowser.open(f'http://localhost:{port}')

    # Start browser opening in a separate thread after 1 second delay
    threading.Timer(1, open_browser).start()

    print(f"\n Starting Forkcast Recipe Recommendation System...")
    print(f" Browser will open automatically at http://localhost:{port}")
    print(f" Please log in to get personalized recipe recommendations!\n")

    app.run(debug=True, port=port)