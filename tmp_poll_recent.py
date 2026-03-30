import requests, os, json
from dotenv import load_dotenv

load_dotenv()
GRAPHQL_URL = os.getenv('GRAPHQL_URL', 'https://api.buffer.com/graphql')
token = os.getenv('X_INSTA_BUFFER_ACCESS_TOKEN')

query_channels = 'query { account { organizations { channels { id name service } } } }'
res = requests.post(GRAPHQL_URL, json={'query': query_channels}, headers={'Authorization': f'Bearer {token}'})
orgs = res.json().get('data', {}).get('account', {}).get('organizations', [])
cid = [c['id'] for org in orgs for c in org.get('channels', []) if c.get('service') == 'instagram'][0]

query_recent = '''
query GetChannelPosts($channelId: String!) {
    channel(id: $channelId) {
        id
        ... on InstagramChannel {
            posts {
                edges {
                    node {
                        id
                        externalLink
                    }
                }
            }
        }
    }
}
'''
res2 = requests.post(GRAPHQL_URL, json={'query': query_recent, 'variables': {'channelId': cid}}, headers={'Authorization': f'Bearer {token}'})
print(json.dumps(res2.json(), indent=2))
