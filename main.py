# Flask web application that connects frontend, backend algorithm, and database
# This serves as the main backend server for the recipe recommendation system

import os
import sqlite3
import sys
import threading
import webbrowser

from flask import Flask, jsonify, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

# Get the absolute path to the project root directory
# Ensures imports work regardless of where the script is run from
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import the recipe matching algorithm from frontend directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend'))
from recipealgorithm import RecipeFinder

# Setup paths
basedir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(basedir, "..", "backend", "forkcast.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # DON'T drop the ingredients table - only create if it doesn't exist
    # cursor.execute("DROP TABLE IF EXISTS ingredients;")  # REMOVED THIS LINE

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        RECIPE_NAME TEXT NOT NULL,
        INGREDIENTS TEXT NOT NULL,
        TIME INT,
        INSTRUCTIONS TEXT,
        CUSINE_TYPE TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        USER_NAME TEXT PRIMARY KEY,
        PASSWORD TEXT,
        USER TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
        USER_NAME TEXT NOT NULL,
        INGREDIENT TEXT NOT NULL,
        FOREIGN KEY (USER_NAME) REFERENCES users(USER_NAME)
    );
    """)

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print(cursor.fetchall())  # shows all tables

    cursor.execute("PRAGMA table_info(ingredients);")
    print(cursor.fetchall())  # shows columns in ingredients

    conn.commit()
    conn.close()

# Initialize Flask web application
app = Flask(
    __name__,
    template_folder="templates",  # templates folder in frontend
    static_folder=os.path.join(
        basedir, "..", "static"
    ),  # static folder in project root
    static_url_path="/static",
)
app.config["SECRET_KEY"] = os.urandom(64)  # Random secret key for session security

# Initialize the recipe recommendation algorithm with the CSV data
recipe_csv_path = os.path.join(basedir, "..", "backend", "recipe.csv")
finder = RecipeFinder(recipe_csv_path)
init_db()


# ============== DATABASE HELPER ==============
def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============== AUTHENTICATION ROUTES ==============
@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle log-in requests and fetch existing user data"""
    print(f"DEBUG: Login route called - Method: {request.method}")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE USER = ?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["PASSWORD"], password):
            session["username"] = username
            return redirect("/")
        else:
            return "Invalid credentials"

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_pw = generate_password_hash(password, method="pbkdf2:sha256")

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (USER_NAME, PASSWORD, USER) VALUES (?, ?, ?)",
                (username, hashed_pw, username),  # Fixed: added third parameter
            )
            conn.commit()
            print(f"Added user {username} successfully")
        except sqlite3.IntegrityError as e:
            print("Database error:", e)
            return "Username already exists"
        finally:
            conn.close()

        return redirect("/login")

    return render_template("signup.html")


@app.route("/logout")
def logout():
    """Log out the current user"""
    session.pop("username", None)
    return redirect("/login")


# ============== MAIN APPLICATION ROUTES ==============
@app.route("/")
def home():
    """Serve the main frontend HTML page when user visits the root URL"""
    # Redirect to login page if user is not logged in
    if "username" not in session:
        return redirect("/login")

    # Serve the main application page
    frontend_path = os.path.join(project_root, "frontend", "index.html")
    with open(frontend_path, "r") as f:
        return f.read()


@app.route("/submit", methods=["POST"])
def submit():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    data = request.get_json()
    
    # Get optional dietary restrictions and allergies from request
    restrictions = data.get("restrictions", [])
    allergies = data.get("allergies", [])
    
    matches = finder.find_recipes(data["ingredients"], top_n=5, restrictions=restrictions, allergies=allergies)
    
    for match in matches:
        match["cook_time"] = int(match["cook_time"])
        match["similarity"] = float(match["similarity"])

    return jsonify({"status": "success", "recipes": matches})


@app.route("/get_recipes", methods=["POST"])
def get_recipes():
    """API endpoint to retrieve all recipes from the database"""
    # Optional: Require login for this endpoint too
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    # Connect to database and fetch all recipe records
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes")
    recipes = cursor.fetchall()
    conn.close()

    # Convert database rows to JSON format
    recipe_list = []
    for recipe in recipes:
        recipe_list.append(
            {
                "id": recipe[0],
                "name": recipe[1],
                "ingredients": recipe[2],
                "time": recipe[3],
                "instructions": recipe[4],
                "cuisine": recipe[5],
            }
        )

    return jsonify(recipe_list)

