import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz


# Read CSV and preprocess

df = pd.read_csv("/Users/daniellecarrol/Downloads/recipe_info.csv", sep=None, engine='python')
df.columns = df.columns.str.strip()
df['ingredients'] = df['ingredients'].str.lower()
df['ingredient_list'] = df['ingredients'].apply(lambda x: [i.strip() for i in x.split(",")])


# Helper functions
def diet_filter(ings, diet):
    if diet == 'vegan':
        forbidden = ['chicken','beef','shrimp','turkey','pork','fish',
                     'egg','cheese','yogurt','butter','parmesan',
                     'mozzarella','sour cream','cream','milk']  # note: milk here will still catch plain milk
        allowed_exceptions = ['coconut milk', 'almond milk', 'soy milk']  # keep plant-based milks
    elif diet == 'vegetarian':
        forbidden = ['chicken','beef','shrimp','turkey','pork','fish']
        allowed_exceptions = []
    else:
        return True

    for ing in ings:
        ing_clean = ing.lower()
        for f in forbidden:
            if f in ing_clean and ing_clean not in allowed_exceptions:
                return False
    return True


def ingredient_overlap_fuzzy(recipe_ings, user_ingredients, threshold=80):
    matches = 0
    for r_ing in recipe_ings:
        for u_ing in user_ingredients:
            if fuzz.partial_ratio(r_ing, u_ing) >= threshold:
                matches += 1
                break
    return matches * 0.1

def protein_boost(recipe_ings, user_ingredients, diet):
    if diet == 'omnivore':
        proteins = ['chicken','beef','shrimp','turkey','pork','fish']
    elif diet == 'vegetarian':
        proteins = ['cheese','eggs','yogurt','milk','butter']
    else:
        proteins = []
    boost = 0
    for r_ing in recipe_ings:
        for p in proteins:
            if p in r_ing and any(fuzz.partial_ratio(r_ing, u) >= 80 for u in user_ingredients):
                boost += 0.3
                break
    return boost


# Main interactive loop
while True:
    # User input
    diet = input("Are you omnivore, vegetarian, or vegan? ").strip().lower()
    user_input = input("What ingredients do you have? (separate with commas): ")
    user_ingredients = list(set([i.lower().strip() for i in user_input.split(",")]))

    # Filter recipes by diet
    filtered_df = df[df['ingredient_list'].apply(lambda x: diet_filter(x, diet))].copy()


    # TF-IDF similarity
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(filtered_df['ingredients'])
    user_vector = vectorizer.transform([' '.join(user_ingredients)])
    filtered_df['similarity'] = cosine_similarity(user_vector, tfidf_matrix).flatten()

    # Adjusted score
    filtered_df['adjusted_score'] = filtered_df.apply(
        lambda row: row['similarity'] + ingredient_overlap_fuzzy(row['ingredient_list'], user_ingredients),
        axis=1
    )
    filtered_df['adjusted_score'] += filtered_df['ingredient_list'].apply(
        lambda x: protein_boost(x, user_ingredients, diet)
    )

    # Top matches
    best_matches = filtered_df[filtered_df['adjusted_score'] > 0].sort_values('adjusted_score', ascending=False).head(5)

    # Display results
    if best_matches.empty:
        print("\nNo recipes found for your diet with enough matching ingredients.\n")
    else:
        print("\nHere are the best recipe matches based on your ingredients and diet:\n")
        for _, row in best_matches.iterrows():
            print(f"{row['recipe']}")
            print(f"Ingredients: {row['ingredients']}\n")

    # Ask if user wants to try again
    again = input("Do you want to try a different diet or update ingredients? (yes/no): ").strip().lower()
    if again != 'yes':
        break
