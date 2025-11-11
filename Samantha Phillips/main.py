# Flask web application that connects frontend, backend algorithm, and database
# This serves as the main backend server for the recipe recommendation system

import os
import sys
import webbrowser
import threading
from flask import Flask, request, jsonify
import sqlite3

# Get the absolute path to the project root directory
# This ensures imports work regardless of where the script is run from
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(project_root, 'Danielle-Carrol'))

# Import the recipe matching algorithm from Danielle's folder
from recipealgorithm import RecipeFinder

# Initialize Flask web application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)  # Random secret key for session security

# Initialize the recipe recommendation algorithm with the CSV data
# This loads all recipes and prepares the machine learning model
finder = RecipeFinder(os.path.join(project_root, 'Izzie-Nielsen', 'recipe.csv'))

@app.route('/')
def home():
    """Serve the main frontend HTML page when user visits the root URL"""
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
                         VALUES (?, ?)''', 
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
    db_path = os.path.join(project_root, 'Izzie-Nielsen', 'forkcast.db')
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
    
    app.run(debug=True, port=port)# Debug mode for development (shows errors and auto-reloads)
