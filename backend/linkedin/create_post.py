import hashlib
import os
import datetime
import json
import time

import requests
from dotenv import load_dotenv
from .token_refresh import TokenManager

load_dotenv()

_REQUEST_TIMEOUT = 45
_VERBOSE = os.getenv("VERBOSE_BUFFER_LOGS", "").lower() in ("1", "true", "yes")

# Avoid re-fetching channel list on every post (same process)
_channel_cache: dict[str, tuple[str, str]] = {}


def _channel_cache_key(token: str) -> str:
    return hashlib.sha256(("linkedin" + token).encode()).hexdigest()


class LinkedIn:
    def __init__(self, content, assets=None):
        self.content = content
        self.assets = assets or []

        # Buffer token from .env — LinkedIn-specific (LINKEDIN_BUFFER_ACCESS_TOKEN)
        token_manager = TokenManager()
        self.access_token = token_manager.get_valid_token()

        self.graphql_url = os.getenv("GRAPHQL_URL", "https://api.buffer.com/graphql")
        self._http = requests.Session()
        self._http.headers.update(
            {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
        )
        self.channel_id = None
        self.channel_name = None

        self.fetch_channel_id()

    # ------------------------------------------------------------------
    # Core GraphQL helper
    # ------------------------------------------------------------------

    def graphql_query(self, query, variables=None):
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        res = self._http.post(
            self.graphql_url,
            json=payload,
            timeout=_REQUEST_TIMEOUT,
        )
        return res.status_code, res.json()

    # ------------------------------------------------------------------
    # Channel resolution
    # ------------------------------------------------------------------

    def fetch_channel_id(self):
        key = _channel_cache_key(self.access_token)
        if key in _channel_cache:
            self.channel_id, self.channel_name = _channel_cache[key]
            if _VERBOSE:
                print(f"[OK] LINKEDIN: channel {self.channel_name} [{self.channel_id}] (cached)")
            return

        query = """
            query { account { organizations { channels { id name service } } } }
        """
        status, data = self.graphql_query(query)

        orgs = data.get("data", {}).get("account", {}).get("organizations", [])
        for org in orgs:
            channels = org.get("channels", [])
            for channel in channels:
                if channel.get("service") == "linkedin":
                    self.channel_id = channel["id"]
                    self.channel_name = f"{channel['name']} ({channel['service']})"
                    break
            if self.channel_id:
                break

        if not self.channel_id:
            raise Exception("No LinkedIn channel found for the provided LinkedIn token.")

        _channel_cache[key] = (self.channel_id, self.channel_name)
        if _VERBOSE:
            print(f"[OK] LINKEDIN: channel {self.channel_name} [{self.channel_id}]")

    # ------------------------------------------------------------------
    # Fallback URL helper
    # ------------------------------------------------------------------

    def _fallback_url(self) -> str:
        username = self.channel_name.split(" ")[0] if self.channel_name else ""
        if self.channel_name and "Fixfield" in self.channel_name:
            return f"https://www.linkedin.com/company/{username}"
        return "https://www.linkedin.com/feed/"

    # ------------------------------------------------------------------
    # Create post — returns immediately with post_id; link may be None
    # ------------------------------------------------------------------

    def create_post(self):
        mutation = """
        mutation CreateTestPost($input: CreatePostInput!) {
            createPost(input: $input) {
                __typename
                ... on PostActionSuccess {
                    post {
                        id
                        externalLink
                    }
                }
                ... on UnexpectedError {
                    message
                }
                ... on InvalidInputError {
                    message
                }
            }
        }
        """

        variables = {
            "input": {
                "channelId": self.channel_id,
                "text": self.content,
                "mode": "shareNow",
                "schedulingType": "automatic",
            }
        }

        if self.assets:
            variables["input"]["assets"] = {}

            images = [a["url"] for a in self.assets if a["type"] == "image"]
            videos = [a for a in self.assets if a["type"] == "video"]
            docs = [a for a in self.assets if a["type"] == "document"]

            if images:
                variables["input"]["assets"]["images"] = [{"url": url} for url in images]

            if videos:
                variables["input"]["assets"]["video"] = {
                    "url": videos[0]["url"],
                    "title": "Video Post",
                    "thumbnailUrl": videos[0]["thumbnail"],
                }

            if docs:
                variables["input"]["assets"]["documents"] = [
                    {
                        "url": docs[0]["url"],
                        "title": docs[0].get("title", "Document"),
                        "thumbnailUrl": docs[0]["thumbnail"],
                    }
                ]

        status_post, data_post = self.graphql_query(mutation, variables)

        if _VERBOSE:
            print(f"LinkedIn createPost HTTP {status_post}")
            print(json.dumps(data_post, indent=2, ensure_ascii=True))

        if "errors" in data_post:
            error_msgs = [e.get("message", "Unknown error") for e in data_post["errors"]]
            raise Exception("GraphQL Error: " + ", ".join(error_msgs))

        post_result = data_post.get("data", {}).get("createPost", {})
        if post_result.get("__typename") != "PostActionSuccess":
            error_msg = post_result.get("message", "Unknown error creating post")
            raise Exception(f"Buffer API Error: {error_msg}")

        post_data = post_result.get("post", {})
        link = post_data.get("externalLink")
        post_id = post_data.get("id")
        fallback = self._fallback_url()

        if _VERBOSE:
            print(f"[OK] Post created — id={post_id}, immediate link={link!r}")

        # Return immediately; if link is None the caller should poll via get_post_link()
        return {"link": link, "post_id": post_id, "fallback": fallback}

    # ------------------------------------------------------------------
    # Poll Buffer for the externalLink after posting
    # Call this from a dedicated /check-link backend endpoint.
    # ------------------------------------------------------------------

    def get_post_link(
        self,
        post_id: str,
        max_attempts: int = 8,
        delay: float = 3.0,
    ) -> dict:
        """
        Poll Buffer's GraphQL API until externalLink is populated or we give up.

        Args:
            post_id:      The Buffer post ID returned by create_post().
            max_attempts: How many times to check before giving up (default 8).
            delay:        Seconds to wait between attempts (default 3 s).

        Returns:
            {
                "link":     str | None,   # Live LinkedIn URL or None on timeout
                "post_id":  str,
                "fallback": str,          # Profile / feed URL as a safe redirect
            }
        """
        query = """
            query GetPost($id: String!) {
                post(id: $id) {
                    id
                    externalLink
                    status
                }
            }
        """

        fallback = self._fallback_url()

        for attempt in range(1, max_attempts + 1):
            status_code, data = self.graphql_query(query, {"id": post_id})

            if _VERBOSE:
                print(f"[get_post_link] attempt {attempt}/{max_attempts} — HTTP {status_code}")
                print(json.dumps(data, indent=2, ensure_ascii=True))

            if "errors" in data:
                error_msgs = [e.get("message", "Unknown") for e in data["errors"]]
                raise Exception("GraphQL error fetching post: " + ", ".join(error_msgs))

            post = data.get("data", {}).get("post", {})

            # Buffer may return null for the post while it is still processing
            if not post:
                if _VERBOSE:
                    print(f"[get_post_link] post not found yet, retrying...")
                if attempt < max_attempts:
                    time.sleep(delay)
                continue

            link = post.get("externalLink")
            post_status = post.get("status", "")

            if _VERBOSE:
                print(f"[get_post_link] status={post_status!r}, link={link!r}")

            if link:
                return {"link": link, "post_id": post_id, "fallback": None}

            # Terminal failure states — no point retrying
            if post_status in ("failed", "error"):
                raise Exception(f"Buffer post failed with status: {post_status!r}")

            if attempt < max_attempts:
                time.sleep(delay)

        # Exhausted all attempts — return None so the frontend can use the fallback
        if _VERBOSE:
            print(f"[get_post_link] exhausted {max_attempts} attempts, returning fallback")

        return {"link": None, "post_id": post_id, "fallback": fallback}


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    post_content = (
        f"Hello! This is a test post from my custom Buffer API script! "
        f"Time: {datetime.datetime.now()}"
    )
    li = LinkedIn(post_content)

    result = li.create_post()
    print("create_post result:", result)

    if result["post_id"] and not result["link"]:
        print("Link not available yet — polling...")
        poll_result = li.get_post_link(result["post_id"])
        print("get_post_link result:", poll_result)
    else:
        print("Immediate link:", result["link"])