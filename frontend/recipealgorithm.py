# Recipe recommendation algorithm using machine learning
# Uses TF-IDF vectorization and cosine similarity to match user ingredients with recipes

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer  # Converts text to numerical vectors
from sklearn.metrics.pairwise import cosine_similarity      # Measures similarity between vectors
import numpy as np
import os

class RecipeFinder:
    """Machine learning-based recipe recommendation system"""
    
    def __init__(self, csv_path):
        """Initialize the recipe finder with CSV data and train the ML model"""
        # Check if the CSV file exists before proceeding
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Load recipe data from CSV (no headers, so we define column names)
        # CSV format: recipe_name, ingredients, cook_time, instructions, cuisine
        self.df = pd.read_csv(csv_path, header=None, names=['recipe', 'ingredients', 'cook_time', 'instructions', 'cuisine'])
        
        # Initialize TF-IDF vectorizer to convert ingredient text to numerical vectors
        # TF-IDF = Term Frequency-Inverse Document Frequency (measures word importance)
        self.vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
        
        # Transform all recipe ingredients into numerical vectors for similarity comparison
        # This creates a matrix where each row represents a recipe's ingredient vector
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['ingredients'])
    
    def find_recipes(self, user_ingredients, top_n=5):
        """Find recipes that best match the user's available ingredients"""
        # Convert user's ingredients to the same vector format as recipe data
        # This ensures we can compare user input with existing recipes
        user_vector = self.vectorizer.transform([user_ingredients])
        
        # Calculate cosine similarity between user ingredients and all recipes
        # Cosine similarity measures the angle between vectors (0=no match, 1=perfect match)
        similarities = cosine_similarity(user_vector, self.tfidf_matrix).flatten()
        
        # Find the indices of the top N most similar recipes
        # argsort() sorts by similarity, [-top_n:] gets the highest values, [::-1] reverses for descending order
        top_indices = similarities.argsort()[-top_n:][::-1]
        
        # Build the results list with recipe details and similarity scores
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include recipes with some similarity (avoid zero matches)
                results.append({
                    'recipe': self.df.iloc[idx]['recipe'],           # Recipe name
                    'ingredients': self.df.iloc[idx]['ingredients'], # Required ingredients
                    'cook_time': self.df.iloc[idx]['cook_time'],     # Cooking time in minutes
                    'instructions': self.df.iloc[idx]['instructions'], # Step-by-step instructions
                    'cuisine': self.df.iloc[idx]['cuisine'],         # Cuisine type (Italian, Chinese, etc.)
                    'similarity': similarities[idx]                  # Similarity score (0-1)
                })
        
        return results

# Example usage and testing code
if __name__ == "__main__":
    """Test the recipe finder with sample ingredients"""
    # Get the path to the recipe CSV file (assumes it's in the same directory)
    csv_path = os.path.join(os.path.dirname(__file__), 'recipe_info.csv')
    
    # Verify the CSV file exists before trying to use it
    if not os.path.exists(csv_path):
        print(f"CSV file not found at {csv_path}")
        print("Please ensure the file exists or update the path.")
        exit(1)
    
    # Create an instance of the recipe finder and load the data
    finder = RecipeFinder(csv_path)
    
    # Test with sample ingredients that a user might have
    user_ingredients = "chicken, garlic, onion, tomato"
    
    # Find the top 5 most similar recipes
    matches = finder.find_recipes(user_ingredients, top_n=3)
    
    # Display the results in a user-friendly format
    print(f"Based on your ingredients: {user_ingredients}")
    print("\nTop matching recipes:")
    for i, match in enumerate(matches, 1):
        print(f"{i}. {match['recipe']} (similarity: {match['similarity']:.3f})")
        print(f"   Ingredients: {match['ingredients']}\n")
