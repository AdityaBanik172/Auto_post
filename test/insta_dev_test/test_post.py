import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("INSTA_DEV_API").strip().replace('"', "").replace("'", "")

if ACCESS_TOKEN:
    ACCESS_TOKEN = ACCESS_TOKEN.strip()

if not ACCESS_TOKEN:
    raise ValueError("INSTA_DEV_API not found in .env")

print("RAW TOKEN:", repr(ACCESS_TOKEN))
print("TOKEN LENGTH:", len(ACCESS_TOKEN) if ACCESS_TOKEN else 0)

# ---------------------------------------------------
# STEP 1: Get Facebook Pages connected to the account
# ---------------------------------------------------
pages_url = "https://graph.facebook.com/v19.0/me/accounts"

pages_res = requests.get(
    pages_url,
    params={
        "access_token": ACCESS_TOKEN
    }
)

pages_data = pages_res.json()
print("Pages Response:")
print(pages_data)

if "data" not in pages_data or len(pages_data["data"]) == 0:
    raise Exception("No Facebook Pages found.")

PAGE_ID = pages_data["data"][0]["id"]
print(f"\nUsing Page ID: {PAGE_ID}")

# ---------------------------------------------------
# STEP 2: Get Instagram Business Account ID
# ---------------------------------------------------
ig_url = f"https://graph.facebook.com/v19.0/{PAGE_ID}"

ig_res = requests.get(
    ig_url,
    params={
        "fields": "instagram_business_account",
        "access_token": ACCESS_TOKEN
    }
)

ig_data = ig_res.json()
print("\nInstagram Business Account Response:")
print(ig_data)

if "instagram_business_account" not in ig_data:
    raise Exception(
        "No Instagram Business account linked to this Facebook Page."
    )

IG_USER_ID = ig_data["instagram_business_account"]["id"]
print(f"\nInstagram Business Account ID: {IG_USER_ID}")

# ---------------------------------------------------
# STEP 3: Create media container
# Image URL must be PUBLICLY accessible
# ---------------------------------------------------
IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Placeholder_LC_blue.svg/1200px-Placeholder_LC_blue.svg.png"

CAPTION = "Test post from Instagram Graph API 🚀"

media_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"

media_res = requests.post(
    media_url,
    data={
        "image_url": IMAGE_URL,
        "caption": CAPTION,
        "access_token": ACCESS_TOKEN
    }
)

media_data = media_res.json()

print("\nCreate Media Container Response:")
print(media_data)

if "id" not in media_data:
    raise Exception("Failed to create media container.")

CREATION_ID = media_data["id"]
print(f"\nCreation ID: {CREATION_ID}")

# ---------------------------------------------------
# STEP 4: Publish the post
# ---------------------------------------------------
publish_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"

publish_res = requests.post(
    publish_url,
    data={
        "creation_id": CREATION_ID,
        "access_token": ACCESS_TOKEN
    }
)

publish_data = publish_res.json()

print("\nPublish Response:")
print(publish_data)

if "id" in publish_data:
    print("\n✅ Successfully posted to Instagram!")
else:
    print("\n❌ Failed to publish.")