import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os

class RecipeFinder:
    def __init__(self, csv_path):
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        self.df = pd.read_csv(csv_path)
        self.df.columns = self.df.columns.str.strip()  # Remove leading/trailing spaces
        self.vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['ingredients'])
    
    def find_recipes(self, user_ingredients, top_n=5):
        # Transform user ingredients using the same vectorizer
        user_vector = self.vectorizer.transform([user_ingredients])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(user_vector, self.tfidf_matrix).flatten()
        
        # Get top N most similar recipes
        top_indices = similarities.argsort()[-top_n:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include recipes with some similarity
                results.append({
                    'recipe': self.df.iloc[idx]['recipe'],
                    'ingredients': self.df.iloc[idx]['ingredients'],
                    'similarity': similarities[idx]
                })
        
        return results

# Example usage
if __name__ == "__main__":
    # Initialize the recipe finder
    csv_path = os.path.join(os.path.dirname(__file__), 'recipe_info.csv')
    
    # Check if file exists, if not create a sample
    if not os.path.exists(csv_path):
        print(f"CSV file not found at {csv_path}")
        print("Please ensure the file exists or update the path.")
        exit(1)
    
    finder = RecipeFinder(csv_path)
    
    # Example: User has these ingredients
    user_ingredients = "chicken, garlic, onion, tomato"
    
    # Find matching recipes
    matches = finder.find_recipes(user_ingredients, top_n=3)
    
    print(f"Based on your ingredients: {user_ingredients}")
    print("\nTop matching recipes:")
    for i, match in enumerate(matches, 1):
        print(f"{i}. {match['recipe']} (similarity: {match['similarity']:.3f})")
        print(f"   Ingredients: {match['ingredients']}\n")
