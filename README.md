# Forkcast - Recipe Recommendation System

A web application that recommends recipes based on available ingredients using machine learning.

## Features
- **Frontend**: HTML form for ingredient input with dietary filtering
- **Backend**: Flask API with recipe matching algorithm
- **Database**: SQLite database for user data, recipes, and favorites
- **Algorithm**: TF-IDF vectorization and cosine similarity for recipe matching
- **Dietary Restrictions**: Vegetarian, Vegan, Pescatarian, Gluten-Free, Keto, Paleo filtering
- **Allergy Management**: Nuts, Dairy, Shellfish, Eggs, Soy, Sesame filtering
- **Party Mode**: Prioritizes recipes suitable for large groups
- **Pantry Management**: Save and manage your available ingredients
- **Recipe Favorites**: Save and view your favorite recipes
- **Quick Ingredients**: One-click addition of common ingredients

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Capstone-Project-4
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python frontend/main.py
   ```

4. **Access the application**
   - Open browser to `http://localhost:5005`
   - Create an account or log in
   - Enter ingredients and dietary preferences
   - Get personalized recipe recommendations!

## Project Structure
- `frontend/` - Contains the main application components:
  - `main.py` - Flask web server with authentication, dietary filtering, and favorites
  - `recipealgorithm.py` - Enhanced ML algorithm with dietary restriction filtering
  - `index.html` - Main interface with dietary options and quick ingredients
  - `templates/` - HTML templates for different pages:
    - `login.html` - User authentication
    - `signup.html` - Account creation
    - `pantry.html` - Ingredient management
    - `party.html` - Party mode interface
    - `favorites.html` - Saved recipes display
- `backend/` - Database and data management:
  - `forkcast.db` - SQLite database with users, ingredients, and favorites tables
  - `recipe.csv` - Master recipe dataset with ingredients, instructions, and metadata
- `requirements.txt` - Python package dependencies (Flask, pandas, scikit-learn, numpy)

## How It Works
1. User creates account and logs in
2. User submits ingredients through web form with optional dietary restrictions/allergies
3. ML algorithm finds similar recipes using TF-IDF and cosine similarity
4. Recipes are filtered based on dietary preferences and allergies
5. Top 5 matching recipes are returned and displayed
6. Users can save favorite recipes and manage pantry ingredients

## New Features

### Dietary Restrictions & Allergies
- **Dietary Options**: Vegetarian, Vegan, Pescatarian, Gluten-Free, Keto, Paleo
- **Allergy Filtering**: Nuts, Dairy, Shellfish, Eggs, Soy, Sesame
- Automatically excludes recipes containing restricted ingredients

### Party Mode
- Accessible via `/party` route
- Prioritizes recipes suitable for large groups (casseroles, stews, batch dishes)
- Same dietary filtering options available

### Pantry Management
- Save ingredients you have at home
- Generate recipes directly from pantry ingredients
- Add/remove ingredients easily

### Recipe Favorites
- Save recipes you like with the "💾 Save" button
- View all saved recipes at `/favorites`
- Organized collection of your preferred recipes

### Quick Ingredients
- One-click buttons for common ingredients (Garlic, Onion, Cheese, Tomato, Chicken)
- Based on most frequent ingredients in the recipe database
- Speeds up ingredient entry process
