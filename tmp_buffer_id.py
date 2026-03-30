import requests, os, json
from dotenv import load_dotenv
load_dotenv()
GRAPHQL_URL = os.getenv('GRAPHQL_URL', 'https://api.buffer.com/graphql')
token = os.getenv('LINKEDIN_BUFFER_ACCESS_TOKEN')

query = 'query { account { organizations { channels { id name service } } } }'
res = requests.post(GRAPHQL_URL, json={'query': query}, headers={'Authorization': f'Bearer {token}'})
orgs = res.json().get('data', {}).get('account', {}).get('organizations', [])
cid = [c['id'] for org in orgs for c in org.get('channels', []) if c.get('service') == 'linkedin'][0]

mutation = '''
mutation CreatePost($input: CreatePostInput!) {
    createPost(input: $input) {
        ... on PostActionSuccess {
            post { id externalLink text }
        }
    }
}
'''
variables = {
    'input': {
        'channelId': cid,
        'text': 'Test with id',
        'mode': 'shareNow',
        'schedulingType': 'automatic'
    }
}
res2 = requests.post(GRAPHQL_URL, json={'query': mutation, 'variables': variables}, headers={'Authorization': f'Bearer {token}'})
print(json.dumps(res2.json(), indent=2))
