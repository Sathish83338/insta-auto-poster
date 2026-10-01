import os
import sys
import json
import time
import requests

IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
GRAPH_API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
POSTS_FILE = "posts.json"

def get_direct_drive_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"

def create_reel_container(video_url: str, caption: str) -> str:
    url = f"{BASE_URL}/{IG_USER_ID}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }
    res = requests.post(url, data=payload).json()
    if "id" not in res:
        print(f"Error creating container: {res}")
        sys.exit(1)
    return res["id"]

def wait_for_encoding(creation_id: str, timeout: int = 240) -> bool:
    url = f"{BASE_URL}/{creation_id}"
    params = {"fields": "status_code", "access_token": ACCESS_TOKEN}
    start = time.time()
    print("Waiting for Instagram video processing...")
    while time.time() - start < timeout:
        res = requests.get(url, params=params).json()
        status = res.get("status_code")
        print(f"Status: {status}")
        if status == "FINISHED":
            return True
        elif status in ["ERROR", "EXPIRED"]:
            print(f"Failed processing: {res}")
            return False
        time.sleep(10)
    return False

def publish_container(creation_id: str) -> str:
    url = f"{BASE_URL}/{IG_USER_ID}/media_publish"
    payload = {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN
    }
    res = requests.post(url, data=payload).json()
    if "id" not in res:
        print(f"Publish failed: {res}")
        sys.exit(1)
    return res["id"]

def main():
    if not IG_USER_ID or not ACCESS_TOKEN:
        print("Missing API credentials.")
        sys.exit(1)

    with open(POSTS_FILE, "r") as f:
        queue = json.load(f)

    target = None
    for item in queue:
        if not item.get("posted", False):
            target = item
            break

    if not target:
        print("All queued videos have already been posted!")
        return

    print(f"Processing File ID: {target['file_id']}")
    video_url = get_direct_drive_url(target["file_id"])
    
    container_id = create_reel_container(video_url, target["caption"])
    if wait_for_encoding(container_id):
        post_id = publish_container(container_id)
        print(f"Success! Post published with ID: {post_id}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
