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

# Add path for recipe algorithm imports
sys.path.append(os.path.dirname(__file__))

# Import the recipe matching algorithm
from recipealgorithm import RecipeFinder

# Setup paths
basedir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(basedir, "..", "backend", "forkcast.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # recipes table
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

    # users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        USER_NAME TEXT PRIMARY KEY,
        PASSWORD TEXT,
        USER TEXT
    );
    """)

    # pantry ingredients table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
        USER_NAME TEXT NOT NULL,
        INGREDIENT TEXT NOT NULL,
        FOREIGN KEY (USER_NAME) REFERENCES users(USER_NAME)
    );
    """)

    # favorites table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        USER_NAME TEXT NOT NULL,
        RECIPE_NAME TEXT NOT NULL,
        INGREDIENTS TEXT NOT NULL,
        INSTRUCTIONS TEXT NOT NULL,
        FOREIGN KEY (USER_NAME) REFERENCES users(USER_NAME)
    );
    """)

    # --- Potlucks: tables that were missing ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS potlucks (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        POTLUCK_NAME TEXT NOT NULL,
        CREATOR TEXT NOT NULL,
        CREATED_AT DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # potluck_members with a UNIQUE constraint to avoid duplicate rows
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS potluck_members (
        POTLUCK_ID INTEGER NOT NULL,
        USER_NAME TEXT NOT NULL,
        PRIMARY KEY (POTLUCK_ID, USER_NAME),
        FOREIGN KEY (POTLUCK_ID) REFERENCES potlucks(ID),
        FOREIGN KEY (USER_NAME) REFERENCES users(USER_NAME)
    );
    """)

    # potluck ingredients (we'll rely on sqlite ROWID for the ID used in deletes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS potluck_ingredients (
        POTLUCK_ID INTEGER NOT NULL,
        USER_NAME TEXT NOT NULL,
        INGREDIENT TEXT NOT NULL,
        FOREIGN KEY (POTLUCK_ID) REFERENCES potlucks(ID),
        FOREIGN KEY (USER_NAME) REFERENCES users(USER_NAME)
    );
    """)

    # Debug prints (optional)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print("Tables in DB:", cursor.fetchall())

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

def scale_ingredients(ingredients_text, serving_size):
    """Scale ingredient quantities for party mode"""
    import re
    
    def scale_number(match):
        number = float(match.group(1))
        scaled = number * serving_size
        # Format nicely (remove .0 for whole numbers)
        if scaled == int(scaled):
            return str(int(scaled))
        else:
            return f"{scaled:.1f}"
    
    # Scale numbers followed by common units
    scaled = re.sub(r'(\d+(?:\.\d+)?)\s*(cups?|tbsp|tsp|lbs?|oz|pounds?|ounces?|cloves?|pieces?)', 
                   lambda m: scale_number(m) + ' ' + m.group(2), ingredients_text)
    
    # Scale standalone numbers at the beginning of ingredient items
    scaled = re.sub(r'\b(\d+(?:\.\d+)?)\s+', 
                   lambda m: scale_number(m) + ' ', scaled)
    
    return scaled


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
    party_mode = data.get("partyMode", False)
    cuisines = data.get("cuisines", [])

    
    matches = finder.find_recipes(data["ingredients"], top_n=5, restrictions=restrictions, allergies=allergies, party_mode=party_mode, cuisines=cuisines)
    
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
        party_mode = data.get("partyMode", False)
        cuisines = data.get("cuisines", [])

        
        # Find recipe matches with optional dietary filtering
        matches = finder.find_recipes(ingredients_string, top_n=5, restrictions=restrictions, allergies=allergies, party_mode=party_mode, cuisines=cuisines)
        for match in matches:
            match["cook_time"] = int(match["cook_time"])
            match["similarity"] = float(match["similarity"])
        
        return jsonify({"status": "success", "recipes": matches})
        
    except Exception as e:
        print(f"ERROR generating recipes from pantry: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============== PANTRY ROUTES ==============

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

# ============== PARTY ROUTES ==============

@app.route("/party")
def party():
    """Party mode page for large group cooking"""
    if "username" not in session:
        return redirect("/login")
    
    return render_template("party.html")


# ============== FAVORITES ROUTES ==============

@app.route("/save_recipe", methods=["POST"])
def save_recipe():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO favorites (USER_NAME, RECIPE_NAME, INGREDIENTS, INSTRUCTIONS) VALUES (?, ?, ?, ?)",
            (session["username"], data["recipe"], data["ingredients"], data["instructions"])
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Recipe saved!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/favorites")
def favorites():
    if "username" not in session:
        return redirect("/login")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ROWID, RECIPE_NAME, INGREDIENTS, INSTRUCTIONS FROM favorites WHERE USER_NAME = ?",
        (session["username"],)
    )
    favorites = cursor.fetchall()
    conn.close()
    
    return render_template("favorites.html", favorites=favorites)

# ============== POTLUCK ==============

@app.route("/potluck")
def potluck():
    """Potluck mode page where users collaborate on ingredients"""
    if "username" not in session:
        return redirect("/login")
    return render_template("potluck.html")


@app.route("/potluck/create", methods=["POST"])
def create_potluck():
    """Create a new potluck event"""
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    data = request.get_json()
    potluck_name = data.get("potluck_name", "").strip()

    if not potluck_name:
        return jsonify({"status": "error", "message": "Potluck name required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create new potluck
        cursor.execute(
            "INSERT INTO potlucks (POTLUCK_NAME, CREATOR) VALUES (?, ?)",
            (potluck_name, session["username"])
        )
        potluck_id = cursor.lastrowid

        # Add creator as first member
        cursor.execute(
            "INSERT INTO potluck_members (POTLUCK_ID, USER_NAME) VALUES (?, ?)",
            (potluck_id, session["username"])
        )

        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Potluck created!",
            "potluck_id": potluck_id
        })

    except Exception as e:
        print(f"ERROR creating potluck: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route("/potluck/list")
def list_potlucks():
    """Get all potlucks the user is a member of"""
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.ID, p.POTLUCK_NAME, p.CREATOR, p.CREATED_AT
            FROM potlucks p
            JOIN potluck_members pm ON p.ID = pm.POTLUCK_ID
            WHERE pm.USER_NAME = ?
            ORDER BY p.CREATED_AT DESC
        """, (session["username"],))

        potlucks = cursor.fetchall()
        conn.close()

        potluck_list = [{
            "id": p["ID"],
            "name": p["POTLUCK_NAME"],
            "creator": p["CREATOR"],
            "created_at": p["CREATED_AT"]
        } for p in potlucks]

        return jsonify({"status": "success", "potlucks": potluck_list})

    except Exception as e:
        print(f"ERROR listing potlucks: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route("/potluck/<int:potluck_id>/join", methods=["POST"])
def join_potluck(potluck_id):
    """Join an existing potluck"""
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if potluck exists
        cursor.execute("SELECT ID FROM potlucks WHERE ID = ?", (potluck_id,))
        if not cursor.fetchone():
            return jsonify({"status": "error", "message": "Potluck not found"}), 404

        # Add user to potluck (ignore if already member)
        try:
            cursor.execute(
                "INSERT INTO potluck_members (POTLUCK_ID, USER_NAME) VALUES (?, ?)",
                (potluck_id, session["username"])
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Already a member

        conn.close()
        return jsonify({"status": "success", "message": "Joined potluck!"})

    except Exception as e:
        print(f"ERROR joining potluck: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route("/potluck/<int:potluck_id>/ingredients")
def get_potluck_ingredients(potluck_id):
    """Get all ingredients for a potluck with who's bringing what"""
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify user is member
        cursor.execute(
            "SELECT 1 FROM potluck_members WHERE POTLUCK_ID = ? AND USER_NAME = ?",
            (potluck_id, session["username"])
        )
        if not cursor.fetchone():
            return jsonify({"status": "error", "message": "Not a potluck member"}), 403

        # Get all ingredients
        cursor.execute("""
            SELECT ROWID as id, INGREDIENT, USER_NAME
            FROM potluck_ingredients
            WHERE POTLUCK_ID = ?
            ORDER BY USER_NAME, INGREDIENT
        """, (potluck_id,))

        ingredients = cursor.fetchall()
        conn.close()

        ingredient_list = [{
            "id": i["id"],
            "ingredient": i["INGREDIENT"],
            "user": i["USER_NAME"]
        } for i in ingredients]

        return jsonify({"status": "success", "ingredients": ingredient_list})

    except Exception as e:
        print(f"ERROR getting potluck ingredients: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route("/potluck/<int:potluck_id>/add_ingredient", methods=["POST"])
def add_potluck_ingredient(potluck_id):
    """Add ingredient to potluck"""
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    data = request.get_json()
    ingredient = data.get("ingredient", "").strip()

    if not ingredient:
        return jsonify({"status": "error", "message": "No ingredient provided"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify user is member
        cursor.execute(
            "SELECT 1 FROM potluck_members WHERE POTLUCK_ID = ? AND USER_NAME = ?",
            (potluck_id, session["username"])
        )
        if not cursor.fetchone():
            return jsonify({"status": "error", "message": "Not a potluck member"}), 403

        # Add ingredient
        cursor.execute(
            "INSERT INTO potluck_ingredients (POTLUCK_ID, USER_NAME, INGREDIENT) VALUES (?, ?, ?)",
            (potluck_id, session["username"], ingredient)
        )
        conn.commit()
        conn.close()

        return jsonify({"status": "success", "message": "Ingredient added!"})

    except Exception as e:
        print(f"ERROR adding potluck ingredient: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route("/potluck/<int:potluck_id>/remove_ingredient/<int:ingredient_id>", methods=["DELETE"])
def remove_potluck_ingredient(potluck_id, ingredient_id):
    """Remove ingredient from potluck (only if you added it)"""
    if "username" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete only if user owns it
        cursor.execute(
            "DELETE FROM potluck_ingredients WHERE ROWID = ? AND POTLUCK_ID = ? AND USER_NAME = ?",
            (ingredient_id, potluck_id, session["username"])
        )
        conn.commit()
        conn.close()

        return jsonify({"status": "success", "message": "Ingredient removed"})

    except Exception as e:
        print(f"ERROR removing potluck ingredient: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route("/potluck/<int:potluck_id>/generate_recipes", methods=["POST"])
def generate_potluck_recipes(potluck_id):
    """Generate recipes for a potluck and return them in the SAME format as /get_recipes"""
    
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify user belongs to the potluck
        cursor.execute(
            "SELECT 1 FROM potluck_members WHERE POTLUCK_ID = ? AND USER_NAME = ?",
            (potluck_id, session["username"])
        )
        if not cursor.fetchone():
            return jsonify({"error": "Not a potluck member"}), 403

        # Get all potluck ingredients
        cursor.execute(
            "SELECT INGREDIENT FROM potluck_ingredients WHERE POTLUCK_ID = ?",
            (potluck_id,)
        )
        ingredients = cursor.fetchall()

        if not ingredients:
            return jsonify({"error": "No ingredients yet"}), 400

        ingredient_list = [row["INGREDIENT"] for row in ingredients]
        ingredients_string = ", ".join(ingredient_list)

        print(f"DEBUG: Generating recipes for potluck {potluck_id}: {ingredients_string}")

        # Generate recipes using ingredient finder
        matches = finder.find_recipes(ingredients_string, top_n=5)

        # Standardize data fields
        for m in matches:
            m["cook_time"] = int(m["cook_time"])
            m["similarity"] = float(m["similarity"])

        # --- Save generated recipes to database (optional but matches index.html behavior) ---
        recipe_ids = []
        for m in matches:
            cursor.execute(
                """
                INSERT INTO potluck_recipes (POTLUCK_ID, NAME, INGREDIENTS, TIME, INSTRUCTIONS, CUISINE)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    potluck_id,
                    m["name"],
                    ", ".join(m["ingredients"]),
                    m["cook_time"],
                    m["steps"],
                    m.get("cuisine", "Unknown")
                )
            )
            recipe_ids.append(cursor.lastrowid)

        conn.commit()

        # Re-fetch recipes so the return EXACTLY matches /get_recipes
        cursor.execute(
            """
            SELECT ID, NAME, INGREDIENTS, TIME, INSTRUCTIONS, CUISINE
            FROM potluck_recipes
            WHERE POTLUCK_ID = ?
            ORDER BY ID DESC
            LIMIT 5
            """,
            (potluck_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        # Convert DB rows → identical JSON structure as /get_recipes
        recipe_list = []
        for r in rows:
            recipe_list.append({
                "id": r["ID"],
                "name": r["NAME"],
                "ingredients": r["INGREDIENTS"],
                "time": r["TIME"],
                "instructions": r["INSTRUCTIONS"],
                "cuisine": r["CUISINE"]
            })

        return jsonify(recipe_list)

    except Exception as e:
        print(f"ERROR generating potluck recipes: {e}")
        return jsonify({"error": str(e)}), 500




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
