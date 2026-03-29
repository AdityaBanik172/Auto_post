import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("LINKEDIN_FB_BUFFER_ACCESS_TOKEN") or os.getenv("X_INSTA_BUFFER_ACCESS_TOKEN")
url = os.getenv("GRAPHQL_URL", "https://api.buffer.com/graphql")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

def query_type(query_str):
    resp = requests.post(url, json={"query": query_str}, headers=headers, timeout=10)
    return resp.json()

try:
    with open("fields.txt", "w", encoding="utf-8") as f:
        f.write("Introspecting 'PostPublishingError' type fields...\n")
        res = query_type('query { __type(name: "PostPublishingError") { fields { name } } }')
        fields = res.get("data", {}).get("__type", {}).get("fields", [])
        for field in fields:
            f.write(f"- {field['name']}\n")
    print("Introspection complete. Check fields.txt.")
except Exception as e:
    print(f"Error: {e}")