@app.route("/generate_from_pantry", methods=["POST"])
def generate_from_pantry():
    """Generate recipes based on user's pantry ingredients"""
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    
    try:
        data = request.get_json() or {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all ingredients from user's pantry
        cursor.execute("SELECT INGREDIENT FROM ingredients WHERE USER_NAME = ?", (session["username"],))
        ingredients = cursor.fetchall()
        conn.close()
        
        if not ingredients:
            return jsonify({"status": "error", "message": "No ingredients in pantry. Add some first!"}), 400
        
        # Convert to comma-separated string
        ingredient_list = [row["INGREDIENT"] for row in ingredients]
        ingredients_string = ", ".join(ingredient_list)
        
        # Get optional dietary restrictions and allergies from request
        restrictions = data.get("restrictions", [])
        allergies = data.get("allergies", [])
        
        # Find recipe matches with optional dietary filtering
        matches = finder.find_recipes(ingredients_string, top_n=5, restrictions=restrictions, allergies=allergies)
        for match in matches:
            match["cook_time"] = int(match["cook_time"])
            match["similarity"] = float(match["similarity"])
        
        return jsonify({"status": "success", "recipes": matches})
        
    except Exception as e:
        print(f"ERROR generating recipes from pantry: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# pantry routes

@app.route("/get_ingredients")
def get_ingredients():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT USER_NAME, INGREDIENT FROM ingredients")
    ingredients = cursor.fetchall()
    conn.close()

    ingredient_list = []
    for row in ingredients:
        ingredient_list.append({"user": row[0], "ingredient": row[1]})

    return jsonify(ingredient_list)

@app.route("/add_ingredient", methods=["POST"])
def add_ingredient():
    """Add a single ingredient to user's pantry"""
    if "username" not in session:
        return redirect("/login")

    # Accept both JSON and form data
    if request.is_json:
        ingredient = request.get_json().get("ingredient", "").strip()
        use_json = True
    else:
        ingredient = request.form.get("ingredient", "").strip()
        use_json = False
    
    if not ingredient:
        if use_json:
            return jsonify({"status": "error", "message": "No ingredient provided"}), 400
        else:
            return redirect("/pantry")  # Redirect back even on error
    
    print(f"DEBUG: Adding ingredient '{ingredient}' for user {session['username']}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ingredients (USER_NAME, INGREDIENT) VALUES (?, ?)",
            (session["username"], ingredient)
        )
        conn.commit()
        print(f"DEBUG: Successfully added ingredient: {ingredient}")
        
        # Return JSON or redirect based on request type
        if use_json:
            return jsonify({"status": "success", "message": "Ingredient added"})
        else:
            return redirect("/pantry")  # Redirect back to pantry page
        
    except Exception as e:
        print(f"ERROR adding ingredient: {e}")
        if use_json:
            return jsonify({"status": "error", "message": str(e)}), 500
        else:
            return redirect("/pantry")
    finally:
        conn.close()

@app.route("/pantry")
def pantry():
    if "username" not in session:
        return redirect("/login")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch ingredients for the current user with ROWID for deletion
    cursor.execute(
        "SELECT ROWID as id, INGREDIENT FROM ingredients WHERE USER_NAME = ?",
        (session["username"],)
    )
    ingredients = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    ingredient_list = []
    for row in ingredients:
        ingredient_list.append({
            "id": row["id"],
            "INGREDIENT": row["INGREDIENT"]
        })
    
    print(f"DEBUG: Fetched ingredients: {ingredient_list}")  # Debug print
    
    return render_template("pantry.html", items=ingredient_list)

@app.route("/get_my_pantry", methods=["GET"])
def get_my_pantry():
    """Get current user's pantry ingredients"""
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT INGREDIENT FROM ingredients WHERE USER_NAME = ?",
            (session["username"],)
        )
        ingredients = cursor.fetchall()
        conn.close()
        
        # Convert to list of strings
        ingredient_list = [row["INGREDIENT"] for row in ingredients]
        
        return jsonify({"status": "success", "ingredients": ingredient_list})
        
    except Exception as e:
        print(f"ERROR getting pantry: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/pantry/remove/<int:ingredient_id>")
def remove_ingredient(ingredient_id):
    """Remove an ingredient from user's pantry"""
    if "username" not in session:
        return redirect("/login")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete the ingredient (only if it belongs to the current user)
        cursor.execute(
            "DELETE FROM ingredients WHERE ROWID = ? AND USER_NAME = ?",
            (ingredient_id, session["username"])
        )
        conn.commit()
        conn.close()
        
        print(f"DEBUG: Removed ingredient with id {ingredient_id}")
        
    except Exception as e:
        print(f"ERROR removing ingredient: {e}")
    
    return redirect("/pantry")



# ============== RUN SERVER ==============
if __name__ == "__main__":
    port = 5005

    def open_browser():
        """Automatically open browser after server starts"""
        webbrowser.open(f"http://localhost:{port}")

    # Start browser opening in a separate thread after 1 second delay
    threading.Timer(1, open_browser).start()

    print(f"\n Starting Forkcast Recipe Recommendation System...")
    print(f" Browser will open automatically at http://localhost:{port}")
    print(f" Please log in to get personalized recipe recommendations!\n")

    app.run(debug=True, port=port, use_reloader=False)
