import sys
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("test_post_output.txt", "w")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        pass
sys.stdout = Logger()

import os
import datetime
from pathlib import Path

def get_test_image_url():
    import requests
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("IMGBB_API_KEY")
    path = Path("test/test.jpeg")
    url = "https://api.imgbb.com/1/upload"
    with open(path, "rb") as f:
        res = requests.post(url, data={"key": api_key}, files={"image": f})
    data = res.json()
    if res.status_code == 200 and data.get("success"):
        return data["data"]["url"]
    else:
        raise Exception("Upload failed")

def test_linkedin(url):
    from backend.linkedin.create_post import LinkedIn
    try:
        p = LinkedIn(f"Test Post with Image linkedin {datetime.datetime.now()}", image_urls=[url])
        print("[LINKEDIN] Link:", p.create_post())
    except Exception as e:
        print(f"[LINKEDIN ERROR] {e}")

def test_instagram(url):
    from backend.instagram.create_post import InstagramPoster
    try:
        p = InstagramPoster(f"Test Post with Image insta {datetime.datetime.now()}", image_urls=[url])
        print("[INSTAGRAM] Link:", p.create_post())
    except Exception as e:
        print(f"[INSTAGRAM ERROR] {e}")

def test_x(url):
    from backend.X.create_post import XPoster
    try:
        p = XPoster(f"Test Post with Image x {datetime.datetime.now()}", image_urls=[url])
        print("[X] Link:", p.create_post())
    except Exception as e:
        print(f"[X ERROR] {e}")

def test_facebook(url):
    from backend.facebook.create_post import FacebookPoster
    try:
        p = FacebookPoster(f"Test Post with Image fb {datetime.datetime.now()}", image_urls=[url])
        print("[FACEBOOK] Link:", p.create_post())
    except Exception as e:
        print(f"[FACEBOOK ERROR] {e}")

if __name__ == "__main__":
    url = get_test_image_url()
    print("Using image URL:", url)
    print("---------------------------------")
    test_linkedin(url)
    test_instagram(url)
    test_x(url)
    test_facebook(url)
