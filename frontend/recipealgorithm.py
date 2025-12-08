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
    
    def find_recipes(self, user_ingredients, top_n=5, restrictions=None, allergies=None, party_mode=False, cuisines=None):
        """Find recipes that best match the user's available ingredients"""
        # Convert user's ingredients to the same vector format as recipe data
        user_vector = self.vectorizer.transform([user_ingredients])
        
        # Calculate cosine similarity between user ingredients and all recipes
        similarities = cosine_similarity(user_vector, self.tfidf_matrix).flatten()
        
        # For party mode, boost recipes that are good for large groups
        if party_mode:
            for idx in range(len(similarities)):
                recipe_name = self.df.iloc[idx]['recipe'].lower()
                recipe_ingredients = self.df.iloc[idx]['ingredients'].lower()
                # Boost recipes that are naturally party-friendly
                if any(word in recipe_name for word in ['casserole', 'bake', 'roast', 'stew', 'soup', 'chili']):
                    similarities[idx] *= 1.2
                if any(word in recipe_ingredients for word in ['large', 'batch', 'family']):
                    similarities[idx] *= 1.1
        
        # Find the indices of the top N most similar recipes
        top_indices = similarities.argsort()[-top_n*3:][::-1]  # Get more to filter
        
        # Build the results list with recipe details and similarity scores
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                recipe_ingredients = self.df.iloc[idx]['ingredients'].lower()

                # Cuisine filtering
                if cuisines:
                    recipe_cuisine = str(self.df.iloc[idx]['cuisine']).lower()
                    if not any(c.lower() in recipe_cuisine for c in cuisines):
                        continue

                
                # Check dietary restrictions
                if restrictions:
                    skip_recipe = False
                    for restriction in restrictions:
                        restriction = restriction.lower()
                        if restriction in ['vegetarian', 'vegan']:
                            meat_words = ['chicken', 'beef', 'pork', 'fish', 'meat', 'turkey', 'lamb', 'bacon', 'ham', 'sausage', 'seafood', 'shrimp', 'crab']
                            if any(meat in recipe_ingredients for meat in meat_words):
                                skip_recipe = True
                                break
                        if restriction == 'vegan':
                            animal_products = ['cheese', 'milk', 'butter', 'cream', 'egg', 'honey', 'yogurt']
                            if any(product in recipe_ingredients for product in animal_products):
                                skip_recipe = True
                                break
                        if restriction == 'gluten-free':
                            gluten_words = ['wheat', 'flour', 'bread', 'pasta', 'noodles', 'soy sauce', 'barley', 'rye']
                            if any(gluten in recipe_ingredients for gluten in gluten_words):
                                skip_recipe = True
                                break
                        if restriction == 'pescatarian':
                            meat_words = ['chicken', 'beef', 'pork', 'meat', 'turkey', 'lamb', 'bacon', 'ham', 'sausage']
                            if any(meat in recipe_ingredients for meat in meat_words):
                                skip_recipe = True
                                break
                        if restriction == 'keto':
                            high_carb_words = ['rice', 'pasta', 'bread', 'potato', 'noodles', 'flour', 'sugar', 'beans', 'corn']
                            if any(carb in recipe_ingredients for carb in high_carb_words):
                                skip_recipe = True
                                break
                        if restriction == 'paleo':
                            non_paleo_words = ['dairy', 'cheese', 'milk', 'beans', 'lentils', 'peanuts', 'grains', 'rice', 'wheat', 'oats']
                            if any(non_paleo in recipe_ingredients for non_paleo in non_paleo_words):
                                skip_recipe = True
                                break
                    if skip_recipe:
                        continue
                
                # Check allergies
                if allergies:
                    skip_recipe = False
                    for allergy in allergies:
                        allergy = allergy.lower()
                        if allergy == 'nuts':
                            nut_words = ['nuts', 'peanut', 'almond', 'walnut', 'cashew', 'pecan', 'hazelnut', 'pistachio']
                            if any(nut in recipe_ingredients for nut in nut_words):
                                skip_recipe = True
                                break
                        elif allergy == 'dairy':
                            dairy_words = ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'dairy']
                            if any(dairy in recipe_ingredients for dairy in dairy_words):
                                skip_recipe = True
                                break
                        elif allergy == 'shellfish':
                            shellfish_words = ['shrimp', 'crab', 'lobster', 'shellfish', 'seafood']
                            if any(shellfish in recipe_ingredients for shellfish in shellfish_words):
                                skip_recipe = True
                                break
                        elif allergy == 'eggs':
                            egg_words = ['egg', 'eggs']
                            if any(egg in recipe_ingredients for egg in egg_words):
                                skip_recipe = True
                                break
                        elif allergy == 'soy':
                            soy_words = ['soy', 'tofu', 'tempeh', 'miso', 'edamame']
                            if any(soy_word in recipe_ingredients for soy_word in soy_words):
                                skip_recipe = True
                                break
                        elif allergy == 'sesame':
                            sesame_words = ['sesame', 'tahini']
                            if any(sesame_word in recipe_ingredients for sesame_word in sesame_words):
                                skip_recipe = True
                                break
                        else:
                            # Direct match for other allergies
                            if allergy in recipe_ingredients:
                                skip_recipe = True
                                break
                    if skip_recipe:
                        continue
                
                results.append({
                    'recipe': self.df.iloc[idx]['recipe'],
                    'ingredients': self.df.iloc[idx]['ingredients'],
                    'cook_time': self.df.iloc[idx]['cook_time'],
                    'instructions': self.df.iloc[idx]['instructions'],
                    'cuisine': self.df.iloc[idx]['cuisine'],
                    'similarity': similarities[idx]
                })
                
                if len(results) >= top_n:
                    break
        
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
