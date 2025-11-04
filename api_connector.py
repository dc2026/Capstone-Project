import os
import requests
from dotenv import load_dotenv

#get access token for API
load_dotenv()

CLIENT_ID = os.getenv("KROGER_CLIENT_ID")
CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET")

def get_access_token():
    url = "https://api.kroger.com/v1/connect/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "scope": "product.basic"
    }
    response = requests.post(url, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    response.raise_for_status()
    token = response.json()["access_token"]
    return token

token = get_access_token()
print("Access token:", token)

'''
# search for products after getting access token
def search_products(term, location_id="01400943", limit=5):
    token = get_access_token()
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    params = {
        "filter.term": term,
        "filter.locationId": location_id,
        "filter.limit": limit
    }
    response = requests.get("https://api.kroger.com/v1/products", headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# search through products

if __name__ == "__main__":
    products = search_products("milk")
    for item in products["data"]:
        print(item["description"], "-", item["items"][0]["price"]["regular"])

def get_product_details(product_id, location_id="01400943"):
    token = get_access_token()
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    params = {"filter.locationId": location_id}
    url = f"https://api.kroger.com/v1/products/{product_id}"
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

details = get_product_details("0001111041700")
print(details["data"]["description"])
'''