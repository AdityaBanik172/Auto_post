import requests, os, time, json, random
from dotenv import load_dotenv

load_dotenv()
GRAPHQL_URL = os.getenv('GRAPHQL_URL', 'https://api.buffer.com/graphql')
token = os.getenv('X_INSTA_BUFFER_ACCESS_TOKEN')

query_channels = 'query { account { organizations { channels { id name service } } } }'
res = requests.post(GRAPHQL_URL, json={'query': query_channels}, headers={'Authorization': f'Bearer {token}'})
orgs = res.json().get('data', {}).get('account', {}).get('organizations', [])
cid = [c['id'] for org in orgs for c in org.get('channels', []) if c.get('service') == 'instagram'][0]

imgbb_key = os.getenv('IMGBB_API_KEY')
with open('test/test.jpeg', 'rb') as f:
    upload_res = requests.post("https://api.imgbb.com/1/upload", data={"key": imgbb_key}, files={"image": f})
img_url = upload_res.json()["data"]["url"]

mutation = '''
mutation CreatePost($input: CreatePostInput!) {
    createPost(input: $input) {
        ... on PostActionSuccess {
            post { id externalLink text }
        }
        ... on UnexpectedError { message }
        ... on InvalidInputError { message }
    }
}
'''
variables = {
    'input': {
        'channelId': cid,
        'text': f'Automated poll test {random.randint(10000, 99999)}',
        'mode': 'shareNow',
        'schedulingType': 'automatic',
        'assets': {'images': [{'url': img_url}]},
        'metadata': {'instagram': {'type': 'post', 'shouldShareToFeed': True}}
    }
}
res2 = requests.post(GRAPHQL_URL, json={'query': mutation, 'variables': variables}, headers={'Authorization': f'Bearer {token}'})
post_id = res2.json().get('data', {}).get('createPost', {}).get('post', {}).get('id')
print("Created Post ID:", post_id)
if not post_id:
    exit(1)

for i in range(15):
    rest_res = requests.get(f"https://api.bufferapp.com/1/updates/{post_id}.json", headers={'Authorization': f'Bearer {token}'})
    p = rest_res.json()
    status = p.get('status')
    link = p.get('service_link')
    print(f"Poll {i}: status={status}, link={link}")
    if link:
        print("Success:", link)
        break
    time.sleep(3)
