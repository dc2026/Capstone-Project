# Forkcast - Recipe Recommendation System

A web application that recommends recipes based on available ingredients using machine learning.

## Features
- **Frontend**: HTML form for ingredient input
- **Backend**: Flask API with recipe matching algorithm
- **Database**: SQLite database for user data and recipes
- **Algorithm**: TF-IDF vectorization and cosine similarity for recipe matching

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Capstone-Project-3
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
   - Enter your name, email, and available ingredients
   - Get personalized recipe recommendations!

## Project Structure
- `frontend/` - Flask backend server, HTML/CSS/JavaScript user interface, and ML algorithm
- `backend/` - Database files, schema, and recipe data
- `requirements.txt` - Python dependencies

## How It Works
1. User submits ingredients through web form
2. Backend saves user data to SQLite database
3. ML algorithm finds similar recipes using TF-IDF and cosine similarity
4. Top 5 matching recipes are returned and displayed
5. Results show recipe name, ingredients, instructions, cook time, and cuisine type