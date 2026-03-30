import requests, os, json
from dotenv import load_dotenv

load_dotenv()
GRAPHQL_URL = os.getenv('GRAPHQL_URL', 'https://api.buffer.com/graphql')
token = os.getenv('X_INSTA_BUFFER_ACCESS_TOKEN')

post_id = "69ca5e82aa29a3f595271dd3"
query_post = '''
query GetPost($id: ID!) {
    post(id: $id) {
        id
        status
        externalLink
    }
}
'''
res3 = requests.post(GRAPHQL_URL, json={'query': query_post, 'variables': {'id': post_id}}, headers={'Authorization': f'Bearer {token}'})
print(json.dumps(res3.json(), indent=2))
