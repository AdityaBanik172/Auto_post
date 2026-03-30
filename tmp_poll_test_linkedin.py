import requests, os, time, json, random
from dotenv import load_dotenv

load_dotenv()
GRAPHQL_URL = os.getenv('GRAPHQL_URL', 'https://api.buffer.com/graphql')
token = os.getenv('LINKEDIN_FB_BUFFER_ACCESS_TOKEN')

query_channels = 'query { account { organizations { channels { id name service } } } }'
res = requests.post(GRAPHQL_URL, json={'query': query_channels}, headers={'Authorization': f'Bearer {token}'})
orgs = res.json().get('data', {}).get('account', {}).get('organizations', [])
cid = [c['id'] for org in orgs for c in org.get('channels', []) if c.get('service') == 'linkedin'][0]

img_url = f"https://picsum.photos/500/500?random={random.randint(10000, 99999)}"

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
        'text': f'LinkedIn poll test {random.randint(10000, 99999)}',
        'mode': 'shareNow',
        'schedulingType': 'automatic',
        'assets': {'images': [{'url': img_url}]}
    }
}
print("Publishing to Buffer...")
res2 = requests.post(GRAPHQL_URL, json={'query': mutation, 'variables': variables}, headers={'Authorization': f'Bearer {token}'})
print(json.dumps(res2.json(), indent=2))
post_info = res2.json().get('data', {}).get('createPost', {}).get('post', {})
post_id = post_info.get('id')
ext_link = post_info.get('externalLink')
print(f"Created Post ID: {post_id}, Initial Link: {ext_link}")
if not post_id:
    exit(1)

print("Polling REST API...")
for i in range(15):
    rest_res = requests.get(f"https://api.bufferapp.com/1/updates/{post_id}.json", headers={'Authorization': f'Bearer {token}'})
    p = rest_res.json()
    status = p.get('status')
    service_link = p.get('service_link')
    service_update_id = p.get('service_update_id')
    print(f"Poll {i}: status={status}, link={service_link}, update_id={service_update_id}")
    if service_link:
        print("Success Link:", service_link)
        break
    time.sleep(2)
