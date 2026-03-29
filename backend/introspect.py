import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("LINKEDIN_FB_BUFFER_ACCESS_TOKEN") or os.getenv("X_INSTA_BUFFER_ACCESS_TOKEN")
url = os.getenv("GRAPHQL_URL", "https://api.buffer.com/graphql")

query = """
query {
  __type(name: "CreatePostInput") {
    inputFields {
      name
      type {
        name
        kind
        ofType {
          name
        }
      }
    }
  }
}
"""

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

try:
    resp = requests.post(url, json={"query": query}, headers=headers, timeout=10)
    data = resp.json()
    assets_field = next(f for f in data["data"]["__type"]["inputFields"] if f["name"] == "assets")
    print(json.dumps(assets_field, indent=2))
except Exception as e:
    print(f"Error: {e}")
